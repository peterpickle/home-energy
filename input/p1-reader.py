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

FEATURE_GAS = 1

MAX_DB_DEBUG_SAMPLES = 200
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
    INTERNAL_GAS_TIMESTAMP = 29
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
    "1-0:31.4.0"  : ObisTag.FUSE_SUPERVISION_THRESHOLD,
    "INT_GAS_TIME": ObisTag.INTERNAL_GAS_TIMESTAMP
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
    ObisTag.FUSE_SUPERVISION_THRESHOLD  : "Fuse supervision threshold",
    ObisTag.INTERNAL_GAS_TIMESTAMP      : "Gas timestamp"
#    ObisTag.TEXT_MESSAGE                : "Text message"
}

def p1_reader_debug(name, value):
    db.debug(name, value)

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
        except Exception as e:
            sys.exit(f'Error while opening serial port. port:"{self.port.name}" error:"{e}"')

    def close(self):
        try:
            self.port.close()
        except Exception as e:
            sys.exit(f'Error while closing serial port. port:"{self.port.name}" error:"{e}"')

    def readline(self):
        line = ""
        try:
            line = self.port.readline()
            p1_reader_debug('serial_input', line)
        except Exception as e:
            logger.error(f'Error while reading from serial port. port:"{self.port.name}" error:"{e}"')
            raise RuntimeError(f'Error while reading from serial port. port:"{self.port.name}" error:"{e}"') from e
        return line

class FileReader(Reader):

    def __init__(self, path_to_file):
        self.path_to_file = path_to_file
        self.read_count = 0

    def open(self):
        try:
             self.file = open(self.path_to_file, 'r')
        except Exception as e:
            sys.exit(f'Error while opening file. file:"{self.path_to_file}" error:"{e}"')

    def close(self):
        try:
            self.file.close()
        except Exception as e:
            sys.exit(f'Error while closing file. file:"{self.path_to_file}" error:"{e}"')

    def readline(self):
        line = ""
        try:
            line = self.file.readline()
            if len(line) == 0:
                self.file.seek(0)
            else:
                p1_reader_debug('file_input', line)
            self.read_count += 1
            if (self.read_count == NB_OF_TELEGRAM_LINES):
                time.sleep(1)
                self.read_count = 0
        except Exception as e:
            logger.error(f'Error while reading from file. file:"{self.path_to_file}" error:"{e}"')
            raise RuntimeError(f'Error while reading from file. file:"{self.path_to_file}" error:"{e}"') from e
        return line.encode()

'''
   Telegram
'''

class Telegram:
    end_regex = re.compile('^![0-9A-Fa-f]{4}')

    def __init__(self):
        self.input_lines = []
        self.data = {}
        self.parsed = False

    def is_parsed(self):
        return self.parsed

    def read(self, reader):
        self.input_lines = []
        self.parsed = False
        
        #search for the start of the telegram
        while(True):
            rawLine = reader.readline()
            line = str(rawLine.decode('utf-8'))
            if line.startswith('/'):
                #Found start of telegram
                self.input_lines.append(line)
                break

        while(True):
            rawLine = reader.readline()
            line = str(rawLine.decode('utf-8'))
            self.input_lines.append(line)
            #print(line)
            if Telegram.end_regex.match(line) != None:
                #Found end of telegram
                break

    def print_input(self):
        for line in self.input_lines:
            print(line.strip())

    def log_input(self):
        logger.error(f'Input')
        for line in self.input_lines:
            logger.error(line.strip())

    def print_data(self):
        for key, value in self.data.items():
            print(f'{obisstrings[key]}, {value[0]}, {value[1]}')

    def log_data(self):
        logger.error(f'Parsed Data')
        for key, value in self.data.items():
            logger.error(f'{obisstrings[key]}, {value[0]}, {value[1]}')

    def get_value(self, key):
        return self.data[key]

    def parse_input(self):
        self.data.clear()
        self.parsed = False
        try:
            for line in self.input_lines:
                self.parse_line(line)
            self.parsed = True
        except Exception as e:
            logger.error(f'Parsing error. exception:"{e}"')
            telegram.log_input()
            telegram.log_data()

    def parse_line(self, line):
        # parse a single line of the telegram
        unit = ""
        # get OBIS code from line (format:OBIS(value)
        obis = line.split("(")[0]
        # check if OBIS code is something we know and parse it
        if obis in obistags:
            # get values from line.
            # format:OBIS(value), gas: OBIS(timestamp)(value)
            values = re.findall(r'\(.*?\)', line)

            #remove parentheses
            for i in range(len(values)):
                values[i] = values[i][1:-1]

            value = values[0]
            if '24.2.3' in obis:
                # gas consumption needs different parsing.
                # It contains 2 values, a timestamp and the gas counter.
                if len(values) != 2:
                    logger.error(f'Gas consumtion only contains 1 value. line:"{line}"')
                    telegram.log_input()
                    return
                # We parse and store the timestamp here
                value = self.parse_timestamp(value)
                self.data[ObisTag.INTERNAL_GAS_TIMESTAMP] = (value, unit)
                #Set the gas counter as value and handle it normally
                value = values[1]

            if obis == '0-0:1.0.0':
                value = self.parse_timestamp(value)
            elif '96.1.1' in obis:
                # serial numbers need different parsing: (hex to ascii)
                value = bytearray.fromhex(value).decode()
            else:
                # separate value and unit (format:value*unit)
                lvalue = value.split('*')
                value = float(lvalue[0])
                if len(lvalue) > 1:
                    unit = lvalue[1]

            self.data[obistags[obis]] = (value, unit)

    @staticmethod
    def parse_timestamp(timestamp_string):
        #convert it to linux epoch time to avoid problems when daylight savings time ends in oktober and time goes backwards
        #os.environ['TZ'] = 'UTC'
        if timestamp_string[-1] == 'S':
            timezone = 'UTC+0200'
        elif timestamp_string[-1] == 'W':
            timezone = 'UTC+0100'
        else:
            logger.error(f'Invalid timestamp. timestamp_string:"{timestamp_string}"')

        timezone = 'UTC+0000'

        timestamp_string = timestamp_string[:-1]
        epoch_time = int(time.mktime(time.strptime(timestamp_string, '%y%m%d%H%M%S')))
        return epoch_time


class Database:

    def __init__(self):
        self.prev_gas_key = None
        self.prev_gas_value = None

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
            logger.error(f'Not all parsed values present. KeyError:"{e}"')
            telegram.log_input()
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

        if FEATURE_GAS:
            try:
                gasTimeKey = telegram.get_value(ObisTag.INTERNAL_GAS_TIMESTAMP)[0] * 1000
                gasValue = telegram.get_value(ObisTag.GAS_CONSUMPTION)[0]
            except KeyError as e:
                logger.error(f'Not all parsed gas values present. KeyError:"{e}"')
                telegram.log_input()
                telegram.log_data()
                return

            if self.prev_gas_key == None:
                logger.debug(f'Storing first gas values gasTimeKey:{gasTimeKey} gasValue:{gasValue}')
                self.prev_gas_key = gasTimeKey
                self.prev_gas_value = gasValue
                return

            if gasValue < self.prev_gas_value:
                logger.error('Received gas value was smaller than old value. '
                             f'gasTimeKey:{gasTimeKey} gasValue:{gasValue} '
                             f'prev_gas_key:{self.prev_gas_key} prev_gas_value:{self.prev_gas_value}')
                self.prev_gas_key = gasTimeKey
                self.prev_gas_value = gasValue
                return

            gasDiff = gasValue - self.prev_gas_value

            if gasTimeKey != self.prev_gas_key or gasDiff != 0:
                logger.info(f'Saving gasTimeKey:{gasTimeKey} gasDiff:{gasDiff}')
                self.rts.add("gas_5min", gasTimeKey, gasDiff)

            self.prev_gas_key = gasTimeKey
            self.prev_gas_value = gasValue

    def debug(self, name, value):
        fields = { }
        fields[name] = str(value)
        self.r.xadd("p1_reader_debug", fields, id='*', maxlen=MAX_DB_DEBUG_SAMPLES, approximate=True)

'''
   Terminal
'''

def clear_terminal():
    print(chr(27) + "[2J")

##############################################################################
#Main program
##############################################################################

reader = SerialReader()
#reader = FileReader('test/telegram_elec.txt')
#reader = FileReader('test/telegram_elec_and_gas.txt')
reader.open()

db = Database()
db.connect()

'''
Loop for terminal
'''

while True:
    try:
        telegram = Telegram()
        telegram.read(reader)
        print('\nInput:')
        telegram.print_input()
        telegram.parse_input()
        print('\nParsed Data:')
        telegram.print_data()
        db.save_telegram(telegram)
    except Exception as e:
        logger.error(f'Unknown error. exception:"{e}"')
        telegram.log_input()
        telegram.log_data()

db.disconnect()
reader.close()

