#!/usr/bin/python3

# DSMR v5.0 P1 reader

from enum import Enum
import logging
import os
import re
import redis
import redistimeseries.client
import sys
import serial
import time

MAX_DB_SAMPLES = (60 * 60 * 24) * 366
NB_OF_TELEGRAM_LINES = 21

# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)

# create file handler and set level to error
fileHandler = logging.FileHandler('p1_error_log.txt')
fileHandler.setLevel(logging.ERROR)

# create formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

# add formatter log handlers
consoleHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

# add handlers to logger
logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)

class ObisTag(Enum):
    TIMESTAMP = 1
    SWITCH_ELECTRICITY = 2
    SWITCH_GAS = 3
    SERIAL_ELECTRICITY = 4
    SERIAL_GAS= 5
    RATE = 6
    TOTAL_CONSUMPTION_DAY = 7
    TOTAL_CONSUMPTION_NIGHT = 8
    TOTAL_PRODUCTION_DAY = 9
    TOTAL_PRODUCTION_NIGHT = 10
    L1_CONSUMPTION = 11
    L2_CONSUMPTION = 12
    L3_CONSUMPTION = 13
    ALL_PHASES_CONSUMPTION = 14
    L1_PRODUCTION = 15
    L2_PRODUCTION = 16
    L3_PRODUCTION = 17
    ALL_PHASES_PRODUCTION = 18
    L1_VOLTAGE = 19
    L2_VOLTAGE = 20
    L3_VOLTAGE = 21
    L1_CURRENT = 22
    L2_CURRENT = 23
    L3_CURRENT = 24
    GAS_CONSUMPTION = 25
    VERSION = 26
    LIMITER_THRESHOLD = 27
    FUSE_SUPERVISION_THRESHOLD = 28
#    TEXT_MESSAGE = XX

obistags = {
    "0-0:1.0.0"   : ObisTag.TIMESTAMP,             #YYMMDDhhmmssX (X = S: Summer, X = W: Winter)
    "0-0:96.3.10" : ObisTag.SWITCH_ELECTRICITY,
    "0-1:24.4.0"  : ObisTag.SWITCH_GAS,
    "0-0:96.1.1"  : ObisTag.SERIAL_ELECTRICITY,
    "0-1:96.1.1"  : ObisTag.SERIAL_GAS,
    "0-0:96.14.0" : ObisTag.RATE,
    "1-0:1.8.1"   : ObisTag.TOTAL_CONSUMPTION_DAY,
    "1-0:1.8.2"   : ObisTag.TOTAL_CONSUMPTION_NIGHT,
    "1-0:2.8.1"   : ObisTag.TOTAL_PRODUCTION_DAY,
    "1-0:2.8.2"   : ObisTag.TOTAL_PRODUCTION_NIGHT,
    "1-0:21.7.0"  : ObisTag.L1_CONSUMPTION,
    "1-0:41.7.0"  : ObisTag.L2_CONSUMPTION,
    "1-0:61.7.0"  : ObisTag.L3_CONSUMPTION,
    "1-0:1.7.0"   : ObisTag.ALL_PHASES_CONSUMPTION, 
    "1-0:22.7.0"  : ObisTag.L1_PRODUCTION,
    "1-0:42.7.0"  : ObisTag.L2_PRODUCTION,
    "1-0:62.7.0"  : ObisTag.L3_PRODUCTION,
    "1-0:2.7.0"   : ObisTag.ALL_PHASES_PRODUCTION,
    "1-0:32.7.0"  : ObisTag.L1_VOLTAGE,
    "1-0:52.7.0"  : ObisTag.L2_VOLTAGE,
    "1-0:72.7.0"  : ObisTag.L3_VOLTAGE,
    "1-0:31.7.0"  : ObisTag.L1_CURRENT,
    "1-0:51.7.0"  : ObisTag.L2_CURRENT,
    "1-0:71.7.0"  : ObisTag.L3_CURRENT,
    "0-1:24.2.3"  : ObisTag.GAS_CONSUMPTION,
    "0-0:96.1.4"  : ObisTag.VERSION,
    "0-0:17.0.0"  : ObisTag.LIMITER_THRESHOLD,
    "1-0:31.4.0"  : ObisTag.FUSE_SUPERVISION_THRESHOLD
#    "0-0:96.13.0" : ObisTag.TEXT_MESSAGE
}

obisstrings = {
    ObisTag.TIMESTAMP                   : "Timestamp",
    ObisTag.SWITCH_ELECTRICITY          : "Switch electricity",
    ObisTag.SWITCH_GAS                  : "Switch gas",
    ObisTag.SERIAL_ELECTRICITY          : "Meter serial electricity",
    ObisTag.SERIAL_GAS                  : "Meter serial gas",
    ObisTag.RATE                        : "Current rate (1=day,2=night)",
    ObisTag.TOTAL_CONSUMPTION_DAY       : "Rate 1 (day) - total consumption",
    ObisTag.TOTAL_CONSUMPTION_NIGHT     : "Rate 2 (night) - total consumption",
    ObisTag.TOTAL_PRODUCTION_DAY        : "Rate 1 (day) - total production",
    ObisTag.TOTAL_PRODUCTION_NIGHT      : "Rate 2 (night) - total production",
    ObisTag.L1_CONSUMPTION              : "L1 consumption",
    ObisTag.L2_CONSUMPTION              : "L2 consumption",
    ObisTag.L3_CONSUMPTION              : "L3 consumption",
    ObisTag.ALL_PHASES_CONSUMPTION      : "All phases consumption",
    ObisTag.L1_PRODUCTION               : "L1 production",
    ObisTag.L2_PRODUCTION               : "L2 production",
    ObisTag.L3_PRODUCTION               : "L3 production",
    ObisTag.ALL_PHASES_PRODUCTION       : "All phases production",
    ObisTag.L1_VOLTAGE                  : "L1 voltage",
    ObisTag.L2_VOLTAGE                  : "L2 voltage",
    ObisTag.L3_VOLTAGE                  : "L3 voltage",
    ObisTag.L1_CURRENT                  : "L1 current",
    ObisTag.L2_CURRENT                  : "L2 current",
    ObisTag.L3_CURRENT                  : "L3 current",
    ObisTag.GAS_CONSUMPTION             : "Gas consumption",
    ObisTag.VERSION                     : "Version",
    ObisTag.LIMITER_THRESHOLD           : "Limiter threshold",
    ObisTag.FUSE_SUPERVISION_THRESHOLD  : "Fuse supervision threshold"
#    ObisTag.TEXT_MESSAGE                : "Text message"
}

class Reader():
    pass

class SerialReader(Reader):

    def __init__(self):
        self.port = serial.Serial()
        self.port.baudrate = 115200
        self.port.bytesize = serial.EIGHTBITS
        self.port.parity = serial.PARITY_NONE
        self.port.stopbits = serial.STOPBITS_ONE
        self.port.xonxoff = 0
        self.port.rtscts = 0
        self.port.timeout = 5
        self.port.port = "/dev/ttyUSB0"

    def open(self):
        try:
            self.port.open()
        except:
            sys.exit("Error while opening serial port. port %s."  % self.port.name)

    def close(self):
        try:
            self.port.close()
        except:
            sys.exit("Error while closing serial port. port %s" % self.port.name)

    def readline(self):
        line = ""
        try:
            line = self.port.readline()
        except:
            sys.exit("Error while reading from serial port. port %s" % self.port.name)
        return line

class FileReader(Reader):

    def __init__(self, path_to_file):
        self.path_to_file = path_to_file
        self.read_count = 0

    def open(self):
        try:
             self.file = open(self.path_to_file, 'r')
        except:
            sys.exit("Error while opening file. file %s"  % self.path_to_file)

    def close(self):
        try:
            self.file.close()
        except:
            sys.exit("Error while closing file. file %s" % self.path_to_file)

    def readline(self):
        line = ""
        try:
            line = self.file.readline()
            if len(line) == 0:
                self.file.seek(0)
            self.read_count += 1
            if (self.read_count == NB_OF_TELEGRAM_LINES):
                time.sleep(1)
                self.read_count = 0
        except:
            sys.exit("Error while reading from file. file %s" % self.path_to_file)
            self.file.close()
        return line.encode()

'''
   Telegram
'''

class Telegram:

    def __init__(self):
        self.input_lines = []
        self.data = {}

    def read(self, reader):
        self.input_lines = []
        
        #search for the start of the telegram
        while(True):
            rawLine = reader.readline()
            line = rawLine.decode('ascii')
            line = str(rawLine)
            if "/" in line:
                #Found start of telegram
                self.input_lines.append(line)
                break

        i = 0
        while i < NB_OF_TELEGRAM_LINES - 1:
            rawLine = reader.readline()
            line = str(rawLine.decode('ascii')).strip()
            self.input_lines.append(line)
            #print(line)
            i += 1

    def print_input(self):
        for line in self.input_lines:
            print(line)

    def log_input(self):
        for line in self.input_lines:
            logger.error(line)

    def print_data(self):
        for key, value in self.data.items():
            print(f'{obisstrings[key]}, {value[0]}, {value[1]}')

    def log_data(self):
        for key, value in self.data.items():
            logger.error(f'{obisstrings[key]}, {value[0]}, {value[1]}')

    def get_value(self, key):
        return self.data[key]

    def parse_input(self):
        self.data.clear()
        for line in self.input_lines:
            self.parse_line(line)

    def parse_line(self, line):
        # parse a single line of the telegram and try to get relevant data from it
        unit = ""
        timestamp = ""
        # get OBIS code from line (format:OBIS(value)
        obis = line.split("(")[0]
        # check if OBIS code is something we know and parse it
        if obis in obistags:
            # get values from line.
            # format:OBIS(value), gas: OBIS(timestamp)(value)
            values = re.findall(r'\(.*?\)', line)
            value = values[0][1:-1]
            ## timestamp requires removal of last char
            #if obis == "0-0:1.0.0" or len(values) > 1:
            #    value = value[:-1]
            if obis == "0-0:1.0.0":
                ##don't parse the timestamp, take it as a string
                #pass

                #convert it to linux epoch time to avoid problems when daylight savings time ends in oktober and time goes backwards
                #os.environ['TZ'] = 'UTC'
                if value[-1] == 'S':
                    timezone = 'UTC+0200'
                elif value[-1] == 'W':
                    timezone = 'UTC+0100'
                else:
                    logger.error(f'Invalid timestamp. value: {value}')

                value = value[:-1] + timezone
                value = int(time.mktime(time.strptime(value, '%y%m%d%H%M%S%Z%z')))
            elif "96.1.1" in obis:
                # serial numbers need different parsing: (hex to ascii)
                value = bytearray.fromhex(value).decode()
            else:
                # separate value and unit (format:value*unit)
                lvalue = value.split("*")
                value = float(lvalue[0])
                if len(lvalue) > 1:
                    unit = lvalue[1]
            self.data[obistags[obis]] = ((value, unit))

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

    def save_telegram(self, telegram):
        fields = { }

        try:
            fields[ObisTag.ALL_PHASES_PRODUCTION.name] = str(telegram.get_value(ObisTag.ALL_PHASES_PRODUCTION)[0])
            fields[ObisTag.ALL_PHASES_CONSUMPTION.name] = str(telegram.get_value(ObisTag.ALL_PHASES_CONSUMPTION)[0])
        except KeyError as e:
            logger.error(f'Not all parsed values present. KeyError \'{e}\'')
            logger.error(f'Input')
            telegram.log_input()
            logger.error(f'Parsed Data')
            telegram.log_data()
            return

        #use the auto generated redis id (linux epoch in ms)
        #timeKey=u'*' 

        #use out own key, linux epoch in ms derived from the time of the measurement
        timeKey = str(telegram.get_value(ObisTag.TIMESTAMP)[0] * 1000)

        logger.info(f'Saving time:{timeKey} up:{fields[ObisTag.ALL_PHASES_PRODUCTION.name]} down:{fields[ObisTag.ALL_PHASES_CONSUMPTION.name]}')
        
        #redis time series
        #self.rts.add("electricity_up_sec", timeKey, fields[ObisTag.ALL_PHASES_PRODUCTION.name])
        #self.rts.add("electricity_down_sec", timeKey, fields[ObisTag.ALL_PHASES_CONSUMPTION.name])

        self.rts.madd([
                       ("electricity_up_sec", timeKey, fields[ObisTag.ALL_PHASES_PRODUCTION.name]), 
                       ("electricity_down_sec", timeKey, fields[ObisTag.ALL_PHASES_CONSUMPTION.name]) 
                      ])

        self.prev_telegram_key = timeKey

'''
   Terminal
'''

def clear_terminal():
    print(chr(27) + "[2J")

##############################################################################
#Main program
##############################################################################

reader = SerialReader()
#reader = FileReader('test/telegram.txt')
reader.open()

db = Database()
db.connect()

'''
Loop for terminal
'''

while True:
    telegram = Telegram()
    telegram.read(reader)
    #clear_terminal()
    print('\nInput:')
    telegram.print_input()
    telegram.parse_input()
    print('\nParsed Data:')
    telegram.print_data()
    db.save_telegram(telegram)

db.disconnect()
reader.close()

