import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
from src.rivex.database.config_database import DatabaseBase, ConexaoDatabaseRivex