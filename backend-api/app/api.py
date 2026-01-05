from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from enum import Enum
import json
import pprint
from os import getenv

import log_setup as log_setup
import logging

logger = log_setup.configure_logging()

anthropic_client = anthropic.Anthropic()

class ChatRequest(BaseModel):
    """Defines the chat request model."""
    message: str = Field(..., description="The user's message to the chatbot")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None, description="Optional conversation history"
    )

class ChatResponse(BaseModel):
    """Defines the chat response model."""
    response: str = Field(..., description="The chatbot's response message")
    conversation_history: List[Dict[str, str]] = Field(
        ..., description="Updated conversation history including the latest exchange"
    )

## define MCP tools for claude
MCP_TOOLS = [
    {
        "name": "return_fourty_two",
        "description": "Returns the number 42",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "create_task_tool",
        "description": "Create a new task witha title, and optional description, status, and due date",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 1, "maxLength": 200},
                        "description": {"type": "string"},
                        "status": {"type": "string", "enum": ["To Do", "In Progress", "Done"]},
                        "due_date": {"type": "string", "format": "date-time"}
                    },
                    "required": ["title"]
                }
            },
            "required": ["task"]
        }
    }
]

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
@app.post("/api/mcp/tasks")
async def create_task(task: Task):
    """Create a new task."""
    logger.debug(f"Creating task: {task.title}")
    logger.debug(f"  with description: {task.description}")
    if not mcp_session:
        raise HTTPException(status_code=503, detail="MCP session not initialized")
    try:
        result = await mcp_session.call_tool("create_task_tool",
            arguments={
                "task": {
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "due_date": task.due_date.isoformat() if task.due_date else None
                }
            }
        )
        if result.isError:
            error_content = result.content[0].text if result.content else "Unknown error"
            logger.error(f"MCP tool returned error: {error_content}")
            if "validation error" in error_content.lower():
                raise HTTPException(status_code=422, detail={
                    "type": "validation_error",
                    "message": error_content
                })
            raise HTTPException(status_code=500, detail="MCP tool error during task creation")
        logger.debug(f"Task creation result: {result.content}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invoking MCP tool to create task: {e}")
        raise HTTPException(status_code=500, detail="Failed to invoke MCP tool to create task")
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

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint that uses Clause to interact with MCP tools.

    Request body:
    {
        "message": "Create a task to buy groceries",
        "conversation_history": [] # Optional
    }
    """
    if not mcp_session:
        raise HTTPException(status_code=503, detail="MCP session not initialized")
    try:
        # Build prompt for Claude
        messages = request.conversation_history or []
        messages.append({
            "role": "user",
            "content": request.message
        })
        response = anthropic_client.messages.create(
            model=getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
            max_tokens=4096,
            tools=MCP_TOOLS,
            messages=messages
        )
        # process tool calls in a loop
        while response.stop_reason == "tool_use":
            # Extract tool use from response
            tool_use_block = next(
                block for block in response.content if block.type == "tool_use"
            )
            # Call the requested MCP tool
            tool_result = await execute_mcp_tool(
                tool_use_block.name,
                tool_use_block.input
            )
            # Add assistant's response and tool result to messages
            messages.append({
                "role": "assistant",
                "content": [block.model_dump() for block in response.content]
            })
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": tool_result
                    }
                ]
            })
            # Get new response from Claude
            response = anthropic_client.messages.create(
                model=getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
                max_tokens=4096,
                tools=MCP_TOOLS,
                messages=messages
            )
        # Extract final response from Claude
        final_response = next(
            (block for block in response.content if hasattr(block, "text")),
            "I've completed your request."
        )
        fun_response = {
            "response": final_response.text,
            "conversation_history": messages + [{"role": "assistant", "content": response.content[0].text}]
        }
        logger.info(f"Chat response: \n{json.dumps(fun_response, indent=2)}")

        return JSONResponse(content={
            "response": final_response.text,
            "conversation_history": messages + [{"role": "assistant", "content": response.content[0].text}]
        })

    except Exception as e:
        logger.error(f"Error during chat interaction: {e}")
        raise HTTPException(status_code=500, detail="Chat interaction failed")

async def execute_mcp_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Helper function to execute an MCP tool and return the result as a string."""
    if not mcp_session:
        raise HTTPException(status_code=503, detail="MCP session not initialized")
    try:
        # Map tool names to MCP tool names
        tool_mapping = {
            "return_fourty_two_tool": "return_fourty_two_tool",
            "create_task_tool": "create_task_tool"
        }
        mcp_tool_name = tool_mapping.get(tool_name)
        if not mcp_tool_name:
            logger.error(f"Unknown tool requested {tool_name}")
            return "Unknown tool requested."
        if tool_name == "return_fourty_two_tool":
            result = await mcp_session.call_tool(mcp_tool_name, arguments={})
        elif tool_name == "create_task_tool":
            logger.debug(f"Executing create_task_tool with input: {tool_input}")
#            arguments={
#                "task": {
#                    "title": tool_input.task["title"],
#                    "description": tool_input.get("description"),
#                    "status": tool_input.get("status")
#                }
#            }
            #logger.debug(f"create_task_tool arguments: {arguments}")
            result = await mcp_session.call_tool(
                mcp_tool_name,
                arguments=tool_input
            )
            logger.debug(f"create_task_tool result: {result}")
        else:
            logger.error(f"Tool {tool_name} not implemented in execute_mcp_tool")
            return "Tool not implemented."

        if result.isError:
            error_content = result.content[0].text if result.content else "Unknown error"
            logger.error(f"MCP tool returned error: {error_content}")
            return f"Error executing tool {tool_name}: {error_content}"

        logger.debug(f"Tool {tool_name} executed successfully with result: {result.content}")
        return result.content[0].text if result.content else "No content returned from tool."
    except Exception as e:
        logger.error(f"Error executing MCP tool {tool_name}: {e}")
        return f"Exception occurred while executing tool {tool_name}."











