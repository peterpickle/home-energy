#!/usr/bin/python3

import json
import redis

#connect to the DB
r = redis.Redis(host='localhost',
                port=6379,
                password=None)
#rts = redistimeseries.client.Client(r)

def get(field):
    value = r.get(field)

    if value is not None:
        value = value.decode("ascii")

    result_dict = { field: value }

    return json.dumps(result_dict)

def get_all():
    keys = r.keys("comfoair.*")
    values = r.mget(keys)

    for i in range(len(keys)):
        keys[i] = keys[i].decode("ascii")
    for i in range(len(values)):
        values[i] = values[i].decode("ascii")

    result_dict = dict(zip(keys, values))

    return json.dumps(result_dict)

if __name__ == '__main__':
    #file executed as script
    result = get_all()
    print(result)
