"""
Database models and setup for the test question generation system.
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid

Base = declarative_base()

# Association tables for many-to-many relationship between questions and tags
question_tags = Table(
    'question_tags',
    Base.metadata,
    Column('question_id', Integer, ForeignKey('question_staging.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

actual_question_tags = Table(
    'actual_question_tags',
    Base.metadata,
    Column('question_id', Integer, ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Run(Base):
    """Run/Session information - Step 1"""
    __tablename__ = 'runs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    summary = Column(Text, nullable=False)  # Summary provided by user in step 1
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = Column(DateTime, nullable=True)  # Last time staging was synced to actual tables
    last_staging_change_at = Column(DateTime, nullable=True)  # Last time any staging table (questions/answers/tags) was modified
    
    # Relationships
    questions = relationship("QuestionStaging", back_populates="run", cascade="all, delete-orphan")
    answers = relationship("AnswerStaging", back_populates="run", cascade="all, delete-orphan")
    actual_questions = relationship("Question", back_populates="run", cascade="all, delete-orphan")
    actual_answers = relationship("Answer", back_populates="run", cascade="all, delete-orphan")


class QuestionStaging(Base):
    """Staging table for generated questions - Step 2 & 3"""
    __tablename__ = 'question_staging'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id', ondelete='CASCADE'), nullable=False)
    question_text = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=None, nullable=True)  # None = pending, True = approved, False = rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    run = relationship("Run", back_populates="questions")
    answers = relationship("AnswerStaging", back_populates="question", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=question_tags, back_populates="questions")


class AnswerStaging(Base):
    """Staging table for generated answers - Step 4 & 5"""
    __tablename__ = 'answer_staging'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id', ondelete='CASCADE'), nullable=False)
    question_id = Column(Integer, ForeignKey('question_staging.id', ondelete='CASCADE'), nullable=False)
    answer_text = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=None, nullable=True)  # None = pending, True = approved, False = rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    run = relationship("Run", back_populates="answers")
    question = relationship("QuestionStaging", back_populates="answers")


class Question(Base):
    """Actual question table - moved from staging after approval"""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id', ondelete='CASCADE'), nullable=False)
    staging_id = Column(Integer, nullable=True)  # Reference to original staging question ID
    question_text = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=True, nullable=False)  # True if question has approved answer, False otherwise
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    run = relationship("Run", back_populates="actual_questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=actual_question_tags, back_populates="actual_questions")


class Answer(Base):
    """Actual answer table - moved from staging after approval"""
    __tablename__ = 'answers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id', ondelete='CASCADE'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    staging_id = Column(Integer, nullable=True)  # Reference to original staging answer ID
    answer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    run = relationship("Run", back_populates="actual_answers")
    question = relationship("Question", back_populates="answers")


class Tag(Base):
    """Tag table for categorizing questions - shared between staging and actual"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)  # Tag name must be unique
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = relationship("QuestionStaging", secondary=question_tags, back_populates="tags")
    actual_questions = relationship("Question", secondary=actual_question_tags, back_populates="tags")


# Database setup
DATABASE_URL = "sqlite:///./test_questions.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables and applying migrations."""
    Base.metadata.create_all(bind=engine)
    
    # Migration: Add last_sync_at and last_staging_change_at columns to runs table if they don't exist
    from sqlalchemy import text
    with engine.begin() as conn:
        # Check if columns exist by querying table info
        result = conn.execute(text("PRAGMA table_info(runs)"))
        columns = [row[1] for row in result]
        
        if 'last_sync_at' not in columns:
            try:
                conn.execute(text("ALTER TABLE runs ADD COLUMN last_sync_at DATETIME"))
                print("Added last_sync_at column to runs table")
            except Exception as e:
                # Column might have been added by another process
                print(f"Note: Could not add last_sync_at column (may already exist): {e}")
        
        if 'last_staging_change_at' not in columns:
            try:
                conn.execute(text("ALTER TABLE runs ADD COLUMN last_staging_change_at DATETIME"))
                print("Added last_staging_change_at column to runs table")
            except Exception as e:
                # Column might have been added by another process
                print(f"Note: Could not add last_staging_change_at column (may already exist): {e}")
        
        # Migration: Add is_approved column to questions table if it doesn't exist
        result = conn.execute(text("PRAGMA table_info(questions)"))
        columns = [row[1] for row in result]
        
        if 'is_approved' not in columns:
            try:
                conn.execute(text("ALTER TABLE questions ADD COLUMN is_approved BOOLEAN DEFAULT 1"))
                print("Added is_approved column to questions table")
            except Exception as e:
                print(f"Note: Could not add is_approved column (may already exist): {e}")


def get_db():
    """Dependency function for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

