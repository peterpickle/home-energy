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

    def printData(self):
        print('')
        print('time: ', self.getTime())
        print('length: ', self.getLength())
        print('logger SN: ', self.getLoggerSerialNumber())
        print('up time: ', self.getUptime())
        print('inverter SN: ', self.getInverterSerialNumber())
        print('temperature: ', self.getTemperature())
        print('vDC1: ', self.getVoltageDC(1))
        print('vDC2: ', self.getVoltageDC(2))
        print('iDC1: ', self.getCurrentDC(1))
        print('iDC2: ', self.getCurrentDC(2))
        print('iAC1: ', self.getCurrentAC(1))
        print('iAC2: ', self.getCurrentAC(2))
        print('iAC3: ', self.getCurrentAC(3))
        print('vAC1: ', self.getVoltageAC(1))
        print('vAC2: ', self.getVoltageAC(2))
        print('vAC3: ', self.getVoltageAC(3))
        print('freq: ', self.getFrequencyAC())
        print('power AC: ', self.getTotalActivePowerAC())
        print('gen today: ', self.getGenerationToday())
        print('gen month: ', self.getGenerationMonth())
        print('gen prev month: ', self.getGenerationPrevMonth())
        print('gen total: ', self.getGenerationTotal())
        print('total vDC: ', self.getVoltageDCTotal())
        print('total power DC: ', self.getPowerDCTotal())
        print('power grid: ', self.getPowerGridTotalApparentPower())
        print('')

