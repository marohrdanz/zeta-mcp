#!/bin/bash

MCP_SESSION_ID=$(curl -L -s -D - -X POST http://localhost:8001/mcp/mcp \
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
  }' | grep "mcp-session-id" | awk '{print $2}' | tr -d '\r')

echo "Using MCP_SESSION_ID: $MCP_SESSION_ID"

## Get all tasks from database
#curl -s -L -X POST http://localhost:8001/mcp/mcp \
#  -H "Accept: application/json, text/event-stream" \
#  -H "Content-Type: application/json" \
#  -H "mcp-session-id: ${MCP_SESSION_ID}" \
#  -d '{
#        "jsonrpc": "2.0",
#        "method": "tools/call",
#        "params": {
#          "name": "get_tasks_tool"
#        },
#        "id": 1
#     }' | grep "^data: " | sed 's/^data: //' | jq

## Add a task
#curl -s -L -X POST http://localhost:8001/mcp/mcp \
#  -H "Accept: application/json, text/event-stream" \
#  -H "Content-Type: application/json" \
#  -H "mcp-session-id: ${MCP_SESSION_ID}" \
#  -d '{
#        "jsonrpc": "2.0",
#        "method": "tools/call",
#        "params": {
#          "name": "create_task_tool",
#          "arguments": {
#            "task": {
#              "title": "MCP tool working",
#              "description": "Testing MCP tool usage",
#              "status": "To Do"
#            }
#          }
#        },
#        "id": 1
#     }'

## Get the version info:
#curl -s -L -X POST http://localhost:8001/mcp/mcp \
#  -H "Accept: application/json, text/event-stream" \
#  -H "Content-Type: application/json" \
#  -H "mcp-session-id: ${MCP_SESSION_ID}" \
#  -d '{
#        "jsonrpc": "2.0",
#        "method": "resources/read",
#        "params": {
#          "uri": "config://version"
#        },
#        "id": 1
#     }' | grep "^data: " | sed 's/^data: //' | jq

curl -s -L -X POST http://localhost:8001/mcp/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: ${MCP_SESSION_ID}" \
  -d '{
        "jsonrpc": "2.0",
        "method": "resources/read",
        "params": {
          "uri": "greetings://sam"
        },
        "id": 1
     }' | grep "^data: " | sed 's/^data: //' | jq

