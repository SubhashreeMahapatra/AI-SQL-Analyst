import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import re


class DBManager:
    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)

    def get_schema_info(self) -> dict:
        """Return a dict of {table_name: [{name, type}]} for all tables."""
        schema = {}
        for table_name in self.inspector.get_table_names():
            columns = []
            for col in self.inspector.get_columns(table_name):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                })
            schema[table_name] = columns
        return schema

    def execute_query(self, sql: str) -> pd.DataFrame:
        """Execute a SQL SELECT query and return a DataFrame."""
        # Strip trailing semicolons
        sql = sql.strip().rstrip(";")

        # Final safety guard
        sql_lower = sql.lower()
        forbidden = ["drop ", "delete ", "update ", "insert ", "alter ", "truncate "]
        for keyword in forbidden:
            if keyword in sql_lower:
                raise ValueError(f"Destructive SQL blocked: '{keyword.strip()}'")

        # Enforce row limit
        if "limit" not in sql_lower:
            sql = f"SELECT * FROM ({sql}) AS subq LIMIT 1000"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error: {str(e)}")

    def get_sample_rows(self, table: str, n: int = 3) -> pd.DataFrame:
        """Return sample rows from a table."""
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table} LIMIT {n}"))
            return pd.DataFrame(result.fetchall(), columns=result.keys())
