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
import json

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
            "fourtytwo": "/api/mcp/fourty-two",
            "mcp-tools": "/api/mcp/tools",
            "mcp-resources": "/api/mcp/resources",
            "tasks": "/api/mcp/tasks"
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
        # The tool is expected to return a single text output with "42"
        return {"result": result.content[0].text}
    except Exception as e:
        logger.error(f"Error invoking MCP tool: {e}")
        raise HTTPException(status_code=500, detail="Failed to invoke MCP tool")


@app.get("/api/mcp/tools")
async def list_mcp_tools():
    """List all available MCP tools."""
    logger.debug("Listing MCP tools")
    if not mcp_session:
        raise HTTPException(status_code=503, detail="MCP session not initialized")
    try:
        result = await mcp_session.list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description
                } for tool in result.tools
            ]
        }
    except Exception as e:
        logger.error(f"Error listing MCP tools: {e}")
        raise HTTPException(status_code=500, detail="Failed to list MCP tools")

@app.get("/api/mcp/resources")
async def list_mcp_resources():
    """List all available MCP resources."""
    if not mcp_session:
        raise HTTPException(status_code=503, detail="MCP session not initialized")
    try:
        result = await mcp_session.list_resources()
        logger.debug(f"Resources: {result.resources}")
        return {
                "resources": [
                    {
                        "uri": resource.uri,
                        "name": resource.name
                    } for resource in result.resources
                ]
        }
    except Exception as e:
        logger.error(f"Error listing MCP resources: {e}")
        raise HTTPException(status_code=500, detail="Unable to list MCP resources")

# Add a task
@app.post("/api/tasks")
def create_task(task: Task):
    """Create a new task."""
    logger.debug(f"Creating task: {task}")
    logger.info("Creating task")
    # Here you would add logic to save the task to the database
    return task

@app.get("/api/mcp/tasks")
async def get_tasks():
    """Invoke the MCP tool to get all tasks."""
    logger.debug("Invoking the MCP tool to get all tasks")
    if not mcp_session:
        raise HTTPException(status_code=503, detail="MCP session not initialized")
    try:
        result = await mcp_session.call_tool("get_tasks_tool", arguments={})
        logger.debug(f"Tasks retrieved: {result.content}")
        first_content = result.content[0] # should only be one text output returned
        text_data = first_content.text

        return JSONResponse(content=json.loads(text_data))
    except Exception as e:
        logger.error(f"Error invoking MCP tool: {e}")
        raise HTTPException(status_code=500, detail="Failed to invoke MCP tool")
