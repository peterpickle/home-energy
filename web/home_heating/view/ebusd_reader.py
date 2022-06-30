#!/usr/bin/python3

# ebusd reader

from enum import Enum
import json
import logging
import socket

'''
# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)

# create file handler and set level to error
fileHandler = logging.FileHandler('ebus_error_log.txt')
fileHandler.setLevel(logging.ERROR)

# create formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

# add formatter to log handlers
consoleHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

# add handlers to logger
logger.addHandler(consoleHandler)
logger.addHandler(fileHandler)
'''

EBUSD_HOST = '127.0.0.1'
EBUSD_PORT = 8888

VRC700_CIRCUIT_NAME = '700'
HEATPUMP_CIRCUIT_NAME = 'hmu' #Heating Mixing unit?
BROADCAST_CIRCUIT_NAME = 'broadcast'

class RETURN_TYPE(Enum):
    FLOAT = 1
    RANGE = 2
    BOOL = 3
    ANY = 4
    FIVE = 5

class Ebus():

	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.socket = None

	def open(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.settimeout(5)
		self.socket.connect((self.host, self.port))

	def close(self):
		self.socket.close()

	def read(self, circuit, name, type=RETURN_TYPE.ANY, ttl=300):
		if self.socket is None:
			return None

		result = None
		""" Send the command """
		READ_COMMAND = 'read -m {2} -c {0} {1}\n'
		command = READ_COMMAND.format(circuit, name, ttl)
		self.socket.sendall(command.encode())

		""" Get the result decoded UTF-8 """
		result = self.socket.recv(256).decode('utf-8').rstrip()
		if 'ERR:' not in result and type != RETURN_TYPE.ANY:
			result = self.humanize(type, result)

		return result

	def write(self, circuit, name, value):
		if self.socket is None:
			return None

		result = None
		""" Send the command """
		WRITE_COMMAND = 'write -c {0} {1} {2}\n'
		command = WRITE_COMMAND.format(circuit, name, value)
		self.socket.sendall(command.encode())
		""" Get the result decoded UTF-8 """
		result = self.socket.recv(256).decode('utf-8').rstrip()

		return result

	def humanize(self, type, value):
		_state = None
		if type == RETURN_TYPE.FLOAT:
			_state = format(
				float(value), '.3f')
		elif type == RETURN_TYPE.RANGE:
			_state = value.replace(';-:-', '')
		elif type == RETURN_TYPE.BOOL:
			if value == 1 or value == 'on':
				_state = 'on'
			else:
				_state = 'off'
		elif type == RETURN_TYPE.ANY:
			return value
		elif type == RETURN_TYPE.FIVE:
			if 'ok' not in value.split(';'):
				return
			_state = value.partition(';')[0]
		return _state

read_fields = [
    # circuit, fieldname, return type, max cache age

    # Heatpump
    [HEATPUMP_CIRCUIT_NAME, 'State', RETURN_TYPE.ANY, 0],
    [HEATPUMP_CIRCUIT_NAME, 'CurrentConsumedPower', RETURN_TYPE.ANY, 0],
    [HEATPUMP_CIRCUIT_NAME, 'WaterThroughput', RETURN_TYPE.ANY, 0],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear1', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear2', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear3', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear4', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear5', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear6', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear7', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear8', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear9', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear10', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear11', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'ConsumptionThisYear12', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear1', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear2', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear3', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear4', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear5', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear6', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear7', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear8', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear9', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear10', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear11', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'YieldThisYear12', RETURN_TYPE.ANY, 3600 * 24],
    [HEATPUMP_CIRCUIT_NAME, 'currenterror', RETURN_TYPE.ANY, 0],
    [HEATPUMP_CIRCUIT_NAME, 'WaterThroughput', RETURN_TYPE.ANY, 0],

    # generic
    [VRC700_CIRCUIT_NAME, 'Time', RETURN_TYPE.ANY, 0],
    #[BROADCAST_CIRCUIT_NAME, 'vdatetime', RETURN_TYPE.ANY, 0],

    # Heating Circuit
    [VRC700_CIRCUIT_NAME, 'z1RoomTemp', RETURN_TYPE.ANY, 300],
    [VRC700_CIRCUIT_NAME, 'z1DayTemp', RETURN_TYPE.ANY, 0],
    [VRC700_CIRCUIT_NAME, 'z1NightTemp', RETURN_TYPE.ANY, 0],
    [VRC700_CIRCUIT_NAME, 'z1ActualRoomTempDesired', RETURN_TYPE.ANY, 0],
    [VRC700_CIRCUIT_NAME, 'DisplayedOutsideTemp', RETURN_TYPE.ANY, 300],
    [VRC700_CIRCUIT_NAME, 'OutsideTempAvg', RETURN_TYPE.ANY, 3600],
    [VRC700_CIRCUIT_NAME, 'z1Timer.Monday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'z1Timer.Tuesday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'z1Timer.Wednesday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'z1Timer.Thursday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'z1Timer.Friday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'z1Timer.Saturday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'z1Timer.Sunday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'Hc1Status', RETURN_TYPE.BOOL, 0],
    [VRC700_CIRCUIT_NAME, 'Hc1CircuitType', RETURN_TYPE.ANY, 3600],
    [VRC700_CIRCUIT_NAME, 'Hc1FlowTemp', RETURN_TYPE.ANY, 30],
    [VRC700_CIRCUIT_NAME, 'Hc1HeatCurve', RETURN_TYPE.ANY, 300],
    [VRC700_CIRCUIT_NAME, 'PrEnergySumHcThisMonth', RETURN_TYPE.ANY, 3600],
    [VRC700_CIRCUIT_NAME, 'PrEnergySumHcLastMonth', RETURN_TYPE.ANY, 3600],

    # Hot Water Circuit
    [VRC700_CIRCUIT_NAME, 'HwcTempDesired', RETURN_TYPE.ANY, 0],
    [VRC700_CIRCUIT_NAME, 'HwcOpMode', RETURN_TYPE.ANY, 0],
    [VRC700_CIRCUIT_NAME, 'HwcStorageTemp', RETURN_TYPE.ANY, 0],
    [VRC700_CIRCUIT_NAME, 'PrEnergySumHwcThisMonth', RETURN_TYPE.ANY, 3600],
    [VRC700_CIRCUIT_NAME, 'PrEnergySumHwcLastMonth', RETURN_TYPE.ANY, 3600],
    [VRC700_CIRCUIT_NAME, 'hwcTimer.Monday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'hwcTimer.Tuesday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'hwcTimer.Wednesday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'hwcTimer.Thursday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'hwcTimer.Friday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'hwcTimer.Saturday', RETURN_TYPE.RANGE, 0],
    [VRC700_CIRCUIT_NAME, 'hwcTimer.Sunday', RETURN_TYPE.RANGE, 0],
]

def read_all_ebus_values():
	ebus = Ebus(EBUSD_HOST, EBUSD_PORT)
	ebus.open()

	result_dict = { }

	for field in read_fields:
		value = ebus.read(field[0], field[1], field[2], field[3]);
		#print(f'{field[1]}: {value}')
		result_dict[field[1]] = value

	ebus.close()

	return json.dumps(result_dict, separators=(',\n', ': '))

if __name__ == '__main__':
    # file executed as script
    result = read_all_ebus_values()
    print(result)
