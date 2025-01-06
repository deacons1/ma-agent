from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import logging

from src.agent.agent_factory import AgentFactory, AgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="PhiAgent API")

# Create agent factory with default config
factory = AgentFactory()

class PromptRequest(BaseModel):
    """Request model for prompt endpoint"""
    message: str
    user_id: Optional[str] = "0d2425a9-0663-4795-b9cb-52b1343a82de"
    run_id: Optional[str] = None

class PromptResponse(BaseModel):
    """Response model for prompt endpoint"""
    response: str
    run_id: Optional[str]
    status: str = "success"

@app.post("/prompt", response_model=PromptResponse)
async def handle_prompt(request: PromptRequest) -> PromptResponse:
    """Handle an agent prompt request"""
    try:
        # Create standard agent instance with user context
        agent = factory.create_standard_agent(
            run_id=request.run_id,
            user_id=request.user_id
        )
        
        # Get response from agent
        run_response = agent.run(request.message)
        
        return PromptResponse(
            response=run_response.content,
            run_id=agent.run_id,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "status": "error",
                "message": "Failed to process prompt"
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": os.getenv("APP_VERSION", "1.0.0")
    } 