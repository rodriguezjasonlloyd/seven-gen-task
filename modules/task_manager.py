from datetime import datetime
from typing import Optional

from modules.database import DatabaseConnector
from modules.task import Priority, Task, TaskDict


class TaskNotFoundError(Exception):
    """Raised when a task is not found."""

    pass


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class TaskManager:
    """Manages task operations and coordinates between cache and database."""

    def __init__(self, database_connector: DatabaseConnector):
        """
        Initialize the TaskManager with a database connector.

        Args:
            database_connector: DatabaseConnector instance for persistence
        """
        self.database_connector: DatabaseConnector = database_connector
        self.task_cache: dict[str, Task] = {}

        self._load_tasks_from_database()

    def _load_tasks_from_database(self) -> None:
        """
        Private method to load all tasks from database into cache on initialization.
        """
        try:
            query = "SELECT * FROM tasks"
            results = self.database_connector.execute_query(query)

            if results:
                for task_data in results:
                    task = Task.from_dict(task_data)
                    self.task_cache[task.task_id] = task
        except Exception as exception:
            print(f"Warning: Failed to load tasks from database: {exception}")

    def add_task(self, task_data: TaskDict) -> Task:
        """
        Create and persist a new task.

        Args:
            task_data: Dictionary containing task information
                      (title, description, due_date, priority)

        Returns:
            Created Task object

        Raises:
            ValidationError: If task data is invalid
        """
        try:
            task = Task(
                title=task_data["title"],
                description=task_data.get("description"),
                due_date=task_data.get("due_date"),
                priority=Priority(task_data["priority"]),
            )

            task_dict = task.to_dict()

            insert_query = """
                INSERT INTO tasks (id, title, description, due_date, priority, status, created_at, updated_at)
                VALUES (%(id)s, %(title)s, %(description)s, %(due_date)s, %(priority)s, %(status)s, %(created_at)s, %(updated_at)s)
            """

            self.database_connector.execute_query(insert_query, task_dict)
            self.database_connector.commit()

            self.task_cache[task.task_id] = task

            print(f"Task '{task.title}' added successfully (ID: {task.task_id})")
            return task
        except ValueError as error:
            raise ValidationError(f"Invalid task data: {error}")
        except Exception as exception:
            self.database_connector.rollback()
            raise Exception(f"Failed to add task: {exception}")

    def get_task(self, task_id: str) -> Task:
        """
        Retrieve a single task by ID.

        Args:
            task_id: Unique task identifier

        Returns:
            Task object

        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        if task_id in self.task_cache:
            return self.task_cache[task_id]

        try:
            query = "SELECT * FROM tasks WHERE id = %s"
            results = self.database_connector.execute_query(query, (task_id,))

            if not results:
                raise TaskNotFoundError(f"Task with ID '{task_id}' not found")

            task = Task.from_dict(results[0])
            self.task_cache[task_id] = task
            return task
        except TaskNotFoundError:
            raise
        except Exception as exception:
            raise Exception(f"Failed to retrieve task: {exception}")

    def get_task_by_partial_id(self, partial_id: str) -> Task:
        """
        Retrieve a single task by partial UUID match.

        Args:
            partial_id: Partial task identifier (first 6-12 characters)

        Returns:
            Task object

        Raises:
            TaskNotFoundError: If no task found or multiple matches
        """
        matches = [
            task
            for task_id, task in self.task_cache.items()
            if task_id.startswith(partial_id)
        ]

        if len(matches) == 0:
            raise TaskNotFoundError(
                f"No task found with ID starting with '{partial_id}'"
            )
        elif len(matches) > 1:
            matching_ids = [task.task_id[:8] for task in matches]

            raise TaskNotFoundError(
                f"Multiple tasks match '{partial_id}': {', '.join(matching_ids)}. "
                f"Please provide more characters."
            )

        return matches[0]

    def get_all_tasks(self, sort_by: Optional[str] = None) -> list[Task]:
        """
        Retrieve all tasks with optional sorting.

        Args:
            sort_by: Sort criteria ('due_date_asc', 'due_date_desc', 'priority_high',
                    'priority_low', 'created_asc', 'created_desc', 'status')

        Returns:
            List of Task objects
        """
        tasks = list(self.task_cache.values())

        if sort_by:
            tasks = self._sort_tasks(tasks, sort_by)

        return tasks

    def update_task(self, task_id: str, updates: TaskDict) -> Task:
        """
        Update an existing task.

        Args:
            task_id: Unique task identifier
            updates: Dictionary of fields to update

        Returns:
            Updated Task object

        Raises:
            TaskNotFoundError: If task doesn't exist
            ValidationError: If update data is invalid
        """
        try:
            task = self.get_task(task_id)

            task.update(**updates)

            update_fields = []
            params = {}

            for key, value in updates.items():
                if key in ["title", "description", "due_date", "priority", "status"]:
                    update_fields.append(f"{key} = %({key})s")
                    params[key] = value

            if not update_fields:
                return task

            update_fields.append("updated_at = %(updated_at)s")
            params["updated_at"] = datetime.now()
            params["id"] = task_id

            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = %(id)s"

            self.database_connector.execute_query(query, params)
            self.database_connector.commit()

            self.task_cache[task_id] = task

            print(f"Task '{task_id}' updated successfully")
            return task
        except TaskNotFoundError:
            raise
        except ValueError as e:
            self.database_connector.rollback()
            raise ValidationError(f"Invalid update data: {e}")
        except Exception as e:
            self.database_connector.rollback()
            raise Exception(f"Failed to update task: {e}")

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            task_id: Unique task identifier

        Returns:
            True if successful

        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        try:
            if task_id not in self.task_cache:
                self.get_task(task_id)

            query = "DELETE FROM tasks WHERE id = %s"
            self.database_connector.execute_query(query, (task_id,))
            self.database_connector.commit()

            del self.task_cache[task_id]

            print(f"Task '{task_id}' deleted successfully")
            return True
        except TaskNotFoundError:
            raise
        except Exception as exception:
            self.database_connector.rollback()
            raise Exception(f"Failed to delete task: {exception}")

    def mark_task_complete(self, task_id: str) -> Task:
        """
        Mark a task as completed.

        Args:
            task_id: Unique task identifier

        Returns:
            Updated Task object

        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        return self.update_task(task_id, {"status": "COMPLETED"})

    def filter_tasks(self, filters: dict) -> list[Task]:
        """
        Filter tasks based on criteria.

        Args:
            filters: Dictionary with filter criteria
                    - status: Task status
                    - priority: Task priority
                    - due_date: Dict with 'type' (before/after/on) and 'date'

        Returns:
            List of filtered Task objects
        """
        tasks = list(self.task_cache.values())
        filtered_tasks = []

        for task in tasks:
            match = True

            if "status" in filters:
                if task.status.value != filters["status"]:
                    match = False

            if "priority" in filters:
                if task.priority.value != filters["priority"]:
                    match = False

            if "due_date" in filters and task.due_date:
                date_filter = filters["due_date"]
                filter_type = date_filter.get("type")
                filter_date = date_filter.get("date")

                if filter_type == "before_date":
                    if task.due_date >= filter_date:
                        match = False
                elif filter_type == "after_date":
                    if task.due_date <= filter_date:
                        match = False
                elif filter_type == "on_date":
                    if task.due_date.date() != filter_date.date():
                        match = False

            if match:
                filtered_tasks.append(task)

        return filtered_tasks

    def _sort_tasks(self, tasks: list[Task], sort_by: str) -> list[Task]:
        """
        Sort tasks based on specified criteria.

        Args:
            tasks: List of Task objects
            sort_by: Sort criteria

        Returns:
            Sorted list of Task objects
        """
        priority_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

        if sort_by == "due_date_asc":
            return sorted(
                tasks, key=lambda task: (task.due_date is None, task.due_date)
            )

        elif sort_by == "due_date_desc":
            return sorted(
                tasks,
                key=lambda task: (task.due_date is None, task.due_date),
                reverse=True,
            )

        elif sort_by == "priority_high":
            return sorted(
                tasks,
                key=lambda task: priority_order.get(task.priority.value, 0),
                reverse=True,
            )

        elif sort_by == "priority_low":
            return sorted(
                tasks, key=lambda task: priority_order.get(task.priority.value, 0)
            )

        elif sort_by == "created_asc":
            return sorted(tasks, key=lambda task: task.created_at)

        elif sort_by == "created_desc":
            return sorted(tasks, key=lambda task: task.created_at, reverse=True)

        elif sort_by == "status":
            return sorted(tasks, key=lambda task: task.status.value)

        return tasks

    def get_statistics(self) -> dict:
        """
        Get task statistics.

        Returns:
            Dictionary with task statistics
        """
        tasks = list(self.task_cache.values())

        stats = {
            "total": len(tasks),
            "by_status": {"pending": 0, "in_progress": 0, "completed": 0},
            "by_priority": {"high": 0, "medium": 0, "low": 0},
            "overdue": 0,
            "due_soon": 0,
        }

        now = datetime.now()

        for task in tasks:
            status = task.status.value.lower()

            if status in stats["by_status"]:
                stats["by_status"][status] = (
                    stats["by_status"].get(status.replace("_", " "), 0) + 1
                )

            priority = task.priority.value.lower()

            if priority in stats["by_priority"]:
                stats["by_priority"][priority] += 1

            if task.due_date and task.status.value != "COMPLETED":
                days_until_due = (task.due_date - now).days

                if days_until_due < 0:
                    stats["overdue"] += 1
                elif days_until_due <= 7:
                    stats["due_soon"] += 1

        return stats
