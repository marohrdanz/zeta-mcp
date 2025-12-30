from fastmcp import FastMCP
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import log_setup as log_setup
import logging
import os

# Import database and models
from database import get_db, init_db, async_session_maker
from schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, 
    ErrorResponse, TaskStatus
)
from crud import TaskCRUD

mcp = FastMCP("My Calculator")
logger = log_setup.configure_logging('DEBUG')

@mcp.tool
def adds(a: int, b: int) -> int:
    """Add two numbers together"""
    logger.debug("adds tool invoked")
    return a + b

@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    logger.debug("multiply tool invoked")
    return a * b

@mcp.tool
def return_four() -> float:
    """Return the number 4"""
    logger.debug("Return four tool invoked")
    return 4

@mcp.tool
async def create_task_tool(task: TaskCreate) -> dict:
    """MCP Tool: Create a new task"""
    logger.info("Creating task: mcp tool")
    async with async_session_maker() as db:
        task_data = await TaskCRUD.create_task(db, task)
        return task_data.to_dict()

@mcp.tool
async def get_tasks_tool() -> dict:
    """MCP Tool: get all tasks from database"""
    logger.info("Getting all tasks from database")
    try:
        async with async_session_maker() as db:
            tasks, total = await TaskCRUD.get_tasks(db)
            task_responses = [TaskResponse(**task.to_dict()) for task in tasks]
            return TaskListResponse(tasks=task_responses, total=total)
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")

@mcp.resource("config://version")
def get_version() -> dict:
    """Provides the app's configuration"""
    logger.debug("version resource invoked")
    return {"version": "2.0", "name": "Calculator"}

@mcp.resource("greetings://{name}")
def greet(name: str) -> str:
    """Generate a personalized greeting"""
    logger.debug("greeting resource invoked")
    return f"Hello, {name}! Welcome to the calculator."

mcp_app = mcp.http_app()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global logger
    logger.info("Server starting up...")
    
    # Initialize database (skip if in test mode)
    if not os.getenv("TESTING", "false").lower() == "true":
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async with mcp_app.lifespan(app):
        logger.info("MCP server starting up")
        yield
        logger.info("MCP server shutting down")
    logger.info("Server shutting down...")

app = FastAPI(
    title="Task Manager API",
    description="A RESTful API for managing tasks with PostgreSQL backend",
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/mcp", mcp_app)

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
    return {
        "message": "Task Manager API",
        "version": "1.0.0",
        "endpoints": {
            "tasks": "/api/tasks",
            "health": "/health",
            "mcp": "/mcp"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "task-manager"}

# Task API endpoints
@app.post(
    "/api/tasks",
    response_model=TaskResponse,
    status_code=201,
    responses={
        201: {"description": "Task created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new task.
    
    - **title**: Task title (required, 1-200 characters)
    - **description**: Task description (optional)
    - **status**: Task status (optional, defaults to "To Do")
    - **due_date**: Task due date (optional, must be in the future)
    """
    try:
        logger.info(f"Creating task: {task.title}")
        new_task = await TaskCRUD.create_task(db, task)
        return TaskResponse(**new_task.to_dict())
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@app.get(
    "/api/tasks",
    response_model=TaskListResponse,
    responses={
        200: {"description": "Tasks retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of tasks to return"),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all tasks with optional filtering and pagination.
    
    - **skip**: Number of tasks to skip (for pagination)
    - **limit**: Maximum number of tasks to return (1-1000)
    - **status**: Filter by task status (optional)
    """
    try:
        logger.info(f"Retrieving tasks: skip={skip}, limit={limit}, status={status}")
        status_value = status.value if status else None
        tasks, total = await TaskCRUD.get_tasks(db, skip=skip, limit=limit, status=status_value)
        task_responses = [TaskResponse(**task.to_dict()) for task in tasks]
        return TaskListResponse(tasks=task_responses, total=total)
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")

@app.get(
    "/api/tasks/{task_id}",
    response_model=TaskResponse,
    responses={
        200: {"description": "Task retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific task by ID.
    
    - **task_id**: The ID of the task to retrieve
    """
    try:
        logger.info(f"Retrieving task: {task_id}")
        task = await TaskCRUD.get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        return TaskResponse(**task.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task")

@app.put(
    "/api/tasks/{task_id}",
    response_model=TaskResponse,
    responses={
        200: {"description": "Task updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing task.
    
    - **task_id**: The ID of the task to update
    - **title**: New task title (optional)
    - **description**: New task description (optional)
    - **status**: New task status (optional)
    - **due_date**: New task due date (optional, must be in the future)
    """
    try:
        logger.info(f"Updating task: {task_id}")
        updated_task = await TaskCRUD.update_task(db, task_id, task)
        if not updated_task:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        return TaskResponse(**updated_task.to_dict())
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@app.delete(
    "/api/tasks/{task_id}",
    status_code=204,
    responses={
        204: {"description": "Task deleted successfully"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a task.
    
    - **task_id**: The ID of the task to delete
    """
    try:
        logger.info(f"Deleting task: {task_id}")
        success = await TaskCRUD.delete_task(db, task_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")


