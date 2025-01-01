from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.storage.assistant.postgres import PgAssistantStorage
from phi.tools.sql import SQLTools
import os
from .tools import run_sql_query, get_schema

def get_current_schema():
    """Fetch the current database schema"""
    schema_info = get_schema()
    print("DEBUG - Schema Info:")
    print(schema_info)
    return schema_info

sql_agent = Agent(
    model=Claude(id=os.getenv("ANTHROPIC_MODEL")),
    tools=[run_sql_query, get_schema],
    storage=PgAssistantStorage(
        table_name="martial_arts_assistant",
        db_url=os.getenv("DATABASE_URL")
    ),
    show_tool_calls=True,
    read_chat_history=True,
    markdown=True,
    debug_mode=True,
    monitoring=True,
    instructions=f"""You are a SQL assistant that helps users query a PostgreSQL database.
{get_current_schema()}

When searching text fields, use ILIKE for case-insensitive pattern matching.
Example: WHERE short_name ILIKE '%search_term%'
"""
) 