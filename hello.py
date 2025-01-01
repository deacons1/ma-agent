import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.tools.sql import SQLTools
from phi.tools.twilio import TwilioTools
from phi.storage.agent.postgres import PgAgentStorage

from knowledge_base import knowledge_base

def get_database_engine():
    """
    Creates and returns a SQLAlchemy engine for database interaction.
    
    Returns:
        SQLAlchemy engine instance
    
    Raises:
        ValueError: If DATABASE_URL environment variable is not properly configured
    """
    raw_db_url = os.environ.get("DATABASE_URL")
    if not raw_db_url:
        raise ValueError("DATABASE_URL environment variable is required")

    # Convert URL to SQLAlchemy format if needed
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw_db_url.startswith("postgresql://"):
        raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    return create_engine(raw_db_url)

def validate_environment():
    """
    Validates all required environment variables are set.
    
    Raises:
        ValueError: If any required environment variable is missing
    """
    required_vars = ["ANTHROPIC_API_KEY", "ORGANIZATION_ID", "DATABASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def create_agent(organization_id: str, run_id: str = None, user: str = "0d2425a9-0663-4795-b9cb-52b1343a82de"):
    """
    Create an Agent with PostgreSQL storage for message history.
    """
    db_engine = get_database_engine()
    
    # Create storage for the agent
    storage = PgAgentStorage(
        table_name="agent_sessions",
        db_url=os.environ.get("DATABASE_URL"),
        auto_upgrade_schema=True
    )
    
    # Create and configure the agent
    agent = Agent(
        run_id=run_id,
        user_id=user,
        model=Claude(
            id=os.getenv("ANTHROPIC_MODEL", "gpt4o"),
            name="Claude",
            provider="Anthropic",
            max_tokens=1024,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        ),
        storage=storage,
        tools=[
            SQLTools(db_engine=db_engine, dialect="postgresql"),
            TwilioTools(),
        ],
        knowledge_base=knowledge_base,
        search_knowledge=True,
        add_history_to_messages=True,
        num_history_responses=5,
        show_tool_calls=False,
        markdown=True
    )
    
    # Load the knowledge base
    agent.knowledge.load(recreate=False)
    
    return agent

def main():
    """
    Main function to run the agent in a CLI loop.
    """
    # Load environment variables
    load_dotenv()
    
    # Validate environment
    validate_environment()
    
    # Get configuration
    organization_id = os.getenv("ORGANIZATION_ID")
    user_id = "0d2425a9-0663-4795-b9cb-52b1343a82de"
    
    # Create agent
    agent = create_agent(organization_id, user=user_id)
    
    print("Started new session (with PostgreSQL message storage).")
    # Run CLI loop
    agent.cli_app(markdown=True)

if __name__ == "__main__":
    main()
