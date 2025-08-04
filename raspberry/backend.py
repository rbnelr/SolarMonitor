from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import database as db
import time
import timestamps as ts
import traceback

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Allow frontend's origin
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"], # Allow all headers
)

# TODO: instead of processing for gaps, then trying to filter by combining solar and meter afterwards
# try to produce raw view data with gaps and filtered version with data in interval (either value or null for missing) first
# then combing the two arrays is easy
def process_results(results, gap_thres, gap_fill_fix):
    timestamps = []
    values = []
    
    if len(results) == 0: return timestamps, values
    
    prev_row = results[0] # no gap on first row
    for row in results:
        # add None entries for gaps if we determine data is missing (so frontend can show gaps by not drawing lines)
        if row[0] - prev_row[0] > gap_thres:
            if gap_fill_fix: # fix for plotly filling gaps for fill="tozeroy"
                # plotly does not actually handle gaps correctly if fill is used
                # gap in line
                timestamps.append(None)
                values.append(None)
                # artificially set line to zero to avoid wrong fill
                timestamps.append(prev_row[0])
                timestamps.append(row[0]) #  - 60*1000
                values.append(0)
                values.append(0)
                # gap in line
                timestamps.append(None)
                values.append(None)
            else:
                # make gap in plotly line trace via nulls
                timestamps.append(None)
                values.append(None)
        #if row[0] - prev_row[0] > 1500:
        #    print(f"{ts.time_from_timestamp(prev_row[0])} - {ts.time_from_timestamp(row[0])} {row[0] - prev_row[0]}")
        
        timestamps.append(row[0])
        values.append(row[1])

        prev_row = row

    return timestamps, values

def filter_and_sum_meter_and_solar(meter_data, solar_data, start, end):
    if len(meter_data['timestamps']) == 0 or len(solar_data['timestamps']) == 0:
        return { 'timestamps': [], 'values': [] }

    t0 = time.perf_counter()

    print(f"start: {start}, end: {end}")

    offs_meter = 0 # -4*1000 # artificial offset to make meter data align with solar data (which is more accurate, since based on solar dips we can sync it and measurements can't predict the future)
    offs_solar = 0

    start = max(start, min(meter_data['timestamps'][0] + offs_meter, solar_data['timestamps'][0] + offs_solar))
    end   = min(end  , max(meter_data['timestamps'][-1] + offs_meter, solar_data['timestamps'][-1] + offs_solar))

    print(f"start: {start}, end: {end}")

    interval = 4*1000
    sample_rate = 1000 # Should get this from the database!

    start_i = start // interval
    end_i   = end // interval # include timeperiod number
    count   = end_i+1 - start_i

    print(f"start_i: {start_i}, end_i: {end_i}, count: {count}")

    res_tim = [i*interval - interval//2 for i in range(start_i, end_i+1)] # center the interval makes most sense for the plot

    # 'accurate' accumulation, anyway here's a picture:
    #  [        5 seconds        ][        5 seconds        ]
    # [    ][    ][    ][    ][ L|R][    ][    ][    ][    ]
    # compute weight of left and right part of the sample falling into different intervals
    def accumulate(data, offs):
        # compute duration of each measurement based on previous timestamp
        times = data['timestamps']
        values = data['values']
        buf = [0]*count

        prev_timestamp = (times[0] + offs - sample_rate) / interval

        for i in range(0, len(times)):
            timestamp = times[i]
            if timestamp is None: continue # gap count as 0
            # keep all timestamps and durations in interval to minimize computation, yes this is confusing
            # NOTE: why does this mean that value * dur is not a energy value but a average power value?
            timestamp = (timestamp + offs) / interval
            
            # duration of sample using previous timestamp (relative to interval)
            dur = timestamp - prev_timestamp
            weighted_value = values[i] * dur # weight the value to result in average power in interval
            # compute the interval the end of the sample falls into
            tmp = int(timestamp)
            interval_ts = float(tmp)
            right_idx = tmp - start_i

            if prev_timestamp >= interval_ts:
                # entire sample is in the interval, fastpath
                if right_idx >= 0 and right_idx < count:
                    buf[right_idx] += weighted_value
            else:
                # split sample, compute duration of l/r part and weight accordingly
                right_dur = timestamp - interval_ts
                right_value = weighted_value * (right_dur / dur) # part of the energy falling into the right interval
                left_value = weighted_value - right_value

                left_idx = right_idx - 1
                if left_idx  >= 0 and right_idx < count:  buf[left_idx ] += left_value
                if right_idx >= 0 and right_idx < count:  buf[right_idx] += right_value

            prev_timestamp = timestamp
        
        return buf
    
    meter_buf = accumulate(meter_data, offs_meter)
    solar_buf = accumulate(solar_data, offs_solar)

    # TODO: could try to turn gaps in source values into gaps in filtered data, but his is a little complicated because gap fix makes detecting gaps harder
    # Instead just accept that missing values will technically introduce error in things like saved energy numbers
    # remove negative values due to glitches
    load_val = [max(val[0] + val[1], 0.0) for val in zip(meter_buf, solar_buf)]

    energy_saving = [
        max(min(val[0], 0.0) + val[1], 0.0) 
        for val in zip(meter_buf, solar_buf)]

    res = (
        { 'timestamps': res_tim, 'values': load_val },
        { 'timestamps': res_tim, 'values': energy_saving }
    )
    
    t1 = time.perf_counter()
    print(f" filter_and_sum_meter_and_solar time: {(t1 - t0)*1000:.2f} ms")

    return res

def query_channel_range(cur, channel_id, start, end, gap_thres, gap_fill_fix=False):
    try:
        t0 = time.perf_counter()
        t0f = time.perf_counter()

        cur.execute("""select timestamp, value
                        from data
                        where channel_id = %s and timestamp between %s and %s
                        """, (channel_id, start, end))
        results = cur.fetchall()
        t1f = time.perf_counter()

        print(f'channel_id: {channel_id} blah: {len(results)}')

        t0p = time.perf_counter()

        timestamps, values = process_results(results, gap_thres, gap_fill_fix)

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
        print(f"Error querying channel range: {traceback.format_exc()}")
        return { 'timestamps': [], 'values': [] }

@app.get("/data")
async def get_data(
            start: int | None = None,
            end:   int | None = None
        ):
    try:
        t0 = time.perf_counter()

        if start == None: start = ts.local_time_to_timestamp(datetime.now() - timedelta(days=1))
        if end   == None: end   = ts.local_time_to_timestamp(datetime.now() + timedelta(days=9999))

        # assume missing data if 3 times more elapsed time than supposed sample rate
        gap_thres_power = 1000 *3
        gap_thres_by_minute = 1000*60 *3
        
        with db.get_cursor(read_timeout=5000) as cur:
            power_id, power_by_minute_id, meter_power_id, meter_reading_id = db.get_channels(cur)

            solar_data = query_channel_range(cur, power_id, start, end, gap_thres_power, gap_fill_fix=True)
            #solar_by_minute_data = query_channel_range(cur, power_by_minute_id, start, end, gap_thres_by_minute, gap_fill_fix=True)
            meter_power = query_channel_range(cur, meter_power_id, start, end, gap_thres_power)
            meter_reading = query_channel_range(cur, meter_reading_id, start, end, gap_thres_by_minute)

        filtered = filter_and_sum_meter_and_solar(meter_power, solar_data, start, end)

        res = {
            'solar': solar_data,
            #'solar_by_minute': solar_by_minute_data,
            'meter_power': meter_power,
            #'meter_reading': meter_reading,
            'load': filtered[0],
            'savings': filtered[1],
            'latest_meter_energy': { 'timestamp': meter_reading['timestamps'][-1], 'value': meter_reading['values'][-1] }
        }

        t1 = time.perf_counter()
        print(f"total time: {(t1 - t0)*1000:.2f} ms")

        return res
    except Exception as ex:
        print(f"Error querying data: {traceback.format_exc()}")
        raise HTTPException(status_code=404, detail=f"Error querying data")
  
#if __name__ == "__main__":
#    import asyncio
#    asyncio.run(get_data())
