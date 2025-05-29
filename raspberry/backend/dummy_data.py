import random
import math
from datetime import datetime, timezone

# Apparently accurate to milliseconds
# volkzaehler_timestamp is int in milliseconds with unix epoch (1.1.1970)
def get_volkzaehler_timestamp_now():
	unix_timestamp_float = datetime.now(timezone.utc).timestamp()
	timestamp = round(unix_timestamp_float * 1000)
	return timestamp
def time_from_timestamp(timestamp):
	return datetime.fromtimestamp(float(timestamp)/1000)

def get_dummy_data():
    """Generate dummy energy usage data for the past hour"""
    now = get_volkzaehler_timestamp_now()
    
    energyUsage_ts = []
    energyUsage_val = []
    solarPower_ts = []
    solarPower_val = []

    for i in range(360):  # 3600 seconds (1 hour)
        timestamp = now - i*1000

        value = max(math.sin((i-40)/90), 0) * 800

        solarPower_ts.append(timestamp)
        solarPower_val.append(value)

        r1 = random.uniform(80, 130)
        value2 = round((math.cos(math.sin(i/120)*4 + i/35)+1.4)*2)/2 * r1
        
        energyUsage_ts.append(timestamp)
        energyUsage_val.append(value2)
    return {
        "energyUsage": { "timestamps": energyUsage_ts, "values": energyUsage_val },
        "solarPower": { "timestamps": solarPower_ts, "values": solarPower_val }
    }
