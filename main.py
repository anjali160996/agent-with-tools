"""
FastAPI backend for test question generation workflow.
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
import os

from database import init_db, get_db, Run, QuestionStaging, AnswerStaging, Tag, question_tags, Question, Answer, actual_question_tags
from models import (
    RunCreate, RunResponse, QuestionResponse, QuestionUpdate,
    AnswerResponse, AnswerUpdate, TagResponse, QuestionTagsUpdate,
    QuestionActualResponse, AnswerActualResponse, QuestionWithAnswerResponse
)
from llm_service import LLMService

app = FastAPI(title="Test Question Generation API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    # Serve index.html at root
    @app.get("/")
    async def read_root():
        from fastapi.responses import FileResponse
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Static files not found"}

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Initialize LLM service (will raise error if API key not set)
try:
    llm_service = LLMService()
except Exception as e:
    llm_service = None
    print(f"Warning: LLM service initialization failed: {e}")


# ==================== Step 1: Create Run ====================
@app.post("/api/runs", response_model=RunResponse)
def create_run(run_data: RunCreate, db: Session = Depends(get_db)):
    """Step 1: Create a new run/session with summary"""
    db_run = Run(
        summary=run_data.summary,
        last_staging_change_at=datetime.datetime.utcnow()  # Set initial staging change time
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run


@app.get("/api/runs", response_model=List[RunResponse])
def get_all_runs(db: Session = Depends(get_db)):
    """Get all runs/sessions"""
    runs = db.query(Run).order_by(Run.created_at.desc()).all()
    return runs


@app.get("/api/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get run details"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# ==================== Step 2: Generate Questions ====================
@app.post("/api/runs/{run_id}/generate-questions", response_model=List[QuestionResponse])
def generate_questions(run_id: str, num_questions: int = 5, db: Session = Depends(get_db)):
    """Step 2: Generate questions using LLM and save to staging table"""
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized. Please check OPENAI_API_KEY.")
    
    # Verify run exists
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        # Generate questions using LLM
        questions_text = llm_service.generate_questions(run.summary, num_questions)
        
        # Save questions to staging table (append to existing)
        questions = []
        for question_text in questions_text:
            db_question = QuestionStaging(
                run_id=run_id,
                question_text=question_text,
                is_approved=None  # Pending approval
            )
            db.add(db_question)
            questions.append(db_question)
        
        db.commit()
        
        # Refresh all questions
        for q in questions:
            db.refresh(q)
        
        return questions
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@app.get("/api/runs/{run_id}/questions", response_model=List[QuestionResponse])
def get_questions(run_id: str, db: Session = Depends(get_db)):
    """Get all questions for a run"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    questions = db.query(QuestionStaging).filter(QuestionStaging.run_id == run_id).all()
    return questions


# ==================== Step 3: Approve/Reject Questions ====================
@app.patch("/api/questions/{question_id}/approval", response_model=QuestionResponse)
def update_question_approval(question_id: int, update: QuestionUpdate, db: Session = Depends(get_db)):
    """Step 3: Update question approval status. If question is rejected, delete all its associated answers."""
    question = db.query(QuestionStaging).filter(QuestionStaging.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    question.is_approved = update.is_approved
    question.updated_at = datetime.datetime.utcnow()
    
    # If question is marked as rejected, delete all its answers
    if update.is_approved == False:
        answers = db.query(AnswerStaging).filter(AnswerStaging.question_id == question_id).all()
        for answer in answers:
            db.delete(answer)
    
    # Update last_staging_change_at on the run
    run = db.query(Run).filter(Run.id == question.run_id).first()
    if run:
        run.last_staging_change_at = datetime.datetime.utcnow()
        run.updated_at = datetime.datetime.utcnow()
    
    db.commit()
    db.refresh(question)
    return question


# ==================== Step 4: Generate Answers ====================
@app.post("/api/runs/{run_id}/generate-answers", response_model=List[AnswerResponse])
def generate_answers(run_id: str, db: Session = Depends(get_db)):
    """Step 4: Generate answers for approved questions using LLM"""
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service not initialized. Please check OPENAI_API_KEY.")
    
    # Verify run exists
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get all approved questions
    approved_questions = db.query(QuestionStaging).filter(
        QuestionStaging.run_id == run_id,
        QuestionStaging.is_approved == True
    ).all()
    
    if not approved_questions:
        raise HTTPException(status_code=400, detail="No approved questions found for this run")
    
    try:
        answers = []
        for question in approved_questions:
            # Check if answer already exists
            existing_answers = db.query(AnswerStaging).filter(
                AnswerStaging.question_id == question.id
            ).all()
            
            # Check if there's a non-rejected answer (pending or approved)
            has_non_rejected_answer = any(
                ans.is_approved is not False for ans in existing_answers
            )
            
            # Only generate if no non-rejected answer exists
            if has_non_rejected_answer:
                # Skip if answer exists and is not rejected (i.e., pending or approved)
                continue
            
            # Delete all existing answers for this question (if any - they're all rejected)
            for existing_answer in existing_answers:
                db.delete(existing_answer)
            
            # Generate answer using LLM
            answer_text = llm_service.generate_answer(question.question_text, run.summary)
            
            # Save answer to staging table
            db_answer = AnswerStaging(
                run_id=run_id,
                question_id=question.id,
                answer_text=answer_text,
                is_approved=None  # Pending approval
            )
            db.add(db_answer)
            answers.append(db_answer)
        
        db.commit()
        
        # Refresh all answers
        for a in answers:
            db.refresh(a)
        
        return answers
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generating answers: {str(e)}")


@app.get("/api/runs/{run_id}/answers", response_model=List[AnswerResponse])
def get_answers(run_id: str, db: Session = Depends(get_db)):
    """Get all answers for a run"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    answers = db.query(AnswerStaging).filter(AnswerStaging.run_id == run_id).all()
    return answers


# ==================== Step 5: Approve/Reject Answers ====================
@app.patch("/api/answers/{answer_id}/approval", response_model=AnswerResponse)
def update_answer_approval(answer_id: int, update: AnswerUpdate, db: Session = Depends(get_db)):
    """Step 5: Update answer approval status"""
    answer = db.query(AnswerStaging).filter(AnswerStaging.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    answer.is_approved = update.is_approved
    answer.updated_at = datetime.datetime.utcnow()
    
    # Update last_staging_change_at on the run
    run = db.query(Run).filter(Run.id == answer.run_id).first()
    if run:
        run.last_staging_change_at = datetime.datetime.utcnow()
        run.updated_at = datetime.datetime.utcnow()
    
    db.commit()
    db.refresh(answer)
    
    return answer


# ==================== Step 6: Tag Questions ====================
@app.get("/api/tags", response_model=List[TagResponse])
def get_all_tags(db: Session = Depends(get_db)):
    """Get all available tags"""
    tags = db.query(Tag).order_by(Tag.name).all()
    return tags


@app.get("/api/questions/{question_id}/tags", response_model=List[TagResponse])
def get_question_tags(question_id: int, db: Session = Depends(get_db)):
    """Get all tags for a specific question"""
    question = db.query(QuestionStaging).filter(QuestionStaging.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return question.tags


@app.put("/api/questions/{question_id}/tags", response_model=List[TagResponse])
def update_question_tags(question_id: int, update: QuestionTagsUpdate, db: Session = Depends(get_db)):
    """Step 6: Update tags for a question (create tags if they don't exist)"""
    question = db.query(QuestionStaging).filter(QuestionStaging.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    try:
        # Clear existing tags
        question.tags = []
        
        # Process each tag name
        tag_objects = []
        for tag_name in update.tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            
            # Check if tag exists, if not create it
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()  # Flush to get the tag ID
            
            tag_objects.append(tag)
        
        # Associate tags with question
        question.tags = tag_objects
        question.updated_at = datetime.datetime.utcnow()
        
        # Update last_staging_change_at on the run
        run = db.query(Run).filter(Run.id == question.run_id).first()
        if run:
            run.last_staging_change_at = datetime.datetime.utcnow()
            run.updated_at = datetime.datetime.utcnow()
        
        db.commit()
        
        # Refresh to get updated tags
        db.refresh(question)
        return question.tags
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating question tags: {str(e)}")


# ==================== Step 7: Sync Staging to Actual Tables ====================
@app.post("/api/runs/{run_id}/sync-to-actual")
def sync_to_actual(run_id: str, db: Session = Depends(get_db)):
    """Step 7: Sync approved questions and answers from staging to actual tables"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        # Get all approved questions and answers from staging
        approved_questions = db.query(QuestionStaging).filter(
            QuestionStaging.run_id == run_id,
            QuestionStaging.is_approved == True
        ).all()
        
        approved_answers = db.query(AnswerStaging).filter(
            AnswerStaging.run_id == run_id,
            AnswerStaging.is_approved == True
        ).all()
        
        # Create sets for quick lookup
        approved_staging_question_ids = {q.id for q in approved_questions}
        approved_staging_answer_ids = {a.id for a in approved_answers}
        
        # Determine which approved questions have approved answers (only sync these)
        approved_questions_with_answers = set()
        for staging_a in approved_answers:
            if staging_a.question_id in approved_staging_question_ids:
                approved_questions_with_answers.add(staging_a.question_id)
        
        # Create a map of staging question ID to actual question (for existing questions)
        staging_to_actual_question = {}
        actual_questions_by_staging_id = db.query(Question).filter(
            Question.run_id == run_id,
            Question.staging_id.isnot(None)
        ).all()
        for aq in actual_questions_by_staging_id:
            staging_to_actual_question[aq.staging_id] = aq
        
        # Track sync statistics
        questions_synced = 0  # Count questions that were newly synced or changed approval status
        
        # Process ALL approved questions (create/update them, but set is_approved flag based on whether they have approved answers)
        for staging_q in approved_questions:
            # Check if question already exists in actual table
            actual_q = staging_to_actual_question.get(staging_q.id)
            
            previous_approved_state = actual_q.is_approved if actual_q else None
            new_approved_state = (staging_q.id in approved_questions_with_answers)
            
            if actual_q:
                # Update existing question (preserves ID)
                actual_q.question_text = staging_q.question_text
                actual_q.updated_at = datetime.datetime.utcnow()
                
                # Check if tags changed
                existing_tag_ids = {tag.id for tag in actual_q.tags}
                staging_tag_ids = {tag.id for tag in staging_q.tags}
                tags_changed = existing_tag_ids != staging_tag_ids
                
                # Count if approval status changed OR tags changed
                if previous_approved_state != new_approved_state or tags_changed:
                    questions_synced += 1
            else:
                # Create new question
                actual_q = Question(
                    run_id=run_id,
                    staging_id=staging_q.id,
                    question_text=staging_q.question_text,
                    is_approved=new_approved_state
                )
                db.add(actual_q)
                db.flush()  # Flush to get the ID
                staging_to_actual_question[staging_q.id] = actual_q
                # Count new questions that are approved (have approved answers)
                if new_approved_state:
                    questions_synced += 1
            
            # Set is_approved flag: True if question has approved answer, False otherwise
            actual_q.is_approved = new_approved_state
            
            # Sync tags (clear and re-add)
            actual_q.tags = []
            for tag in staging_q.tags:
                actual_q.tags.append(tag)
        
        # Process answers - only sync if BOTH question AND answer are approved
        for staging_a in approved_answers:
            # Check if both question and answer are approved
            if staging_a.question_id not in approved_staging_question_ids:
                # Question is not approved, skip this answer
                continue
            
            # Find the corresponding actual question (question exists - created/updated above)
            actual_q = staging_to_actual_question.get(staging_a.question_id)
            
            if actual_q and actual_q.id:  # Only process if question exists (will have approved answer)
                # Check if answer already exists
                existing_answer = db.query(Answer).filter(
                    Answer.run_id == run_id,
                    Answer.question_id == actual_q.id,
                    Answer.staging_id == staging_a.id
                ).first()
                
                if existing_answer:
                    # Update existing answer
                    existing_answer.answer_text = staging_a.answer_text
                    existing_answer.updated_at = datetime.datetime.utcnow()
                else:
                    # Create new answer
                    new_answer = Answer(
                        run_id=run_id,
                        question_id= actual_q.id,
                        staging_id=staging_a.id,
                        answer_text=staging_a.answer_text
                    )
                    db.add(new_answer)
        
        # Update is_approved flag for questions that are no longer approved in staging
        # Get all actual questions for this run
        all_actual_questions = db.query(Question).filter(Question.run_id == run_id).all()
        
        for actual_q in all_actual_questions:
            if actual_q.staging_id:
                previous_state = actual_q.is_approved
                # Set is_approved to False if question is not approved in staging, or doesn't have approved answer
                if actual_q.staging_id not in approved_staging_question_ids:
                    # Question was rejected in staging - mark as unapproved
                    if previous_state is True:  # Only count if it was previously approved
                        questions_synced += 1
                    actual_q.is_approved = False
                    actual_q.updated_at = datetime.datetime.utcnow()
                elif actual_q.staging_id not in approved_questions_with_answers:
                    # Question is approved but doesn't have approved answer - mark as unapproved
                    if previous_state is True:  # Only count if it was previously approved
                        questions_synced += 1
                    actual_q.is_approved = False
                    actual_q.updated_at = datetime.datetime.utcnow()
                # Note: Questions that have approved answers already had is_approved set to True above
        
        # Delete answers that are no longer approved or whose question is not approved
        # Get all actual answers for this run
        all_actual_answers = db.query(Answer).filter(Answer.run_id == run_id).all()
        
        for actual_a in all_actual_answers:
            # Remove answer if:
            # 1. Answer's staging ID is not in approved answers, OR
            # 2. Answer's question staging ID is not in approved questions
            should_delete = False
            if actual_a.staging_id and actual_a.staging_id not in approved_staging_answer_ids:
                should_delete = True
            
            # Check if the question for this answer is still approved
            if actual_a.question_id:
                actual_q = db.query(Question).filter(Question.id == actual_a.question_id).first()
                if actual_q and actual_q.staging_id and actual_q.staging_id not in approved_staging_question_ids:
                    should_delete = True
            
            if should_delete:
                db.delete(actual_a)
        
        # Update last_sync_at
        run.last_sync_at = datetime.datetime.utcnow()
        run.updated_at = datetime.datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Sync completed successfully",
            "last_sync_at": run.last_sync_at.isoformat(),
            "questions_synced": questions_synced
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error syncing to actual tables: {str(e)}")


# ==================== View Actual Questions ====================
@app.get("/api/actual/questions", response_model=List[QuestionWithAnswerResponse])
def get_actual_questions(run_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Get all actual questions with tags and answers (optionally filtered by run_id). Only returns approved questions."""
    query = db.query(Question).filter(Question.is_approved == True)  # Only show approved questions
    if run_id:
        query = query.filter(Question.run_id == run_id)
    
    questions = query.order_by(Question.created_at.desc()).all()
    
    result = []
    for q in questions:
        # Get answer for this question
        answer = db.query(Answer).filter(Answer.question_id == q.id).first()
        
        # Build response
        question_data = {
            "id": q.id,
            "run_id": q.run_id,
            "staging_id": q.staging_id,
            "question_text": q.question_text,
            "is_approved": q.is_approved,
            "created_at": q.created_at,
            "updated_at": q.updated_at,
            "tags": [TagResponse(id=tag.id, name=tag.name, created_at=tag.created_at) for tag in q.tags],
            "answer": None
        }
        
        if answer:
            question_data["answer"] = AnswerActualResponse(
                id=answer.id,
                run_id=answer.run_id,
                question_id=answer.question_id,
                staging_id=answer.staging_id,
                answer_text=answer.answer_text,
                created_at=answer.created_at,
                updated_at=answer.updated_at
            )
        
        result.append(QuestionWithAnswerResponse(**question_data))
    
    return result


# Health check endpoint
@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

