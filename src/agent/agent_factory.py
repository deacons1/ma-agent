import os
import logging
from typing import Optional, Callable

from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.tools.sql import SQLTools
from phi.tools.twilio import TwilioTools

from ..db.message_logger import MessageLogger
from ..db.organization_service import OrganizationService

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentFactory:
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

    Table: contacts
    - Columns:
        id (uuid primary key),
        first_name (text),
        last_name (text),
        phone (text),
        email (text),
        location_id (uuid),
        motivations (array of text),
        pain_points (array of text),
        membership_status (array of text)
    """

    def __init__(self, db_engine, knowledge_base):
        self.db_engine = db_engine
        self.knowledge_base = knowledge_base
        self.message_logger = MessageLogger(db_engine)
        self.org_service = OrganizationService(db_engine)

    def _create_message_callback(self, user: str) -> Callable[[str, str], None]:
        """
        Creates a message callback function that will be called after each interaction.
        
        Args:
            user: The user ID to associate with logged messages (UUID string)
            
        Returns:
            A callback function that takes user_message and ai_response as arguments
        """
        def callback(user_message: str, ai_response: str) -> None:
            """Internal callback function to log messages"""
            logger.info("=== Message Callback Triggered ===")
            logger.info(f"User ID: {user}")
            
            try:
                self.message_logger.log_message(user, user_message, ai_response)
                logger.info("Message successfully logged to database")
            except Exception as e:
                logger.error("Failed to log message to database")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error message: {str(e)}")
        
        return callback

    def create_agent(self, organization_id: str, run_id: Optional[str] = None, user: str = "0d2425a9-0663-4795-b9cb-52b1343a82de") -> Agent:
        """
        Creates and configures a new Agent instance.
        
        Args:
            organization_id: The UUID of the organization
            run_id: Optional run ID for the agent
            user: The user ID (defaults to the specified UUID)
            
        Returns:
            A configured Agent instance
        """
        # Validate Twilio configuration
        twilio_from_number = os.environ.get("TWILIO_FROM_NUMBER")
        if not twilio_from_number:
            raise ValueError("TWILIO_FROM_NUMBER environment variable not set!")

        # Get organization info
        organization_info = self.org_service.get_organization_info(organization_id)

        # Create the message callback
        message_callback = self._create_message_callback(user)
        
        logger.info("Creating agent with message callback")
        
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
            description=self.SCHEMA_INFO + "\n\n" + organization_info,
            instructions=[
                "You are an AI Agent that can create or modify records in the martial_arts_crm database by generating PostgreSQL queries.",
                "Always respond concisely and directly to the user, summarizing what you did or found.  The user is not interested in the tool calls you made or the database queries you ran.",
                "Use the schema info to ensure your queries are correct. If something is unclear, ask clarifying questions.",
                "Use the knowledge base to follow best practices for schedule and contact management."
            ],
            tools=[
                SQLTools(db_engine=self.db_engine, dialect="postgresql"),
                TwilioTools(),
            ],
            knowledge_base=self.knowledge_base,
            search_knowledge=True,
            add_history_to_messages=True,
            num_history_responses=5,
            show_tool_calls=False,
            markdown=True,
            message_callback=message_callback
        )

        # Load the knowledge base
        agent.knowledge.load(recreate=False)
        
        # Verify the callback is registered
        if not hasattr(agent, '_message_callback') or agent._message_callback is None:
            logger.error("Message callback was not properly registered with the agent!")
        else:
            logger.info("Message callback successfully registered with agent")

        return agent 