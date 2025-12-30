# Task Manager API

A RESTful API for managing tasks with PostgreSQL backend, built using FastAPI and the Model Context Protocol (MCP).

## Features

- **CRUD Operations**: Create, Read, Update, and Delete tasks
- **Task Management**: Each task has a title, description, status, and due date
- **Database Persistence**: PostgreSQL database for reliable data storage
- **Input Validation**: Comprehensive validation with meaningful error messages
- **RESTful API**: Standard HTTP methods and status codes
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Docker Support**: Easy deployment with Docker Compose
- **Testing**: Comprehensive test suite included

## Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.10+ and PostgreSQL 13+

### Option 1: Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/marohrdanz/zeta-mcp.git
cd zeta-mcp
```

2. Start the services:
```bash
docker-compose up -d
```

3. The API will be available at `http://localhost:8001`

4. Access the interactive API documentation at `http://localhost:8001/docs`

### Option 2: Local Development

1. Clone the repository:
```bash
git clone https://github.com/marohrdanz/zeta-mcp.git
cd zeta-mcp
```

2. Create a virtual environment and install dependencies:
```bash
cd app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up PostgreSQL database:
```bash
# Install PostgreSQL if not already installed
# Then create a database
createdb taskmanager
```

4. Configure environment variables:
```bash
cp ../.env.example .env
# Edit .env with your database credentials
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

## Database Configuration

The application uses environment variables for database configuration:

```bash
DATABASE_URL=postgresql+asyncpg://taskuser:taskpass@localhost:5432/taskmanager
```

### Environment Variables

Create a `.env` file in the project root (see `.env.example` for template):

- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_USER`: PostgreSQL username (for Docker Compose)
- `POSTGRES_PASSWORD`: PostgreSQL password (for Docker Compose)
- `POSTGRES_DB`: PostgreSQL database name (for Docker Compose)

### Database Schema

The database schema is managed by SQLAlchemy. The main `tasks` table includes:

- `id`: Primary key (auto-increment)
- `title`: Task title (required, max 200 characters)
- `description`: Task description (optional)
- `status`: Task status (default: "To Do")
- `due_date`: Task due date (optional)
- `created_at`: Timestamp when task was created
- `updated_at`: Timestamp when task was last updated

### Database Management

Initialize or reset the database:

```bash
# Initialize database (creates tables)
python app/init_db.py

# Reset database (WARNING: deletes all data)
python app/init_db.py --reset
```

## API Endpoints

### Base URL

- Local: `http://localhost:8001`
- Docker: `http://localhost:8001`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API information |
| GET | `/health` | Health check endpoint |
| GET | `/docs` | Interactive API documentation (Swagger UI) |
| GET | `/redoc` | Alternative API documentation (ReDoc) |
| POST | `/api/tasks` | Create a new task |
| GET | `/api/tasks` | Get all tasks (with pagination and filtering) |
| GET | `/api/tasks/{id}` | Get a specific task by ID |
| PUT | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |

## API Usage Examples

### 1. Create a Task

**Request:**
```bash
curl -X POST http://localhost:8001/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive README and API docs",
    "status": "To Do",
    "due_date": "2025-12-31T23:59:59"
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "title": "Complete project documentation",
  "description": "Write comprehensive README and API docs",
  "status": "To Do",
  "due_date": "2025-12-31T23:59:59",
  "created_at": "2025-12-30T10:00:00",
  "updated_at": "2025-12-30T10:00:00"
}
```

### 2. Get All Tasks

**Request:**
```bash
curl http://localhost:8001/api/tasks
```

**With pagination and filtering:**
```bash
# Get 10 tasks, skip first 0, filter by status
curl "http://localhost:8001/api/tasks?skip=0&limit=10&status=To%20Do"
```

**Response (200 OK):**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Complete project documentation",
      "description": "Write comprehensive README and API docs",
      "status": "To Do",
      "due_date": "2025-12-31T23:59:59",
      "created_at": "2025-12-30T10:00:00",
      "updated_at": "2025-12-30T10:00:00"
    }
  ],
  "total": 1
}
```

### 3. Get a Specific Task

**Request:**
```bash
curl http://localhost:8001/api/tasks/1
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Complete project documentation",
  "description": "Write comprehensive README and API docs",
  "status": "To Do",
  "due_date": "2025-12-31T23:59:59",
  "created_at": "2025-12-30T10:00:00",
  "updated_at": "2025-12-30T10:00:00"
}
```

### 4. Update a Task

**Request:**
```bash
curl -X PUT http://localhost:8001/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "In Progress"
  }'
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Complete project documentation",
  "description": "Write comprehensive README and API docs",
  "status": "In Progress",
  "due_date": "2025-12-31T23:59:59",
  "created_at": "2025-12-30T10:00:00",
  "updated_at": "2025-12-30T10:05:00"
}
```

### 5. Delete a Task

**Request:**
```bash
curl -X DELETE http://localhost:8001/api/tasks/1
```

**Response (204 No Content):**
```
(empty response body)
```

## Task Status Values

Tasks can have one of the following status values:

- `To Do` - Task has not been started
- `In Progress` - Task is currently being worked on
- `Done` - Task has been completed

## Validation Rules

### Task Creation/Update

- **Title**: Required, 1-200 characters
- **Description**: Optional, any length
- **Status**: Optional, must be one of: "To Do", "In Progress", "Done"
- **Due Date**: Optional, must be in the future (cannot be a past date)

### Error Responses

The API returns appropriate HTTP status codes and error messages:

- `200 OK` - Successful GET/PUT request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Validation error (e.g., empty title, past due date)
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Request validation error
- `500 Internal Server Error` - Server error

**Example Error Response:**
```json
{
  "detail": "Due date cannot be in the past",
  "status_code": 400
}
```

## Testing

### Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
cd app
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=html
```

### Test Coverage

The test suite includes:

- Health check and root endpoint tests
- Task creation with various inputs
- Task retrieval (single and list)
- Task updates (full and partial)
- Task deletion
- Pagination and filtering
- Edge cases and error scenarios
- Complete workflow tests

## Model Context Protocol (MCP)

This application also includes MCP (Model Context Protocol) functionality:

### MCP Server

The MCP server is available at `/mcp` and provides:

- **Tools**: Calculator operations (add, multiply)
- **Resources**: Version info and greetings

### Using MCP

To run the MCP development server:

```bash
fastmcp dev server.py 
```

Then visit http://localhost:6274/ for the MCP dashboard.

Alternatively, run:

```bash
fastmcp run --transport=http --host=0.0.0.0 --port=8001 server.py
```

And use curl commands as documented in the [MCP section](README.md#mcp-usage).

## Project Structure

```
zeta-mcp/
├── app/
│   ├── server.py           # Main application and API endpoints
│   ├── database.py         # Database configuration and models
│   ├── schemas.py          # Pydantic models for validation
│   ├── crud.py             # CRUD operations
│   ├── init_db.py          # Database initialization script
│   ├── log_setup.py        # Logging configuration
│   ├── requirements.txt    # Python dependencies
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py     # Test fixtures
│       └── test_api.py     # API tests
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker image definition
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Development

### Code Style

The project follows Python best practices:

- PEP 8 style guide
- Type hints where applicable
- Comprehensive docstrings
- Async/await patterns for database operations

### Adding New Features

1. Update database models in `database.py`
2. Update Pydantic schemas in `schemas.py`
3. Implement CRUD operations in `crud.py`
4. Add API endpoints in `server.py`
5. Write tests in `tests/test_api.py`
6. Update documentation in README.md

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:

1. Verify PostgreSQL is running:
```bash
docker-compose ps
```

2. Check database logs:
```bash
docker-compose logs postgres
```

3. Verify environment variables in `.env` file

### Port Already in Use

If port 8001 is already in use:

1. Change the port in `docker-compose.yml`
2. Or stop the conflicting service:
```bash
lsof -ti:8001 | xargs kill
```

### Database Reset

To reset the database and start fresh:

```bash
# Using Docker Compose
docker-compose down -v
docker-compose up -d

# Or manually
python app/init_db.py --reset
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Database ORM: [SQLAlchemy](https://www.sqlalchemy.org/)
- MCP support: [FastMCP](https://github.com/jlowin/fastmcp)
- Testing: [pytest](https://pytest.org/)

## Contact

For issues and questions, please open an issue on GitHub.

