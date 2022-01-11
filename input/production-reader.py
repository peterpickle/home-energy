#!/usr/bin/python3

# Ginglong Solis reader

from enum import Enum
import InverterMsg
import logging
import os
import re
import redis
import redistimeseries.client
import socket
import sys
import time

# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)

# create file handler and set level to error
fileHandler = logging.FileHandler('production_error_log.txt')
fileHandler.setLevel(logging.ERROR)

# create formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

# add formatter to log handlers
consoleHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

# add handlers to logger
logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)

HOST = ''
PORT = 43800
LOGGER_SERIAL = 1913831118
INVERTER_SERIAL = '110A82204060040'
DATA_MSG_LEN = 248

class InverterListener():

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.connAddr = None

    def open(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(0)

    def waitOnConnection(self):
        self.conn, self.connAddr = self.socket.accept()
        self.conn.settimeout(180)
        logger.info(f'Connected to {self.connAddr[0]}:{self.connAddr[1]}')

    def close(self):
        self.socket.close()

    def receive(self):
        if self.conn:
            try:
                data = self.conn.recv(DATA_MSG_LEN + 14)
                if not data:
                    logger.info('Socket connection broken')
                    self.conn.close()
                    self.conn = None
                    self.connAddr = None
                    return None
                return data
            except socket.timeout as e:
                logger.info(f'Socket timeout. Error:"{e}"')
                self.conn.close()
                self.conn = None
                self.connAddr = None
                return None
            except ConnectionResetError as e:
                logger.info(f'Connection reset by peer. Error:"{e}"')
                self.conn.close()
                self.conn = None
                self.connAddr = None
                return None
        else:
            logger.error('No existing connection while trying to wait for data')
            return None

class Database:

    def __init__(self):
        self.prev_telegram_key = ''

    def connect(self):
        self.r = redis.Redis(host='localhost',
                             port=6379, 
                             password=None)
        self.rts = redistimeseries.client.Client(self.r)

    def disconnect(self):
        #Nothing to do for redis
        pass

    def save_inverter_msg(self, invMsg):
        #use our own key, linux epoch in ms derived from the time of the measurement
        timeKey = invMsg.getTime()
        currentProd = invMsg.getTotalActivePowerAC() / 1000
        dayProd = invMsg.getGenerationToday()

        #logger.debug(f'time:{timeKey} currentProd:{currentProd} dayProd:{dayProd}')
        
        #redis time series
        self.rts.add("electricity_prod_1min", timeKey, currentProd)
        self.rts.add("electricity_prod_gen_daily_1min", timeKey, dayProd)

'''
   Terminal
'''

def clear_terminal():
    print(chr(27) + "[2J")

##############################################################################
#Main program
##############################################################################

listener = InverterListener(HOST, PORT)
listener.open()

db = Database()
db.connect()

'''
Loop for terminal
'''

while True:
    logger.info('Waiting for connection')
    listener.waitOnConnection()
    data = bytearray()
    while True:
        logger.info('Waiting for data')
        new_data = listener.receive()
        if not new_data:
            #connection broken
            logger.info('Connection broken')
            break

        logger.debug(f'Received new data. length:{len(new_data)} new_data:"{new_data}"')

        data.extend(bytearray(new_data))

        if len(data) < DATA_MSG_LEN:
            logger.info(f'Too little data. length:{len(data)} data:"{data}"')
            continue

        offset = data.find(b'\xa5\xeb\x00\x10')
        if offset == -1:
            logger.info(f'Start of message not found, collecting more data. length:{len(data)} data:"{data}"')
            #collect more data
            continue
        else:
            logger.info(f'Found start of message at offset. offset:{offset}')

        remaining_data_len = len(data) - offset
        if remaining_data_len < DATA_MSG_LEN:
            logger.info(f'Remaining data length too small, collecting more data. remaining_data_len:{remaining_data_len} length:{len(data)} data:"{data}"')
            continue

        invMsg = InverterMsg.InverterMsg(data[offset:])
        
        if invMsg.getLoggerSerialNumber() != LOGGER_SERIAL:
            logger.error(f'Received message with unexpected logger serial. offset:{offset} length:{len(data)} data:"{data}"')
            continue

        if invMsg.getInverterSerialNumber() != INVERTER_SERIAL:
            logger.error(f'Received message with unexpected inverter serial. offset:{offset}  length:{len(data)} data:"{data}"')
            continue

        invMsg.printData()
        db.save_inverter_msg(invMsg)

        if offset != 0:
            logger.error(f'Discarding data. length:{offset} data:"{data[:offset]}"')

        #remove the part to discard and the message we handled
        data = data[(offset  + DATA_MSG_LEN):]
        logger.debug(f'Remaining data. length:{len(data)} data:"{data}"')

db.disconnect()
listener.close()

