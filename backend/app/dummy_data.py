import random
import math
from datetime import datetime, timedelta

def get_dummy_data():
    """Generate dummy energy usage data for the past hour"""
    now = datetime.now()
    data = []
    for i in range(3600):  # 3600 seconds (1 hour)
        timestamp = now - timedelta(seconds=i)

        r1 = random.uniform(-30, 30)
        r2 = random.uniform(.1, 1)

        value = math.sin(i/80) * 300 + r1 * r2
        data.append({"timestamp": timestamp.isoformat(), "value": value})
    return data
