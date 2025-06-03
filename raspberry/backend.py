from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import database as db
import time
import timestamps as ts

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

def query_channel_range(cur, channel_id, start, end, gap_thres, gap_fill_fix=False):
    try:
        t0 = time.perf_counter()
        t0f = time.perf_counter()
        start_ts = ts.local_time_to_timestamp(start)
        end_ts = ts.local_time_to_timestamp(end)

        cur.execute("""select timestamp, value
                        from data
                        where channel_id = %s and timestamp between %s and %s
                        """, (channel_id, start_ts, end_ts))
        results = cur.fetchall()
        t1f = time.perf_counter()

        t0p = time.perf_counter()
        timestamps = []
        values = []

        if len(results) > 0:
            prev_row = results[0] # no gap on first row
            for row in results:
                # add None entries for gaps if we determine data is missing (so frontend can show gaps by not drawing lines)
                if row[0] - prev_row[0] > gap_thres:
                    timestamps.append(None)
                    values.append(None)
                    if gap_fill_fix: # fix for plotly filling gaps for fill="tozeroy"
                        timestamps.append(prev_row[0])
                        timestamps.append(row[0] - 60*1000)
                        values.append(0)
                        values.append(0)
                
                timestamps.append(row[0])
                values.append(row[1])

                prev_row = row

        # TODO: is this slow in python? optimize? how? numpy or directly in sql?
        # how slow is json conversion? If sql produces string, can we avoid expensive conversion?
        #res = { 'timestamps': [row[0] for row in results], 'values': [row[1] for row in results] }

        res = { 'timestamps': timestamps, 'values': values }
        t1p = time.perf_counter()
        t1 = time.perf_counter()
        
        # fatch is the bottleneck by far, takes a lot more time than iterating the data in python, so json conversion is likely fast as well
        # but of course once backend is deployed to raspberry, performance will change dramatically
        print(f"  fetch time: {(t1f - t0f)*1000:.2f} ms")
        print(f"  processing time: {(t1p - t0p)*1000:.2f} ms")
        print(f" total query time: {(t1 - t0)*1000:.2f} ms")

        return res
    except Exception as ex:
        print(f"Error querying channel range: {ex}")
        return { 'timestamps': [], 'values': [] }

@app.get("/data")
async def get_data():
    try:
        t0 = time.perf_counter()

        # show all for now
        start = datetime.now() - timedelta(days=1)
        end = datetime.now() + timedelta(days=9999)

        # assume missing data if 3 times more elapsed time than supposed sample rate
        gap_thres_power = 1000 *3
        gap_thres_by_minute = 1000*60 *3
        
        with db.get_db_cursor() as cur:
            power_id, power_by_minute_id = db.get_channels(cur)

            power_data = query_channel_range(cur, power_id, start, end, gap_thres_power)
            by_minute_data = query_channel_range(cur, power_by_minute_id, start, end, gap_thres_by_minute, gap_fill_fix=True)
        with db.get_vz_db_cursor() as cur2:
            vz_meter_data = query_channel_range(cur2, 5, start, end, gap_thres_power)

        res = {
            'power': power_data,
            'by_minute': by_minute_data,
            'meter': vz_meter_data
        }

        t1 = time.perf_counter()
        print(f"total time: {(t1 - t0)*1000:.2f} ms")

        return res
    except Exception as ex:
        print(f"Error querying data: {ex}")
        raise HTTPException(status_code=404, detail=f"Error querying data")
        

