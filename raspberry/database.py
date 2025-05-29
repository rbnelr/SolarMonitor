import mysql.connector
from contextlib import contextmanager

def get_db_conn():
    from dotenv import load_dotenv
    import os

    load_dotenv(os.path.abspath("database.env"))

    return mysql.connector.connect(
        host = os.getenv("DB_HOST"),
        port = os.getenv("DB_PORT"),
        user = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        database = os.getenv("DB_NAME")
    )

@contextmanager
def get_db_cursor():
    with get_db_conn() as conn:
        cursor = conn.cursor(buffered=True) # TODO: buffered? raw? Depends on if I want to work with json, numpy etc
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

def create_tables():
    with get_db_cursor() as cur:
        #cur.execute("DROP TABLE IF EXISTS data")
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS data (
                channel_id INT(3) NOT NULL,
                timestamp BIGINT(20) NOT NULL,
                value FLOAT NOT NULL,
                PRIMARY KEY (channel_id, timestamp)
            )
        """)
    
