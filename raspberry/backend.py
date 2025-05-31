from fastapi import FastAPI
from dummy_data import get_dummy_data
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)



#@app.get("/data")
#async def get_data():
#    """Endpoint to fetch dummy energy use data"""
#    return get_dummy_data()

def get_test_data():
    try:
        with open('data.txt', 'r') as f:
            lines = f.readlines()
            
        data = []
        for line in lines:
            timestamp, json_str = line.split(': ', 1)
            reading = json.loads(json_str)
            data.append({
                'timestamp': int(timestamp),
                'apower': -reading['apower'], # W
                'ret_aenergy': {
                    'total': reading['ret_aenergy']['total'] / 1000, # Wh -> kWh (accumulated)
                    'by_minute': [
                        reading['ret_aenergy']['by_minute'][0] * (60.0 / 1000), # mWh / min -> W (avg in minute)
                        reading['ret_aenergy']['by_minute'][1] * (60.0 / 1000),
                        reading['ret_aenergy']['by_minute'][2] * (60.0 / 1000),
                    ],
                    'minute_ts': reading['ret_aenergy']['minute_ts']
                }
            })
        return data
    except Exception as e:
        print(f"Error reading data file: {e}")
        return []

@app.get("/data")
async def get_data():
    return { 'readings': get_test_data() }
