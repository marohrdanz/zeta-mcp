from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import Task
from schemas import TaskCreate, TaskUpdate
from typing import Optional, List
from datetime import datetime, timezone

class TaskCRUD:
    """CRUD operations for tasks"""
    
    @staticmethod
    async def create_task(db: AsyncSession, task_data: TaskCreate) -> Task:
        """Create a new task"""
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status.value if task_data.status else "To Do",
            due_date=task_data.due_date
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def get_task(db: AsyncSession, task_id: int) -> Optional[Task]:
        """Get a task by ID"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_tasks(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> tuple[List[Task], int]:
        """Get all tasks with optional filtering"""
        query = select(Task)
        
        if status:
            query = query.where(Task.status == status)
        
        # Get total count
        count_query = select(func.count(Task.id))
        if status:
            count_query = count_query.where(Task.status == status)
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return list(tasks), total
    
    @staticmethod
    async def update_task(
        db: AsyncSession, 
        task_id: int, 
        task_data: TaskUpdate
    ) -> Optional[Task]:
        """Update a task"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        # Update fields if provided
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.status is not None:
            task.status = task_data.status.value
        if task_data.due_date is not None:
            task.due_date = task_data.due_date
        
        task.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(task)
        return task
    
    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int) -> bool:
        """Delete a task"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if not task:
            return False
        
        await db.delete(task)
        await db.commit()
        return True
