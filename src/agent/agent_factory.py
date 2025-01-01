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

    def __init__(self, db_url: str):
        self.db_url = db_url
        
    def create_agent(self, model: Optional[str] = None) -> Agent:
        """Create a new agent instance with SQL and Twilio tools"""
        return Agent(
            model=Claude(id=model or os.getenv("ANTHROPIC_MODEL")),
            tools=[
                SQLTools(db_url=self.db_url),
                TwilioTools()
            ],
            instructions=self.SCHEMA_INFO,
            show_tool_calls=True,
            read_chat_history=True,
            markdown=True
        ) 