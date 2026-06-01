import psycopg2
from psycopg2 import Error
import os

def get_db_connection():
    try:
        # For Render deployment
        if os.environ.get('RENDER'):
            connection = psycopg2.connect(
                host=os.environ.get('PGHOST'),
                database=os.environ.get('PGDATABASE'),
                user=os.environ.get('PGUSER'),
                password=os.environ.get('PGPASSWORD'),
                port=os.environ.get('PGPORT', 5432),
                sslmode='require'
            )
        else:
            # Local development
            connection = psycopg2.connect(
                host='localhost',
                database='perfume_shop',
                user='postgres',
                password='',  # Your local PostgreSQL password
                port=5432
            )
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None
