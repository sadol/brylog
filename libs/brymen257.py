#!/usr/bin/env python
# encoding: utf-8
import time
import sys
import serial
import re

# Protocol description:
# http://www.brymen.com/images/DownloadList/ProtocolList/BM250-BM250s_List/BM250-BM250s-6000-count-digital-multimeters-r1.pdf

class PeriodError(Exception):
    """error class for Brymen257.period function"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def binBit(hexByte):
    '''converts bytes to binary string with leading zeros
       not very efficent because of str convertion'''
    return "{0:0>8}".format(bin(hexByte)[2:])


multiplier = {'n': 0.000000001,
              'u': 0.000001,
              'm': 0.001,
              'k': 1000,
              'M': 1000000}

# digits decoder dictionary : key->(first Bit, second Bit), value->output digit
digits = {('111', '1011'): '0',
          ('000', '1010'): '1',
          ('101', '1101'): '2',
          ('100', '1111'): '3',
          ('010', '1110'): '4',
          ('110', '0111'): '5',
          ('111', '0111'): '6',
          ('100', '1010'): '7',
          ('111', '1111'): '8',
          ('110', '1111'): '9',
          ('111', '1110'): 'A',     # Auto
          ('001', '0011'): 'u',     # Auto
          ('011', '0101'): 't',     # Auto
          ('001', '0111'): 'o',     # Auto
          ('111', '0101'): 'E',     # E.F.
          ('111', '0001'): 'C',     # Celsius Temperature
          ('111', '0100'): 'F',     # Fahrenheit Temperature, E.F.
          ('011', '0001'): 'L',
          ('000', '0000'): ' ',
          ('000', '0100'): '-'}


class Brymen257(serial.Serial):
    """Brymen 257 multimeter class"""
    def __init__(self, port):
        """Arguments:
            port ->(string) linux port id"""
        serial.Serial.__init__(self, port=port, baudrate=9600,
                               bytesize=serial.EIGHTBITS,
                               parity=serial.PARITY_NONE,
                               stopbits=serial.STOPBITS_ONE, timeout=1)
        self.value = 0.00
        self.states = ""
        self.unit = ' '
        self.display = ''
        self.seconds = 0.00
        self.port = port

    def _setFrame(self, dataFrame):
        """populates internal data buffers"""
        self.seconds = time.time()
        characters = ""                  # temporary buffer
        self.unit = self._currentType(dataFrame)
        for i in range(1, 5):            # extract 7-segment
            prefixCharacter = '-' if i == 1  else '.'
            characters += self._give7Segment(dataFrame, 2 * i + 1, 2 * i + 2, prefixCharacter)
        self.value = self._getFloat(characters)
        prefix = self._prefix(dataFrame)
        if(self.value is not None and prefix != ''):
            self.value *= multiplier[prefix]
        self.unit += self._names(dataFrame, characters)
        self.display = characters + re.sub('u', 'µ', prefix) + re.sub('O', 'Ω', self._names(dataFrame, None))
        self.states = self._states(dataFrame)

    def getFrame(self):
        """returns raw data frame and triggers its processing

        Arguments:

        Returns:
            raw data frame from multimeter"""
        rawData = self.read(15)      # magic number of read bytes for brymen257
        if(self._isOK(rawData)):
            self._setFrame(rawData)
            return rawData           # for further checks in higher classes
        else:
            return None

    def getData(self):
        """returns output buffer values

        Argumentrs:

        Returns:
            tuple: (timebase, value, unit)"""
        self.getFrame()
        return (self.seconds, self.value, self.unit, self.display, self.states)

    def _currentType(self, dataFrame):
        """returns current type indicators

        Arguments:
            dataFrame -> raw frame of data from multimeter

        Returns:
            string -> ~(AC), =(DC), ' '(other)"""
        byte1 = binBit(dataFrame[1])
        if(byte1[5] == '1'):     # DC
            return "="
        if(byte1[6] == '1'):     # AC
            return "~"
        if(byte1[5:7] == '00'):
            return " "           # for Ohms etc.

    def _give7Segment(self, dataFrame, firstByte, secondByte, prefixCharacters):
        """decodes 7 segment bits from two bytes

        Arguments:
            dataFrame  -> raw data object
            firstByte  -> first bite of the data
            secondByte -> second bite of the data

        Returns:
            one digit or error code"""
        byte1 = binBit(dataFrame[firstByte])[4:8]
        byte2 = binBit(dataFrame[secondByte])[4:8]
        try:
            return (prefixCharacters if byte1[3] == '1' else '') + digits[(byte1[:3], byte2)]
        except KeyError:
            print('Unknown 7-segment bits, bytes1: ' + byte1 + ', bytes2: ' + byte2)
            print(' ' * len(prefixCharacters) + ' ' + ('_' if byte1[0] == '1' else ' '))
            print(' ' * len(prefixCharacters) + ('|' if byte1[1] == '1' else ' ') + ' ' + ('|' if byte2[0] == '1' else ''))
            print((prefixCharacters if byte1[3] == '1' else ' ' * len(prefixCharacters)) + ' ' + ('-' if byte2[1] == '1' else ' '))
            print(' ' * len(prefixCharacters) + ('|' if byte1[2] == '1' else ' ') + ' ' + ('|' if byte2[2] == '1' else ''))
            print(' ' * len(prefixCharacters) + ' ' + ('^' if byte2[3] == '1' else ' '))
            return ''

    def _prefix(self, dataFrame):
        """returns sci prefix

        Arguments:
            dataFrame -> raw data frame from multimeter

        Returns:
            prefix"""
        byte11 = binBit(dataFrame[11])
        byte12 = binBit(dataFrame[12])
        byte13 = binBit(dataFrame[13])
        if(byte11[6] == '1'):
            return 'M'
        if(byte11[7] == '1'):
            return 'k'
        if(byte12[7] == '1'):
            return 'n'
        if(byte13[6] == '1'):
            return 'u'
        if(byte13[7] == '1'):
            return 'm'
        return ''

    def _getFloat(self, characters):
        try:
            if(characters[-1] == 'C'):              # Celsius
                return float(characters[:-1])
            elif(characters[-1] == 'F'):            # Fahrenheit
                return float(characters[:-1])
            elif(characters == ' E.F. '):           # Electric Field Detection
                return 0
            elif(re.match(r'^--* *$', characters)): # Electric Field Detection
                return characters.count('-')
            else:
                return float(characters)
        except ValueError:
            return None     # Cannot convert to float

    def _names(self, dataFrame, characters):
        """returns physical quantity

        Arguments:
            dataFrame -> raw data frame from multimeter

        Return:
            quantity"""
        byte12 = binBit(dataFrame[12])
        byte13 = binBit(dataFrame[13])
        byte14 = binBit(dataFrame[14])
        if(byte14[5] == '1'):
            return 'V' # Priority over 'O', which will otherwise fail at startup
        if(byte12[5] == '1'):
            return 'O'
        if(byte12[6] == '1'):
            return 'H'
        if(byte13[5] == '1'):
            return 'F'
        if(byte14[6] == '1'):
            return 'A'
        if(characters is not None):
            if(characters[-1] == 'C'):
                return 'C'
            if(characters[-1] == 'F'):
                return 'f'    # F for Farad
            if(characters == ' E.F. '):
                return 'E'    # Electric Field Detection
            if(re.match(r'^--* *$', characters)):
                return 'E'    # Electric Field Detection
        return ' '

    def _states(self, dataFrame):
        """returns states

        Arguments:
            dataFrame -> raw data frame from multimeter

        Return:
            states"""
        byte1 = binBit(dataFrame[1])
        byte2 = binBit(dataFrame[2])
        byte11 = binBit(dataFrame[11])
        byte12 = binBit(dataFrame[12])
        byte13 = binBit(dataFrame[13])
        byte14 = binBit(dataFrame[14])
        states = set()
        if(byte1[4] == '1'):
            states.add('AUTO')
        if(byte1[7] == '1'):
            states.add('Relative-Zero')
        if(byte2[4] == '1'):
            states.add('Beep')
        if(byte2[5] == '1'):
            states.add('Low-Battery')
        if(byte2[6] == '1'):
            states.add('Low-Impedance')
        if(byte2[7] == '1'):
            states.add('Negative-Scale')
        if(byte11[4] == '1'):
            states.add('Hold')
        if(byte11[5] == '1'):
            states.add('dBm')
        if(byte12[4] == '1'):
            states.add('Crest')
        if(byte13[4] == '1'):
            states.add('MAX')
        if(byte14[4] == '1'):
            states.add('MIN')
        if(byte14[4] == '1'):
            states.add('Scale')
        return states

    def restartSerialDevice(self):
        """restarts connection with brymen"""
        serial.Serial.close(self)
        serial.Serial.open(self)
        time.sleep(0.2)

    def _isOK(self, dataFrame):
        """simple format check for brymen257

        Arguments:
            dataFrame -> raw data frame from multimeter

        Returns:
            boolean"""
        if(len(dataFrame) != 15):
            self.restartSerialDevice()
            return False
        first = dataFrame[0] & 0x0F
        if(first != 2):
                print('Wrong header byte. Expected 2, found ' + str(first))
                self.restartSerialDevice()
                return False
        for i in range(0,14):
            dataIndex = (dataFrame[i] & 0xF0) >> 4
            if(dataIndex != i):
                print('Wrong sequence index. Expected ' + str(i) + ', found ' + str(dataIndex))
                self.restartSerialDevice()
                return False
        return True

if __name__ == "__main__":
    device = '/dev/ttyUSB0'
    multimeter = Brymen257(device)
    time.sleep(.5)
    with open('test.txt', 'a') as f:
        while True:
            buf = multimeter.getData()  # decodes this frame
            #print(str(buf[0]) + '\t' + str(buf[1]) + '\t' + str(buf[2]))
            f.write('\t'.join((str(buf[0]), str(buf[1]), str(buf[2]), '\n')))
            f.flush()
            multimeter.flushOutput()
    f.close()
    multimeter.close()
