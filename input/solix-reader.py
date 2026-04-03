#!/usr/bin/python3

# Anker Solix reader

import json
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

def on_mqtt_connect(client, userdata, flags, rc):
    logger.info('subscribe to MQTT topics')
    client.subscribe('solix/site/Zwaluwstraat/scenInfo')

def on_mqtt_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        #print(json.dumps(payload, indent=2))  # Pretty-print the JSON
        # SOC: State of Charge (%)
        soc = round(float(payload['solarbank_info']['total_battery_power']) * 100, 1)
        # power (W) positive for charging, negative for discharging
        power = int(float(payload['solarbank_info']['total_charging_power']) - float(payload['solarbank_info']['battery_discharge_power']))
        timeKey = int(time.time()) * 1000
        #logger.info(f"time {timeKey} soc {soc}%, power {power}W")
        if power >=0:
            logger.info(f"charge: {power}W")
            rts.madd([
                      ("battery_charge_sec", timeKey, float(power)),
                      ("battery_discharge_sec", timeKey, 0.0)
                     ])
        else:
            logger.info(f"discharge: {-power}W")
            rts.madd([
                      ("battery_charge_sec", timeKey, 0.0),
                      ("battery_discharge_sec", timeKey, float(-power))
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




