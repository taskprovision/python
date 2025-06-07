"""
Tests for the TaskManager class
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from taskprovision.core.task_manager import (
    TaskManager,
    Task,
    TaskStatus,
    TaskPriority,
    TaskDependency
)

@pytest.fixture
def task_manager():
    """Create a TaskManager instance for testing"""
    return TaskManager()

@pytest.fixture
def sample_task():
    """Create a sample task for testing"""
    return Task(
        title="Test Task",
        description="This is a test task",
        priority=TaskPriority.MEDIUM,
        due_date=datetime.utcnow() + timedelta(days=7)
    )

@pytest.mark.asyncio
async def test_create_task(task_manager, sample_task):
    """Test creating a task"""
    task = await task_manager.create_task(
        title=sample_task.title,
        description=sample_task.description,
        priority=sample_task.priority,
        due_date=sample_task.due_date
    )
    
    assert task.id is not None
    assert task.title == sample_task.title
    assert task.status == TaskStatus.TODO
    assert task.priority == sample_task.priority
    assert task.due_date == sample_task.due_date
    
    # Verify task was added to the manager
    retrieved = await task_manager.get_task(task.id)
    assert retrieved == task

@pytest.mark.asyncio
async def test_update_task(task_manager):
    """Test updating a task"""
    task = await task_manager.create_task("Original Title", "Original Description")
    
    # Update the task
    updated = await task_manager.update_task(
        task.id,
        title="Updated Title",
        description="Updated Description",
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH
    )
    
    assert updated.title == "Updated Title"
    assert updated.description == "Updated Description"
    assert updated.status == TaskStatus.IN_PROGRESS
    assert updated.priority == TaskPriority.HIGH
    assert updated.updated_at > task.updated_at
    
    # Verify the update is reflected in the manager
    retrieved = await task_manager.get_task(task.id)
    assert retrieved.title == "Updated Title"

@pytest.mark.asyncio
async def test_delete_task(task_manager):
    """Test deleting a task"""
    task = await task_manager.create_task("Task to delete", "Will be deleted")
    
    # Delete the task
    result = await task_manager.delete_task(task.id)
    assert result is True
    
    # Verify the task is gone
    assert await task_manager.get_task(task.id) is None
    
    # Try to delete non-existent task
    assert await task_manager.delete_task("non-existent-id") is False

@pytest.mark.asyncio
async def test_list_tasks(task_manager):
    """Test listing tasks with filters"""
    # Create test tasks
    task1 = await task_manager.create_task("Task 1", status=TaskStatus.TODO, assignee="user1")
    task2 = await task_manager.create_task("Task 2", status=TaskStatus.IN_PROGRESS, assignee="user1")
    task3 = await task_manager.create_task("Task 3", status=TaskStatus.DONE, assignee="user2")
    
    # Test listing all tasks
    all_tasks = await task_manager.list_tasks()
    assert len(all_tasks) == 3
    
    # Test filtering by status
    in_progress = await task_manager.list_tasks(status=TaskStatus.IN_PROGRESS)
    assert len(in_progress) == 1
    assert in_progress[0].id == task2.id
    
    # Test filtering by assignee
    user2_tasks = await task_manager.list_tasks(assignee="user2")
    assert len(user2_tasks) == 1
    assert user2_tasks[0].id == task3.id

@pytest.mark.asyncio
async def test_task_dependencies(task_manager):
    """Test task dependencies"""
    # Create tasks
    task1 = await task_manager.create_task("Task 1")
    task2 = await task_manager.create_task("Task 2")
    
    # Add dependency
    result = await task_manager.add_dependency(
        task_id=task2.id,
        depends_on_id=task1.id,
        description="Task 2 depends on Task 1"
    )
    assert result is True
    
    # Verify dependency was added
    task2_updated = await task_manager.get_task(task2.id)
    assert len(task2_updated.dependencies) == 1
    assert task2_updated.dependencies[0].task_id == task1.id
    
    # Test getting blocked tasks
    blocked = await task_manager.get_blocked_tasks()
    assert len(blocked) == 1
    assert blocked[0].id == task2.id
    
    # Complete task1 and check if task2 is unblocked
    await task_manager.update_task(task1.id, status=TaskStatus.DONE)
    blocked_after = await task_manager.get_blocked_tasks()
    assert len(blocked_after) == 0
