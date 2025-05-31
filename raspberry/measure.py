import database as db
import json

db.create_tables()

with db.get_db_cursor() as cur:
    cur.execute("""
        INSERT IGNORE INTO channels (name, type, unit)
        VALUES ('solar_power', 'power', 'W')
    """)
    cur.execute("SELECT channel_id FROM channels WHERE name = 'solar_power'")
    solar_power_id = cur.fetchone()[0]

    cur.execute("""
        INSERT IGNORE INTO channels (name, type, unit)
        VALUES ('solar_power_by_minute', 'power', 'W')
    """)
    cur.execute("SELECT channel_id FROM channels WHERE name = 'solar_power_by_minute'")
    solar_power_by_minute_id = cur.fetchone()[0]

    print(f"solar_power: {solar_power_id}, solar_power_by_minute: {solar_power_by_minute_id}")

with db.get_db_cursor() as cur:
    with open('data.txt', 'r') as f:
        lines = f.readlines()
        
    data_power = []
    data_by_minute = []
    for line in lines:
        timestamp, json_str = line.split(': ', 1)
        reading = json.loads(json_str)

        data_power.append({
            'timestamp': int(timestamp),
            'value': -reading['apower'], # W
        })
        by_minute = {
            'timestamp': int(reading['ret_aenergy']['minute_ts']) * 1000,
            'value': reading['ret_aenergy']['by_minute'][0] * (60.0 / 1000), # mWh / min -> W (avg in minute)
        }

        if not data_by_minute or data_by_minute[-1]['timestamp'] != by_minute['timestamp']:
            data_by_minute.append(by_minute)

    cur.executemany("""insert into data (channel_id, timestamp, value) values (%s,%s,%s)""",
                    [(solar_power_id, x['timestamp'], x['value']) for x in data_power])
    cur.executemany("""insert into data (channel_id, timestamp, value) values (%s,%s,%s)""",
                    [(solar_power_by_minute_id, x['timestamp'], x['value']) for x in data_by_minute])
        