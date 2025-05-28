import random
import math
from datetime import datetime, timedelta

def get_dummy_data():
    """Generate dummy energy usage data for the past hour"""
    now = datetime.now()
    data = []
    for i in range(360):  # 3600 seconds (1 hour)
        timestamp = now - timedelta(seconds=i)

        r1 = random.uniform(-30, 30)
        r2 = max(0.0, math.sin(i/40))

        value = math.sin(i/130) * 300 + r1 * r2
        data.append({"timestamp": timestamp.isoformat(), "value": value})
    return data
