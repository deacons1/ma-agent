import os
import psycopg2
from dotenv import load_dotenv

# load_dotenv will parse and load your .env file into os.environ
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]  # Now it should find it from .env
conn = psycopg2.connect(DATABASE_URL)
print("Connection succeeded!")