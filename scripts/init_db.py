import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_database():
    try:
        # Connect to PostgreSQL server using the same configuration as the app
        conn = psycopg2.connect(
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create a cursor
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'travel_recommender'")
        exists = cur.fetchone()
        
        if not exists:
            # Create database
            cur.execute('CREATE DATABASE travel_recommender')
            print("Database 'travel_recommender' created successfully")
        else:
            print("Database 'travel_recommender' already exists")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    init_database() 