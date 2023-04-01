#!/usr/bin/python3

import datetime
import calendar
from enum import Enum
import redis
import sys

from django.conf import settings
from home_energy.view.energy_common import *

if not settings.configured:
    settings.configure(FEATURE_GAS=1, FEATURE_PRODUCTION=1, FEATURE_SOLAR_FORECAST=1)

FEATURE_PRODUCTION = settings.FEATURE_PRODUCTION
FEATURE_GAS = settings.FEATURE_GAS
FEATURE_SOLAR_FORECAST = settings.FEATURE_SOLAR_FORECAST

#The buckset size should be a number that could used to divide 15 minutes
day_bucket_size_msec = 3 * 60 * 1000
if FEATURE_GAS:
    day_bucket_size_msec = 5 * 60 * 1000

r = db_connect()
rts = db_timeseries_connect(r)

class Mode(Enum):
    DAY = 1
    MONTH = 2
    YEAR = 3

def get_default_day():
    return datetime.date.today()

def get_day(day_str):
    day = get_default_day()
    try:
        day = parse_day(day_str)
    except ValueError:
        pass
    return day

def get_script_arg_day():
    if len(sys.argv) >= 2:
        #return the first argument
        return sys.argv[1]
    return ''

def parse_mode(mode_str):
    return Mode(int(mode_str))

def get_default_mode():
    return Mode.DAY

def get_mode(mode_str):
    mode = get_default_mode()
    try:
        mode = parse_mode(mode_str)
    except ValueError:
        pass
    return mode

def get_script_arg_mode():
    if len(sys.argv) >= 3:
        #return the second argument
        return sys.argv[2]
    return ''

'''
Gets the time, value entries without the labels
'''
def get_entries(output_entries, label, value):
    for direction in output_entries:
        key = label + '=' + value
        if key in direction:
            return direction[key][1]
    return None

'''
Adds samples in the future untill the end of the month or year.
'''
def add_missing_data(entries, mode, value):
    if entries:
        last_date = datetime.datetime.fromtimestamp(entries[-1][0]/1000)
        if mode == Mode.MONTH:
            month_nb_of_days = calendar.monthrange(last_date.year, last_date.month)[1]
            for i in range(last_date.day + 1, month_nb_of_days + 1):
                last_date = last_date.replace(day=i)
                epoch_time = get_epoch_time_ms(last_date)
                entries.append([epoch_time, value])
        elif mode == Mode.YEAR:
            for i in range(last_date.month + 1, 13):
                last_date = last_date.replace(month=i)
                epoch_time = get_epoch_time_ms(last_date)
                entries.append([epoch_time, value])
    return entries


'''
{
  "detailed_data" : [
    {"t": "timeValue", "u": "upValue", "d": "downValue"},
    {"t": "timeValue", "u": "upValue", "d": "downValue"}
  ]
}
'''
def generate_result(day, mode,
                    up_entries, down_entries, peak_down_entries, prod_entries, gas_entries, solar_forecast_entries):
    result = {}
    sf_i = 0;
    correction_factor = 1

    if mode == Mode.DAY:
        correction_factor = 1000

    result["date"] = day.strftime('%Y-%m-%d')
    result["mode"] = mode.name

    detailed_up_down = []

    for i, up_entry in enumerate(up_entries):
        detailed_result_entry = {}
        down_entry = down_entries[i]
        if (up_entry[0] == down_entry[0]):
            detailed_result_entry["t"] = up_entry[0]
            detailed_result_entry["u"] = up_entry[1] * correction_factor
            detailed_result_entry["d"] = down_entry[1] * correction_factor

            detailed_result_entry["pd"] = None
            peak_down_entry = [item for item in peak_down_entries if item[0] == up_entry[0]]
            if len(peak_down_entry):
                peak_down_entry = peak_down_entry[0]
                detailed_result_entry["pd"] = peak_down_entry[1] * correction_factor

            detailed_result_entry["p"] = None
            if FEATURE_PRODUCTION:
                prod_entry = [item for item in prod_entries if item[0] == up_entry[0]]
                if len(prod_entry):
                    prod_entry = prod_entry[0]
                    detailed_result_entry["p"] = prod_entry[1] * correction_factor

            detailed_result_entry["g"] = None
            if FEATURE_GAS:
                gas_entry = [item for item in gas_entries if item[0] == up_entry[0]]
                if len(gas_entry):
                    gas_entry = gas_entry[0]
                    detailed_result_entry["g"] = gas_entry[1]

            detailed_result_entry["sf"] = None
            if FEATURE_SOLAR_FORECAST:
                solar_forecast_entry = [item for item in solar_forecast_entries if item[0] == up_entry[0]]
                if len(solar_forecast_entry):
                    solar_forecast_entry = solar_forecast_entry[0]
                    detailed_result_entry["sf"] = solar_forecast_entry[1] * correction_factor
                    sf_i += 1

            detailed_up_down.append(detailed_result_entry)
        else:
            print('Keys don\'t match for up and down entries. i ' + str(i) + ', up_key ' + str(up_entry[0]) + ', down_key ' + str(down_entry[0]))

    if FEATURE_SOLAR_FORECAST:
        if sf_i < len(solar_forecast_entries):
            for solar_forecast_entry in solar_forecast_entries[sf_i:]:
                detailed_result_entry = {}
                detailed_result_entry["t"] = solar_forecast_entry[0]
                detailed_result_entry["u"] = None
                detailed_result_entry["d"] = None
                detailed_result_entry["pd"] = None
                if FEATURE_PRODUCTION:
                    detailed_result_entry["p"] = None
                if FEATURE_GAS:
                    detailed_result_entry["g"] = None
                if len(solar_forecast_entry):
                    detailed_result_entry["sf"] = solar_forecast_entry[1] * correction_factor

                detailed_up_down.append(detailed_result_entry)

    result["detailed_up_down"] = detailed_up_down
    return result

def get_electricity_current_hour(rts, dir_str):
    # Get the latest value in the 1h series.
    latest_1h = rts.get("electricity_" + dir_str + "_1h")
    if latest_1h is None:
        return 0
    # Use this time as a start time + 1h.
    latest_hour_result = rts.range("electricity_" + dir_str + "_1min", latest_1h[0] + 3600000, latest_1h[0] + 7200000, align='start', aggregation_type='sum', bucket_size_msec=3600000)
    if len(latest_hour_result):
        return latest_hour_result[0][1] / 60
    return 0

def get_detailed_usage(date_str, mode_str):
    day = get_day(date_str)
    mode = get_mode(mode_str)

    #calculate the range to get data from
    if mode == Mode.DAY:
        start_day = day
        days = 1
    elif mode == Mode.MONTH:
        start_day = day.replace(day=1)
        days = calendar.monthrange(day.year, day.month)[1]
    elif mode == Mode.YEAR:
        start_day = day.replace(day=1)
        start_day = start_day.replace(month=1)
        days = 366 if calendar.isleap(day.year) else 365
    else:
        raise ValueError("Invalid mode")

    now = get_now_epoch_in_ms()
    start_time = get_epoch_time_ms(start_day)
    end_time = get_epoch_end_time(start_time, days)
    total_bucket_size = days * 86400000

    prod_entries = []
    gas_entries = []
    solar_forecast_entries = []

    #Get the detailed up/down data
    if mode == Mode.DAY:
        #Get usage per 2 minutes
        #TS.MRANGE - + AGGREGATION avg 120000 FILTER dir=(up,down) granularity=(1m,15m) GROUPBY dir REDUCE min
        #only query the needed granularity to make the query faster. The 15min data is kept forever, so no need to query the hourly data or the 1s data
        mixed_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='avg', bucket_size_msec=day_bucket_size_msec, filters=['dir=(up,down)', 'granularity=(1m,15m)'], groupby='dir', reduce='min')
        up_entries = get_entries(mixed_entries, 'dir', 'up')
        down_entries = get_entries(mixed_entries, 'dir', 'down')
        peak_down_entries = rts.range("electricity_down_15min", start_time, end_time)
        if FEATURE_PRODUCTION:
            prod_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='avg', bucket_size_msec=day_bucket_size_msec, filters=['type=prod', 'granularity=(1m,15m)'], groupby='type', reduce='min')
            prod_entries = get_entries(prod_entries, 'type', 'prod')
        if FEATURE_GAS:
            gas_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='sum', bucket_size_msec=day_bucket_size_msec, filters=['type=gas', 'granularity=(5m,15m)'], groupby='type', reduce='min')
            gas_entries = get_entries(gas_entries, 'type', 'gas')
        if FEATURE_SOLAR_FORECAST:
            solar_forecast_entries = rts.range("solar_forecast_1h", start_time, end_time)
    elif mode == Mode.MONTH:
        mixed_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='sum', bucket_size_msec=86400000, filters=['dir=(up,down)', 'granularity=1h'], groupby='dir', reduce='min')
        up_entries = get_entries(mixed_entries, 'dir', 'up')
        down_entries = get_entries(mixed_entries, 'dir', 'down')
        peak_down_entries = rts.range("electricity_down_15min", start_time, end_time, align='start', aggregation_type='max', bucket_size_msec=86400000)
        if FEATURE_PRODUCTION:
            prod_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='max', bucket_size_msec=86400000, filters=['type=prod', 'value=dayGen'], groupby='value', reduce='max')
            prod_entries = get_entries(prod_entries, 'value', 'dayGen')
        if FEATURE_GAS:
            gas_entries = rts.range("gas_15min", start_time, end_time, align='start', aggregation_type='sum', bucket_size_msec=86400000)
    elif mode == Mode.YEAR:
        up_entries = []
        down_entries = []
        peak_down_entries = []
        for i in range(1, 13):
            month_start = start_day.replace(month=i)
            month_nb_of_days = calendar.monthrange(month_start.year, month_start.month)[1]
            month_start_epoch = get_epoch_time_ms(month_start)
            month_end_epoch = get_epoch_end_time(month_start_epoch, month_nb_of_days)
            month_bucket_size = month_nb_of_days * 86400000

            mixed_entries = rts.mrange(month_start_epoch, month_end_epoch, align='start', aggregation_type='sum', bucket_size_msec=month_bucket_size, filters=['dir=(up,down)', 'granularity=1h'], groupby='dir', reduce='min')
            up_entries.extend(get_entries(mixed_entries, 'dir', 'up'))
            down_entries.extend(get_entries(mixed_entries, 'dir', 'down'))
            peak_down_entries.extend(rts.range("electricity_down_15min", month_start_epoch, month_end_epoch, align='start', aggregation_type='max', bucket_size_msec=month_bucket_size))

            if FEATURE_GAS:
                gas_entries.extend(rts.range("gas_15min", month_start_epoch, month_end_epoch, align='start', aggregation_type='sum', bucket_size_msec=month_bucket_size))

            if FEATURE_PRODUCTION:
                prod_result = rts.range("electricity_prod_gen_daily_1day", month_start_epoch, month_end_epoch, align='start', aggregation_type='sum', bucket_size_msec=month_bucket_size)
                #add the current day
                if now >= month_start_epoch and now <= month_end_epoch:
                    now_start_day = now - (now % 86400000)
                    today_prod_result = rts.range("electricity_prod_gen_daily_1min", now_start_day, now_start_day + 86400000 -1, align='start', aggregation_type='max', bucket_size_msec=86400000)
                    if len(today_prod_result):
                        if len(prod_result):
                            #Add the production of the current day to the sum of the other days
                            prod_result[0] = (prod_result[0][0], prod_result[0][1] + today_prod_result[0][1])
                        else:
                            #This only happens if it's the first day of the month
                            #1. reset the timestamp to the start of the day
                            #2. use the result
                            prod_result = [(month_start_epoch, today_prod_result[0][1])]
                prod_entries.extend(prod_result)

    #Add missing data at end
    up_entries = add_missing_data(up_entries, mode, 0.0)
    down_entries = add_missing_data(down_entries, mode, 0.0)
    peak_down_entries = add_missing_data(peak_down_entries, mode, 0.0)
    prod_entries = add_missing_data(prod_entries, mode, 'null')
    gas_entries = add_missing_data(gas_entries, mode, '0.0')

    #generate the output
    result = generate_result(day, mode,
                             up_entries, down_entries, peak_down_entries, prod_entries, gas_entries, solar_forecast_entries)
    return result

def get_total_usage(starttime, endtime, mode):
    total_usage = {}

    mode = Mode(mode)
    now = get_now_epoch_in_ms()
    starttime_ms = starttime * 1000
    endtime_ms = endtime * 1000
    total_bucket_size = endtime_ms - starttime_ms

    #Get total usage
    #TS.RANGE electricity_down_1h <startTime> <stopTime> AGGREGATION SUM 86400000
    total_up = 0
    total_down = 0
    total_up_result = rts.range("electricity_up_1h", starttime_ms, endtime_ms, align='start', aggregation_type='sum', bucket_size_msec=total_bucket_size)
    total_down_result = rts.range("electricity_down_1h", starttime_ms, endtime_ms, align='start', aggregation_type='sum', bucket_size_msec=total_bucket_size)
    if len(total_up_result):
        total_up = total_up_result[0][1]
    if len(total_down_result):
        total_down = total_down_result[0][1]
    
    if now >= starttime and now <= endtime:
        #add the last/current hour
        total_up += get_electricity_current_hour(rts, "up")
        total_down += get_electricity_current_hour(rts, "down")

    #Get peak usage
    peak_down = 0
    if total_bucket_size <= (31 * 86400000):
        # Show the MAX peak
        # TS.RANGE electricity_down_15min <startTime> <stopTime> ALIGN start AGGREGATION MAX 86400000
        peak_down_result = rts.range("electricity_down_15min", starttime_ms, endtime_ms, align='start', aggregation_type='max', bucket_size_msec=total_bucket_size)
        if len(peak_down_result):
            peak_down = peak_down_result[0][1]
    else:
        # Show the AVG peak of the MAX of the months
        # This requires getting the peak of each month
        peak_down_entries = []
        current_day = get_datetime_from_epoch_in_s(starttime)
        end_day = get_datetime_from_epoch_in_s(endtime)
        print(f"end: {end_day}")
        while current_day < end_day:
            print(f"cur: {current_day}")
            month_start = current_day.replace(day=1)
            month_nb_of_days = calendar.monthrange(month_start.year, month_start.month)[1]
            month_start_epoch = get_epoch_time_ms(month_start)
            month_end_epoch = get_epoch_end_time(month_start_epoch, month_nb_of_days)
            month_bucket_size = month_nb_of_days * 86400000

            peak_down_entries.extend(rts.range("electricity_down_15min", month_start_epoch, month_end_epoch, align='start', aggregation_type='max', bucket_size_msec=month_bucket_size))
            current_day = month_start + datetime.timedelta(days=month_nb_of_days)

        nb_of_peak_entries = 0;
        for month_peak_entry in peak_down_entries:
            peak_down += max(2.5, month_peak_entry[1])
            nb_of_peak_entries += 1
        if nb_of_peak_entries != 0:
            peak_down /= nb_of_peak_entries

    #total production
    total_prod = 0
    if FEATURE_PRODUCTION:
        if mode == Mode.DAY:
            #TS.MRANGE - + AGGREGATION max 86400000 FILTER value=dayGen GROUPBY value REDUCE max
            total_prod_result = rts.mrange(starttime_ms, endtime_ms, align='start', aggregation_type='max', bucket_size_msec=86400000, filters=['type=prod', 'value=dayGen'], groupby='value', reduce='max')
            total_prod_result = get_entries(total_prod_result, 'value', 'dayGen')
            if total_prod_result:
                total_prod =  total_prod_result[0][1]
        elif mode == Mode.MONTH or mode == Mode.YEAR:
            total_prod_result = rts.range("electricity_prod_gen_daily_1day", starttime_ms, endtime_ms, align='start', aggregation_type='sum', bucket_size_msec=total_bucket_size)
            if len(total_prod_result):
                total_prod = total_prod_result[0][1]
            if now >= starttime and now <= endtime:
                #add the current day
                now_start_day = now - (now % 86400000)
                total_prod_result = rts.range("electricity_prod_gen_daily_1min", now_start_day, now_start_day + 86400000, align='start', aggregation_type='max', bucket_size_msec=86400000)
                if len(total_prod_result):
                    total_prod += total_prod_result[0][1]

    #total gas
    total_gas = 0
    if FEATURE_GAS:
        total_gas_result = rts.range("gas_15min", starttime_ms, endtime_ms, align='start', aggregation_type='sum', bucket_size_msec=total_bucket_size)
        if len(total_gas_result):
            total_gas = total_gas_result[0][1]

    #total solar forecast
    total_solar_forecast = 0
    if FEATURE_SOLAR_FORECAST:
        total_solar_forecast_result = rts.range("solar_forecast_1h", starttime_ms, endtime_ms, align='start', aggregation_type='sum', bucket_size_msec=total_bucket_size)
        if len(total_solar_forecast_result):
            total_solar_forecast = total_solar_forecast_result[0][1]


    total_usage["total_usage_up"] = total_up
    total_usage["total_usage_down"] = total_down
    total_usage["total_usage_peak_down"] = peak_down
    if FEATURE_PRODUCTION:
        total_usage["total_usage_prod"] = total_prod
    if FEATURE_GAS:
        total_usage["total_usage_gas"] = total_gas
    if FEATURE_SOLAR_FORECAST:
        total_usage["total_usage_solar_forecast"] = total_solar_forecast

    return total_usage

def convert_usage(value):
    result = float(value)
    result *= 1000
    return int(result)

def set_value_if_data_older_than(data, value, timeout_ms):
    now = int(time.time() * 1000)
    if (now - data[0]) >= timeout_ms:
        return (data[0], value)
    return data

def get_latest_usage():
    #redis command: xrevrange elektricity + - COUNT 1
    #latest_stream_entry = r.xrevrange("electricity", max=u'+', min=u'-', count=1)

    latest_prod = (0.0, 0.0)

    #redis command: TS.GET electricity_down_sec
    latest_up = rts.get("electricity_up_sec")
    latest_down = rts.get("electricity_down_sec")

    if latest_up is None or latest_down is None:
        return generate_json_ouput(0, 0, 0, 0)

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

    result = { "up": convert_usage(latest_up[1]),
               "down": convert_usage(latest_down[1]),
               "predicted_peak_down": round(predicted_peak_down, 5)}

    if FEATURE_PRODUCTION:
        latest_prod = rts.get("electricity_prod_1min")
        if latest_prod is None:
            latest_prod = (latest_up[0] - 180001, 0.0)
        latest_prod = set_value_if_data_older_than(latest_prod, 0.0, 180000)
        result["prod"] = convert_usage(latest_prod[1])

    return result

if __name__ == '__main__':
    #file executed as script   
    #get input params
    day_str = get_script_arg_day()
    mode_str = get_script_arg_mode()
    result = get_detailed_usage(day_str, mode_str)
    print(result)

