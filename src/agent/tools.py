from typing import Dict, Any, List
import json
import os
from phi.tools.sql import SQLTools
from phi.tools import tool
from ..db.config import get_db_url

@tool(name="get_schema", description="Fetches the database schema for specified tables or all tables if none specified.")
def get_schema(tables: str = None) -> Dict[str, Any]:
    """Fetches database schema information.
    Args:
        tables: Optional comma-separated list of table names. If None, fetches all tables.
    """
    sql_tools = SQLTools(db_url=get_db_url(use_connection_pooling=True))
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
        print("DEBUG - Raw Query Result:")
        print(json.dumps(result, indent=2))

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

        print("DEBUG - Formatted Schema Info:")
        print(schema_info)
        return schema_info

    except Exception as e:
        print("DEBUG - Error in get_schema:")
        print(str(e))
        return {
            "error": str(e),
            "message": "Failed to fetch schema",
        }

@tool(name="run_sql_query", description="Executes a raw SQL query on the martial_arts_crm database and returns JSON.")
def run_sql_query(query: str) -> str:
    """Executes SQL queries using Supabase Postgres."""
    sql_tools = SQLTools(db_url=get_db_url(use_connection_pooling=True))
    try:
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