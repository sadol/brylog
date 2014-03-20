#!/usr/bin/env python
"""main config panel for serial device frame"""
import tkinter as tk
from tkinter import filedialog as fidal
import libs.configDictionaries as cfd
from tkinter import messagebox as msb
import os
import serial

class ConfigSubFrame(tk.Frame):
    """subframe fireing after config button pressed"""
    def __init__(self, root, **rest):
        tk.Frame.__init__(self, master=root, **rest)
        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.deviceFileName = None    # \
        self.deviceBaudRate = None    # |
        self.deviceByteSize = None    # |-> radio button variables
        self.deviceParity = None      # |
        self.deviceStopBits = None    # |
        self.deviceTimeout = None     # /
        self.findFrame = tk.Frame(master=self, **cfd.frConf)
        self.findFrame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)
        self.findFrame.grid_columnconfigure(0, weight=1)
        self.findFrame.grid_rowconfigure(0, weight=1)
        tk.Button(self.findFrame, text='FIND DEVICE',
                  command=self._openFileName,
                  **cfd.okbConf).grid(row=0, column=0)
        self.pathLabel = tk.Label(master=self.findFrame,
                                  text=self.deviceFileName)
        self.pathLabel.grid(row=1, column=0, sticky=tk.NSEW)

        #baud rates selection values -->radiobutton----------------------------
        baudRateFrame = tk.Frame(master=self, **cfd.frConf)
        baudRateFrame.grid(row=1, column=0, sticky=tk.NSEW)
        tk.Label(master=baudRateFrame, text='BAUD RATE SELECTOR',
                 **cfd.lbConf).grid(row=0, column=0, sticky=tk.W)
        self.valBaud = tk.IntVar()  # internal radiobutton variable
        self.valBaud.set(None)
        BAUDMODES = (('2400 Bauds', 2400), ('4800 Bauds', 4800),
                     ('9600 Bauds', 9600))
        self._buildRadioPanel(BAUDMODES, self.valBaud,
                              baudRateFrame, self._setBaudRate)

        #parity selection values -->radiobutton--------------------------------
        parityFrame = tk.Frame(master=self, **cfd.frConf)
        parityFrame.grid(row=1, column=1, sticky=tk.NSEW)
        tk.Label(master=parityFrame, text='PARITY SELECTOR',
                 **cfd.lbConf).grid(row=0, column=0, sticky=tk.W)
        self.valParity = tk.IntVar()
        self.valParity.set(None)
        PARITYMODES = (('Parity None', 0), ('Parity Even', 2),
                       ('Parity Odd', 1))
        self._buildRadioPanel(PARITYMODES, self.valParity,
                              parityFrame, self._setParity)

        #Bytesize selection values -->radiobutton-----------------------------
        bytesizeFrame = tk.Frame(master=self, **cfd.frConf)
        bytesizeFrame.grid(row=2, column=0, sticky=tk.NSEW)
        tk.Label(master=bytesizeFrame, text='BYTESIZE SELECTOR',
                 **cfd.lbConf).grid(row=0, column=0, sticky=tk.W)
        self.valBytesize = tk.IntVar()
        self.valBytesize.set(None)
        BYTESIZEMODES = (('Bytesize 5 bits', 5), ('Bytesize 6 bits', 6),
                         ('Bytesize 7 bits', 7), ('Bytesize 8 bits', 8))
        self._buildRadioPanel(BYTESIZEMODES, self.valBytesize,
                              bytesizeFrame, self._setBytesize)

        #stop bits selection values -->radiobutton----------------------------
        stopbitFrame = tk.Frame(master=self, **cfd.frConf)
        stopbitFrame.grid(row=2, column=1, sticky=tk.NSEW)
        tk.Label(master=stopbitFrame, text='STOP BIT SELECTOR',
                 **cfd.lbConf).grid(row=0, column=0, sticky=tk.W)
        self.valStopBit = tk.IntVar()
        self.valStopBit.set(None)
        STOPBITSMODES = (('One stop bit ', 1), ('Two stop bits', 2))
        self._buildRadioPanel(STOPBITSMODES, self.valStopBit,
                              stopbitFrame, self._setStopBit)

        #timeout selection values -->radiobutton-------------------------------
        timeoutFrame = tk.Frame(master=self, **cfd.frConf)
        timeoutFrame.grid(row=3, column=0, sticky=tk.NSEW)
        tk.Label(master=timeoutFrame, text='TIMEOUT SELECTOR',
                 **cfd.lbConf).grid(row=0, column=0, sticky=tk.W)
        self.valTimeout = tk.IntVar()
        self.valTimeout.set(None)
        TIMEOUTMODES = (('Timeout 0 s', 0), ('Timeout 1 s', 1))
        self._buildRadioPanel(TIMEOUTMODES, self.valTimeout, timeoutFrame,
                              self._setTimeout)

        #-------ok cancel load save frame--------------------------------------
        actionFrame = tk.Frame(master=self)
        actionFrame.grid(row=3, column=1, sticky=tk.NSEW)
        for i in range(2):
            actionFrame.grid_columnconfigure(i, weight=1)
            actionFrame.grid_rowconfigure(i, weight=1)
        tk.Button(actionFrame, text='CANCEL', command=self._cancelAction,
                  **cfd.clbConf).grid(row=0, column=0, sticky=tk.E + tk.S)
        tk.Button(actionFrame, text='OK', command=self._okAction,
                  **cfd.okbConf).grid(row=0, column=1, sticky=tk.W + tk.S)
        self.configDir = os.path.join(os.getcwd(), 'configure')
        tk.Button(actionFrame, text='SAVE', command=self._saveAction,
                  **cfd.okbConf).grid(row=1, column=0, sticky=tk.E + tk.N)
        tk.Button(actionFrame, text='LOAD', command=self._loadAction,
                  **cfd.okbConf).grid(row=1, column=1, sticky=tk.W + tk.N)

    def _buildRadioPanel(self, MODES, radioVar, radioFrame, radioComm):
        """builds radiobutton panel

        Arguments:
            Modes      -> modes tuple
            radioVar   -> radiobutton tkinter variable
            radioFrame -> tkinter Frame
            radioComm  -> radiobutton tkinter widget handler

        Returns:"""
        i = 1
        for (t, v) in MODES:
            tk.Radiobutton(master=radioFrame, text=t, value=v,
                           command=radioComm,
                           variable=radioVar).grid(row=i, column=0,
                                                   sticky=tk.W)
            i += 1

    def _saveAction(self):
        """saves configurations in config file
        (config file is picke not text)"""
        import pickle
        if(not os.path.exists(self.configDir)):
            os.mkdir(path=self.configDir)
        sfd = fidal.asksaveasfilename(title='Saving configuration',
                                      initialdir=self.configDir,
                                      parent=self,
                                      defaultextension='.pkl',
                                      filetypes=[('pickle config files',
                                                  '*.pkl')],
                                      confirmoverwrite=True)
        if not self._checkValues():
            return
        self.getData()                                 # fill parent buffer
        with open(sfd, mode='wb') as configFile:       # save parent buffer
            pickle.dump(self.master.tempBuffor, configFile)
        self.master.destroy()

    def _loadAction(self):
        """loads configurations from config file"""
        import pickle
        if(not os.path.exists(self.configDir)):
            msb.showerror(message='No config directory.\nPlease save first.',
                          parent=self)
            return
        lf = fidal.askopenfile(mode='rb',
                               defaultextension='.pkl',
                               initialdir=self.configDir,
                               title='Load saved configurations.',
                               filetypes=[('pickle config files', '*pkl')],
                               parent=self)
        if(not lf):  # cancel button pressed
            return
        self.master.tempBuffor = pickle.load(lf)  # load into parents' buffor
        lf.close()  # don't forget to close descriptor!!!!
        self.master.destroy()  # dont need main frame anymore

    def _checkValues(self):
        """checks if every important value is set

        Arguments:

        Returns:
            boolean"""
        if(self.deviceFileName is None):
            msb.showerror(message='Please choose serial device.',
                          parent=self)
            return False
        if(self.deviceBaudRate is None):
            msb.showerror(message='Please choose baud rate.',
                          parent=self)
            return False
        if(self.deviceByteSize is None):
            msb.showerror(message='Please choose byte size.',
                          parent=self)
            return False
        if(self.deviceStopBits is None):
            msb.showerror(message='Please choose stop bit number.',
                          parent=self)
            return False
        if(self.deviceParity is None):
            msb.showerror(message='Please choose parity.',
                          parent=self)
            return False
        if(self.deviceTimeout is None):
            msb.showerror(message='Please choose timeout period.',
                          parent=self)
            return False
        return True

    def _okAction(self):
        """ok button handler,
        checks if every variable is filled with proper data,
        and creates output tuple for parent object"""
        if not self._checkValues():
            self.master.tempBuffor = (None, None, None, None, None, None)
        self.getData()
        self.master.destroy()

    def _cancelAction(self):
        """cancel button handler"""
        self.master.tempBuffor = (None, None, None, None, None, None)
        self.master.destroy()

    def _setBytesize(self):
        """sets multimeter`s byte size"""
        temp = int(self.valBytesize.get())
        if(temp == 5):
            self.deviceByteSize = serial.FIVEBITS
        elif(temp == 6):
            self.deviceByteSize = serial.SIXBITS
        elif(temp == 7):
            self.deviceByteSize = serial.SEVENBITS
        elif(temp == 8):
            self.deviceByteSize = serial.EIGHTBITS

    def _setStopBit(self):
        """sets multimeter`s stop bit"""
        temp = int(self.valStopBit.get())
        if(temp == 1):
            self.deviceStopBits = serial.STOPBITS_ONE
        elif(temp == 2):
            self.deviceStopBits = serial.STOPBITS_TWO

    def _setParity(self):
        """sets multimeter`s parity"""
        temp = int(self.valParity.get())
        if(temp == 0):
            self.deviceParity = serial.PARITY_NONE
        elif(temp == 2):
            self.deviceParity = serial.PARITY_EVEN
        elif(temp == 1):
            self.deviceParity = serial.PARITY_ODD

    def _setBaudRate(self):
        """sets multimeter`s baudrate"""
        self.deviceBaudRate = int(self.valBaud.get())

    def _setTimeout(self):
        """sets multimeter`s timeout"""
        self.deviceTimeout = int(self.valTimeout.get())

    def _openFileName(self):
        """open file button handler"""
        fl = fidal.askopenfilename(title='Serial device file choosing',
                                   filetypes=[('Linux serial devices',
                                               'ttyUSB*')],
                                   multiple=False,
                                   initialdir='/dev',
                                   parent=self)
        if(str(fl).startswith('/dev/ttyUSB')):
            self.deviceFileName = str(fl)
            self.pathLabel.config(text=self.deviceFileName)

    def getData(self):
        """main getter function for ConfigSubFrame class
        populates temporary buffor variable in self.master caller class
        (device filename , device baud rate, device byte size,
         device parity, device stop bits, device timeout)
        all created values are serial.py constants.
        You must create such tuple!!!"""
        self.master.tempBuffor = (self.deviceFileName, self.deviceBaudRate,
                                  self.deviceStopBits, self.deviceByteSize,
                                  self.deviceParity, self.deviceTimeout)


if __name__ == '__main__':

    def openDeviceConfig():
        win = tk.Toplevel()
        win.tempBuffor = ()  # such python trick -> add new varialbe to old cl
        ConfigSubFrame(win).grid()
        win.focus_set()
        win.focus_get()
        win.wait_window()
        msb.showinfo(title='Captured config tuple', message=win.tempBuffor)

    ot = tk.Tk()
    tk.Button(ot, text='CONFIG', command=openDeviceConfig).grid()
    ot.mainloop()
