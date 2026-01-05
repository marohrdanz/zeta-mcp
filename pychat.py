import asyncio
import websockets
import json
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

console = Console()

## Instead of making a web intterface, I made a simple command-line
## interface to interact with the WebSocket API.
##
## Usage;
##
##   python pychat.py

async def chat():
    """Connect to the WebSocket server and handle sending and receiving messages."""

    uri = "ws://localhost:8004/ws/chat"
    async with websockets.connect(uri) as websocket:
        console.print("[bold green]Connected to the chat server![/bold green]")
        console.print(Panel.fit("Type your messages below. Type 'exit' to quit.",
            title="Chat Instructions", border_style="blue"))


        async def send_messages():
            """Send user input messages to the websocket server."""
            loop = asyncio.get_event_loop()
            while True:
                # Use run_in_executor to get user input w/o blocking event loop
                user_input = await loop.run_in_executor(None, input, ">> ")
                if user_input.lower() == "exit":
                    console.print("[yellow]Bye![/yellow]")
                    await websocket.close()
                    break
                await websocket.send(json.dumps({"role": "user", "message": user_input}))

        async def receive_messages():
            """Receive messages from websocket and print them."""
            try:
                while True:
                    response = await websocket.recv()
                    try:
                        data = json.loads(response)
                        if data["type"] == "tool_use":
                            console.print()
                            console.print(Panel.fit(
                                f"Tool Used: {data['tool_name']}\nInput: {json.dumps(data['tool_input'], indent=2)}",
                                title="Tool Use",
                                border_style="yellow"
                            ))
                        elif data["type"] == 'tool_result':
                            console.print()
                            console.print(Panel.fit(
                                f"Result: {data['result']}", 
                                title="Tool Result", 
                                border_style="blue"
                            ))
                        elif data["type"] == 'response':
                            console.print()
                            console.print(Panel.fit(
                                f"{data['message']}", 
                                title="Assistant", 
                                border_style="green"
                            ))
                        elif data["type"] == 'error':
                            console.print()
                            console.print(Panel.fit(
                                f"{data['message']}", 
                                title="Error", 
                                border_style="red"
                            ))
                    except json.JSONDecodeError:
                        console.print("[red]Received non-JSON response:[/red]")
                        console.print(response)
        
            except websockets.exceptions.ConnectionClosed:
                console.print("[red]Connection closed by the server.[/red]")

        await asyncio.gather(
            send_messages(),
            receive_messages()
        )



asyncio.run(chat())
