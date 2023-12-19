#!/usr/bin/python3

import datetime
import redis
import time

from enum import Enum

class Mode(Enum):
    DAY = 1
    MONTH = 2
    YEAR = 3
    ALL = 4

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

def get_datetime_from_epoch_in_s(epoch_in_s):
    return datetime.datetime.fromtimestamp(epoch_in_s)

def get_datetime_from_epoch_in_ms(epoch_in_ms):
    return datetime.datetime.fromtimestamp(epoch_in_ms / 1000)

def format_epoch(epoch_in_ms, format_str):
    return epoch_in_ms.strftime(format_str)

def get_now_epoch_in_s():
    return int(time.time())

def get_now_epoch_in_ms():
    return  get_now_epoch_in_s() * 1000

def get_epoch_time_s(date):
    return int(date.strftime("%s"))

def get_epoch_time_ms(date):
    return int(date.strftime("%s")) * 1000

def get_epoch_end_time(start_epoch_time, days):
    return start_epoch_time + (days * 86400000) - 1
