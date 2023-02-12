#!/usr/bin/python3

import datetime
import redis
import time

def db_connect():
    #connect to the DB
    r = redis.Redis(host='localhost',
                    port=6379,
                    password=None,
                    decode_responses=True)
    return r

def db_timeseries_connect(r):
    return r.ts()
    
def parse_day(day_str):
    return datetime.datetime.strptime(day_str, '%Y-%m-%d')

def get_now_epoch_in_s():
    return int(time.time())

def get_now_epoch_in_ms():
    return  get_now_epoch_in_s() * 1000

def get_epoch_time_ms(date):
    return int(date.strftime("%s")) * 1000

def get_epoch_end_time(start_epoch_time, days):
    return start_epoch_time + (days * 86400000) - 1
