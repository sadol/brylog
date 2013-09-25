#!/usr/bin/env python
"""
abstract class of the serial device
"""
import serial


class SerialDevice(serial.Serial):
    """
    custom serial meta class for GUI classes
    """

    def getData(self):
        """
        virtual function : returns decoded data frame
        """
        raise NotImplementedError('Serial.Device:' +
                                  'getData must be implemented!!!')

    def getFrame(self, dataFrame):
        """
        virtual function : returns  VALID data frame
        """
        raise NotImplementedError('Serial.Device:' +
                                  'getFrame must be implemented!!!')

    def restartSerialDevice(self):
        """
        virtual function : restarts serial device
        """
        raise NotImplementedError('Serial.Device:' +
                                  'restartSerialDevice must be implemented!!!')
