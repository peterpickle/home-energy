#!/usr/bin/python3

'''
usage:
python simulate_battery.py YYYY-MM-DD YYYY-MM-DD <battery capacity in kWh>
python simulate_battery.py 2022-01-01 2022-12-31 5.0
'''

import datetime
import calendar
from enum import Enum
import redis
import redistimeseries.client
import sys
import time


def get_script_arg_start_day():
    if len(sys.argv) >= 2:
        #return the first argument
        return sys.argv[1]
    return ''

def get_script_arg_end_day():
    if len(sys.argv) >= 3:
        #return the second argument
        return sys.argv[2]
    return ''

def get_script_arg_capacity():
    if len(sys.argv) >= 4:
        #return the third argument
        return sys.argv[3]
    return ''

def parse_day(day_str):
    return datetime.datetime.strptime(day_str, '%Y-%m-%d')

'''
Gets the time, value entries without the labels
'''
def get_entries(output_entries, label, value):
    for direction in output_entries:
        key = label + '=' + value
        if key in direction:
            return direction[key][1]
    return None

def get_epoch_time_ms(date):
    return int(date.strftime("%s")) * 1000

def get_epoch_end_time(start_epoch_time, days):
    return start_epoch_time + (days * 86400000) - 1



def simulate(start_day_str, end_day_str, capacity_str):
    start_day = parse_day(start_day_str)
    end_day = parse_day(end_day_str)
    capacity = float(capacity_str)

    #calculate the range to get data from
    days = (end_day - start_day).days

    start_time = get_epoch_time_ms(start_day)
    end_time = get_epoch_time_ms(end_day)
    bucket_size_s = 1 * 60
    bucket_size_ms = bucket_size_s * 1000
    buckets_per_hour = 3600 / bucket_size_s

    #connect to the DB
    r = redis.Redis(host='localhost',
                    port=6379,
                    password=None)
    rts = redistimeseries.client.Client(r)

    down_entries = rts.range("electricity_down_1min", start_time, end_time, align='start', aggregation_type='avg', bucket_size_msec=bucket_size_ms)
    up_entries = rts.range("electricity_up_1min", start_time, end_time, align='start', aggregation_type='avg', bucket_size_msec=bucket_size_ms)
    #prod_entries = rts.range("electricity_prod_1min", start_time, end_time, align='start', aggregation_type='avg', bucket_size_msec=bucket_size_ms)
    print(len(down_entries))
    print(len(up_entries))
    #print(len(prod_entries))

    '''
    all_entries = rts.mrange(start_time, end_time, align='start', aggregation_type='avg', bucket_size_msec=bucket_size_ms, filters=['type=(up,down,prod)', 'granularity=(1m)'], groupby='type', reduce='min')
    #print(all_entries)

    down_entries = get_entries(all_entries, 'type', 'down')
    up_entries = get_entries(all_entries, 'type', 'up')
    prod_entries = get_entries(all_entries, 'type', 'prod')
    print(len(down_entries))
    print(len(up_entries))
    print(len(prod_entries))
    '''

    nbOfDetailedEntries = 0
    current_charge = 0
    charged = 0
    discharged = 0

    for i, up_entry in enumerate(up_entries):
        down_entry = down_entries[i]
        if (up_entry[0] == down_entry[0]):
            nbOfDetailedEntries += 1

            '''
            prod_entry = [item for item in prod_entries if item[0] == up_entry[0]]
            if len(prod_entry):
                prod_entry = prod_entry[0]
            else:
                prod_entry = (up_entry[0], 0.0)

            if up_entry[1] > prod_entry[1]:
                prod_entry = up_entry
            '''

            d = down_entry[1] / buckets_per_hour
            u = up_entry[1] / buckets_per_hour
            #p = prod_entry[1]

            if current_charge != 0:
                if d > current_charge:
                    discharged += current_charge
                    current_charge = 0
                else:
                    discharged += d
                    current_charge -= d

            if u > 0:
                if current_charge + u > capacity:
                    charged += capacity - current_charge
                    current_charge = capacity
                else:
                    charged += u
                    current_charge += u

        else:
            print('Keys don\'t match for up and down entries. i ' + str(i) + ', up_key ' + str(up_entry[0]) + ', down_key ' + str(down_entry[0]))


    return (nbOfDetailedEntries, charged, discharged)

if __name__ == '__main__':
    #file executed as script
    start_day_str = get_script_arg_start_day()
    end_day_str = get_script_arg_end_day()
    capacity_str = get_script_arg_capacity()
    result = simulate(start_day_str, end_day_str, capacity_str)
    print(result)
