# Task Management Application

A powerful command-line task management application built with Python, featuring an interactive CLI, persistent storage with MySQL/MariaDB, and beautiful terminal UI.

## Features

- **Interactive CLI** - Beautiful terminal interface with arrow-key navigation using `questionary` and `rich`
- **Full CRUD Operations** - Create, read, update, and delete tasks with ease
- **Smart Task Selection** - Select tasks interactively or use partial UUID matching
- **Advanced Filtering** - Filter tasks by status, priority, and due date
- **Flexible Sorting** - Sort by due date, priority, creation date, or status
- **Task Statistics** - View comprehensive statistics about your tasks
- **Persistent Storage** - All tasks saved to MySQL/MariaDB database
- **Data Validation** - Comprehensive input validation and error handling
- **Type Safety** - Fully type-hinted codebase for better IDE support

## Task Attributes

Each task contains:

- **Task ID** - Unique UUID identifier
- **Title** - Task name (max 100 characters)
- **Description** - Optional details (max 500 characters)
- **Due Date** - Optional deadline
- **Priority** - LOW, MEDIUM, or HIGH
- **Status** - PENDING, IN_PROGRESS, or COMPLETED
- **Timestamps** - Creation and last update times

## Technology Stack

- **Python 3.14** - Core language
- **MySQL/MariaDB** - Persistent storage
- **mysql-connector-python** - Database driver
- **questionary** - Interactive CLI prompts
- **rich** - Beautiful terminal formatting

## Prerequisites

- Python 3.14 or higher
- MySQL 8.0+ or MariaDB 10.5+
- uv (Python package manager)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd task-management-app
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Set Up Database

Login to MySQL/MariaDB:

```bash
sudo mariadb -u root -p
```

Create the database and user:

```sql
CREATE DATABASE task_manager;
CREATE USER 'task_manager_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON task_manager.* TO 'task_manager_user'@'localhost';
FLUSH PRIVILEGES;
USE task_manager;
```

Create the tasks table:

```sql
CREATE TABLE tasks (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    due_date DATETIME,
    priority ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL,
    status ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED') NOT NULL DEFAULT 'PENDING',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_due_date (due_date),
    INDEX idx_status (status),
    INDEX idx_status_priority (status, priority)
);
```

Exit MySQL:

```sql
EXIT;
```

### 4. Configure Database Connection

Edit `main.py` if you need to change database credentials:

```python
db_connector = DatabaseConnector(
    host='localhost',
    port=3306,
    user='task_manager_user',
    password='password',
    database='task_manager'
)
```

## Project Structure

```text
task-management-app/
├── main.py                   # Application entry point
├── modules/
│   ├── cli.py                # CLI interface
│   ├── database.py           # DatabaseConnector class
│   ├── task.py               # Task, Priority, Status classes
│   └── task_manager.py       # TaskManager business logic
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Usage

### Starting the Application

```bash
uv run main.py
```

### Main Menu

The application presents an interactive menu with the following options:

1. **Add New Task** - Create a new task
2. **List All Tasks** - View all tasks with sorting options
3. **Filter Tasks** - Filter by status, priority, or due date
4. **Update Task** - Modify an existing task
5. **Mark Task Complete** - Quickly complete a task
6. **Delete Task** - Remove a task
7. **View Statistics** - See task statistics and analytics
8. **Exit** - Close the application

### Adding a Task

1. Select "Add New Task"
2. Enter task title (required)
3. Enter description (optional)
4. Set due date (optional)
5. Select priority level
6. Task is automatically created with status "PENDING"

### Selecting Tasks

When updating, completing, or deleting tasks, you can:

- **Use arrow keys** to select from a list of tasks
- **Type partial ID** - Enter first 6-8 characters of task UUID
- **Type full UUID** - Enter complete task ID

Example partial IDs:

```text
Full ID:    a1b2c3d4-e5f6-7890-1234-567890abcdef
Partial ID: a1b2c3d4  (first 8 chars)
```

### Filtering Tasks

Apply multiple filters simultaneously:

- **Status**: Pending, In Progress, Completed
- **Priority**: Low, Medium, High
- **Due Date**: Before/After/On specific date

### Sorting Tasks

Sort your task list by:

- Due Date (earliest or latest first)
- Priority (high to low or low to high)
- Created Date (newest or oldest first)
- Status

### Statistics Dashboard

View comprehensive statistics including:

- Total tasks and breakdown by status
- Task distribution by priority
- Overdue tasks count
- Tasks due in next 7 days

## Features in Detail

### Smart Task Selection

Instead of typing long UUIDs, the application offers:

1. **Interactive Selection** - Browse and select tasks with arrow keys
2. **Partial ID Matching** - Type just the first few characters
3. **Disambiguation** - Clear error messages if multiple tasks match

### Beautiful Terminal UI

- Color-coded priorities
- Status indicators with colors
- Formatted tables with borders
- Rich panels for sections
- Clear success/error messages

### Data Validation

- Title length validation (max 100 chars)
- Description length validation (max 500 chars)
- Date format validation (YYYY-MM-DD)
- Priority and status enum validation
- Comprehensive error messages

### Database Design

Optimized schema with:

- Primary key on task ID
- Indexes on frequently queried fields (due_date, status)
- Composite index for combined queries
- Automatic timestamp management

## Configuration

### Database Settings

Modify in `main.py`:

```python
DatabaseConnector(
    host='localhost',
    port=3306,
    user='your_user',
    password='your_pass',
    database='task_manager'
)
```

## Troubleshooting

### Database Connection Issues

**Error**: "Access denied for user"

```bash
# Verify user exists and has permissions
SHOW GRANTS FOR 'task_manager_user'@'localhost';
```

**Error**: "Unknown database 'task_manager'"

```bash
# Create the database
CREATE DATABASE task_manager;
```

### Import Errors

**Error**: "No module named 'mysql.connector'"

```bash
uv sync
```

**Error**: "No module named 'questionary'"

```bash
uv sync
```

### Task Selection Issues

**Error**: "Multiple tasks match"

- Provide more characters for the partial ID
- Use the interactive selection menu instead

**Error**: "No task found"

- Check the task ID is correct
- Verify task exists using "List All Tasks"

## Development

### Adding New Features

The modular architecture makes it easy to extend:

1. **New Task Fields** - Add to `Task` class and database schema
2. **New Filters** - Extend `filter_tasks()` in TaskManager
3. **New Sort Options** - Add to `_sort_tasks()` method
4. **New CLI Commands** - Add handler method and menu option

### Code Structure

- **database.py** - Generic database connector (SOLID principles)
- **task.py** - Task model with validation
- **task_manager.py** - Business logic layer
- **cli.py** - Presentation layer (questionary + rich)
- **main.py** - Application initialization

### Type Safety

All code is fully type-hinted:

```python
def add_task(self, task_data: TaskDict) -> Task:
    ...

def get_all_tasks(self, sort_by: Optional[str] = None) -> list[Task]:
    ...
```

## License

This project is licensed under the MIT License.
