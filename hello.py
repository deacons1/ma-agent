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

def get_database_engine():
    """
    Creates and returns a SQLAlchemy engine for database interaction.

    The function retrieves the database URL from the environment variables,
    adjusts the URL format for SQLAlchemy compatibility, and then creates
    an engine object.

    Returns:
        engine: A SQLAlchemy engine object connected to the database.
    """
    raw_db_url = os.environ["DATABASE_URL"]
    db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(db_url)

def validate_environment_variables():
    """
    Validates the presence of required environment variables.

    Raises:
        ValueError: If the ANTHROPIC_API_KEY environment variable is not set.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

@tool(name="run_sql_query", description="Executes a raw SQL query on the martial_arts_crm database and returns JSON.")
def run_sql_query(query: str) -> str:
    """
    Executes SQL queries using SQL Postgres.
    Returns results in JSON format.
    
    Args:
        query: The SQL query string to execute.
    
    Returns:
        A JSON string containing the results of the query or an error message.
    """
    try:
        # Initialize SQLTools with the database engine and dialect
        sql_tools = SQLTools(db_engine=get_database_engine(), dialect="postgresql")
        # Execute the query using SQLTools
        result = sql_tools.run_sql_query(query)
        # Return the results in JSON format
        return json.dumps({
            "rows": result.get("rows", []),
            "count": len(result.get("rows", [])),
            "message": "Query successful"
        })
    except Exception as e:
        # Return an error message in JSON format if the query fails
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
    
    Args:
        run_id: An optional identifier for the conversation run.
        user: The user identifier.
    
    Returns:
        An instance of the Assistant configured with the specified settings.
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
    """
    Main function to run the assistant in a CLI loop.
    """
    validate_environment_variables()
    # Initialize the assistant with a default user
    assistant = get_assistant(user="user")
    print("Started new session (ephemeral memory only with the last 5 messages retained).")
    # Run a CLI loop with the assistant; conversation is kept in memory only (no DB)
    assistant.cli_app(markdown=True)

if __name__ == "__main__":
    main()
