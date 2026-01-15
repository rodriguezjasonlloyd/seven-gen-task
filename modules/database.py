from typing import Optional

import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursorDict
from mysql.connector.types import RowItemType


class DatabaseConnector:
    """Handles MySQL database connection and operations."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: str = "task_manager_user",
        password: str = "password",
        database: str = "task_manager",
    ) -> None:
        """
        Initialize database connection.

        Args:
            host: MySQL server host (default: localhost)
            port: MySQL server port (default: 3306)
            user: Database user (default: task_manager_user)
            password: Database password (default: password)
            database: Database name (default: task_manager)
        """
        self.host: str = host
        self.port: int = port
        self.user: str = user
        self.password: str = password
        self.database: str = database
        self.connection: MySQLConnection | None = None
        self.cursor: MySQLCursorDict | None = None

        self.connect()

    def connect(self) -> None:
        """
        Establish connection to the MySQL database.

        Raises:
            Exception: If connection fails
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
            )

            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)

        except Error as error:
            print(f"Error connecting to MySQL: {error}")
            raise

    def disconnect(self) -> None:
        """
        Close cursor and database connection.
        """
        try:
            if self.cursor:
                self.cursor.close()

            if self.connection and self.connection.is_connected():
                self.connection.close()

        except Error as error:
            print(f"Error disconnecting from MySQL: {error}")

    def execute_query(
        self, query, params=None
    ) -> list[Optional[dict[str, RowItemType]]] | None:
        """
        Execute a SQL query with optional parameters.

        Args:
            query: SQL query string
            params: Tuple of parameters for parameterized query

        Returns:
            List of dictionaries for SELECT queries, None for others

        Raises:
            Exception: If query execution fails
        """
        try:
            if not self.connection or not self.connection.is_connected():
                print("Connection lost. Reconnecting.")
                self.connect()

            self.cursor.execute(query, params or ())

            if query.strip().upper().startswith("SELECT"):
                results = self.cursor.fetchall()
                return results

            return None

        except Error as exception:
            print(f"Query execution error: {exception}")
            print(f"\tQuery: {query}")
            print(f"\tParams: {params}")
            raise

    def commit(self) -> None:
        """
        Commit the current transaction.

        Raises:
            Exception: If commit fails
        """
        try:
            if self.connection:
                self.connection.commit()

        except Error as error:
            print(f"Commit error: {error}")
            raise

    def rollback(self) -> None:
        """
        Rollback the current transaction.

        Raises:
            Exception: If rollback fails
        """
        try:
            if self.connection:
                self.connection.rollback()
                print("Transaction rolled back.")

        except Error as error:
            print(f"Rollback error: {error}")
            raise
