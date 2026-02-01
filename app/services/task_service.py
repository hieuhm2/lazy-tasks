"""Task service for CRUD operations on tasks."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks in the database.

    Args:
        db: Async database session (per-request).
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize task service with database session."""
        self.db = db

    async def create_task(
        self,
        content: str,
        priority: int = 3,
        deadline: datetime | None = None,
        tags: list[str] | None = None,
        project_id: int | None = None,
        complexity: str | None = None,
    ) -> Task:
        """Create a new task.

        Args:
            content: Task description.
            priority: Priority level 1-5 (default 3).
            deadline: Optional deadline.
            tags: Optional list of tags.
            project_id: Optional project ID.
            complexity: Optional complexity (low, medium, high).

        Returns:
            The created Task instance.
        """
        task = Task(
            content=content,
            priority=priority,
            deadline=deadline,
            tags=tags,
            project_id=project_id,
            complexity=complexity,
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        logger.info(f"Created task #{task.id}: {content[:50]}")
        return task

    async def get_task_by_id(self, task_id: int) -> Task | None:
        """Get a task by its ID.

        Args:
            task_id: Task ID.

        Returns:
            Task instance or None if not found.
        """
        stmt = select(Task).where(Task.id == task_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tasks_by_status(
        self,
        status: str,
        limit: int = 20,
    ) -> list[Task]:
        """List tasks filtered by status.

        Args:
            status: Task status (todo, in_progress, done, cancelled).
            limit: Maximum number of tasks to return.

        Returns:
            List of Task instances.
        """
        stmt = (
            select(Task)
            .where(Task.status == status)
            .order_by(Task.priority.asc(), Task.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_tasks(self, limit: int = 20) -> list[Task]:
        """Get active tasks (todo + in_progress).

        Args:
            limit: Maximum number of tasks to return.

        Returns:
            List of active Task instances, ordered by priority then date.
        """
        stmt = (
            select(Task)
            .where(or_(Task.status == "todo", Task.status == "in_progress"))
            .order_by(Task.priority.asc(), Task.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_tasks_by_status(self) -> dict[str, int]:
        """Count tasks grouped by status.

        Returns:
            Dict mapping status to count, e.g. {"todo": 3, "in_progress": 2}.
        """
        stmt = (
            select(Task.status, func.count(Task.id))
            .group_by(Task.status)
        )
        result = await self.db.execute(stmt)
        return dict(result.all())

    async def update_task(self, task_id: int, **fields: Any) -> Task | None:
        """Update a task's fields.

        Args:
            task_id: Task ID.
            **fields: Fields to update (status, priority, deadline, etc.).

        Returns:
            Updated Task instance or None if not found.
        """
        task = await self.get_task_by_id(task_id)
        if task is None:
            return None

        allowed_fields = {"status", "priority", "deadline", "tags", "content",
                          "complexity", "project_id"}
        for key, value in fields.items():
            if key in allowed_fields:
                setattr(task, key, value)

        await self.db.flush()
        await self.db.refresh(task)
        logger.info(f"Updated task #{task_id}: {fields}")
        return task
