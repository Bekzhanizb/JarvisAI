import os
from dotenv import load_dotenv


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


DB_CONFIG = {
"dbname": "shyraq_db",
"user": "postgres",
"password": "1234",
"host": "localhost",
"port": 5432
}