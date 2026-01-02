from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
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

# Global MCP session variable
mcp_session = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage MCP client lifecycle."""
    global mcp_session
    mcp_server_url = "http://mcp-server:8001/sse"
    logger.info(f"Connecting to MCP server at {mcp_server_url}")
    print(f"Connecting to MCP server at {mcp_server_url}")
    try:
        async with sse_client(mcp_server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_session = session
                logger.info("MCP clent session initialized")
                #tools = await session.list_tools()
                #logger.info(f"Available tools: {[tool.name for tool in tools]}")

                yield # FastAPI runs while this context is active

                logger.info("Shutting down MCP client session")
    except Exception as e:
        logger.error(f"Failed to connect to MCP server: {e}")
        yield # start anyways, but endpoints fail gracefully

    logger.info("MCP client session closed")
    mcp_session = None

app = FastAPI(
    title="Task Manager API",
    description="A RESTful API for managing tasks with PostgreSQL backend",
    version="1.0.0",
    lifespan=lifespan
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
            "value-error": "/value-error",
            "tasks": "/api/tasks",
            "mcp-tools": "/api/mcp/tools"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check endpoint accessed")
    mcp_status = "connected" if mcp_session else "disconnected"
    return {
        "status": "healthy",
        "service": "task-manager",
        "mcp_status": mcp_status
    }

@app.get("/api/mcp/fourty-two")
async def get_fourty_two():
    """Invoke the MCP tool to return the number 42."""
    logger.debug("Invoking the MCP tool to get 42")
    if not mcp_session:
        raise HTTPException(status_code=503, detail="MCP session not initialized")
    try:
        result = await mcp_session.call_tool("return_fourty_two", arguments={})
        return {"result": result.content}
    except Exception as e:
        logger.error(f"Error invoking MCP tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invoke MCP tool: {e}")


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
