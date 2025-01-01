import os
from dotenv import load_dotenv
from src.agent.agent_factory import AgentFactory
from phi.utils.pprint import pprint_run_response

def main():
    # Load environment variables
    load_dotenv()
    
    # Create agent factory and agent
    factory = AgentFactory(db_url=os.getenv("DATABASE_URL"))
    agent = factory.create_agent()
    
    # Run the agent
    user_message = "Add a Krav Maga class for Monday at 6pm"
    response_stream = agent.run(user_message, stream=True)
    pprint_run_response(response_stream, markdown=True)

if __name__ == "__main__":
    main() 