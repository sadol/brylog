#!/usr/bin/env python
# encoding: utf-8
import libs.serialDevice as sd  # virtual class for serial devices
import time
import sys


class PeriodError(Exception):
    """
    error class for Brymen257.period function
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def binBit(hexByte):
    '''converts bytes to binary string with leading zeros
       not very efficent because of str convertion'''
    return "{0:0>8}".format(bin(hexByte)[2:])


multiplier = {' ': 1,
              'n': 0.000000001,
              'u': 0.000001,
              'm': 0.001,
              'k': 1000,
              'M': 1000000}


#-------------------- brymen 257 class-----------------------------------------
class Brymen257(sd.SerialDevice):
    """
    Brymen 257 multimeter class
    """

    def __init__(self, port):
        """
        serial.Serial.__init__()
        value : (float) -> value read from mulimeter
        unit : string
        seconds : float -> base time
        """
        sd.serial.Serial.__init__(self, port=port, baudrate=9600,
                                  bytesize=sd.serial.EIGHTBITS,
                                  parity=sd.serial.PARITY_NONE,
                                  stopbits=sd.serial.STOPBITS_ONE,
                                  timeout=1)
        self.value = 0.00
        self.unit = ' '
        self.seconds = 0.0

    def _setFrame(self, dataFrame):
        '''populates internal output buffer --> for immediate use in program
         - minus   + plus   0[.]0[.]0[.]0 number format
        u mikro   n nano   m mili   k kilo   M mega   [=|~]V Volt   A Amper
        O Ohm   F Farad   H Hertz   C Celcius'''
        self.seconds = time.time()
        characters = ""  # characters intermediate bufor
        self.unit = self._currentType(dataFrame)
        characters += self._signType(dataFrame)
        characters += self._firstDigit(dataFrame)
        characters += self._secondDigit(dataFrame)
        characters += self._thirdDigit(dataFrame)
        characters += self._fourthDigit(dataFrame)
        if(characters[-1] == ' '):  # temperature
            self.unit = 'C'
            self.value = float(characters)
        else:
            characters = self._period(dataFrame, characters)
            try:  # multimeter lcd error values handling
                self.value = float(characters[1:7])
            except ValueError:
                self.value = (-1000)  # error code for further handling!!!!
            if(self.value != (-1000)):
                self.value *= multiplier[self._prefix(dataFrame)]
            self.unit += self._names(dataFrame)

    def getFrame(self):
        """
        returns raw data frame and triggers its processing
        """
        rawData = self.read(15)  # magic number of read bytes for brymen257
        if(self._isOK(rawData)):
            self._setFrame(rawData)
            return rawData  # for further checks in higher classes
        else:
            return None

    def getData(self):
        '''returns output buffer values
        output: (timebase, value, unit) tuple'''
        self.getFrame()
        return (self.seconds, self.value, self.unit)

    def _currentType(self, dataFrame):
        '''returns current type indicators'''
        byte1 = binBit(dataFrame[1])
        if(byte1[5] == '1'):  # DC
            return "="
        if(byte1[6] == '1'):  # AC
            return "~"
        if(byte1[5:7] == '00'):
            return " "  # for Ohms etc.

    def _signType(self, dataFrame):
        '''returns sign of the number'''
        byte1 = binBit(dataFrame[3])
        if(byte1[7] == '1'):
            return "-"
        else:
            return "+"

    def _giveDigit(self, dataFrame, firstByte, secondByte):
        '''decodes digit bits from two bytes'''
        byte1 = binBit(dataFrame[firstByte])[4:7]
        byte2 = binBit(dataFrame[secondByte])[4:]
        if((byte1 == '111' and byte2 == '1011') or
                (byte1 == '000' and byte2 == '0000')):
            return '0'
        if(byte1 == '000' and byte2 == '1010'):
            return '1'
        if(byte1 == '101' and byte2 == '1101'):
            return '2'
        if(byte1 == '100' and byte2 == '1111'):
            return '3'
        if(byte1 == '010' and byte2 == '1110'):
            return '4'
        if(byte1 == '110' and byte2 == '0111'):
            return '5'
        if(byte1 == '111' and byte2 == '0111'):
            return '6'
        if(byte1 == '100' and byte2 == '1010'):
            return '7'
        if(byte1 == '111' and byte2 == '1111'):
            return '8'
        if(byte1 == '110' and byte2 == '1111'):
            return '9'
        if(byte1 == '111' and byte2 == '0001'):
            return ' '  # it is for temperature measuring
        return 'R'  # for various lcd error codes

    def _firstDigit(self, dataFrame):
        return self._giveDigit(dataFrame, 3, 4)

    def _secondDigit(self, dataFrame):
        return self._giveDigit(dataFrame, 5, 6)

    def _thirdDigit(self, dataFrame):
        return self._giveDigit(dataFrame, 7, 8)

    def _fourthDigit(self, dataFrame):
        return self._giveDigit(dataFrame, 9, 10)

    def _period(self, dataFrame, characters):
        '''returns string with period at correct position'''
        if(len(characters) != 5):
            raise PeriodError('period error : characters <> 5')
            sys.exit(1)

        bit1 = binBit(dataFrame[5])[7]
        bit2 = binBit(dataFrame[7])[7]
        bit3 = binBit(dataFrame[9])[7]
        if(bit1 == '1'):
            return characters[:2] + '.' + characters[2:]
        if(bit2 == '1'):
            return characters[:3] + '.' + characters[3:]
        if(bit3 == '1'):
            return characters[:4] + '.' + characters[4:]

    def _prefix(self, dataFrame):
        '''returns sci prefix'''
        byte1 = binBit(dataFrame[11])
        byte2 = binBit(dataFrame[12])
        byte3 = binBit(dataFrame[13])
        if(byte1[6] == '1'):
            return 'M'
        if(byte1[7] == '1'):
            return 'k'
        if(byte2[7] == '1'):
            return 'n'
        if(byte3[6] == '1'):
            return 'u'
        if(byte3[7] == '1'):
            return 'm'
        return " "  # else -> no prefix

    def _names(self, dataFrame):
        '''returns V ,O, A , H'''
        byte1 = binBit(dataFrame[12])
        byte2 = binBit(dataFrame[13])
        byte3 = binBit(dataFrame[14])
        if(byte1[5] == '1'):
            return 'O'
        if(byte1[6] == '1'):
            return 'H'
        if(byte2[5] == '1'):
            return 'F'
        if(byte3[5] == '1'):
            return 'V'
        if(byte3[6] == '1'):
            return 'A'
        return ' '  # else

    def restartSerialDevice(self):
        '''restarts connection with brymen'''
        sd.serial.Serial.close(self)
        sd.serial.Serial.open(self)
        time.sleep(0.2)

    def _isOK(self, dataFrame):
        """
        simple format check for brymen257
        """
        if(len(dataFrame) != 15):
            self.restartSerialDevice()
            return False
        first = binBit(dataFrame[0])[:4]
        last = binBit(dataFrame[14])[:4]
        if(first == '0000' and last == '1110'):
            return True
        else:
            self.restartSerialDevice()
            return False

if __name__ == "__main__":
    device = '/dev/ttyUSB0'
    multimeter = Brymen257(device)
    time.sleep(.5)
    with open('test.txt', 'a') as f:
        while True:
            buf = multimeter.getData()  # decodes this frame
            #print(str(buf[0]) + '\t' + str(buf[1]) + '\t' + str(buf[2]))
            f.write('\t'.join((str(buf[0]),  str(buf[1]),  str(buf[2]), '\n')))
            f.flush()
            multimeter.flushOutput()
    f.close()
    multimeter.close()
