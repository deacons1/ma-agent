import os
from dotenv import load_dotenv
import logging

from .agent_factory import AgentFactory, AgentConfig
from .semantic_model_agent import semantic_model_agent
from .tools import run_sql_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SQLAgent:
    """SQL Agent that uses semantic model for schema validation and access control"""
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig(
            model_name=os.getenv("ANTHROPIC_MODEL", "claude-2"),
            show_tool_calls=True,
            markdown=True,
            monitoring=True,
            storage_table="sql_assistant"
        )
        self.factory = AgentFactory(self.config)
        self.agent = self.factory.create_sql_agent()
        
    def get_schema(self, tables: str = None) -> dict:
        """Get schema information using the semantic model agent"""
        return semantic_model_agent.get_semantic_model(tables)
        
    def execute_query(self, query: str, user_id: str = None) -> dict:
        """Execute a SQL query after validation through semantic model"""
        if user_id and not semantic_model_agent.validate_query(query, user_id):
            return {
                "error": "Access denied: Query references unauthorized tables",
                "status": "error"
            }
            
        try:
            result = run_sql_query(query)
            return {
                "result": result,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
            
    def get_table_relationships(self) -> list:
        """Get table relationships from semantic model"""
        return semantic_model_agent.get_table_relationships()

# Create SQL agent instance
sql_agent = SQLAgent() 