import datetime
import redis
import requests
import time

LATITUDE = 51.168776
LONGITUDE = 4.501905
DECLENATION = 45
INVERTER_MAX_POWER = 3250

BASE_URL = 'https://api.forecast.solar/estimate'


proxies = { }
proxies = { 
              "http"  : "http://135.245.192.7:8000", 
              "https" : "http://135.245.192.7:8000", 
              "ftp"   : "ftp://135.245.192.7:8000"
          }

faces = [ { 'latitude':LATITUDE, 'longitude':LONGITUDE, 'declination':DECLENATION, 'azimuth':-94, 'kwp':2.24, 'options':{'damping':0, 'time':'seconds', 'start':'now'}},
          { 'latitude':LATITUDE, 'longitude':LONGITUDE, 'declination':DECLENATION, 'azimuth':86, 'kwp':3.2,   'options':{'damping':0, 'time':'seconds', 'start':'now'}},
        ]

headers = { 'Accept': 'application/json' }

totals = { }

class Database:

    def __init__(self):
        pass

    def connect(self):
        self.r = redis.Redis(host='localhost',
                             port=6379, 
                             password=None)
        self.rts = self.r.ts()

    def disconnect(self):
        #Nothing to do for redis
        pass

    def save_forecast_entry(self, timeKey, value):
        print(f'time:{timeKey} value:{value}')
        
        #redis time series
        self.rts.add("solar_forecast_1h", timeKey, value)

#TODO: make the time functions common
def get_epoch_time_ms(date):
    return int(date.strftime("%s")) * 1000

def get_epoch_end_time(start_epoch_time, days):
    return start_epoch_time + (days * 86400000) - 1

def get_local_readable_str_from_epoch_ms(epoch_ms):
    return time.strftime('%d-%m-%Y %H:%M', time.localtime(epoch_ms / 1000))

def get_UTC_readable_str_from_epoch_ms(epoch_ms):
    return time.strftime('%d-%m-%Y %H:%M', time.gmtime(epoch_ms / 1000))

def get_highest_value(data, minKey, maxKey):
    keyOfHighestValue = 0
    highestValue = -1

    for k in data.keys():
        if k < minKey or k > maxKey:
            continue
        if data[k] > highestValue:
            keyOfHighestValue = k
            highestValue = data[k]
    
    return (keyOfHighestValue, highestValue)

def get_total_Kwh(data, minKey, maxKey):
    totalWh = 0

    for k in data.keys():
        if k < minKey or k > maxKey:
            continue
        totalWh += data[k]

    return totalWh / 1000

for f in faces:
    url = f"{BASE_URL}/{f['latitude']}/{f['longitude']}/{f['declination']}/{f['azimuth']}/{f['kwp']}"
    print(f'{url}')
    r = requests.get(url=url, params=f['options'], headers=headers)

    #check if result is success
    if r.status_code != 200:
        print('Request failed')
        continue
    
    jsonResult = r.json()
    #jsonResult = {'result': {'watts': {'1663305420': 0, '1663308000': 56, '1663311600': 139, '1663315200': 316, '1663318800': 551, '1663322400': 800, '1663326000': 842, '1663329600': 452, '1663333200': 217, '1663336800': 134, '1663340400': 137, '1663344000': 78, '1663347600': 22, '1663350960': 0, '1663391880': 0, '1663394400': 38, '1663398000': 309, '1663401600': 437, '1663405200': 562, '1663408800': 694, '1663412400': 645, '1663416000': 482, '1663419600': 300, '1663423200': 193, '1663426800': 112, '1663430400': 65, '1663434000': 7, '1663437240': 0}, 'watt_hours': {'1663305420': 0, '1663308000': 20, '1663311600': 118, '1663315200': 345, '1663318800': 779, '1663322400': 1454, '1663326000': 2275, '1663329600': 2922, '1663333200': 3257, '1663336800': 3432, '1663340400': 3568, '1663344000': 3675, '1663347600': 3725, '1663350960': 3735, '1663391880': 0, '1663394400': 13, '1663398000': 187, '1663401600': 560, '1663405200': 1059, '1663408800': 1687, '1663412400': 2357, '1663416000': 2920, '1663419600': 3311, '1663423200': 3558, '1663426800': 3710, '1663430400': 3799, '1663434000': 3835, '1663437240': 3838}, 'watt_hours_day': {'1663279200': 3735, '1663365600': 3838}}, 'message': {'code': 0, 'type': 'success', 'text': '', 'info': {'latitude': 51.1688, 'longitude': 4.5019, 'place': '2530 Boechout, Antwerpen, Anvers, Vlaanderen, BE', 'timezone': 'Europe/Brussels', 'timezone_utc': 'UTC+02:00'}, 'ratelimit': {'period': 3600, 'limit': 12, 'remaining': 11}}}
    #print(jsonResult)

    #check if result is success
    if (jsonResult['message']['code'] != 0):
        print(f"Request failed with code jsonResult['message']['code'] message {jsonResult['message']['text']}")
        continue

    #sum data
    for k in jsonResult['result']['watt_hours_period'].keys():
        v = jsonResult['result']['watt_hours_period'][k]
        print(f"{k} {v}")

        if v == 0:
            continue

        k_ms = int(k) * 1000

        if k_ms in totals:
            totals[k_ms] += v
        else:
            totals[k_ms] = v

# Cap data
for k in totals.keys():
    v = totals[k]

    if v > INVERTER_MAX_POWER:
        v = INVERTER_MAX_POWER
        totals[k] = v

    timeStr = get_local_readable_str_from_epoch_ms(k)
    print(f"{k} {timeStr} {v}")


today_start   = get_epoch_time_ms(datetime.date.today())
today_end     = get_epoch_end_time(today_start, 1)
today_highest = get_highest_value(totals, today_start, today_end)
today_total   = get_total_Kwh(totals, today_start, today_end)

tomorrow_start   = today_start + 86400000
tomorrow_end     = get_epoch_end_time(tomorrow_start, 1)
tomorrow_highest = get_highest_value(totals, tomorrow_start, tomorrow_end)
tomorrow_total   = get_total_Kwh(totals, tomorrow_start, tomorrow_end)

print('Today:')
print(f'  highest: {get_local_readable_str_from_epoch_ms(today_highest[0])} {today_highest[1]}')
print(f'  total:   {today_total}')

print('Tomorrow:')
print(f'  highest: {get_local_readable_str_from_epoch_ms(tomorrow_highest[0])} {tomorrow_highest[1]}')
print(f'  total:   {tomorrow_total}')

db = Database()
db.connect()

for k in totals.keys():
    db.save_forecast_entry(k, totals[k] / 1000)
