from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.storage.agent.postgres import PgAgentStorage
import os
from .tools import run_sql_query, get_schema

# Use get_schema directly in instructions
schema_info = get_schema()

sql_agent = Agent(
    model=Claude(id=os.getenv("ANTHROPIC_MODEL")),
    tools=[run_sql_query, get_schema],
    storage=PgAgentStorage(
        table_name="martial_arts_assistant",
        db_url=os.getenv("DATABASE_URL")
    ),
    show_tool_calls=True,
    read_chat_history=True,
    markdown=True,
    debug_mode=True,
    monitoring=True,
    instructions=f"""You are a SQL assistant that helps users query a PostgreSQL database.
{schema_info}

When searching text fields, use ILIKE for case-insensitive pattern matching.
Example: WHERE short_name ILIKE '%search_term%'
"""
) 