#!/usr/bin/python3
import json

from django.conf import settings
from home_energy.view.energy_common import *
from home_energy.view import prices as pr

if not settings.configured:
    settings.configure(FEATURE_GAS=1, FEATURE_PRODUCTION=1, FEATURE_SOLAR_CONSUMPTION=1)

FEATURE_GAS = settings.FEATURE_GAS
FEATURE_PRODUCTION = settings.FEATURE_PRODUCTION
FEATURE_SOLAR_CONSUMPTION = settings.FEATURE_SOLAR_CONSUMPTION


def get_period_cost_current_day(unit_name, timeseries_name, price, price_starttime_ms, price_endtime_ms, bucket_size, rts):
    period_cost = 0
    now = get_now_epoch_in_ms()
    if now >= price_starttime_ms and now <= price_endtime_ms:
        unit_price = price.get(unit_name)
        if unit_price:
            unit_price = float(unit_price)
            usage = 0
            now_start_day = now - (now % 86400000)
            usage_result = rts.range(timeseries_name, now_start_day, now_start_day + 86400000, align='start', aggregation_type='max', bucket_size_msec=86400000)
            if len(usage_result):
                usage = usage_result[0][1]
            period_cost = usage * unit_price

    return period_cost

def get_period_cost(unit_name, timeseries_name, price, price_starttime_ms, price_endtime_ms, bucket_size, rts):
    period_cost = 0
    unit_price = price.get(unit_name)
    if unit_price:
        unit_price = float(unit_price)
        usage = 0
        usage_result = rts.range(timeseries_name, price_starttime_ms, price_endtime_ms, align='start', aggregation_type='sum', bucket_size_msec=bucket_size)
        if len(usage_result):
            usage = usage_result[0][1]
        period_cost = usage * unit_price

    return period_cost

def get_cost_for_unit(unit_name, timeseries_name, starttime, endtime, period_cost_function, rts):
    cost = 0
    starttime_ms = starttime * 1000
    endtime_ms = endtime * 1000
    
    prices = pr.get_prices_in_range(unit_name, starttime, endtime)

    for i, price in enumerate(prices):
        price_starttime = int(price["starttime"])
        if price_starttime < starttime:
            price_starttime = starttime

        price_endtime = endtime
        if i != len(prices)-1:
            price_endtime = int(prices[i+1]["starttime"]) - 1

        price_starttime_ms = price_starttime * 1000
        price_endtime_ms = price_endtime * 1000
        bucket_size = price_endtime_ms - price_starttime_ms + 1000

        #print(f'{format_epoch(get_datetime_from_epoch_in_s(price_starttime), "%Y-%m-%d %H:%M:%S")} - {format_epoch(get_datetime_from_epoch_in_s(price_endtime), "%Y-%m-%d %H:%M:%S")}')
        #print(bucket_size / 86400000)

        cost += period_cost_function(unit_name, timeseries_name, price, price_starttime_ms, price_endtime_ms, bucket_size, rts)

    return cost    

def get_total_costs(starttime, endtime, mode):
    total_costs = {}
    r = db_connect()
    rts = db_timeseries_connect(r)

    total_cost_down_high = 0
    total_cost_up_high = 0
    total_cost_gas = 0
    total_cost_solar_consumption = 0

    total_cost_down_high += get_cost_for_unit("down_high", "electricity_down_1h", starttime, endtime, get_period_cost, rts)
    total_cost_up_high   += get_cost_for_unit("up_high", "electricity_up_1h", starttime, endtime, get_period_cost, rts)
    if FEATURE_GAS:
        total_cost_gas   += get_cost_for_unit("gas", "gas_15min", starttime, endtime, get_period_cost, rts)
    if FEATURE_PRODUCTION and FEATURE_SOLAR_CONSUMPTION:
        total_cost_solar_consumption += get_cost_for_unit("down_high", "electricity_prod_gen_daily_1day", starttime, endtime, get_period_cost, rts)
        total_cost_solar_consumption += get_cost_for_unit("down_high", "electricity_prod_gen_daily_1min", starttime, endtime, get_period_cost_current_day, rts)
        total_cost_solar_consumption -= get_cost_for_unit("down_high", "electricity_up_1h", starttime, endtime, get_period_cost, rts)
        total_cost_solar_consumption -= get_cost_for_unit("up_high",   "electricity_prod_gen_daily_1day", starttime, endtime, get_period_cost, rts)
        total_cost_solar_consumption -= get_cost_for_unit("up_high",   "electricity_prod_gen_daily_1min", starttime, endtime, get_period_cost_current_day, rts)
        total_cost_solar_consumption += total_cost_up_high

    total_costs["total_cost_down_high"] = total_cost_down_high
    total_costs["total_cost_up_high"]   = total_cost_up_high
    if FEATURE_GAS:
        total_costs["total_cost_gas"]   = total_cost_gas
    if FEATURE_PRODUCTION and FEATURE_SOLAR_CONSUMPTION:
        total_costs["total_cost_solar_consumption"] = total_cost_solar_consumption

    return total_costs

if __name__ == '__main__':
    #file executed as script

    result  = get_total_cost(1672527600, 1680299999) #1 jan 2023 - 31 mar 2023 23:59:59

    print(result)
