"""
Task Manager Module

This module provides task management and workflow automation capabilities for the TaskProvision platform.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import logging
import asyncio
from uuid import uuid4

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """Status of a task"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    ARCHIVED = "archived"

class TaskPriority(str, Enum):
    """Priority levels for tasks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TaskDependency:
    """Represents a dependency between tasks"""
    task_id: str
    required: bool = True
    description: str = ""

@dataclass
class Task:
    """Task representation"""
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    assignee: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    dependencies: List[TaskDependency] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class TaskManager:
    """Manages tasks and their workflows"""
    
    def __init__(self):
        """Initialize the task manager"""
        self.tasks: Dict[str, Task] = {}
        self.logger = logging.getLogger(f"{__name__}.TaskManager")
    
    async def create_task(self, title: str, description: str = "", **kwargs) -> Task:
        """
        Create a new task
        
        Args:
            title: Task title
            description: Task description
            **kwargs: Additional task attributes
            
        Returns:
            The created task
        """
        task = Task(title=title, description=description, **kwargs)
        self.tasks[task.id] = task
        self.logger.info(f"Created task {task.id}: {task.title}")
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            The task if found, None otherwise
        """
        return self.tasks.get(task_id)
    
    async def update_task(self, task_id: str, **updates) -> Optional[Task]:
        """
        Update a task
        
        Args:
            task_id: ID of the task to update
            **updates: Fields to update
            
        Returns:
            The updated task if found, None otherwise
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
            
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
                
        task.updated_at = datetime.utcnow()
        self.logger.info(f"Updated task {task_id}")
        return task
    
    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            True if the task was deleted, False otherwise
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.logger.info(f"Deleted task {task_id}")
            return True
        return False
    
    async def list_tasks(self, status: Optional[TaskStatus] = None, 
                        assignee: Optional[str] = None) -> List[Task]:
        """
        List tasks with optional filtering
        
        Args:
            status: Filter by status
            assignee: Filter by assignee
            
        Returns:
            List of matching tasks
        """
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        if assignee:
            tasks = [t for t in tasks if t.assignee == assignee]
            
        return tasks
    
    async def add_dependency(self, task_id: str, depends_on_id: str, 
                           required: bool = True, description: str = "") -> bool:
        """
        Add a dependency between tasks
        
        Args:
            task_id: ID of the dependent task
            depends_on_id: ID of the task it depends on
            required: Whether the dependency is required
            description: Description of the dependency
            
        Returns:
            True if the dependency was added, False otherwise
        """
        if task_id not in self.tasks or depends_on_id not in self.tasks:
            return False
            
        task = self.tasks[task_id]
        dependency = TaskDependency(
            task_id=depends_on_id,
            required=required,
            description=description
        )
        task.dependencies.append(dependency)
        return True
    
    async def get_blocked_tasks(self) -> List[Task]:
        """
        Get a list of tasks that are blocked by their dependencies
        
        Returns:
            List of blocked tasks
        """
        blocked_tasks = []
        
        for task in self.tasks.values():
            if task.status == TaskStatus.BLOCKED:
                blocked_tasks.append(task)
                continue
                
            for dep in task.dependencies:
                if dep.required and dep.task_id in self.tasks:
                    dep_task = self.tasks[dep.task_id]
                    if dep_task.status != TaskStatus.DONE:
                        if task.status != TaskStatus.BLOCKED:
                            task.status = TaskStatus.BLOCKED
                            blocked_tasks.append(task)
                        break
                        
        return blocked_tasks

