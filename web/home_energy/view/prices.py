#!/usr/bin/python3

from energy_common import *

#get price id

#HMSET price:1 id 1 starttime 0  down 0.1 up 0.01 peak 40
#ZADD price.starttime.index 0 price:1
def add_price(starttime, down , up, peak):
    r = db_connect()

    #check if id exists and inc
    while True:
        id = 'price:' + str(r.incr('price.id'))
        nbOfExistingKeys = r.exists(id)
        if nbOfExistingKeys == 0:
            break

    price = {'id': id, 'starttime': starttime, 'down': down, 'up': up, 'peak': peak}
    
    p = r.pipeline()
    p.hset(id, mapping=price)
    p.zadd('price.starttime.index', {id : starttime})
    p.execute()
    
    return id

def modify_price(id, starttime, down , up, peak):
    r = db_connect()

    #check if id exists
    nbOfExistingKeys = r.exists(id)
    if nbOfExistingKeys == 0:
        return False

    price = {'id': id, 'starttime': starttime, 'down': down, 'up': up, 'peak': peak}

    p = r.pipeline()
    p.hset(id, mapping=price)
    p.zadd('price.starttime.index', {id : starttime})
    p.execute()
    
    return True

def remove_price(id):
    r = db_connect()
    p = r.pipeline()
    p.zrem('price.starttime.index', id)
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

    if len(prices) and starttime < int(prices[0]['starttime']):
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
    id = add_price(now, 0.5, 0.05, 50)
    rv = modify_price(id, now + 10, 0.6, 0.06, 60)
    print(rv)
    remove_price(id)
    '''

    result = get_all_prices_reversed()
    print(result)

    #add_price(1, 1, 0.01, 10)
    #add_price(20, 2, 0.02, 20)
    #add_price(30, 3, 0.03, 30)
    #add_price(50, 5, 0.05, 50)
    
    result = get_prices_in_range(25, 50)
    print(result)
