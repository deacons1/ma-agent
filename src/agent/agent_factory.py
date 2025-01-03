import os
import logging
from typing import Optional, Callable

from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.tools.twilio import TwilioTools

from ..db.message_logger import MessageLogger
from ..db.organization_service import OrganizationService
from .tools import get_schema, select_query, insert_data, update_data

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentFactory:

    def __init__(self, db_url: str):
        self.db_url = db_url
        
    def create_agent(self, model: Optional[str] = None) -> Agent:
        """Create a new agent instance with SQL and Twilio tools"""
        return Agent(
            model=Claude(id=model or os.getenv("ANTHROPIC_MODEL")),
            tools=[
                select_query,  # Read-only SQL queries
                insert_data,   # Safe insert operations
                update_data,   # Safe update operations
                get_schema,    # Schema inspection
                TwilioTools(),
            ],
            show_tool_calls=True,
            read_chat_history=True,
            markdown=True
        ) 