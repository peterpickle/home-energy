#!/usr/bin/python3

import datetime
import calendar
from enum import Enum
import redis
import redistimeseries.client
import sys
import time

FEATURE_PRODUCTION = 1

class Mode(Enum):
    DAY = 1
    MONTH = 2
    YEAR = 3

def get_day():
    day = datetime.date.today()

    #check script arguments
    if len(sys.argv) >= 2:
        #check the first argument and parse it
        try:
            day = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        except ValueError:
            pass

    return day

def get_mode():
    mode = Mode.DAY

    #check script arguments
    if len(sys.argv) >= 3:
        #check the second argument and parse it
        try:
            mode = Mode(int(sys.argv[2]))
        except ValueError:
            pass

    return mode

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
def generate_json_ouput(day, mode, total_day_up, total_day_down, peak_day_down, total_prod, 
                        up_entries, down_entries, peak_down_entries, prod_entries):
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

#get input params
day = get_day()
mode = get_mode()

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

start_time = get_epoch_time_ms(start_day)
end_time = get_epoch_end_time(start_time, days)
total_bucket_size = days * 86400000

#connect to the DB
r = redis.Redis(host='localhost',
                port=6379, 
                password=None)
rts = redistimeseries.client.Client(r)

prod_entries = []

#Get the detailed up/down data
if mode == Mode.DAY:
    #Get usage per 2 minutes
    #TS.MRANGE - + AGGREGATION avg 120000 FILTER dir=(up,down) granularity=(1m,15m) GROUPBY dir REDUCE min
    #only query the needed granularity to make the query faster. The 15min data is kept forever, so no need to query the hourly data or the 1s data
    mixed_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='avg', bucket_size_msec=180000, filters=['dir=(up,down)', 'granularity=(1m,15m)'], groupby='dir', reduce='min')
    up_entries = get_entries(mixed_entries, 'dir', 'up')
    down_entries = get_entries(mixed_entries, 'dir', 'down')
    peak_down_entries = rts.range("electricity_down_15min", start_time, end_time)
    if FEATURE_PRODUCTION:
        prod_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='avg', bucket_size_msec=180000, filters=['type=prod', 'granularity=(1m,15m)'], groupby='type', reduce='min')
        prod_entries = get_entries(prod_entries, 'type', 'prod')
elif mode == Mode.MONTH:
    mixed_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='sum', bucket_size_msec=86400000, filters=['dir=(up,down)', 'granularity=1h'], groupby='dir', reduce='min')
    up_entries = get_entries(mixed_entries, 'dir', 'up')
    down_entries = get_entries(mixed_entries, 'dir', 'down')
    peak_down_entries = rts.range("electricity_down_15min", start_time, end_time, align='start', aggregation_type='max', bucket_size_msec=86400000)
    if FEATURE_PRODUCTION:
        prod_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='max', bucket_size_msec=86400000, filters=['type=prod', 'value=dayGen'], groupby='value', reduce='max')
        prod_entries = get_entries(prod_entries, 'value', 'dayGen')
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

        if FEATURE_PRODUCTION:
            prod_result = rts.range("electricity_prod_gen_daily_1day", month_start_epoch, month_end_epoch, align='start', aggregation_type='sum', bucket_size_msec=month_bucket_size)
            #add the current day
            now = int(time.time() * 1000)
            if now >= month_start_epoch and now <= month_end_epoch:
                now_start_day = now - (now % 86400000)
                today_prod_result = rts.range("electricity_prod_gen_daily_1min", now_start_day, now_start_day + 86400000, align='start', aggregation_type='max', bucket_size_msec=86400000)
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

#Get peak usage
#TS.RANGE electricity_down_15min <startTime> <stopTime> ALIGN start AGGREGATION MAX 86400000
peak_down = 0
peak_down_result = rts.range("electricity_down_15min", start_time, end_time, align='start', aggregation_type='max', bucket_size_msec=total_bucket_size)
if len(peak_down_result):
    peak_down = peak_down_result[0][1]
       
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
        now = int(time.time() * 1000)
        if now >= start_time and now <= end_time:
            #add the current day
            now_start_day = now - (now % 86400000)
            total_prod_result = rts.range("electricity_prod_gen_daily_1min", now_start_day, now_start_day + 86400000, align='start', aggregation_type='max', bucket_size_msec=86400000)
            if len(total_prod_result):
                total_prod += total_prod_result[0][1]

#Add missing data at end
up_entries = add_missing_data(up_entries, mode, 0.0)
down_entries = add_missing_data(down_entries, mode, 0.0)
peak_down_entries = add_missing_data(peak_down_entries, mode, 0.0)
prod_entries = add_missing_data(prod_entries, mode, 'null')

#generate the output
result = generate_json_ouput(day, mode, total_up, total_down, peak_down, total_prod, up_entries, down_entries, peak_down_entries, prod_entries)

print(result)

