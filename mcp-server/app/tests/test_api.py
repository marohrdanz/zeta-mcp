import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
class TestTaskAPI:
    """Test cases for Task API endpoints"""
    
    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "task-manager"
    
    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    async def test_create_task_success(self, client, sample_task_data):
        """Test creating a task successfully"""
        response = await client.post("/api/tasks", json=sample_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task_data["title"]
        assert data["description"] == sample_task_data["description"]
        assert data["status"] == sample_task_data["status"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    async def test_create_task_minimal(self, client, sample_task_data_minimal):
        """Test creating a task with minimal data"""
        response = await client.post("/api/tasks", json=sample_task_data_minimal)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task_data_minimal["title"]
        assert data["status"] == "To Do"
        assert data["description"] is None
    
    async def test_create_task_missing_title(self, client):
        """Test creating a task without title (should fail)"""
        response = await client.post("/api/tasks", json={
            "description": "Task without title"
        })
        assert response.status_code == 422  # Validation error
    
    async def test_create_task_empty_title(self, client):
        """Test creating a task with empty title (should fail)"""
        response = await client.post("/api/tasks", json={
            "title": ""
        })
        assert response.status_code == 422  # Validation error
    
    async def test_create_task_past_due_date(self, client):
        """Test creating a task with past due date (should fail)"""
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        response = await client.post("/api/tasks", json={
            "title": "Task with past due date",
            "due_date": past_date
        })
        assert response.status_code == 422  # Validation error
    
    async def test_get_tasks_empty(self, client):
        """Test getting tasks when database is empty"""
        response = await client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total"] == 0
    
    async def test_get_tasks_with_data(self, client, sample_task_data):
        """Test getting tasks after creating some"""
        # Create tasks
        await client.post("/api/tasks", json=sample_task_data)
        await client.post("/api/tasks", json={
            "title": "Second Task",
            "status": "In Progress"
        })
        
        response = await client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total"] == 2
    
    async def test_get_tasks_with_pagination(self, client):
        """Test pagination of tasks"""
        # Create multiple tasks
        for i in range(5):
            await client.post("/api/tasks", json={
                "title": f"Task {i+1}"
            })
        
        # Get first 2 tasks
        response = await client.get("/api/tasks?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total"] == 5
        
        # Get next 2 tasks
        response = await client.get("/api/tasks?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 2
        assert data["total"] == 5
    
    async def test_get_tasks_filter_by_status(self, client):
        """Test filtering tasks by status"""
        await client.post("/api/tasks", json={
            "title": "Todo Task",
            "status": "To Do"
        })
        await client.post("/api/tasks", json={
            "title": "In Progress Task",
            "status": "In Progress"
        })
        await client.post("/api/tasks", json={
            "title": "Done Task",
            "status": "Done"
        })
        
        # Filter by "In Progress"
        response = await client.get("/api/tasks?status=In%20Progress")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["status"] == "In Progress"
        assert data["total"] == 1
    
    async def test_get_task_by_id_success(self, client, sample_task_data):
        """Test getting a specific task by ID"""
        # Create a task
        create_response = await client.post("/api/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Get the task
        response = await client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == sample_task_data["title"]
    
    async def test_get_task_by_id_not_found(self, client):
        """Test getting a non-existent task"""
        response = await client.get("/api/tasks/99999")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    async def test_update_task_success(self, client, sample_task_data):
        """Test updating a task"""
        # Create a task
        create_response = await client.post("/api/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Update the task
        update_data = {
            "title": "Updated Task",
            "status": "Done"
        }
        response = await client.put(f"/api/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["status"] == update_data["status"]
        assert data["description"] == sample_task_data["description"]  # Unchanged
    
    async def test_update_task_partial(self, client, sample_task_data):
        """Test partial update of a task"""
        # Create a task
        create_response = await client.post("/api/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Update only the status
        response = await client.put(f"/api/tasks/{task_id}", json={
            "status": "In Progress"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "In Progress"
        assert data["title"] == sample_task_data["title"]  # Unchanged
    
    async def test_update_task_not_found(self, client):
        """Test updating a non-existent task"""
        response = await client.put("/api/tasks/99999", json={
            "title": "Updated Task"
        })
        assert response.status_code == 404
    
    async def test_update_task_invalid_title(self, client, sample_task_data):
        """Test updating a task with empty title"""
        # Create a task
        create_response = await client.post("/api/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Try to update with empty title
        response = await client.put(f"/api/tasks/{task_id}", json={
            "title": ""
        })
        assert response.status_code == 422
    
    async def test_delete_task_success(self, client, sample_task_data):
        """Test deleting a task"""
        # Create a task
        create_response = await client.post("/api/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Delete the task
        response = await client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204
        
        # Verify task is deleted
        get_response = await client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 404
    
    async def test_delete_task_not_found(self, client):
        """Test deleting a non-existent task"""
        response = await client.delete("/api/tasks/99999")
        assert response.status_code == 404
    
    async def test_complete_workflow(self, client):
        """Test a complete workflow: create, read, update, delete"""
        # Create a task
        create_data = {
            "title": "Workflow Test Task",
            "description": "Testing complete workflow",
            "status": "To Do"
        }
        create_response = await client.post("/api/tasks", json=create_data)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Read the task
        get_response = await client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 200
        
        # Update the task
        update_response = await client.put(f"/api/tasks/{task_id}", json={
            "status": "Done"
        })
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "Done"
        
        # Delete the task
        delete_response = await client.delete(f"/api/tasks/{task_id}")
        assert delete_response.status_code == 204
        
        # Verify deletion
        verify_response = await client.get(f"/api/tasks/{task_id}")
        assert verify_response.status_code == 404
