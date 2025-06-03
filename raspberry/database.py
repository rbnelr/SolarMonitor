import mysql.connector
from contextlib import contextmanager

def get_db_conn(use_vz_db=False):
    from dotenv import dotenv_values
    import os

    config = dotenv_values(os.path.abspath("database.env"))

    if use_vz_db:
        config["DB_NAME"] = "volkszaehler"

    return mysql.connector.connect(
        host = config["DB_HOST"],
        port = config["DB_PORT"],
        user = config["DB_USER"],
        password = config["DB_PASSWORD"],
        database = config["DB_NAME"]
    )

# HACK: pull volkszeahler db for now
@contextmanager
def get_vz_db_cursor():
    with get_db_conn(use_vz_db=True) as conn:
        cursor = conn.cursor(buffered=True) # TODO: buffered? raw? Depends on if I want to work with json, numpy etc
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

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

# doing this to lazily create the tables used to work I think, but now gives error for some reason
def create_tables():
    with get_db_cursor() as cur:
        #cur.execute("DROP TABLE IF EXISTS data")
        
        # type -> power, energy
        # unit ->
        cur.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel_id INT(3) PRIMARY KEY NOT NULL AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE,
                type VARCHAR(20) NOT NULL,
                unit VARCHAR(20) NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS data (
                channel_id INT(3) NOT NULL,
                timestamp BIGINT(20) NOT NULL,
                value FLOAT NOT NULL,
                PRIMARY KEY (channel_id, timestamp)
            )
        """)
        cur.execute("""
            ALTER TABLE data ADD CONSTRAINT fk_channel_id FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
        """)
    
def get_or_create_channels():
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT IGNORE INTO channels (name, type, unit)
            VALUES ('solar_power', 'power', 'W')
        """)
        cur.execute("SELECT channel_id FROM channels WHERE name = 'solar_power'")
        power_id = cur.fetchone()[0]

        cur.execute("""
            INSERT IGNORE INTO channels (name, type, unit)
            VALUES ('solar_power_by_minute', 'power', 'W')
        """)
        cur.execute("SELECT channel_id FROM channels WHERE name = 'solar_power_by_minute'")
        power_by_minute_id = cur.fetchone()[0]

        #print(f"power: {power_id}, power_by_minute: {power_by_minute_id}")
        return power_id, power_by_minute_id

def get_channels(cur):
    cur.execute("SELECT channel_id FROM channels WHERE name = 'solar_power'")
    power_id = cur.fetchone()[0]

    cur.execute("SELECT channel_id FROM channels WHERE name = 'solar_power_by_minute'")
    power_by_minute_id = cur.fetchone()[0]

    return power_id, power_by_minute_id
