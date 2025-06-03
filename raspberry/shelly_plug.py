from os import error
import requests

# https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/Switch/
def read_shelly_plug_status():
	url = 'http://192.168.2.109/rpc/Switch.GetStatus?id=0'
	return requests.get(url).json()

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

'''
def measure_to_file():
	with open("data.txt", "a") as output_file:
		while True:
			try:
				status = read_shelly_plug_status()
				ts = get_volkzaehler_timestamp()

				print(f"{time_from_timestamp(ts)}:\n{json.dumps(status, indent=4)}\n")

				output_file.write(f"{ts}: {json.dumps(status)}\n")
				output_file.flush()
			except:
				pass
			time.sleep(1)
'''

def get_measurement_by_second():
	status = read_shelly_plug_status()
	ts = get_volkzaehler_timestamp()

	# TODO:

