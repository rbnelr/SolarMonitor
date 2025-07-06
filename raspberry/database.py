from contextlib import contextmanager
import asyncio
import traceback
import timestamps as ts
import aiomysql
import mysql.connector

queue = asyncio.Queue(128)

async def get_conn_async(autocommit = False):
    from dotenv import dotenv_values
    import os

    config = dotenv_values(os.path.abspath("database.env"))

    return await aiomysql.connect(
        host = config["DB_HOST"],
        port = int(config["DB_PORT"]),
        user = config["DB_USER"],
        password = config["DB_PASSWORD"],
        db = config["DB_NAME"],
        connect_timeout = 20,
        autocommit = autocommit
    )
def get_conn():
    from dotenv import dotenv_values
    import os

    config = dotenv_values(os.path.abspath("database.env"))

    return mysql.connector.connect(
        host = config["DB_HOST"],
        port = int(config["DB_PORT"]),
        user = config["DB_USER"],
        password = config["DB_PASSWORD"],
        db = config["DB_NAME"],
        connect_timeout = 20,
    )

vz_meter_power_uuid = "37738e30-59ed-11f0-9591-9b7c17f0375b"

async def write_loop(log):
    log.info("Starting db_write_loop")

    conn = None
    while True:
        try:
            conn = await get_conn_async(autocommit=True)
            
            async with conn.cursor() as cursor:
                while True:
                    tup = await queue.get()
                    
                    await cursor.execute(
                        "insert into data (timestamp, channel_id, value) values (%s,%s,%s)", tup
                    )
                    #print(f"Write {ts.time_from_timestamp(tup[0])}: Insert ({tup[1]}, {tup[2]})")
                    
                    queue.task_done()
                        
        except Exception as e:
            log.error(f"Error in db_write_loop: {traceback.format_exc()}")
            log.info(f"Retrying in {10} seconds...")
            await asyncio.sleep(10)
        finally:
            if conn:
                conn.close()

def queue_write(log, tup):
    try:
        queue.put_nowait(tup)
    except asyncio.QueueFull:
        log.error("Database Writer queue is full, dropping measurement")
    except Exception as e:
        log.error(f"Error adding to Database Writer queue: {e}")

@contextmanager
def get_cursor():
    with get_conn() as conn:
        cursor = conn.cursor() # TODO: buffered? raw? Depends on if I want to work with json, numpy etc
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
    with get_cursor() as cur:
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
    with get_cursor() as cur:
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

        cur.execute("""
            INSERT IGNORE INTO channels (name, type, unit)
            VALUES ('meter_power', 'power', 'W')
        """)
        cur.execute("SELECT channel_id FROM channels WHERE name = 'meter_power'")
        meter_power = cur.fetchone()[0]

        #print(f"power: {power_id}, power_by_minute: {power_by_minute_id}")
        return power_id, power_by_minute_id, meter_power

def get_channels(cur):
    cur.execute("SELECT channel_id FROM channels WHERE name = 'solar_power'")
    power_id = cur.fetchone()[0]

    cur.execute("SELECT channel_id FROM channels WHERE name = 'solar_power_by_minute'")
    power_by_minute_id = cur.fetchone()[0]

    cur.execute("SELECT channel_id FROM channels WHERE name = 'meter_power'")
    meter_power_id = cur.fetchone()[0]

    return power_id, power_by_minute_id, meter_power_id
