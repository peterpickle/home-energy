#credits to gytisgreitai
#https://github.com/gytisgreitai
#https://github.com/gytisgreitai/zehnder-can-mqtt

import binascii
import logging
import os
import paho.mqtt.client as mqtt
import redis
#import redistimeseries.client
import sys

import mapping
from can import CANInterface
from hass import publish_hass_mqtt_discovery
from time import sleep

#Get the relative path from the script
dirname = os.path.dirname(__file__)
errorLogFile = os.path.join(dirname, 'vent_error_log.txt')

#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# create logger
logger = logging.getLogger('vent-reader')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)

# create file handler and set level to error
fileHandler = logging.FileHandler(errorLogFile)
fileHandler.setLevel(logging.ERROR)

# create formatter
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s:%(message)s')

# add formatter log handlers
consoleHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

# add handlers to logger
logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)

#Connect to redis
r = redis.Redis(host='localhost',
                     port=6379, 
                     password=None)
#rts = redistimeseries.client.Client(r)


def on_mqtt_connect(client, userdata, flags, rc):
  logger.info('subscribing to comfoair/action')
  client.subscribe('comfoair/action')
  client.publish('comfoair/status', 'online', 0, True)
  publish_hass_mqtt_discovery(client, logger)

def on_mqtt_message(client, userdata, msg):
  action =str(msg.payload.decode('utf-8'))
  logger.info('got mqtt message %s %s', msg.topic, action)
  if action in mapping.commands:
    command = mapping.commands[action]
    logger.info('action ok, executing: %s', action)
    try:
      for i in range(3):
        can.send(command)
        sleep(1)
    except Exception as e:
      logger.error('failed in send %s', e)
  else:
    logger.error('action not found %s', action)

def process_can_message(pdid, id_hex, data):
  if id_hex in mapping.data:
    config = mapping.data[id_hex]
    value =  config.get('transformation')(data)
    name = config.get('name')
    if config.get('ok') and value is not None:
      r.set('comfoair.' + name, value)
      mqtt_client.publish('comfoair/status/' + name, value, 0, True)
    else:
      logger.info(f'No parsing details. id:{pdid} id_hex:{hex(id_hex)} name:{name} decoded:{value} raw:{binascii.hexlify(bytearray(data))}')
  elif id_hex != 0x01000010:
      logger.info(f'Id not found. id:{pdid} id_hex:{hex(id_hex)} raw:{binascii.hexlify(bytearray(data))}')


logger.info('starting up')
mqtt_client = mqtt.Client()
mqtt_client.connect('127.0.0.1', 1883, 60)
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message
mqtt_client.loop_start()

can = CANInterface('/dev/ttyUSB_CAN_VENT', 2000000)
can.open(logger)
can.read(process_can_message)
