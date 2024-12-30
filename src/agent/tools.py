from typing import Dict, Any
import json
import os
from phi.tools.sql import SQLTools
from phi.tools import tool

@tool(name="run_sql_query", description="Executes a raw SQL query on the martial_arts_crm database and returns JSON.")
def run_sql_query(query: str) -> str:
    """Executes SQL queries using Supabase Postgres."""
    sql_tools = SQLTools(db_url=os.getenv("DATABASE_URL"))
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