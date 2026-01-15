import uuid
from datetime import datetime
from enum import Enum
from typing import Literal, Optional, TypedDict


class Priority(Enum):
    """Task priority levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Status(Enum):
    """Task status levels."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class TaskDict(TypedDict):
    id: str
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime


TaskDictKey = Literal[
    "id",
    "title",
    "description",
    "due_date",
    "priority",
    "status",
    "created_at",
    "updated_at",
]


class Task:
    """Represents a task with all its attributes."""

    def __init__(
        self,
        title: str,
        priority: Priority,
        description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        status: Status = Status.PENDING,
        task_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        """
        Initialize a Task object.

        Args:
            title: Task title (required, max 100 chars)
            priority: Task priority level (LOW, MEDIUM, HIGH)
            description: Task description (optional, max 500 chars)
            due_date: Task due date (optional)
            status: Task status (default: PENDING)
            task_id: Unique identifier (auto-generated if not provided)
            created_at: Creation timestamp (auto-set if not provided)
            updated_at: Last update timestamp (auto-set if not provided)
        """
        self.task_id: str = task_id or str(uuid.uuid4())
        self.title: str = title
        self.description: Optional[str] = description
        self.due_date: Optional[datetime] = due_date
        self.priority: Priority = priority
        self.status: Status = status
        self.created_at: datetime = created_at or datetime.now()
        self.updated_at: datetime = updated_at or datetime.now()

        self.validate_fields()

    def validate_fields(self) -> None:
        """
        Validate all task fields.

        Raises:
            ValueError: If any field validation fails
        """
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")

        if len(self.title) > 100:
            raise ValueError("Title cannot exceed 100 characters")

        if self.description and len(self.description) > 500:
            raise ValueError("Description cannot exceed 500 characters")

        if not isinstance(self.priority, Priority):
            raise ValueError(
                f"Invalid priority. Must be one of: {', '.join([priority.value for priority in Priority])}"
            )

        if not isinstance(self.status, Status):
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join([status.value for status in Status])}"
            )

    def to_dict(self) -> TaskDict:
        """
        Convert Task object to dictionary for database storage.

        Returns:
            Dictionary representation of the task
        """
        return {
            "id": self.task_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date if self.due_date else None,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """
        Create a Task object from a dictionary (typically from database).

        Args:
            data: Dictionary containing task data

        Returns:
            Task object
        """
        return cls(
            task_id=data.get("id"),
            title=data["title"],
            description=data.get("description"),
            due_date=data.get("due_date"),
            priority=Priority(data["priority"]),
            status=Status(data["status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def mark_completed(self) -> None:
        """
        Mark the task as completed and update the timestamp.
        """
        self.status = Status.COMPLETED
        self.updated_at = datetime.now()

    def update(self, **kwargs) -> None:
        """
        Update task attributes with validation.

        Args:
            **kwargs: Keyword arguments for fields to update
                     (title, description, due_date, priority, status)

        Raises:
            ValueError: If validation fails for any field
        """
        if "title" in kwargs:
            self.title = kwargs["title"]

        if "description" in kwargs:
            self.description = kwargs["description"]

        if "due_date" in kwargs:
            self.due_date = kwargs["due_date"]

        if "priority" in kwargs:
            self.priority = Priority(kwargs["priority"])

        if "status" in kwargs:
            self.status = Status(kwargs["status"])

        self.updated_at = datetime.now()

        self.validate_fields()
