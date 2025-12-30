# Basic MCP tutorial

This is just me poking around in a basic tutorial on
Model Context Protocol.

To run the dev server:

```bash
fastmcp dev server.py 
```

then visti http://localhost:6274/ for a dashboard.

Althernatively, run:

```bash
fastmcp run --transport=http --host=0.0.0.0 --port=8001 server.py
```

And use curl commands like the following:

First collect the mcp-session-id header from:


```bash
curl -s -D - -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "curl-client",
        "version": "1.0.0"
      }
    },
    "id": 1
  }'
```

Then use it to, for example, list tools. The gymnatics to pipe to `jq`
is because the output format is Server-Sent Events (SSE):

```bash
curl -s -L -X POST http://localhost:8001/mcp/ \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: ${MCP_SESSION_ID}" \
  -d '{
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1
     }' | grep "^data: " | sed 's/^data: //' | jq
```

Or invoke the add tool:

```bash
curl -s -L -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: ${MCP_SESSION_ID}" \
  -d '{
          "jsonrpc": "2.0",
          "method": "tools/call",
          "params": {
              "name": "adds",
              "arguments": {
                  "a": 5,
                  "b": 3
               }
           },
           "id":2
        }' | grep "^data: " | sed 's/^data: //' | jq
```

Or the version resource:

```bash
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: ${MCP_SESSION_ID}" \
  -d '{
         "jsonrpc": "2.0",
         "method": "resources/read",
         "params": {
              "uri": "config://version"
         },
         "id": 3
       }' | grep "^data: " | sed 's/^data: //' | jq
```

Or the greeting resource:

```bash
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: ${MCP_SESSION_ID}" \
  -d '{
         "jsonrpc": "2.0",
         "method": "resources/read",
         "params": {
              "uri": "greetings://Susan"
         },
         "id": 3
       }'
```
