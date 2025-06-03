from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import timestamps as ts
from datetime import datetime, timedelta
import database as db

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

def query_channel_range(channel_id, start, end):
    with db.get_db_cursor() as cur:
        start_ts = ts.local_time_to_timestamp(start)
        end_ts = ts.local_time_to_timestamp(end)

        cur.execute("""select timestamp, value
                        from data
                        where channel_id = %s and timestamp between %s and %s
                        """, (channel_id, start_ts, end_ts))
        results = cur.fetchall()
        # TODO: is this slow in python? optimize? how? numpy or directly in sql?
        # how slow is json conversion? If sql produces string, can we avoid expensive conversion?
        return { 'timestamps': [row[0] for row in results], 'values': [row[1] for row in results] }

@app.get("/data")
async def get_data():
    power_id, power_by_minute_id = db.get_channels()
    # show all for now
    start = datetime.now() - timedelta(days=9999)
    end = datetime.now() + timedelta(days=9999)

    return {
        'power': query_channel_range(power_id, start, end),
        'by_minute': query_channel_range(power_by_minute_id, start, end),
    }


