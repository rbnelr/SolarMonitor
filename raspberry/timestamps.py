from datetime import datetime, timezone

# Apparently accurate to milliseconds
# volkzaehler_timestamp is int in milliseconds with unix epoch (1.1.1970)
def get_volkzaehler_timestamp():
	unix_timestamp_float = datetime.now(timezone.utc).timestamp()
	return round(unix_timestamp_float * 1000)

def time_from_timestamp(timestamp):
	return datetime.fromtimestamp(float(timestamp)/1000)

# convert time datetime in local timezone to unix timestamp in milliseconds
def local_time_to_timestamp(time):
	utc_time = time.astimezone(timezone.utc)
	return round(utc_time.timestamp() * 1000)
