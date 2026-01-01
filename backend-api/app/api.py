from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager
import anthropic
from mcp import ClientSession, StdioServerParameters
from enum import Enum

import log_setup as log_setup
import logging

logger = log_setup.configure_logging('DEBUG')

class TaskStatus(str, Enum):
    """Defines task status enumeration."""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"

class Task(BaseModel):
    """Defines a Task model."""
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[TaskStatus] = Field(TaskStatus.TODO, description="Task status")
    due_date: Optional[datetime] = Field(None, description="Task due date")

app = FastAPI(
    title="Task Manager API",
    description="A RESTful API for managing tasks with PostgreSQL backend",
    version="1.0.0"
)

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "status_code": 400}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint providing API information."""
    logger.debug("Root endpoint accessed")
    return {
        "message": "Task Manager API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "value-error": "/value-error"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy", "service": "task-manager"}

# Add a task
@app.post("/api/tasks")
def create_task(task: Task):
    """Create a new task."""
    logger.debug(f"Creating task: {task}")
    logger.info("Creating task")
    # Here you would add logic to save the task to the database
    return task

@app.get("/value-error")
async def trigger_value_error():
    """Raise a ValueError for testing purposes."""
    logger.debug("Triggering ValueError for testing")
    return await value_error_handler(None, ValueError("This is a test ValueError"))
