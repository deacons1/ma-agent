from typing import Dict, Any, List, Optional
import json
import os
import re
from phi.tools.sql import SQLTools
from phi.tools import tool

class SafeSQLTools(SQLTools):
    """Extended SQLTools with safety measures and operation-specific methods"""
    
    def __init__(self, db_url: str, allow_insert: bool = True, allow_update: bool = True, 
                 allow_delete: bool = False, allow_drop: bool = False):
        super().__init__(db_url=db_url)
        self.allow_insert = allow_insert
        self.allow_update = allow_update
        self.allow_delete = allow_delete
        self.allow_drop = allow_drop

    def validate_query(self, query: str) -> bool:
        """Validates if the query is allowed based on configuration"""
        query = query.lower().strip()
        
        # Check for DROP operations
        if not self.allow_drop and ("drop table" in query or "drop database" in query):
            raise ValueError("DROP operations are not allowed")
            
        # Check for DELETE operations    
        if not self.allow_delete and "delete from" in query:
            raise ValueError("DELETE operations are not allowed")
            
        # Check for UPDATE operations
        if not self.allow_update and "update" in query:
            raise ValueError("UPDATE operations are not allowed")
            
        # Check for INSERT operations    
        if not self.allow_insert and "insert into" in query:
            raise ValueError("INSERT operations are not allowed")
            
        return True

@tool(name="select_query", description="Executes a SELECT query on the database. Only allows read operations.")
def select_query(query: str) -> str:
    """Executes a SELECT query using Supabase Postgres."""
    sql_tools = SafeSQLTools(db_url=os.getenv("DATABASE_URL"))
    try:
        # Validate it's a SELECT query
        if not query.lower().strip().startswith("select"):
            raise ValueError("Only SELECT queries are allowed in this function")
            
        result = sql_tools.run_sql_query(query)
        return json.dumps({
            "rows": result.get("rows", []),
            "count": len(result.get("rows", [])),
            "message": "Query successful"
        })
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "Query failed"
        })

@tool(name="insert_data", description="Inserts data into the specified table.")
def insert_data(table: str, data: Dict[str, Any]) -> str:
    """Inserts a row into the specified table."""
    sql_tools = SafeSQLTools(db_url=os.getenv("DATABASE_URL"), allow_insert=True)
    try:
        columns = ", ".join(data.keys())
        values = ", ".join([f"%({k})s" for k in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({values}) RETURNING id"
        
        result = sql_tools.run_sql_query(query, parameters=data)
        return json.dumps({
            "message": "Insert successful",
            "id": result.get("rows", [{}])[0].get("id")
        })
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "Insert failed"
        })

@tool(name="update_data", description="Updates data in the specified table.")
def update_data(table: str, data: Dict[str, Any], where_clause: str) -> str:
    """Updates rows in the specified table."""
    sql_tools = SafeSQLTools(db_url=os.getenv("DATABASE_URL"), allow_update=True)
    try:
        set_clause = ", ".join([f"{k} = %({k})s" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause} RETURNING id"
        
        result = sql_tools.run_sql_query(query, parameters=data)
        return json.dumps({
            "message": "Update successful",
            "count": len(result.get("rows", []))
        })
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "Update failed"
        })

@tool(name="get_schema", description="Fetches the database schema for specified tables or all tables if none specified.")
def get_schema(tables: str = None) -> Dict[str, Any]:
    """Fetches database schema information."""
    sql_tools = SafeSQLTools(db_url=os.getenv("DATABASE_URL"))
    try:
        # Query to get table schema with descriptions
        query = """
        WITH table_comments AS (
            SELECT 
                c.relname as table_name,
                pd.description as table_description
            FROM pg_class c
            LEFT JOIN pg_description pd ON c.oid = pd.objoid AND pd.objsubid = 0
            WHERE c.relkind = 'r' AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        ),
        column_info AS (
            SELECT 
                c.table_name,
                jsonb_agg(
                    jsonb_build_object(
                        'column_name', c.column_name,
                        'data_type', c.data_type,
                        'is_nullable', c.is_nullable,
                        'column_default', c.column_default,
                        'description', pd.description
                    ) ORDER BY c.ordinal_position
                ) as columns
            FROM information_schema.columns c
            LEFT JOIN pg_class pc ON c.table_name = pc.relname
            LEFT JOIN pg_description pd ON 
                pc.oid = pd.objoid AND 
                c.ordinal_position = pd.objsubid
            WHERE c.table_schema = 'public'
            GROUP BY c.table_name
        )
        SELECT 
            ci.table_name,
            tc.table_description,
            ci.columns
        FROM column_info ci
        LEFT JOIN table_comments tc ON ci.table_name = tc.table_name
        """

        parameters = {}
        if tables:
            table_list = [t.strip() for t in tables.split(',')]
            query += " WHERE ci.table_name = ANY(%(table_list)s)"
            parameters["table_list"] = table_list

        query += " ORDER BY table_name"

        result = sql_tools.run_sql_query(query, parameters=parameters)

        # Format the schema info into a structured dictionary
        schema_info: Dict[str, Any] = {}
        for table in result.get("rows", []):
            table_name = table["table_name"]
            schema_info[table_name] = {
                "description": table["table_description"],
                "columns": [
                    {
                        "name": col["column_name"],
                        "data_type": col["data_type"],
                        "is_nullable": col["is_nullable"] == "YES",
                        "default": col["column_default"],
                        "description": col["description"],
                    }
                    for col in table["columns"]
                ],
            }

        return schema_info

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to fetch schema",
        } 