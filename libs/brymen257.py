#!/usr/bin/env python
# encoding: utf-8
import time
import sys
import serial


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


multiplier = {' ': 1,
              'n': 0.000000001,
              'u': 0.000001,
              'm': 0.001,
              'k': 1000,
              'M': 1000000}

# digits decoder dictionary : key->(first Bit, second Bit), value->output digit
digits = {('111', '1011'): '0', ('000', '0000'): '0',
          ('000', '1010'): '1',
          ('101', '1101'): '2',
          ('100', '1111'): '3',
          ('010', '1110'): '4',
          ('110', '0111'): '5',
          ('111', '0111'): '6',
          ('100', '1010'): '7',
          ('111', '1111'): '8',
          ('110', '1111'): '9',
          ('111', '0001'): ' '}     # for temperature measuring


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
        self.unit = ' '
        self.seconds = 0.00
        self.port = port

    def _setFrame(self, dataFrame):
        """populates internal data buffers"""
        self.seconds = time.time()
        characters = ""                  # temporary buffer
        self.unit = self._currentType(dataFrame)
        characters += self._signType(dataFrame)
        for i in range(1, 5):            # extract digits
            characters += self._giveDigit(dataFrame, 2 * i + 1, 2 * i + 2)
        if(characters[-1] == ' '):       # temperature special code
            self.unit = 'C'
            self.value = float(characters)
        else:
            characters = self._period(dataFrame, characters)
            try:                         # multimeter lcd error values handling
                self.value = float(characters[1:7])
            except ValueError:
                self.value = (-1000)     # error code for further handling!!!!
            if(self.value != (-1000)):
                self.value *= multiplier[self._prefix(dataFrame)]
            self.unit += self._names(dataFrame)

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
        return (self.seconds, self.value, self.unit)

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

    def _signType(self, dataFrame):
        """returns sign of the number

        Arguments:
            dataFrame -> raw frame of data from multimeter

        Returns:
            string -> - or +"""
        byte1 = binBit(dataFrame[3])
        if(byte1[7] == '1'):
            return "-"
        return "+"

    def _giveDigit(self, dataFrame, firstByte, secondByte):
        """decodes digit bits from two bytes

        Arguments:
            dataFrame  -> raw data object
            firstByte  -> first bite of the data
            secondByte -> second bite of the data

        Returns:
            one digit or error code"""
        byte1 = binBit(dataFrame[firstByte])[4:7]
        byte2 = binBit(dataFrame[secondByte])[4:]
        try:
            return digits[(byte1, byte2)]
        except KeyError:
            return 'R'      # for various error codes

    def _period(self, dataFrame, characters):
        """returns string with period at correct position

        Arguments:
            dataFrame  -> raw data frame from multimeter
            characters -> preprepared string of digits

        Returns:
            string with correctly positioned period sign"""
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
        """returns sci prefix

        Arguments:
            dataFrame -> raw data frame from multimeter

        Returns:
            prefix"""
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
        return ' '

    def _names(self, dataFrame):
        """returns physical quantity

        Arguments:
            dataFrame -> raw data frame from multimeter

        Return:
            quantity"""
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
        return ' '

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
            f.write('\t'.join((str(buf[0]), str(buf[1]), str(buf[2]), '\n')))
            f.flush()
            multimeter.flushOutput()
    f.close()
    multimeter.close()
