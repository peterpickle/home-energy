#!/usr/bin/python3

import datetime
import redis

r = redis.Redis(host='localhost',
                port=6379, 
                password=None)

#redis command: xrange p1_reader_debug - + COUNT 200
debug_entries = r.xrange("p1_reader_debug", min=u'-', max=u'+')

result = ''

for entry in debug_entries:
    time = float(entry[0].decode('ascii').split('-')[0])
    timestr = datetime.datetime.fromtimestamp(time/1000).strftime('%c')
    values = list(entry[1].items())[0]
    location = values[0].decode('ascii')
    message = values[1].decode('ascii')
    result += f'{timestr}: {location} - {message}</br>'


print(result)

