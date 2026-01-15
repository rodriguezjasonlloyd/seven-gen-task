"""
Task Management Application - Main Entry Point
"""

import sys

from modules.cli import TaskManagerCLI
from modules.database import DatabaseConnector
from modules.task_manager import TaskManager


def main():
    """
    Main entry point for the Task Management Application.
    """
    database_connector = None

    try:
        database_connector = DatabaseConnector(
            host="localhost",
            port=3306,
            user="task_manager_user",
            password="password",
            database="task_manager",
        )

        task_manager = TaskManager(database_connector)

        cli = TaskManagerCLI(task_manager)
        cli.run()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
    except Exception as exception:
        print(f"\nFatal error: {exception}")
        sys.exit(1)
    finally:
        if database_connector:
            database_connector.disconnect()


if __name__ == "__main__":
    main()
