# FastAPI service

Example usage:

```bash
curl -X POST http://localhost:8004/api/tasks \
     -H "Content-Type: application/json" \
     -d '{
	   "title": "Simple Task",
	   "description": "This is a simple task description.",
	   "status": "To Do"
	 }'
```
