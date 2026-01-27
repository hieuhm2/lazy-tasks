"""Task and related models."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """Project for grouping tasks."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )  # active, paused, archived
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="project",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Project(id={self.id}, name={self.name})>"


class Task(Base):
    """Task with SMART criteria tracking."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="todo",
        nullable=False,
    )  # todo, in_progress, done, cancelled
    priority: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )  # 1 (P1) to 5 (P5)
    complexity: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )  # low, medium, high
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True,
    )
    project_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("projects.id"),
        nullable=True,
    )
    parent_task_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    project: Mapped[Project | None] = relationship(
        "Project",
        back_populates="tasks",
    )
    parent_task: Mapped["Task | None"] = relationship(
        "Task",
        remote_side=[id],
        back_populates="subtasks",
    )
    subtasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="parent_task",
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        "Reminder",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Task(id={self.id}, status={self.status})>"


class Reminder(Base):
    """Reminder linked to a task."""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    remind_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_sent: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    task: Mapped[Task] = relationship(
        "Task",
        back_populates="reminders",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Reminder(id={self.id}, remind_at={self.remind_at})>"
