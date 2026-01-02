from fastmcp import FastMCP
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

mcp = FastMCP("Task Manager")
logger = log_setup.configure_logging('DEBUG')

@mcp.tool
def return_fourty_two() -> float:
    """Return the number 42"""
    logger.debug("Return fourty two tool invoked")
    return 42

@mcp.tool
async def create_task_tool(task: TaskCreate) -> dict:
    """MCP Tool: Create a new task"""
    logger.info("Creating task: MCP tool")
    async with async_session_maker() as db:
        task_data = await TaskCRUD.create_task(db, task)
        return task_data.to_dict()

@mcp.tool
async def get_tasks_tool() -> dict:
    """MCP Tool: get all tasks from database"""
    logger.info("Getting all tasks from database with MCP tool")
    try:
        async with async_session_maker() as db:
            tasks, total = await TaskCRUD.get_tasks(db)
            task_responses = [TaskResponse(**task.to_dict()) for task in tasks]
            task_list = TaskListResponse(tasks=task_responses, total=total)
            logger.debug(f"Retrieved tasks successfully: {task_list.model_dump()}")
            return task_list.model_dump()
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise Exception(f"Failed to retrieve tasts: {e}")

@mcp.resource("config://version")
def get_version() -> dict:
    """Provides the app's configuration"""
    logger.debug("version resource invoked")
    return {"version": "3.0", "name": "Task Manager"}

@mcp.resource("greetings://{name}")
def greet(name: str) -> str:
    """Generate a personalized greeting"""
    logger.debug("greeting resource invoked")
    return f"Hello, {name}! Welcome to the task manager."

