from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.storage.assistant.postgres import PgAssistantStorage
from phi.tools.sql import SQLTools
import os
from .tools import run_sql_query

sql_agent = Agent(
    model=Claude(id=os.getenv("ANTHROPIC_MODEL")),
    tools=[run_sql_query],
    storage=PgAssistantStorage(
        table_name="martial_arts_assistant",
        db_url=os.getenv("DATABASE_URL")
    ),
    show_tool_calls=True,
    read_chat_history=True,
    markdown=True
) 

SCHEMA_INFO = """
You have access to a Postgres database with the following tables:

Table: class_schedules
- Columns:
    id (uuid primary key),
    class_name (text),
    program_id (uuid),
    day_of_week (integer, 0=Sunday, 1=Monday, ... 6=Saturday),
    start_time (time),
    end_time (time),
    created_at (timestamp with time zone)

Table: programs
- Columns:
    id (uuid primary key),
    name (text),
    min_age (integer),
    max_age (integer),
    description (text),
    location_id (uuid),
    created_at (timestamp with time zone)

Table: locations
- Columns:
    id (uuid primary key),
    short_name (text),
    street (text),
    city (text),
    state (text),
    zip_code (text),
    phone_number (text),
    organization_id (uuid),
    created_at (timestamp with time zone)

When searching text fields, use ILIKE for case-insensitive pattern matching.
Example: WHERE short_name ILIKE '%search_term%'
""" 