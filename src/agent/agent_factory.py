import os
import logging
from typing import Optional, Callable

from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.tools.sql import SQLTools
from phi.tools.twilio import TwilioTools

from ..db.message_logger import MessageLogger
from ..db.organization_service import OrganizationService
from .tools import get_schema

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentFactory:

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.schema_info = get_schema()
        
    def create_agent(self, model: Optional[str] = None) -> Agent:
        """Create a new agent instance with SQL and Twilio tools"""
        return Agent(
            model=Claude(id=model or os.getenv("ANTHROPIC_MODEL")),
            tools=[
                SQLTools(db_url=self.db_url),
                TwilioTools()
            ],
            instructions=self.schema_info,
            show_tool_calls=True,
            read_chat_history=True,
            markdown=True
        ) 