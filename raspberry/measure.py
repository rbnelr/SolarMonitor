import database as db
import requests
import timestamps as ts
import time
import math
import traceback

#db.create_tables()
power_id, power_by_minute_id = db.get_or_create_channels()

#"id": 0,
#"source": "WS_in",
#"output": true,
#"apower": -88.9,   # Last measured instantaneous active power (in Watts) 
#"voltage": 233.2,
#"freq": 50,
#"current": 0.388,
#"aenergy": {       # Information about the active energy counter (shown if applicable)
#  "total": 21.78,  # Absolute energy (positive and negative (?))
#  "by_minute": [
#    1047.135,      
#    837.708,
#    628.281
#  ],
#  "minute_ts": 1748418360
#},
#"ret_aenergy": {    # Total returned (negative) energy consumed in Watt-hours (accumulated since last reset, not sure if can overflow)
#  "total": 21.78,
#  "by_minute": [
#    1047.135,       # Energy use each minute (last 3 minutes) in mWh (*60/1000 to get average Watt in minute)
#    837.708,
#    628.281
#  ],
#  "minute_ts": 1748418360 # Start of the current minute as unix timestamp (seconds), eg. 13:04:00 means by_minute[0] is 13:03-04 reading
#},
#"temperature": {
#  "tC": 37.3,
#  "tF": 99.1
#}

# I think aenergy is total energy flowing through plug (absolute of positive and negative)
# ret_aenergy is just the negative flow (due to solar panel)
# by_minute contains measured energy per minute (previous 3 minutes)

# https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/Switch/
def read_shelly_plug_status():
    try:
        url = 'http://192.168.2.109/rpc/Switch.GetStatus?id=0'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to read Shelly status: {traceback.format_exc()}")
        raise

def high_res_measurement_loop(db_conn, db_cursor):
    period = 1
    prev_by_minute_ts = 0
    zero_power_count = 0
    zero_power_threshold = math.ceil(60 / period)
    while True:
        try:
            status = read_shelly_plug_status()

            timestamp = ts.get_volkzaehler_timestamp()
            apower = -status['apower'] # Negative Watts = solar power

            # If power is zero for a while, assume night and don't write to db to save space and speed up queries
            if apower <= 0.001: zero_power_count += 1
            else: zero_power_count = 0
            if zero_power_count >= zero_power_threshold:
                print(f"Zero power for {zero_power_count*period} seconds, skipping...")
                continue

            by_minute_ts        = status['ret_aenergy']['minute_ts'] * 1000 # s -> ms
            by_minute_avg_power = float(status['ret_aenergy']['by_minute'][0]) * (60.0 / 1000) # mWh / min -> W (avg in minute)

            if prev_by_minute_ts == by_minute_ts:
                # insert per-second power data
                db_cursor.execute("insert into data (channel_id, timestamp, value) values (%s,%s,%s)",
                    (power_id, timestamp, apower))
                #print(f"{ts.time_from_timestamp(timestamp)}: {apower} W")
            else:
                # insert per-minute power data and per-minute average power data
                # probably more efficient to do this in a single query
                # could also use execute() with hard coded 6 values instead of executemany() with list (supposedly faster?)
                db_cursor.executemany("insert into data (channel_id, timestamp, value) values (%s,%s,%s)",
                    [(power_id, timestamp, apower),
                    (power_by_minute_id, by_minute_ts, by_minute_avg_power)])
                print(f"minute {ts.time_from_timestamp(by_minute_ts)}: {by_minute_avg_power} W")

            db_conn.commit()
            prev_by_minute_ts = by_minute_ts
        except Exception as e:
            db_conn.rollback()
            print(f"Error trying to insert data into database, possibly because app was restarted to quickly, retrying...")
        except KeyboardInterrupt:
            break
        finally:
            time.sleep(period)

while True:
    try:
        with db.get_db_conn() as db_conn:
            with db_conn.cursor() as db_cursor:
                high_res_measurement_loop(db_conn, db_cursor)
    except Exception:
        raise
