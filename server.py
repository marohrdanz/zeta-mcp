from fastmcp import FastMCP

mcp = FastMCP("My Calculator")

@mcp.tool
def adds(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

@mcp.resource("config://version")
def get_version() -> dict:
    """Provides the app's configuration"""
    return {"version": "1.0", "name": "Calculator"}

@mcp.resource("greetings://{name}")
def greet(name: str) -> str:
    """Generate a personalized greeting"""
    return f"Hello, {name}! Welcome to the calculator."

if __name__ == "__main__":
    mcp.run()

