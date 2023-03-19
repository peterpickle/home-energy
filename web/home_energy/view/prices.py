#!/usr/bin/python3
from home_energy.view.energy_common import *

allowed_rate_keys = ['down_high', 'down_low', 'up_high', 'up_low', 'peak_down', 'gas']

def validate_rates(rates):
    #validate the keys, only allow the ones we know
    filtered_keys = rates.keys() & allowed_rate_keys

    if len(filtered_keys) != len(rates):
        return False, rates

    filtered_rates = {key: rates[key] for key in filtered_keys}

    #check if we have at least 1 key
    if len(filtered_rates) == 0:
        return 0, filtered_rates

    return True, filtered_rates

#HMSET price:1 id 1 starttime 0  down 0.1 up 0.01 peak 40
#ZADD price.starttime.index 0 price:1
def add_price(starttime, rates):
    valid, rates = validate_rates(rates)
    if not valid:
        return -1

    r = db_connect()

    #check if id exists and inc
    while True:
        id = 'price:' + str(r.incr('price.id'))
        nbOfExistingKeys = r.exists(id)
        if nbOfExistingKeys == 0:
            break

    price = {'id': id, 'starttime': starttime}
    price.update(rates)
    
    p = r.pipeline()
    p.hset(id, mapping=price)
    p.zadd('price.starttime.index', {id : starttime})
    for rate in rates:
        p.zadd('price.starttime.index.' + rate, {id : starttime})
    p.execute()
    
    return id

def modify_price(id, starttime, rates):
    valid, rates = validate_rates(rates)
    if not valid:
        return -1

    r = db_connect()

    #check if id exists
    nbOfExistingKeys = r.exists(id)
    if nbOfExistingKeys == 0:
        return -2

    price = {'id': id, 'starttime': starttime}
    price.update(rates)

    p = r.pipeline()
    for rate in allowed_rate_keys:
        p.zrem('price.starttime.index.' + rate, id)
    p.delete(id)
    p.hset(id, mapping=price)
    p.zadd('price.starttime.index', {id : starttime})
    for rate in rates:
        p.zadd('price.starttime.index.' + rate, {id : starttime})
    p.execute()
    
    return 0

def remove_price(id):
    r = db_connect()
    p = r.pipeline()
    p.zrem('price.starttime.index', id)
    for rate in allowed_rate_keys:
        p.zrem('price.starttime.index.' + rate, id)
    p.delete(id)
    p.execute()

def get_all_prices_reversed():
    r = db_connect()
    prices = []
    price_ids = r.zrange('price.starttime.index', 0, -1, desc=True)
    for id in price_ids:
        price = r.hgetall(id)
        prices.append(price)
    return prices

def get_prices_in_range(starttime, stoptime):
    r = db_connect()
    prices = []
    # ZRANGE price.starttime.index 25 55 BYSCORE
    price_ids = r.zrange('price.starttime.index', starttime, stoptime, byscore=True)
    for id in price_ids:
        price = r.hgetall(id)
        prices.append(price)

    if (len(prices) == 0) or (starttime < int(prices[0]['starttime'])):
        # ZRANGE price.starttime.index 25 0 BYSCORE REV LIMIT 0 1
        price_ids = r.zrange('price.starttime.index', starttime, 0, desc=True, byscore=True, offset=0, num=1)
        if len(price_ids):
            price = r.hgetall(price_ids[0])
            prices.insert(0, price)        
    
    return prices

if __name__ == '__main__':
    #file executed as script
    '''
    now = get_now_epoch_in_s()
    id = add_price(now, {'down_high': 5, 'up_high': 0.05, 'peak_down': 50})
    rv = modify_price(id, now + 10, {'down_high': 6, 'up_high': 0.06, 'peak_down': 60})
    print(rv)
    remove_price(id)
    '''

    result = get_all_prices_reversed()
    print(result)

    #result = add_price(1, {'down_high': 1, 'up_high': 0.01, 'peak_down': 10})
    #add_price(20, {'down_high': 2, 'up_high': 0.02, 'peak_down': 20})
    #add_price(30, {'down_high': 3, 'up_high': 0.03, 'peak_down': 30})
    #add_price(50, {'down_high': 5, 'up_high': 0.05, 'peak_down': 50})
    
    #result = get_prices_in_range(25, 50)
    #print(result)
