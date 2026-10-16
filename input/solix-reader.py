#!/usr/bin/python3

# Anker Solix reader

import json
import math
import logging
import os
import paho.mqtt.client as mqtt
import redis
import time

#Get the relative path from the script
dirname = os.path.dirname(__file__)
errorLogFile = os.path.join(dirname, 'solix_error_log.txt')

# create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create console handler and set level to debug
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)

# create file handler and set level to error
fileHandler = logging.FileHandler(errorLogFile)
fileHandler.setLevel(logging.ERROR)

# create formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

# add formatter to log handlers
consoleHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

# add handlers to logger
logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)

#Connect to redis
r = redis.Redis(host='localhost',
                port=6379,
                password=None, socket_timeout=5, socket_connect_timeout=5)
rts = r.ts()

def safe_float(value):
    """Convert a value to float, handling null and invalid values."""
    if value is None:
        return None

    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None

def on_mqtt_connect(client, userdata, flags, rc):
    logger.info('subscribe to MQTT topics')
    client.subscribe('solix/live')

def on_mqtt_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        #print(json.dumps(payload, indent=2))  # Pretty-print the JSON
        # SOC: State of Charge (%)
        soc = safe_float(payload.get('battery_pct'))
        charge_w = safe_float(payload.get('bat_charging_w'))
        discharge_w = safe_float(payload.get('bat_discharging_w'))

        power_valid = charge_w is not None and discharge_w is not None

        charge_kw = max(0.0, charge_w or 0.0) / 1000
        discharge_kw = max(0.0, discharge_w or 0.0) / 1000

        timeKey = int(time.time()) * 1000
        #logger.info(f"time {timeKey} soc {soc}%, charge {charge_w}W, discharge {discharge_w}W")
        rts.madd([
                  ("battery_charge_sec", timeKey, charge_kw),
                  ("battery_discharge_sec", timeKey, discharge_kw)
                ])
        r.set('battery.soc', soc)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse payload: {msg.payload}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message
mqtt_client.connect('127.0.0.1', 1883, 60)
mqtt_client.loop_forever()




