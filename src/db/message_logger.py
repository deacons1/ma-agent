import logging
from sqlalchemy import text, inspect
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
import traceback
import uuid

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageLogger:
    def __init__(self, db_engine):
        self.db_engine = db_engine

    def log_message(self, user_id: str, user_message: str, ai_response: str, is_good_response: Optional[bool] = True):
        """
        Logs messages to the agent_messages table.
        
        Args:
            user_id: The ID of the user (UUID string)
            user_message: The message from the user
            ai_response: The response from the AI
            is_good_response: Optional flag to mark if the response was good
        """
        try:
            # Input validation
            if not user_id or not isinstance(user_id, str):
                raise ValueError(f"Invalid user_id: {user_id}")
            try:
                # Convert string to UUID to validate format
                user_uuid = uuid.UUID(user_id)
            except ValueError as e:
                raise ValueError(f"Invalid UUID format for user_id: {user_id}")
                
            if not user_message or not isinstance(user_message, str):
                raise ValueError(f"Invalid user_message: {user_message}")
            if not ai_response or not isinstance(ai_response, str):
                raise ValueError(f"Invalid ai_response: {ai_response}")
            
            with self.db_engine.begin() as connection:
                logger.info(f"Logging message for user {user_id}")
                
                query = text("""
                    INSERT INTO agent_messages 
                    (user_id, user_message, ai_response, is_good_response)
                    VALUES 
                    (:user_id, :user_message, :ai_response, :is_good_response)
                    RETURNING id, created_at
                """)
                
                params = {
                    "user_id": user_uuid,  # Use the UUID object
                    "user_message": user_message,
                    "ai_response": ai_response,
                    "is_good_response": is_good_response
                }
                
                # Execute the query
                result = connection.execute(query, params)
                row = result.fetchone()
                
                if row:
                    logger.info(f"Successfully logged message - ID: {row.id}, Created at: {row.created_at}")
                else:
                    logger.error("Insert succeeded but no ID was returned")
                
        except SQLAlchemyError as e:
            logger.error("Database error while logging message")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            raise
        except Exception as e:
            logger.error("Unexpected error while logging message")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            raise 