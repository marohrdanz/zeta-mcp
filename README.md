# Learning MCP

This repository is for me to learn the Model Context Protocol (MCP) by building a
simple task manager application. This application uses an MCP (FastMCP), an
API server (FastAPI), language model (Anthropic Claude) to manage tasks, and
a postgreSQL database to store tasks. I haven't (yet) built a web interface, so
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
is availabe at http://localhost:8004/docs.

## Work-in-Progress usage

I don't yet have a web interface. So interactions are via API calls. Here are some
examples (see above-mentioned FastAPI docs for more):

**List all the MCP tools:**

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


The final resonse from this type of POST is similar to:

```text
I've created the task \"Finish the report\" with a note that it's due next Friday. Since today
appears to be January 5, 2026, next Friday would be January 9, 2026. Would you like me to update
the task with the specific due date of January 9, 2026?
```

Since I don't yet have a web interface, you can't respond directly to the LLM's
follow-up question. But you can see the newly created task in the database:

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
