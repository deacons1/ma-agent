from typing import Dict, Any
import json
import os
from dotenv import load_dotenv
from supabase import create_client

# Import Assistant directly
from phi.assistant import Assistant
from phi.model.anthropic import Claude
from phi.tools import tool
from sqlalchemy import create_engine
from phi.tools.sql import SQLTools

# Load environment variables
load_dotenv()

# Use DATABASE_URL directly, converting "postgresql://" to "postgresql+psycopg2://"
raw_db_url = os.environ["DATABASE_URL"]  # Raises KeyError if not set
db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
engine = create_engine(db_url)

# Ensure ANTHROPIC_API_KEY is set
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

@tool(name="run_sql_query", description="Executes a raw SQL query on the martial_arts_crm database and returns JSON.")
def run_sql_query(query: str) -> str:
    """
    Executes SQL queries using SQL Postgres.
    Returns results in JSON format.
    """
    try:
        sql_tools = SQLTools(db_engine=engine, dialect="postgresql")
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

# Schema description for reference in the Assistant
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
"""

def get_assistant(run_id: str = None, user: str = "user"):
    """
    Create an assistant with ephemeral in-memory history (no database storage),
    keeping the last 5 messages in context.
    """
    return Assistant(
        run_id=run_id,
        user_id=user,
        model=Claude(
            id=os.getenv("ANTHROPIC_MODEL", "gpt4o"),  # Default fallback model ID
            name="Claude",
            provider="Anthropic",
            max_tokens=1024,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ),
        description=SCHEMA_INFO,
        instructions=[
            "You are an AI Assistant that can create or modify records in the martial_arts_crm database by generating PostgreSQL queries.",
            "When a user asks to add, update, or retrieve data, generate the appropriate SQL and call the run_sql_query tool with it.",
            "Always respond in JSON to the user, summarizing what you did or found.",
            "Use the schema info to ensure your queries are correct. If something is unclear, ask clarifying questions."
        ],
        tools=[run_sql_query],
        # We set this to True so previous exchanges are added to each request:
        add_history_to_messages=True,
        # Limit how many of the last messages are repeated back to the model:
        num_history_responses=5,
        show_tool_calls=True,
        markdown=True
    )

def main():
    assistant = get_assistant(user="user")
    print("Started new session (ephemeral memory only with the last 5 messages retained).")
    # Run a CLI loop with the assistant; conversation is kept in memory only (no DB)
    assistant.cli_app(markdown=True)

if __name__ == "__main__":
    main()
