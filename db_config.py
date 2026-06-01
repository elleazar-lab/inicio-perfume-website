import psycopg2
from psycopg2 import Error
import os

def get_db_connection():
    try:
        # Check if running on Render (production)
        if os.environ.get('RENDER'):
            connection = psycopg2.connect(
                host=os.environ.get('PGHOST'),
                database=os.environ.get('PGDATABASE'),
                user=os.environ.get('PGUSER'),
                password=os.environ.get('PGPASSWORD'),
                port=os.environ.get('PGPORT', 5432)
            )
        else:
            # Local development - you'll need PostgreSQL installed locally
            # Or comment this out and use render's database for testing
            connection = psycopg2.connect(
                host='localhost',
                database='perfume_shop',
                user='postgres',
                password=''  # Your local PostgreSQL password
            )
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None