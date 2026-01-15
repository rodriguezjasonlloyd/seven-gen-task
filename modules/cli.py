from datetime import datetime
from typing import Optional

import questionary
from questionary import Style
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from modules.task import Task
from modules.task_manager import TaskManager, TaskNotFoundError, ValidationError

custom_style = Style(
    [
        ("qmark", "fg:#673ab7 bold"),
        ("question", "bold"),
        ("answer", "fg:#f44336 bold"),
        ("pointer", "fg:#673ab7 bold"),
        ("highlighted", "fg:#673ab7 bold"),
        ("selected", "fg:#cc5454"),
        ("separator", "fg:#cc5454"),
        ("instruction", ""),
        ("text", ""),
    ]
)

console = Console()


class TaskManagerCLI:
    """Command-line interface for the Task Management Application."""

    def __init__(self, task_manager: TaskManager):
        """Initialize the CLI with a TaskManager instance."""
        self.task_manager = task_manager
        self.running = True

    def display_welcome(self):
        """Display welcome message."""
        welcome_panel = Panel(
            "[bold cyan]TASK MANAGEMENT APPLICATION[/bold cyan]\n"
            "[dim]Organize your tasks efficiently![/dim]",
            border_style="cyan",
            box=box.DOUBLE,
        )
        console.print(welcome_panel)

    def display_main_menu(self):
        """Display and handle the main menu."""
        choices = [
            "Add New Task",
            "List All Tasks",
            "Filter Tasks",
            "Update Task",
            "Mark Task Complete",
            "Delete Task",
            "View Statistics",
            "Exit",
        ]

        action = questionary.select(
            "What would you like to do?", choices=choices, style=custom_style
        ).ask()

        if action is None:
            return self.handle_exit()

        action_map = {
            choices[0]: self.handle_add_task,
            choices[1]: self.handle_list_tasks,
            choices[2]: self.handle_filter_tasks,
            choices[3]: self.handle_update_task,
            choices[4]: self.handle_mark_complete,
            choices[5]: self.handle_delete_task,
            choices[6]: self.handle_statistics,
            choices[7]: self.handle_exit,
        }

        return action_map[action]()

    def handle_add_task(self):
        """Handle adding a new task."""
        console.print(Panel("[bold]ADD NEW TASK[/bold]", border_style="green"))

        title = questionary.text(
            "Task Title:",
            validate=lambda text: len(text) > 0
            and len(text) <= 100
            or "Title is required (max 100 characters)",
            style=custom_style,
        ).ask()

        if title is None:
            return self.handle_cancel()

        description = questionary.text(
            "Description (optional, press Enter to skip):",
            validate=lambda text: len(text) <= 500
            or "Description too long (max 500 characters)",
            style=custom_style,
        ).ask()

        if description is None:
            return self.handle_cancel()

        has_due_date = questionary.confirm(
            "Set a due date?", default=False, style=custom_style
        ).ask()

        due_date = None
        if has_due_date:
            due_date_str = questionary.text(
                "Due Date (YYYY-MM-DD):",
                validate=self.validate_date,
                style=custom_style,
            ).ask()

            if due_date_str is None:
                return self.handle_cancel()

            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                except ValueError:
                    console.print("[red]Invalid date format.[/red]")
                    self.press_enter_to_continue()
                    return

        priority = questionary.select(
            "Priority Level:", choices=["Low", "Medium", "High"], style=custom_style
        ).ask()

        if priority is None:
            return self.handle_cancel()

        task_data = {
            "title": title,
            "description": description if description else None,
            "due_date": due_date,
            "priority": priority.upper(),
        }

        try:
            task = self.task_manager.add_task(task_data)

            success_text = (
                f"[green]Task added successfully![/green]\n\n"
                f"[cyan]ID:[/cyan] {task.task_id}\n"
                f"[cyan]Title:[/cyan] {task.title}\n"
                f"[cyan]Priority:[/cyan] {task.priority.value}"
            )
            if task.due_date:
                success_text += (
                    f"\n[cyan]Due Date:[/cyan] {task.due_date.strftime('%Y-%m-%d')}"
                )

            console.print(Panel(success_text, border_style="green"))

        except ValidationError as error:
            console.print(f"[red]Validation Error: {error}[/red]")
        except Exception as exception:
            console.print(f"[red]Error: {exception}[/red]")

        self.press_enter_to_continue()

    def handle_list_tasks(self):
        """Handle listing all tasks."""
        console.print(Panel("[bold]ALL TASKS[/bold]", border_style="blue"))

        sort_by = questionary.select(
            "Sort tasks by:",
            choices=[
                "Due Date (Earliest First)",
                "Due Date (Latest First)",
                "Priority (High to Low)",
                "Priority (Low to High)",
                "Created Date (Newest First)",
                "Created Date (Oldest First)",
                "Status",
            ],
            style=custom_style,
        ).ask()

        if sort_by is None:
            return self.handle_cancel()

        sort_map = {
            "Due Date (Earliest First)": "due_date_asc",
            "Due Date (Latest First)": "due_date_desc",
            "Priority (High to Low)": "priority_high",
            "Priority (Low to High)": "priority_low",
            "Created Date (Newest First)": "created_desc",
            "Created Date (Oldest First)": "created_asc",
            "Status": "status",
        }

        try:
            tasks = self.task_manager.get_all_tasks(sort_by=sort_map.get(sort_by))
            self.display_tasks(tasks)
        except Exception as error:
            console.print(f"[red]Error: {error}[/red]")

        self.press_enter_to_continue()

    def handle_filter_tasks(self):
        """Handle filtering tasks."""
        console.print(Panel("[bold]FILTER TASKS[/bold]", border_style="magenta"))

        filters = {}

        filter_status = questionary.confirm(
            "Filter by status?", default=False, style=custom_style
        ).ask()

        if filter_status is None:
            return self.handle_cancel()

        if filter_status:
            status = questionary.select(
                "Select status:",
                choices=["Pending", "In Progress", "Completed"],
                style=custom_style,
            ).ask()

            if status is None:
                return self.handle_cancel()

            filters["status"] = status.upper().replace(" ", "_")

        filter_priority = questionary.confirm(
            "Filter by priority?", default=False, style=custom_style
        ).ask()

        if filter_priority is None:
            return self.handle_cancel()

        if filter_priority:
            priority = questionary.select(
                "Select priority:",
                choices=["Low", "Medium", "High"],
                style=custom_style,
            ).ask()

            if priority is None:
                return self.handle_cancel()

            filters["priority"] = priority.upper()

        filter_date = questionary.confirm(
            "Filter by due date?", default=False, style=custom_style
        ).ask()

        if filter_date is None:
            return self.handle_cancel()

        if filter_date:
            date_filter_type = questionary.select(
                "Filter type:",
                choices=["Before date", "After date", "On date"],
                style=custom_style,
            ).ask()

            if date_filter_type is None:
                return self.handle_cancel()

            date_str = questionary.text(
                "Enter date (YYYY-MM-DD):",
                validate=self.validate_date,
                style=custom_style,
            ).ask()

            if date_str is None:
                return self.handle_cancel()

            try:
                filter_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                filters["due_date"] = {
                    "type": date_filter_type.lower().replace(" ", "_"),
                    "date": filter_date_obj,
                }
            except ValueError:
                console.print("[red]❌ Invalid date format.[/red]")
                self.press_enter_to_continue()
                return

        try:
            tasks = self.task_manager.filter_tasks(filters)
            console.print(f"\n[cyan]Filtered tasks (found {len(tasks)})[/cyan]")
            self.display_tasks(tasks)
        except Exception as exception:
            console.print(f"[red]Error: {exception}[/red]")

        self.press_enter_to_continue()

    def handle_update_task(self):
        """Handle updating a task."""
        console.print(Panel("[bold]UPDATE TASK[/bold]", border_style="yellow"))

        task = self.select_task_interactive()

        if task is None:
            return self.handle_cancel()

        try:
            current_info = (
                f"[cyan]Title:[/cyan] {task.title}\n"
                f"[cyan]Description:[/cyan] {task.description or 'None'}\n"
                f"[cyan]Priority:[/cyan] {task.priority.value}\n"
                f"[cyan]Status:[/cyan] {task.status.value}\n"
                f"[cyan]Due Date:[/cyan] {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'None'}"
            )
            console.print(
                Panel(current_info, title="Current Task Details", border_style="blue")
            )

        except Exception as exception:
            console.print(f"[red]Error: {exception}[/red]")
            self.press_enter_to_continue()
            return

        update_fields = questionary.checkbox(
            "Select fields to update:",
            choices=["Title", "Description", "Priority", "Status", "Due Date"],
            style=custom_style,
        ).ask()

        if update_fields is None:
            return self.handle_cancel()

        if not update_fields:
            console.print("[yellow]No fields selected for update.[/yellow]")
            self.press_enter_to_continue()
            return

        updates = {}

        if "Title" in update_fields:
            new_title = questionary.text(
                "New Title:",
                validate=lambda text: len(text) > 0
                and len(text) <= 100
                or "Invalid title",
                style=custom_style,
            ).ask()
            if new_title:
                updates["title"] = new_title

        if "Description" in update_fields:
            new_desc = questionary.text(
                "New Description (leave empty to clear):",
                validate=lambda text: len(text) <= 500 or "Too long",
                style=custom_style,
            ).ask()
            if new_desc is not None:
                updates["description"] = new_desc if new_desc else None

        if "Priority" in update_fields:
            new_priority = questionary.select(
                "New Priority:", choices=["Low", "Medium", "High"], style=custom_style
            ).ask()
            if new_priority:
                updates["priority"] = new_priority.upper()

        if "Status" in update_fields:
            new_status = questionary.select(
                "New Status:",
                choices=["Pending", "In Progress", "Completed"],
                style=custom_style,
            ).ask()
            if new_status:
                updates["status"] = new_status.upper().replace(" ", "_")

        if "Due Date" in update_fields:
            new_due_date = questionary.text(
                "New Due Date (YYYY-MM-DD, leave empty to clear):",
                validate=lambda text: self.validate_date(text) if text else True,
                style=custom_style,
            ).ask()
            if new_due_date is not None:
                if new_due_date:
                    try:
                        updates["due_date"] = datetime.strptime(
                            new_due_date, "%Y-%m-%d"
                        )
                    except ValueError:
                        console.print("[red]Invalid date format.[/red]")
                        self.press_enter_to_continue()
                        return
                else:
                    updates["due_date"] = None

        confirm = questionary.confirm(
            "Confirm update for task?", default=True, style=custom_style
        ).ask()

        if confirm:
            try:
                self.task_manager.update_task(task.task_id, updates)
                console.print("[green]Task updated successfully![/green]")
            except ValidationError as error:
                console.print(f"[red]Validation Error: {error}[/red]")
            except Exception as exception:
                console.print(f"[red]Error: {exception}[/red]")
        else:
            console.print("[red]Update cancelled.[/red]")

        self.press_enter_to_continue()

    def handle_mark_complete(self):
        """Handle marking a task as complete."""
        console.print(Panel("[bold]MARK TASK COMPLETE[/bold]", border_style="green"))

        task = self.select_task_interactive()

        if task is None:
            return self.handle_cancel()

        confirm = questionary.confirm(
            f"Mark task '{task.title}' as completed?", default=True, style=custom_style
        ).ask()

        if confirm:
            try:
                self.task_manager.mark_task_complete(task.task_id)
                console.print("[green]Task marked as complete![/green]")
            except TaskNotFoundError as error:
                console.print(f"[red]{error}[/red]")
            except Exception as exception:
                console.print(f"[red]Error: {exception}[/red]")
        else:
            console.print("[red]Action cancelled.[/red]")

        self.press_enter_to_continue()

    def handle_delete_task(self):
        """Handle deleting a task."""
        console.print(Panel("[bold]DELETE TASK[/bold]", border_style="red"))

        task = self.select_task_interactive()

        if task is None:
            return self.handle_cancel()

        confirm = questionary.confirm(
            f"Are you sure you want to delete task '{task.title}'? This cannot be undone!",
            default=False,
            style=custom_style,
        ).ask()

        if confirm:
            try:
                self.task_manager.delete_task(task.task_id)
                console.print("[green]Task deleted successfully![/green]")
            except TaskNotFoundError as error:
                console.print(f"[red]{error}[/red]")
            except Exception as exception:
                console.print(f"[red]Error: {exception}[/red]")
        else:
            console.print("[red]Deletion cancelled.[/red]")

        self.press_enter_to_continue()

    def handle_statistics(self):
        """Display task statistics."""
        console.print(Panel("[bold]TASK STATISTICS[/bold]", border_style="cyan"))

        try:
            stats = self.task_manager.get_statistics()

            overview_table = Table(title="Overview", box=box.ROUNDED, show_header=False)
            overview_table.add_column("Metric", style="cyan")
            overview_table.add_column("Count", style="bold")

            overview_table.add_row("Total Tasks", str(stats["total"]))
            overview_table.add_row("Completed", str(stats["by_status"]["completed"]))
            overview_table.add_row(
                "In Progress", str(stats["by_status"]["in_progress"])
            )
            overview_table.add_row("Pending", str(stats["by_status"]["pending"]))

            console.print(overview_table)

            priority_table = Table(
                title="By Priority", box=box.ROUNDED, show_header=False
            )
            priority_table.add_column("Priority", style="cyan")
            priority_table.add_column("Count", style="bold")

            priority_table.add_row("High", str(stats["by_priority"]["high"]))
            priority_table.add_row("Medium", str(stats["by_priority"]["medium"]))
            priority_table.add_row("Low", str(stats["by_priority"]["low"]))

            console.print(priority_table)

            due_table = Table(title="Due Soon", box=box.ROUNDED, show_header=False)
            due_table.add_column("Status", style="cyan")
            due_table.add_column("Count", style="bold")

            due_table.add_row("Tasks due in next 7 days", str(stats["due_soon"]))
            due_table.add_row("Overdue tasks", str(stats["overdue"]))

            console.print(due_table)

        except Exception as exception:
            console.print(f"[red]Error: {exception}[/red]")

        self.press_enter_to_continue()

    def handle_exit(self):
        """Handle application exit."""
        exit_panel = Panel(
            "[bold cyan]Thank you for using Task Manager![/bold cyan]\n"
            "[dim]See you next time![/dim]",
            border_style="cyan",
            box=box.DOUBLE,
        )
        console.print(exit_panel)
        self.running = False

    def handle_cancel(self):
        """Handle cancelled operation."""
        console.print("[red]Operation cancelled.[/red]")
        self.press_enter_to_continue()

    def select_task_interactive(self) -> Optional[Task]:
        """
        Interactive task selection with arrow keys.

        Returns:
            Selected Task object or None if cancelled
        """
        try:
            tasks = self.task_manager.get_all_tasks()

            if not tasks:
                console.print("[yellow]No tasks available to select.[/yellow]")
                return None

            choices = []

            for task in tasks:
                short_id = task.task_id[:8]
                status = task.status.value.replace("_", " ").title()
                choice_text = (
                    f"[{short_id}] {task.title} - {task.priority.value} - {status}"
                )
                choices.append(choice_text)

            choices.append("Type ID manually")

            selection = questionary.select(
                "Select a task:", choices=choices, style=custom_style
            ).ask()

            if selection is None:
                return None

            if selection == "Type ID manually":
                task_id = questionary.text(
                    "Enter Task ID (full or partial):",
                    validate=lambda text: len(text) > 0 or "Task ID is required",
                    style=custom_style,
                ).ask()

                if task_id is None:
                    return None

                try:
                    return self.task_manager.get_task_by_partial_id(task_id)
                except TaskNotFoundError:
                    return self.task_manager.get_task(task_id)

            short_id = selection.split("]")[0][1:]

            for task in tasks:
                if task.task_id.startswith(short_id):
                    return task

            return None
        except Exception as exception:
            console.print(f"[red]Error: {exception}[/red]")
            return None

    def display_tasks(self, tasks):
        """Display tasks in a rich table."""
        if not tasks:
            console.print("[yellow]No tasks found.[/yellow]")
            return

        table = Table(title="Tasks", box=box.ROUNDED, show_lines=True)

        table.add_column("Short ID", style="dim", width=10)
        table.add_column("Title", style="cyan")
        table.add_column("Priority", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Due Date", justify="center")

        for task in tasks:
            priority_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(
                task.priority.value, "white"
            )

            status_color = {
                "COMPLETED": "green",
                "IN_PROGRESS": "yellow",
                "PENDING": "blue",
            }.get(task.status.value, "white")

            table.add_row(
                task.task_id[:8],
                task.title,
                f"[{priority_color}]{task.priority.value}[/{priority_color}]",
                f"[{status_color}]{task.status.value.replace('_', ' ').title()}[/{status_color}]",
                task.due_date.strftime("%Y-%m-%d") if task.due_date else "None",
            )

        console.print(table)
        console.print(f"\n[dim]Total tasks: {len(tasks)}[/dim]")

    def validate_date(self, date_str: str) -> bool:
        """Validate date format."""
        if not date_str:
            return True

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return "Invalid date format. Use YYYY-MM-DD"

    def press_enter_to_continue(self):
        """Wait for user to press enter."""
        questionary.press_any_key_to_continue(
            "Press Enter to continue...", style=custom_style
        ).ask()

    def run(self):
        """Main application loop."""
        self.display_welcome()

        while self.running:
            try:
                self.display_main_menu()
            except KeyboardInterrupt:
                self.handle_exit()
                break
            except Exception as exception:
                console.print(f"[red]An error occurred: {str(exception)}[/red]")
                self.press_enter_to_continue()
