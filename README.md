# Learning MCP

This repository is for me to learn the Model Context Protocol (MCP) by building a
simple task manager application. This application uses an MCP (FastMCP), an
API server (FastAPI), language model (Anthropic Claude) to manage tasks, and
a PostgreSQL database to store tasks. I haven't (yet) built a web interface, so
interactions, even the chat ones, are via API calls.


## Initial Setup

```bash
docker compose build
docker compose up
```

The only required env is the `ANTHROPIC_API_KEY`, but you can also set:

- `ANTHROPIC_MODEL`
- `LOG_LEVEL`


Once the system is running, the automatically generated FastAPI documentation
is available at http://localhost:8004/docs.

I don't yet have a web interface, just a WebSocket API and a RESTful API.

## WebSocket API Example Usage

The WebSocket API accepts JSON (in anticipation of a web interface). So
it's not the most user-friendly experience with tools like [wscat](https://www.npmjs.com/package/wscat).

To make it more bearable, I wrote a simple python script to connect with the WebSocket API
and allow you to type messages in a more user-friendly way. You can find it at `pychat.py` in the root of this repo.

Here's some example interactions:

NOTE: Claude is sometimes slow to respond, so you may have to wait a few seconds for the responses to come back.

```bash
$ python3 pychat.py
Connected to the chat server!
╭────────────── Chat Instructions ───────────────╮
│ Type your messages below. Type 'exit' to quit. │
╰────────────────────────────────────────────────╯
>> Hi! Can you add a task to buy berries?
>> 
╭───────── Tool Use ──────────╮
│ Tool Used: create_task_tool │
│ Input: {                    │
│   "task": {                 │
│     "title": "Buy berries"  │
│   }                         │
│ }                           │
╰─────────────────────────────╯

╭────────────────────────────────────────────────────────────────────────────────── Tool Result ──────────────────────────────────────────────────────────────────────────────────╮
│ Result: {"id":62,"title":"Buy berries","description":null,"status":"To Do","due_date":null,"created_at":"2026-01-05T22:03:05.238914","updated_at":"2026-01-05T22:03:05.238919"} │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────── Assistant ───────────────────────────────────────────────╮
│ Done! I've added a task "Buy berries" to your list. The task has been created with a status of "To Do". │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────╯

>> Can you add a task to wash the car before next Saturday?
>> 
╭────────────── Tool Use ───────────────╮
│ Tool Used: create_task_tool           │
│ Input: {                              │
│   "task": {                           │
│     "title": "Wash the car",          │
│     "due_date": "2026-01-10T23:59:59" │
│   }                                   │
│ }                                     │
╰───────────────────────────────────────╯

╭─────────────────────────────────────────────────────────────────────────────────────────── Tool Result ───────────────────────────────────────────────────────────────────────────────────────────╮
│ Result: {"id":63,"title":"Wash the car","description":null,"status":"To Do","due_date":"2026-01-10T23:59:59","created_at":"2026-01-05T22:03:39.236930","updated_at":"2026-01-05T22:03:39.236935"} │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────────────────────────────────── Assistant ────────────────────────────────────────────────────────────────────────────╮
│ Done! I've added a task "Wash the car" with a due date of January 10th, 2026 (next Friday, before Saturday). The task has been created with a status of "To Do". │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

>> Could you list all the existing tasks?
>> 
╭────────────────────────────────────────────────────────────────────────────────── Assistant ───────────────────────────────────────────────────────────────────────────────────╮
│ I don't have a tool available to list or retrieve existing tasks. I can only create new tasks with the `create_task_tool`.                                                     │
│                                                                                                                                                                                │
│ From our conversation, I know I've created these two tasks for you:                                                                                                            │
│ 1. "Buy berries" (ID: 62, Status: To Do)                                                                                                                                       │
│ 2. "Wash the car" (ID: 63, Status: To Do, Due: January 10th, 2026)                                                                                                             │
│                                                                                                                                                                                │
│ But I'm unable to show you a complete list of all tasks that might exist in your system. You would need to check your task management interface directly to see the full list. │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

exit
Bye!
Connection closed by the server.
```

## RESTful API Example Useage

Here are a few REST examples (see above-mentioned FastAPI docs for more):

**List all the MCP tools:**

Invokes the MCP tools endpoint to list all available tools.

```bash
$ curl -s http://localhost:8004/api/mcp/tools | jq .
{
  "tools": [
    {
      "name": "return_fourty_two",
      "description": "Return the number 42"
    },
    {
      "name": "create_task_tool",
      "description": "MCP Tool: Create a new task"
    },
    {
      "name": "get_tasks_tool",
      "description": "MCP Tool: get all tasks from database"
    }
  ]
}
```

**List all tasks in the database:**

Invokes the MCP tool `get_tasks_tool` to retrieve all tasks from the PostgreSQL database.

```bash
$ curl -s http://localhost:8004/api/mcp/tasks | jq .
{
  "tasks": [
    {
      "id": 40,
      "title": "Clean the garage",
      "description": null,
      "status": "To Do",
      "due_date": null,
      "created_at": "2026-01-05T15:53:59.960202",
      "updated_at": "2026-01-05T15:53:59.960203"
    },
...
  ]
}
```

**Create a new task via the chat endpoint:**

This invokes an LLM to interpret the request and use the appropriate MCP tool to create
the task:

```bash
$ curl -s -X POST http://localhost:8044/api/chat \
    -H "Content-Type: application/json" \
    -d '{
       "messages": "Could you please create a new task to finish the report by next Friday?"
    }' | jq .
```


The final response from this type of POST is similar to:

```text
I've created the task \"Finish the report\" with a note that it's due next Friday.
Since today appears to be January 5, 2026, next Friday would be January 9, 2026.
Would you like me to update the task with the specific due date of January 9, 2026?
```

With HTTP requests, it's a bit clunky to respond to the LLM's follow-up question.
But you can see the newly created task in the database:

```bash
$ curl -s http://localhost:8004/api/mcp/tasks | jq .

...
    {
      "id": 41,
      "title": "Finish the report",
      "description": "Due by next Friday",
      "status": "To Do",
      "due_date": null,
      "created_at": "2026-01-05T16:14:37.251711",
      "updated_at": "2026-01-05T16:14:37.251714"
    },

...
```

