"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RunCreate(BaseModel):
    """Request model for creating a run"""
    summary: str


class RunResponse(BaseModel):
    """Response model for run"""
    id: str
    summary: str
    created_at: datetime
    updated_at: datetime
    last_sync_at: Optional[datetime] = None
    last_staging_change_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    """Response model for question"""
    id: int
    run_id: str
    question_text: str
    is_approved: Optional[bool]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuestionUpdate(BaseModel):
    """Request model for updating question approval status"""
    is_approved: bool


class AnswerResponse(BaseModel):
    """Response model for answer"""
    id: int
    run_id: str
    question_id: int
    answer_text: str
    is_approved: Optional[bool]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnswerUpdate(BaseModel):
    """Request model for updating answer approval status"""
    is_approved: bool


class TagResponse(BaseModel):
    """Response model for tag"""
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuestionTagsUpdate(BaseModel):
    """Request model for updating question tags"""
    tag_names: List[str]  # List of tag names to associate with the question


class QuestionActualResponse(BaseModel):
    """Response model for actual question with tags"""
    id: int
    run_id: str
    staging_id: Optional[int]
    question_text: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []
    
    class Config:
        from_attributes = True


class AnswerActualResponse(BaseModel):
    """Response model for actual answer"""
    id: int
    run_id: str
    question_id: int
    staging_id: Optional[int]
    answer_text: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuestionWithAnswerResponse(BaseModel):
    """Response model for actual question with answer and tags"""
    id: int
    run_id: str
    staging_id: Optional[int]
    question_text: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []
    answer: Optional[AnswerActualResponse] = None
    
    class Config:
        from_attributes = True

