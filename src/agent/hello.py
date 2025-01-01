import os
from typing import Optional, List
from urllib.parse import urlparse
from dataclasses import dataclass
from dotenv import load_dotenv

from phi.agent import Agent
from phi.model.anthropic import Claude
from phi.tools.postgres import PostgresTools
from phi.tools.twilio import TwilioTools
from phi.storage.agent.postgres import PgAgentStorage

from knowledge_base import knowledge_base

AGENT_INSTRUCTIONS = """You are a powerful agentic AI assistant designed to help users with their tasks.
You have access to a PostgreSQL database and can:
- Query and analyze data
- Summarize table structures
- Inspect queries before execution
- Export table data when needed

Guidelines:
1. Always validate inputs and queries before execution
2. Provide clear explanations of your actions.  You do not need to explain every tool call or interactions with the database.
3. If unsure about a query's impact, ask for confirmation
4. Keep responses concise and focused on the initital question or request asked.  Don't provide a play by play of your actions.

You also have access to Twilio for communication capabilities when needed.

The table structure is as follows:

organizations table:
- id (uuid, primary key)
- name (text, not null)
- created_at (timestamp with time zone, not null)
- updated_at (timestamp with time zone, not null)

locations table:
- id (uuid, primary key)
- short_name (text, not null)
- street (text, not null)
- city (text, not null)
- state (text, not null)
- zip_code (text, not null)
- phone_number (text, not null)
- organization_id (uuid, not null, foreign key to organizations.id)
- created_at (timestamp with time zone, not null)
- updated_at (timestamp with time zone, not null)

programs table:
- id (uuid, primary key)
- name (text, not null)
- min_age (integer, not null, default: 0)
- max_age (integer, not null, default: 99)
- description (text, not null)
- location_id (uuid, not null, foreign key to locations.id)
- created_at (timestamp with time zone, not null)
- updated_at (timestamp with time zone, not null)

class_schedules table:
- id (uuid, primary key)
- class_name (text, not null)
- program_id (uuid, not null, foreign key to programs.id)
- day_of_week (integer, not null)
- start_time (time without time zone, not null)
- end_time (time without time zone, not null)
- created_at (timestamp with time zone, not null)
- updated_at (timestamp with time zone, not null)

"""

@dataclass
class DatabaseConfig:
    """Database configuration parsed from URL"""
    host: str
    port: int
    name: str
    user: str
    password: str
    url: str

    @classmethod
    def from_url(cls, db_url: str) -> 'DatabaseConfig':
        """Create DatabaseConfig from URL string"""
        if not db_url:
            raise ValueError("Database URL is required")
        
        parsed = urlparse(db_url)
        return cls(
            host=parsed.hostname,
            port=parsed.port or 5432,
            name=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            url=db_url
        )

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

class AgentFactory:
    """Factory class for creating and configuring agents"""
    
    def __init__(self, db_config: DatabaseConfig, agent_config: AgentConfig = AgentConfig()):
        self.db_config = db_config
        self.agent_config = agent_config
    
    def create_storage(self) -> PgAgentStorage:
        """Create and configure agent storage"""
        return PgAgentStorage(
            table_name="agent_sessions",
            db_url=self.db_config.url,
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
            PostgresTools(
                host=self.db_config.host,
                port=self.db_config.port,
                db_name=self.db_config.name,
                user=self.db_config.user,
                password=self.db_config.password,
                run_queries=True,
                inspect_queries=True,
                summarize_tables=True
            ),
            TwilioTools(),
        ]
    
    def create_agent(self, run_id: Optional[str] = None, user_id: str = "0d2425a9-0663-4795-b9cb-52b1343a82de") -> Agent:
        """Create a fully configured agent"""
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
            instructions=self.agent_config.instructions,
            monitoring=True,
        )
        
        # Load the knowledge base
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
    # Load environment variables
    load_dotenv()
    
    # Validate environment
    validate_environment()
    
    # Parse configuration
    db_config = DatabaseConfig.from_url(os.getenv("DATABASE_URL"))
    
    # Create agent factory
    factory = AgentFactory(db_config)
    
    # Create agent with configuration
    agent = factory.create_agent(user_id=os.getenv("USER_ID", "0d2425a9-0663-4795-b9cb-52b1343a82de"))
    
    print("Started new session (with PostgreSQL message storage).")
    # Run CLI loop
    agent.cli_app(markdown=True)

if __name__ == "__main__":
    main()
