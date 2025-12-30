from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime, timezone
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
        if v:
            # Make timezone-naive datetime timezone-aware (assume UTC)
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            # Compare with current UTC time
            if v < datetime.now(timezone.utc):
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
        if v:
            # Make timezone-naive datetime timezone-aware (assume UTC)
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            # Compare with current UTC time
            if v < datetime.now(timezone.utc):
                raise ValueError("Due date cannot be in the past")
        return v

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str]
    status: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int

class ErrorResponse(BaseModel):
    detail: str
    status_code: int
