import os
from typing import Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv

from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.tools.sql import SQLTools
from phi.tools.twilio import TwilioTools
from phi.storage.agent.postgres import PgAgentStorage

from knowledge_base import knowledge_base
from ..db.config import get_db_url



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
4. Keep responses concise and focused on the initital question or request asked.  Don't provide a play by play of your actions.

You also have access to Twilio for communication capabilities when needed.
"""

@dataclass
class AgentConfig:
    """Configuration for the agent"""
    model_name: str = os.getenv("ANTHROPIC_MODEL", "gpt4o")
    model_provider: str = "Anthropic"
    max_tokens: int = 1024
    search_knowledge: bool = True
    add_history_to_messages: bool = True
    num_history_responses: int = 5
    show_tool_calls: bool = False
    markdown: bool = True
    instructions: str = AGENT_INSTRUCTIONS

def get_org_data(user_id: str) -> str:
    """Fetch organization data and format it for instructions"""
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
        return f"Error fetching organization data: {str(e)}"

class AgentFactory:
    """Factory class for creating and configuring agents"""
    
    def __init__(self, agent_config: AgentConfig = AgentConfig()):
        self.agent_config = agent_config
    
    def create_storage(self) -> PgAgentStorage:
        """Create and configure agent storage"""
        return PgAgentStorage(
            table_name="agent_sessions",
            db_url=get_db_url(use_connection_pooling=True),
            auto_upgrade_schema=True
        )
    
    def create_model(self) -> Claude:
        """Create and configure the LLM model"""
        return Claude(
            id=os.getenv("ANTHROPIC_MODEL", self.agent_config.model_name),
            name="Claude",
            provider=self.agent_config.model_provider,
            max_tokens=self.agent_config.max_tokens,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    
    def create_tools(self) -> List:
        """Create and configure agent tools"""
        return [
            SQLTools(db_url=get_db_url(use_connection_pooling=True)),
            TwilioTools(),
        ]
    
    def create_agent(self, run_id: Optional[str] = None, user_id: str = "0d2425a9-0663-4795-b9cb-52b1343a82de") -> Agent:
        """Create a fully configured agent"""
        # Get organization data for this user
        org_data = get_org_data(user_id)
        
        # Update instructions with org data
        instructions = AGENT_INSTRUCTIONS + "\n\n" + org_data
        
        agent = Agent(
            run_id=run_id,
            user_id=user_id,
            model=self.create_model(),
            storage=self.create_storage(),
            tools=self.create_tools(),
            knowledge_base=knowledge_base,
            search_knowledge=self.agent_config.search_knowledge,
            add_datetime_to_instructions=True,
            add_history_to_messages=self.agent_config.add_history_to_messages,
            num_history_responses=self.agent_config.num_history_responses,
            show_tool_calls=self.agent_config.show_tool_calls,
            markdown=self.agent_config.markdown,
            instructions=instructions,
            monitoring=True,
        )
        
        # Load the knowledge base test
        agent.knowledge.load(recreate=False)
        return agent

def validate_environment() -> None:
    """Validate required environment variables"""
    required_vars = ["ANTHROPIC_API_KEY", "ORGANIZATION_ID", "DATABASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def main() -> None:
    """Main application entry point"""
    # Load environment variables hello
    load_dotenv()
    
    # Validate environment
    validate_environment()
    
    # Create agent factory
    factory = AgentFactory()
    
    # Create agent with configuration
    agent = factory.create_agent(user_id=os.getenv("USER_ID", "0d2425a9-0663-4795-b9cb-52b1343a82de"))
    
    print("Started new session (with PostgreSQL message storage).")
    # Run CLI loop
    agent.cli_app(markdown=True)

if __name__ == "__main__":
    main()
