import database as db
import requests
import timestamps as ts
import time
import math
import traceback
import log_setup
import asyncio

log = log_setup.setup_logging('solarmon.measure')

#db.create_tables()
power_id, power_by_minute_id, meter_power_id = db.get_or_create_channels()

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
        log.error(f"Failed to read Shelly status: {traceback.format_exc()}")
        raise

async def high_res_measurement_loop():
    period = 1
    prev_by_minute_ts = 0
    zero_power_count = 0
    zero_power_threshold = math.ceil(60 / period)
    zero_power_state = False

    log.info("Starting measurement loop")
    
    while True:
        start_ts = time.time()
        
        try:
            timestamp = ts.get_volkzaehler_timestamp()
            status = read_shelly_plug_status()

            apower = -status['apower'] # Negative Watts = solar power

            # If power is zero for a while, assume night and don't write to db to save space and speed up queries
            if apower <= 0.001: zero_power_count += 1
            else: zero_power_count = 0
            
            if zero_power_count >= zero_power_threshold:
                if not zero_power_state: # Only print once
                    zero_power_state = True
                    log.info(f"Zero power for {zero_power_count*period} seconds, skipping...")
            else:
                zero_power_state = False

                by_minute_ts        = status['ret_aenergy']['minute_ts'] * 1000 # s -> ms
                by_minute_avg_power = float(status['ret_aenergy']['by_minute'][0]) * (60.0 / 1000) # mWh / min -> W (avg in minute)
                
                db.queue_write(log, (timestamp, power_id, apower))
                print(f"Measure Shelly {ts.time_from_timestamp(timestamp)}: {apower} W")

                if prev_by_minute_ts != by_minute_ts:
                    db.queue_write(log, (by_minute_ts, power_by_minute_id, by_minute_avg_power))
                    log.info(f"Measure Shelly minute {ts.time_from_timestamp(by_minute_ts)}: {by_minute_avg_power} W")
                
                prev_by_minute_ts = by_minute_ts

            sleep_time = math.ceil(start_ts/period)*period - start_ts # good way to get consistent timings close to exactly on whole seconds
        except Exception:
            log.error(f"Error in measurement loop: {traceback.format_exc()}")
            log.info("Retrying in 10 seconds...")
            sleep_time = 10

        await asyncio.sleep(sleep_time)

## HTTP server for push data
from aiohttp import web

async def handle_push(request):
    try:
        data = await request.json()
        print(f"Received push data: {data}")

        for obj in data['data']:
            if (obj['uuid'] == db.vz_meter_power_uuid):
                for (timestamp, value) in obj['tuples']:
                    db.queue_write(log, (timestamp, meter_power_id, value))

        return web.Response(text="OK")
    except Exception as e:
        print(f"Error handling push: {e}")
        return web.Response(status=500, text="Error")

async def http_push_receiver():
    log.info("Starting http_push_receiver")
    
    while True:
        try:
            app = web.Application()
            app.router.add_post('/vzlogger_data', handle_push)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', 8082)

            print("HTTP push receiver server running on http://localhost:8082...")
            await site.start()
            
            # Keep the server running indefinitely
            # Really? 
            while True:
                await asyncio.sleep(3600)
        except Exception:
            log.error(f"Error in push receiver loop: {traceback.format_exc()}")
            log.info("Retrying in 10 seconds...")
            await asyncio.sleep(10)

async def main_async():
    log.info("measure.py starting up")
    
    await asyncio.gather(
        db.write_loop(log),
        high_res_measurement_loop(),
        http_push_receiver()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        log.info("Received keyboard interrupt, shutting down...")
