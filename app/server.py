from fastmcp import FastMCP
from fastapi import FastAPI
from contextlib import asynccontextmanager
import log_setup as log_setup
import logging

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
    async with mcp_app.lifespan(app):
        logger.info("MCP server starting up")
        yield
        logger.info("MCP server shutting down")
    logger.info("Server shutting down...")

app = FastAPI(lifespan=lifespan)

app.mount("/mcp", mcp_app)

@app.get("/")
def read_root():
    return {"message": "Hello World!"}

