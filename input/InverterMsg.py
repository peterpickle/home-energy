import struct
import time

class InverterMsg:

    rawmsg = ""

    def __init__(self, msg):
        self.rawmsg = msg
        self.last_update = time.time()

    def __getString(self, begin, end):
        return str(self.rawmsg[begin:end], encoding="UTF-8")

    def __getShort(self, offset, divider=1):
        num = struct.unpack("<H", self.rawmsg[offset : offset + 2])[0]
        if num == 65535:
            return float(-1)
        else:
            return float(num) / divider

    def __getLong(self, offset, divider=1):
        return float(struct.unpack("<I", self.rawmsg[offset : offset + 4])[0]) / divider

    def getLength(self):
        return len(self.rawmsg)

    def getLoggerSerialNumber(self):
        return self.__getLong(7)

    '''
    Not sure relative to what this is.
    def getTimestamp(self):
        return self.__getLong(14)
    '''

    def getUptime(self):
        return self.__getLong(18)

    def getInverterSerialNumber(self):
        return self.__getString(32, 47)

    def getTemperature(self):
        return self.__getShort(48, 10)

    def getVoltageDC(self, i=1):
        if i not in range(1, 3):
            i = 1
        offset = 50 + (i - 1) * 2
        return self.__getShort(offset, 10)

    def getCurrentDC(self, i=1):
        if i not in range(1, 3):
            i = 1
        offset = 54 + (i - 1) * 2
        return self.__getShort(offset, 10)

    def getCurrentAC(self, i=1):
        if i not in range(1, 4):
            i = 1
        offset = 58 + (i - 1) * 2
        return self.__getShort(offset, 10)

    def getVoltageAC(self, i=1):
        if i not in range(1, 4):
            i = 1
        offset = 64 + (i - 1) * 2
        return self.__getShort(offset, 10)

    def getFrequencyAC(self):
        return self.__getShort(70, 100)

    def getTotalActivePowerAC(self):
        return int(self.__getShort(72))

    def getGenerationToday(self):
        return self.__getShort(76, 100)

    def getGenerationTotal(self):
        return self.__getLong(80, 10)

    def getVoltageDCTotal(self):
        return self.__getShort(108, 10)

    def getPowerDCTotal(self):
        return self.__getShort(116)

    def getGenerationMonth(self):
        return int(self.__getLong(120))

    def getGenerationPrevMonth(self):
        return int(self.__getLong(124))

    def getPowerGridTotalApparentPower(self):
        return int(self.__getShort(142))

    def getTime(self):
        return int(self.last_update) * 1000

    def printData(self, logger):
        logger.debug(f'time: {self.getTime()}')
        logger.debug(f'length: {self.getLength()}')
        logger.debug(f'logger SN: {self.getLoggerSerialNumber()}')
        logger.debug(f'up time: {self.getUptime()}')
        logger.debug(f'inverter SN: {self.getInverterSerialNumber()}')
        logger.debug(f'temperature: {self.getTemperature()}')
        logger.debug(f'vDC1: {self.getVoltageDC(1)}')
        logger.debug(f'vDC2: {self.getVoltageDC(2)}')
        logger.debug(f'iDC1: {self.getCurrentDC(1)}')
        logger.debug(f'iDC2: {self.getCurrentDC(2)}')
        logger.debug(f'iAC1: {self.getCurrentAC(1)}')
        logger.debug(f'iAC2: {self.getCurrentAC(2)}')
        logger.debug(f'iAC3: {self.getCurrentAC(3)}')
        logger.debug(f'vAC1: {self.getVoltageAC(1)}')
        logger.debug(f'vAC2: {self.getVoltageAC(2)}')
        logger.debug(f'vAC3: {self.getVoltageAC(3)}')
        logger.debug(f'freq: {self.getFrequencyAC()}')
        logger.debug(f'power AC: {self.getTotalActivePowerAC()}')
        logger.debug(f'gen today: {self.getGenerationToday()}')
        logger.debug(f'gen month: {self.getGenerationMonth()}')
        logger.debug(f'gen prev month: {self.getGenerationPrevMonth()}')
        logger.debug(f'gen total: {self.getGenerationTotal()}')
        logger.debug(f'total vDC: {self.getVoltageDCTotal()}')
        logger.debug(f'total power DC: {self.getPowerDCTotal()}')
        logger.debug(f'power grid: {self.getPowerGridTotalApparentPower()}')

