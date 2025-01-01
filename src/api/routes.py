from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

from src.agent.hello import AgentFactory, DatabaseConfig, validate_environment

# Load environment variables
load_dotenv()
validate_environment()

# Initialize FastAPI app
app = FastAPI(title="PhiAgent API")

# Create database config and agent factory
db_config = DatabaseConfig.from_url(os.getenv("DATABASE_URL"))
factory = AgentFactory(db_config)

class PromptRequest(BaseModel):
    """Request model for prompt endpoint"""
    message: str
    user_id: Optional[str] = "0d2425a9-0663-4795-b9cb-52b1343a82de"
    run_id: Optional[str] = None

class PromptResponse(BaseModel):
    """Response model for prompt endpoint"""
    response: str
    run_id: Optional[str]

@app.post("/prompt", response_model=PromptResponse)
async def handle_prompt(request: PromptRequest) -> PromptResponse:
    """Handle an agent prompt request"""
    try:
        # Create agent instance
        agent = factory.create_agent(
            run_id=request.run_id,
            user_id=request.user_id
        )
        
        # Get response from agent
        run_response = agent.run(request.message)
        
        return PromptResponse(
            response=run_response.content,
            run_id=agent.run_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 