import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any, Optional, List

from .agent_factory import AgentFactory, AgentConfig
from .tools import get_schema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SemanticModelAgent:
    """Agent responsible for managing the semantic model of the database"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig(
            model_name=os.getenv("ANTHROPIC_MODEL", "claude-2"),
            show_tool_calls=True,
            markdown=True,
            monitoring=True,
            storage_table="semantic_model_assistant"
        )
        self.factory = AgentFactory(self.config)
        self.schema_cache: Dict[str, Any] = {}
        
    def refresh_schema(self, tables: Optional[str] = None) -> Dict[str, Any]:
        """Refresh the schema cache for specified tables or all tables"""
        try:
            schema = get_schema(tables)
            if isinstance(schema, dict) and not schema.get("error"):
                if tables:
                    # Update only specified tables
                    for table in tables.split(","):
                        table = table.strip()
                        if table in schema:
                            self.schema_cache[table] = schema[table]
                else:
                    # Update entire cache
                    self.schema_cache = schema
            return self.schema_cache
        except Exception as e:
            logger.error(f"Error refreshing schema: {e}")
            return {"error": str(e)}
            
    def get_semantic_model(self, tables: Optional[str] = None) -> Dict[str, Any]:
        """Get the semantic model for specified tables or all tables"""
        if not self.schema_cache or tables:
            self.refresh_schema(tables)
            
        if tables:
            return {table.strip(): self.schema_cache.get(table.strip()) 
                   for table in tables.split(",") 
                   if table.strip() in self.schema_cache}
        return self.schema_cache
        
    def get_table_relationships(self) -> List[Dict[str, str]]:
        """Analyze and return table relationships based on foreign key constraints"""
        relationships = []
        schema = self.get_semantic_model()
        
        for table_name, table_info in schema.items():
            for column in table_info.get("columns", []):
                # Look for columns that might be foreign keys (ends with _id)
                if column["name"].endswith("_id"):
                    referenced_table = column["name"][:-3]  # Remove _id suffix
                    if referenced_table in schema:
                        relationships.append({
                            "from_table": table_name,
                            "to_table": referenced_table,
                            "from_column": column["name"],
                            "to_column": "id"  # Assuming standard primary key name
                        })
                        
        return relationships
        
    def get_allowed_tables(self, user_id: str) -> List[str]:
        """Get list of tables the user has access to"""
        # This could be expanded to implement actual access control
        # For now, return all tables
        return list(self.get_semantic_model().keys())
        
    def validate_query(self, query: str, user_id: str) -> bool:
        """Validate if a query only accesses allowed tables for the user"""
        allowed_tables = set(self.get_allowed_tables(user_id))
        # This is a simple implementation - in practice you'd want to use a proper
        # SQL parser to analyze the query and extract all referenced tables
        query = query.lower()
        for table in allowed_tables:
            query = query.replace(table.lower(), "")
            
        # Check if any other table names remain in the query
        remaining_tables = set(self.get_semantic_model().keys())
        for table in remaining_tables:
            if table.lower() in query:
                return False
        return True

# Create semantic model agent instance
semantic_model_agent = SemanticModelAgent() 