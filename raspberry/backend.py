from fastapi import FastAPI
from dummy_data import get_dummy_data
from fastapi.middleware.cors import CORSMiddleware
import json

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
            if (not data_by_minute or data_by_minute[-1]['timestamp'] != by_minute['timestamp']):
                data_by_minute.append(by_minute)
            
        return { 'power': data_power, 'by_minute': data_by_minute }
    except Exception as e:
        print(f"Error reading data file: {e}")
        return { 'power': [], 'by_minute': [] }

@app.get("/data")
async def get_data():
    return get_test_data()
