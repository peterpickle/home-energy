#!/usr/bin/python3

import datetime
import redis

def get_debug_entries():
    r = redis.Redis(host='localhost',
                    port=6379, 
                    password=None)

    debug_result = []
    #redis command: xrange p1_reader_debug - + COUNT 200
    debug_entries = r.xrange("p1_reader_debug", min=u'-', max=u'+')

    for entry in debug_entries:
        time = float(entry[0].decode('utf-8').split('-')[0])
        timestr = datetime.datetime.fromtimestamp(time/1000).strftime('%c')
        values = list(entry[1].items())[0]
        location = values[0].decode('utf-8')
        message = values[1].decode('utf-8')
        debug_result.append({"time":timestr, "location":location, "message":message})

    return debug_result


if __name__ == '__main__':
    # file executed as script
    debug_result = get_debug_entries()
    result = ''
    for entry in debug_result:
        result += f'{entry["time"]}: {entry["location"]} - {entry["message"]}\n'
    print(result)
