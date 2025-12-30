import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncConnection
from sqlalchemy.pool import StaticPool
import sys
import os

# Set testing mode
os.environ["TESTING"] = "true"

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import app
from database import Base, get_db

# Test database URL (using in-memory SQLite for tests)
# Use StaticPool to share the same in-memory database across connections
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine with StaticPool to share the in-memory database
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Create test session maker
test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Create database tables before each test and clean up after."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Override the dependency
    async def _get_test_db():
        async with test_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = _get_test_db
    
    yield
    
    # Clean up
    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "status": "To Do",
        "due_date": "2025-12-31T23:59:59"
    }

@pytest.fixture
def sample_task_data_minimal():
    """Minimal sample task data for testing."""
    return {
        "title": "Minimal Task"
    }
