from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[TaskStatus] = Field(TaskStatus.TODO, description="Task status")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Due date cannot be in the past")
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v and v < datetime.now():
            raise ValueError("Due date cannot be in the past")
        return v

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int

class ErrorResponse(BaseModel):
    detail: str
    status_code: int
