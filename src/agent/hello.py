import os
from dotenv import load_dotenv
import logging

from .agent_factory import AgentFactory, AgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_INSTRUCTIONS = """You are a powerful agentic AI assistant designed to help users with their tasks.
You have access to a PostgreSQL database and can:
- Query and analyze data
- Summarize table structures
- Inspect queries before execution
- Insert or update data
- You can never drop data or delete data.

Guidelines:
1. Always validate inputs and queries before execution
2. Provide clear explanations of your actions.  You do not need to explain every tool call or interactions with the database.
3. If unsure about a query's impact, ask for confirmation
4. Keep responses concise and focused on the initial question or request asked.  Don't provide a play by play of your actions.

You also have access to Twilio for communication capabilities when needed.
"""

def validate_environment() -> None:
    """Validate required environment variables"""
    required_vars = ["ANTHROPIC_API_KEY", "ORGANIZATION_ID", "DATABASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def main() -> None:
    """Main application entry point"""
    # Load environment variables
    load_dotenv()
    
    # Validate environment
    validate_environment()
    
    # Create agent factory with custom config
    config = AgentConfig(
        model_name=os.getenv("ANTHROPIC_MODEL", "claude-2"),
        show_tool_calls=True,
        markdown=True,
        monitoring=True
    )
    factory = AgentFactory(config)
    
    # Create agent with configuration
    agent = factory.create_standard_agent(
        user_id=os.getenv("USER_ID", "0d2425a9-0663-4795-b9cb-52b1343a82de"),
        instructions=AGENT_INSTRUCTIONS
    )
    
    print("Started new session (with PostgreSQL message storage).")
    # Run CLI loop
    agent.cli_app(markdown=True)

if __name__ == "__main__":
    main()
