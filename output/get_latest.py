#!/usr/bin/python3

import redis
import redistimeseries.client
import time

FEATURE_PRODUCTION = 1

'''
{
  "up": 0,
  "down": 100,
  "predicted_peak_down": 2.7,
  "production": 100,
}
'''
def generate_json_ouput(up, down, predicted_peak_down, prod=0):
    result = '{\n'
    result += '  "up": ' + str(up) + ',\n'
    result += '  "down": ' + str(down) + ',\n'
    result += '  "predicted_peak_down": ' + str(predicted_peak_down) + ''
    if FEATURE_PRODUCTION:
        result += ',\n'
        result += '  "prod": ' + str(prod) + '\n'
    else:
        result += '\n'
    result += '}'
    return result

def convert_usage(value):
    result = float(value)
    result *= 1000
    return int(result)

def set_value_if_data_older_than(data, value, timeout_ms):
    now = int(time.time() * 1000)
    if (now - data[0]) >= timeout_ms:
       return (data[0], value)
    return data

r = redis.Redis(host='localhost',
                port=6379, 
                password=None)
rts = redistimeseries.client.Client(r)

#redis command: xrevrange elektricity + - COUNT 1 
#latest_stream_entry = r.xrevrange("electricity", max=u'+', min=u'-', count=1)

latest_prod = (0.0, 0.0)

#redis command: TS.GET electricity_down_sec
latest_up = rts.get("electricity_up_sec")
latest_down = rts.get("electricity_down_sec")

latest_up = set_value_if_data_older_than(latest_up, -0.001, 10000)
latest_down = set_value_if_data_older_than(latest_down, -0.001, 10000)

#predict the peak usage of the current quarter (if the production remains the same untill the end of the quarter)
peak_down = 0
predicted_peak_down = 0
ms_passed_in_last_quarter = latest_down[0] % 900000
ms_remaining_in_last_quarter = 900000 - ms_passed_in_last_quarter
last_quarter_start_time = latest_down[0] - ms_passed_in_last_quarter
last_quarter_end_time = last_quarter_start_time + 900000 - 1
peak_down_result = rts.range("electricity_down_sec", last_quarter_start_time, last_quarter_end_time, align='start', aggregation_type='avg', bucket_size_msec=900000)
if len(peak_down_result):
    peak_down = peak_down_result[0][1]
predicted_peak_down = ((peak_down * ms_passed_in_last_quarter) + (latest_down[1] * ms_remaining_in_last_quarter)) / 900000

if FEATURE_PRODUCTION:
    latest_prod = rts.get("electricity_prod_1min")
    latest_prod = set_value_if_data_older_than(latest_prod, 0.0, 180000)

result = generate_json_ouput(convert_usage(latest_up[1]),
                             convert_usage(latest_down[1]),
                             round(predicted_peak_down, 5),
                             convert_usage(latest_prod[1]))


print(result)

