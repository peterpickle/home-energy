#!/usr/bin/python3

import datetime
import calendar
from enum import Enum
import redis
import redistimeseries.client
import sys
import time

from django.conf import settings

if not settings.configured:
    settings.configure(FEATURE_GAS=1, FEATURE_PRODUCTION=1)

FEATURE_PRODUCTION = settings.FEATURE_PRODUCTION
FEATURE_GAS = settings.FEATURE_GAS

#The buckset size should be a number that could used to divide 15 minutes
day_bucket_size_msec = 3 * 60 * 1000
if FEATURE_GAS:
    day_bucket_size_msec = 5 * 60 * 1000


class Mode(Enum):
    DAY = 1
    MONTH = 2
    YEAR = 3

def parse_day(day_str):
    return datetime.datetime.strptime(day_str, '%Y-%m-%d')

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
  "date": "2021-12-10",
  "total_day_up": "totalUpValue",
  "total_day_down": "totalDownValue",
  "peak_day_down": "peakDownValue",
  "detailed_data" : [
    {"t": "timeValue", "u": "upValue", "d": "downValue"},
    {"t": "timeValue", "u": "upValue", "d": "downValue"}
  ],
  "detailed_prod" : [
    {"t": "timeValue", "p": "prodValue"},
    {"t": "timeValue", "p": "prodValue"}
  ]
}
'''
def generate_json_ouput(day, mode,
                        total_day_up, total_day_down, peak_day_down, total_prod, total_gas,
                        up_entries, down_entries, peak_down_entries, prod_entries, gas_entries):
    if mode == Mode.DAY:
        correction_factor = 1000
    elif mode == Mode.MONTH or mode == Mode.YEAR:
        correction_factor = 1

    result = '{\n'
    result += '"date": "' + day.strftime('%Y-%m-%d') + '",\n'
    result += '"mode": "' + mode.name + '",\n'
    result += '"total_up": ' + str(total_day_up) + ',\n'
    result += '"total_down": ' + str(total_day_down) + ',\n'
    result += '"peak_down": ' + str(peak_day_down) + ',\n'
    if FEATURE_PRODUCTION:
        result += '"total_prod": ' + str(total_prod) + ',\n'
    if FEATURE_GAS:
        result += '"total_gas": ' + str(total_gas) + ',\n'

    result += '"detailed_up_down" : [\n'
    for i, up_entry in enumerate(up_entries):
        if i != 0:
            result += ',\n'
        down_entry = down_entries[i]
        if (up_entry[0] == down_entry[0]):
            result += '{"t":' + str(up_entry[0]) + \
                      ',"u":' + str(up_entry[1] * correction_factor) + \
                      ',"d":' + str(down_entry[1] * correction_factor) 

            peak_down_entry = [item for item in peak_down_entries if item[0] == up_entry[0]]
            if len(peak_down_entry):
                peak_down_entry = peak_down_entry[0]
                result += ',"pd":'+ str(peak_down_entry[1] * correction_factor)
            else:
                result += ',"pd":null'

            if FEATURE_PRODUCTION:
                prod_entry = [item for item in prod_entries if item[0] == up_entry[0]]
                if len(prod_entry):
                    prod_entry = prod_entry[0]
                    result += ',"p":' + str(prod_entry[1] * correction_factor)
                else:
                    result += ',"p":null'
            else:
                result += ',"p":null'

            if FEATURE_GAS:
                gas_entry = [item for item in gas_entries if item[0] == up_entry[0]]
                if len(gas_entry):
                    gas_entry = gas_entry[0]
                    result += ',"g":' + str(gas_entry[1])
                else:
                    result += ',"g":null'
            else:
                result += ',"g":null'

            result += '}'
        else:
            print('Keys don\'t match for up and down entries. i ' + str(i) + ', up_key ' + str(up_entry[0]) + ', down_key ' + str(down_entry[0]))
    result += '\n]'
    '''
    #report the production in a seperate table
    if FEATURE_PRODUCTION:
        result += ',\n'
        result += '"detailed_prod" : [\n'
        for i, entry in enumerate(prod_entries):
            if i != 0:
                result += ',\n'
            result += '{"t":' + str(entry[0]) + ',"p":' + str(entry[1] * correction_factor) + '}'
        result += '\n]'
    '''

    result += '\n}'
    return result

def get_epoch_time_ms(date):
    return int(date.strftime("%s")) * 1000

def get_epoch_end_time(start_epoch_time, days):
    return start_epoch_time + (days * 86400000) - 1

def get_electricity_current_hour(rts, dir_str):
    # Get the latest value in the 1h series.
    latest_1h = rts.get("electricity_" + dir_str + "_1h")
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

    now = int(time.time() * 1000)
    start_time = get_epoch_time_ms(start_day)
    end_time = get_epoch_end_time(start_time, days)
    total_bucket_size = days * 86400000

    #connect to the DB
    r = redis.Redis(host='localhost',
                    port=6379, 
                    password=None)
    rts = redistimeseries.client.Client(r)

    prod_entries = []
    gas_entries = []

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

    #Get total usage
    #TS.RANGE electricity_down_1h <startTime> <stopTime> AGGREGATION SUM 86400000
    total_up = 0
    total_down = 0
    total_up_result = rts.range("electricity_up_1h", start_time, end_time, align='start', aggregation_type='sum', bucket_size_msec=total_bucket_size)
    total_down_result = rts.range("electricity_down_1h", start_time, end_time, align='start', aggregation_type='sum', bucket_size_msec=total_bucket_size)
    if len(total_up_result):
        total_up = total_up_result[0][1]
    if len(total_down_result):
        total_down = total_down_result[0][1]
    
    if now >= start_time and now <= end_time:
        #add the last/current hour
        total_up += get_electricity_current_hour(rts, "up")
        total_down += get_electricity_current_hour(rts, "down")

    #Get peak usage

    peak_down = 0
    if mode != Mode.YEAR:
        # Show the MAX peak
        #TS.RANGE electricity_down_15min <startTime> <stopTime> ALIGN start AGGREGATION MAX 86400000
        peak_down_result = rts.range("electricity_down_15min", start_time, end_time, align='start', aggregation_type='max', bucket_size_msec=total_bucket_size)
        if len(peak_down_result):
            peak_down = peak_down_result[0][1]
    else:
        # Show the AVG peak of the MAX of the months
        nb_of_peak_entries = 0;
        for month_peak_entry in peak_down_entries:
            peak_down += month_peak_entry[1]
            nb_of_peak_entries += 1
        if nb_of_peak_entries != 0:
            peak_down /= nb_of_peak_entries

    #total production
    total_prod = 0
    if FEATURE_PRODUCTION:
        if mode == Mode.DAY:
            #TS.MRANGE - + AGGREGATION max 86400000 FILTER value=dayGen GROUPBY value REDUCE max
            total_prod_result = rts.mrange(start_time, end_time, align='start', aggregation_type='max', bucket_size_msec=86400000, filters=['type=prod', 'value=dayGen'], groupby='value', reduce='max')
            total_prod_result =  get_entries(total_prod_result, 'value', 'dayGen')
            if total_prod_result:
                total_prod =  total_prod_result[0][1]
        elif mode == Mode.MONTH or mode == Mode.YEAR:
            total_prod_result = rts.range("electricity_prod_gen_daily_1day", start_time, end_time, align='start', aggregation_type='sum', bucket_size_msec=total_bucket_size)
            if len(total_prod_result):
                total_prod = total_prod_result[0][1]
            if now >= start_time and now <= end_time:
                #add the current day
                now_start_day = now - (now % 86400000)
                total_prod_result = rts.range("electricity_prod_gen_daily_1min", now_start_day, now_start_day + 86400000, align='start', aggregation_type='max', bucket_size_msec=86400000)
                if len(total_prod_result):
                    total_prod += total_prod_result[0][1]

    #total gas
    total_gas = 0
    if FEATURE_GAS:
        total_gas_result = rts.range("gas_15min", start_time, end_time, align='start', aggregation_type='sum', bucket_size_msec=total_bucket_size)
        if len(total_gas_result):
            total_gas = total_gas_result[0][1]

    #Add missing data at end
    up_entries = add_missing_data(up_entries, mode, 0.0)
    down_entries = add_missing_data(down_entries, mode, 0.0)
    peak_down_entries = add_missing_data(peak_down_entries, mode, 0.0)
    prod_entries = add_missing_data(prod_entries, mode, 'null')
    gas_entries = add_missing_data(gas_entries, mode, '0.0')

    #generate the output
    result = generate_json_ouput(day, mode,
                                total_up, total_down, peak_down, total_prod, total_gas,
                                up_entries, down_entries, peak_down_entries, prod_entries, gas_entries)

    return result

if __name__ == '__main__':
    #file executed as script   
    #get input params
    day_str = get_script_arg_day()
    mode_str = get_script_arg_mode()
    result = get_detailed_usage(day_str, mode_str)
    print(result)
