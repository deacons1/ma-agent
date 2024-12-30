from src.agent.sql_agent import sql_agent
from phi.utils.pprint import pprint_run_response

def main():
    user_message = "Add a Krav Maga class for Monday at 6pm"
    response_stream = sql_agent.run(user_message, stream=True)
    pprint_run_response(response_stream, markdown=True)

if __name__ == "__main__":
    main() 