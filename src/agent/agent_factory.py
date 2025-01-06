import os
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.tools.sql import SQLTools
from phi.tools.twilio import TwilioTools
from phi.storage.agent.postgres import PgAgentStorage

from ..db.config import get_db_url
from .tools import get_schema, run_sql_query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for agent instances"""
    model_name: str = os.getenv("ANTHROPIC_MODEL", "claude-2")
    model_provider: str = "Anthropic"
    max_tokens: int = 1024
    search_knowledge: bool = True
    add_history_to_messages: bool = True
    num_history_responses: int = 5
    show_tool_calls: bool = True
    markdown: bool = True
    monitoring: bool = True
    storage_table: str = "agent_sessions"

class AgentFactory:
    """Unified factory for creating different types of agents"""
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        
    def create_model(self) -> Claude:
        """Create and configure the LLM model"""
        return Claude(
            id=self.config.model_name,
            name="Claude",
            provider=self.config.model_provider,
            max_tokens=self.config.max_tokens,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    
    def create_storage(self, table_name: str = None) -> PgAgentStorage:
        """Create and configure agent storage"""
        return PgAgentStorage(
            table_name=table_name or self.config.storage_table,
            db_url=get_db_url(use_connection_pooling=True),
            auto_upgrade_schema=True
        )
    
    def create_base_tools(self) -> List:
        """Create base set of tools used by all agents"""
        return [
            SQLTools(db_url=get_db_url(use_connection_pooling=True)),
            TwilioTools(),
        ]

    def get_org_data(self, user_id: str) -> str:
        """Fetch organization data for user context"""
        sql = SQLTools(db_url=get_db_url(use_connection_pooling=True))
        query = """
        WITH user_org AS (
            SELECT organization_id 
            FROM profiles 
            WHERE id = %(user_id)s
        )
        SELECT 
            o.id as organization_id,
            o.name as organization_name,
            l.id as location_id,
            l.short_name as location_name,
            p.id as program_id,
            p.name as program_name
        FROM user_org
        JOIN organizations o ON o.id = user_org.organization_id
        LEFT JOIN locations l ON l.organization_id = o.id
        LEFT JOIN programs p ON p.location_id = l.id
        ORDER BY o.name, l.short_name, p.name;
        """
        try:
            results = sql.query(query, parameters={"user_id": user_id})
            
            if not results:
                return "No organization data found for this user."
            
            formatted = "Current Organization Structure:\n"
            for row in results:
                formatted += f"\nOrg: {row['organization_name']} ({row['organization_id']})"
                if row['location_id']:
                    formatted += f"\n  Location: {row['location_name']} ({row['location_id']})"
                    if row['program_id']:
                        formatted += f"\n    Program: {row['program_name']} ({row['program_id']})"
            
            return formatted
        except Exception as e:
            logger.error(f"Error fetching organization data: {e}")
            return f"Error fetching organization data: {str(e)}"

    def create_standard_agent(
        self,
        run_id: Optional[str] = None,
        user_id: str = None,
        instructions: str = None
    ) -> Agent:
        """Create a standard agent with full capabilities"""
        if instructions:
            if user_id:
                org_data = self.get_org_data(user_id)
                instructions = f"{instructions}\n\n{org_data}"
        
        return Agent(
            run_id=run_id,
            user_id=user_id,
            model=self.create_model(),
            storage=self.create_storage(),
            tools=self.create_base_tools(),
            search_knowledge=self.config.search_knowledge,
            add_datetime_to_instructions=True,
            add_history_to_messages=self.config.add_history_to_messages,
            num_history_responses=self.config.num_history_responses,
            show_tool_calls=self.config.show_tool_calls,
            markdown=self.config.markdown,
            instructions=instructions,
            monitoring=self.config.monitoring,
        )

    def create_sql_agent(self) -> Agent:
        """Create an agent specialized for SQL operations"""
        return Agent(
            model=self.create_model(),
            tools=[get_schema, run_sql_query],
            storage=self.create_storage("sql_assistant"),
            show_tool_calls=self.config.show_tool_calls,
            read_chat_history=True,
            markdown=self.config.markdown,
            monitoring=self.config.monitoring,
            instructions="""You are a SQL assistant that helps users query a PostgreSQL database.

When searching text fields, use ILIKE for case-insensitive pattern matching.
Example: WHERE short_name ILIKE '%search_term%'
"""
        ) 