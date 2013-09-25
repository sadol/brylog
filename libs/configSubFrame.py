#!/usr/bin/env python
"""
main config panel for serial device frame
"""
import libs.serialDevice as sd
import tkinter as tk
from tkinter import filedialog as fidal
import libs.configDictionaries as cfd
from tkinter import messagebox as msb
import os


class ConfigSubFrame(tk.Frame):
    """
    subframe fireing after config button pressed
    """
    def __init__(self, root, **rest):
        tk.Frame.__init__(self, master=root, **rest)
        self.pack()
        self.deviceFileName = None
        self.deviceBaudRate = None
        self.deviceByteSize = None
        self.deviceParity = None
        self.deviceStopBits = None
        self.deviceTimeout = None
        self.findFrame = tk.Frame(master=self, **cfd.frConf)
        self.findFrame.pack(side=tk.TOP, fill=tk.X)
        tk.Button(self.findFrame, text='FIND DEVICE',
                  command=self._openFileName,
                  **cfd.okbConf).pack(side=tk.TOP)
        self.pathLabel = tk.Label(master=self.findFrame,
                                  text=self.deviceFileName)
        self.pathLabel.pack(side=tk.TOP, fill=tk.X)

        #baud rates selection values -->radiobutton----------------------------
        self.baudRateFrame = tk.Frame(master=self, **cfd.frConf)
        self.baudRateFrame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(master=self.baudRateFrame, text='BAUD RATE SELECTOR',
                 **cfd.lbConf).pack(side=tk.TOP, anchor=tk.W)
        self.valBaud = tk.IntVar()  # internal radiobutton variable
        self.valBaud.set(None)
        BAUDMODES = (('2400 Bauds', 2400), ('4800 Bauds', 4800),
                     ('9600 Bauds', 9600))
        self._buildRadioPanel(BAUDMODES, self.valBaud,
                              self.baudRateFrame, self._setBaudRate)

        #parity selection values -->radiobutton--------------------------------
        self.parityFrame = tk.Frame(master=self, **cfd.frConf)
        self.parityFrame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(master=self.parityFrame, text='PARITY SELECTOR',
                 **cfd.lbConf).pack(side=tk.TOP, anchor=tk.W)
        self.valParity = tk.IntVar()
        self.valParity.set(None)
        PARITYMODES = (('Parity None', 0), ('Parity Even', 2),
                       ('Parity Odd', 1))
        self._buildRadioPanel(PARITYMODES, self.valParity,
                              self.parityFrame, self._setParity)

        #Bytesize selection values -->radiobutton-----------------------------
        self.bytesizeFrame = tk.Frame(master=self, **cfd.frConf)
        self.bytesizeFrame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(master=self.bytesizeFrame, text='BYTESIZE SELECTOR',
                 **cfd.lbConf).pack(side=tk.TOP, anchor=tk.W)
        self.valBytesize = tk.IntVar()
        self.valBytesize.set(None)
        BYTESIZEMODES = (('Bytesize 5 bits', 5), ('Bytesize 6 bits', 6),
                         ('Bytesize 7 bits', 7), ('Bytesize 8 bits', 8))
        self._buildRadioPanel(BYTESIZEMODES, self.valBytesize,
                              self.bytesizeFrame, self._setBytesize)

        #stop bits selection values -->radiobutton----------------------------
        self.stopbitFrame = tk.Frame(master=self, **cfd.frConf)
        self.stopbitFrame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(master=self.stopbitFrame, text='STOP BIT SELECTOR',
                 **cfd.lbConf).pack(side=tk.TOP, anchor=tk.W)
        self.valStopBit = tk.IntVar()
        self.valStopBit.set(None)
        STOPBITSMODES = (('One stop bit ', 1), ('Two stop bits', 2))
        self._buildRadioPanel(STOPBITSMODES, self.valStopBit,
                              self.stopbitFrame, self._setStopBit)

        #timeout selection values -->radiobutton-------------------------------
        self.timeoutFrame = tk.Frame(master=self, **cfd.frConf)
        self.timeoutFrame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(master=self.timeoutFrame, text='TIMEOUT SELECTOR',
                 **cfd.lbConf).pack(side=tk.TOP, anchor=tk.W)
        self.valTimeout = tk.IntVar()
        self.valTimeout.set(None)
        TIMEOUTMODES = (('Timeout 0 s', 0), ('Timeout 1 s', 1))
        self._buildRadioPanel(TIMEOUTMODES, self.valTimeout, self.timeoutFrame,
                              self._setTimeout)

        #-------ok cancel load save frame--------------------------------------
        self.actionFrame = tk.Frame(master=self)
        self.actionFrame.pack(side=tk.TOP, anchor=tk.E)
        tk.Button(self.actionFrame, text='CANCEL',
                  command=self._cancelAction,
                  **cfd.clbConf).pack(side=tk.LEFT)
        tk.Button(self.actionFrame, text='OK',
                  command=self._okAction,
                  **cfd.okbConf).pack(side=tk.RIGHT)
        self.configDir = os.path.join(os.getcwd(), 'configure')
        tk.Button(self.actionFrame, text='SAVE',
                  command=self._saveAction,
                  **cfd.okbConf).pack(side=tk.LEFT)
        tk.Button(self.actionFrame, text='LOAD',
                  command=self._loadAction,
                  **cfd.okbConf).pack(side=tk.LEFT)

    def _buildRadioPanel(self, MODES, radioVar, radioFrame, radioComm):
        """
        builds radiobutton panel
        """
        for (t, v) in MODES:
            tk.Radiobutton(master=radioFrame, text=t, value=v,
                           command=radioComm,
                           variable=radioVar).pack(anchor=tk.W)

    def _saveAction(self):
        """
        saves configurations in config file
        config file is picke not text
        """
        import pickle
        if(not os.path.exists(self.configDir)):  # create dir if needed
            os.mkdir(path=self.configDir)
        sfd = fidal.asksaveasfilename(title='Saving configuration',
                                      initialdir=self.configDir,
                                      parent=self,
                                      defaultextension='.pkl',
                                      filetypes=[('pickle config files',
                                                  '*.pkl')],
                                      confirmoverwrite=True)
        if not self._checkValues():
            return False
        self.getData()  # fill parent buffer
        with open(sfd, mode='wb') as configFile:  # save parent buffer
            pickle.dump(self.master.tempBuffor, configFile)
        self.master.destroy()

    def _loadAction(self):
        """
        loads configurations from config file
        """
        import pickle
        if(not os.path.exists(self.configDir)):
            msb.showerror(message='No config directory.\nPlease save first.',
                          parent=self)
            return False
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
        """
        checks if every important value is set
        """
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
        """
        checks if every variable is filled with proper data
        and returns output tuple for parent object
        """
        if not self._checkValues():  # return "empty" tuple
            self.master.tempBuffor = (None, None, None, None, None, None)
        self.getData()  # return "full" tuple
        self.master.destroy()

    def _cancelAction(self):
        #analogycaly to getData
        self.master.tempBuffor = (None, None, None, None, None, None)
        self.master.destroy()

    def _setBytesize(self):
        temp = int(self.valBytesize.get())
        if(temp == 5):
            self.deviceByteSize = sd.serial.FIVEBITS
        elif(temp == 6):
            self.deviceByteSize = sd.serial.SIXBITS
        elif(temp == 7):
            self.deviceByteSize = sd.serial.SEVENBITS
        elif(temp == 8):
            self.deviceByteSize = sd.serial.EIGHTBITS

    def _setStopBit(self):
        temp = int(self.valStopBit.get())
        if(temp == 1):
            self.deviceStopBits = sd.serial.STOPBITS_ONE
        elif(temp == 2):
            self.deviceStopBits = sd.serial.STOPBITS_TWO

    def _setParity(self):
        temp = int(self.valParity.get())
        if(temp == 0):
            self.deviceParity = sd.serial.PARITY_NONE
        elif(temp == 2):
            self.deviceParity = sd.serial.PARITY_EVEN
        elif(temp == 1):
            self.deviceParity = sd.serial.PARITY_ODD

    def _setBaudRate(self):
        self.deviceBaudRate = int(self.valBaud.get())

    def _setTimeout(self):
        self.deviceTimeout = int(self.valTimeout.get())

    def _openFileName(self):
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
        """
        main getter function for ConfigSubFrame class
        populates temporary buffor variable in self.master caller class
        (device filename , device baud rate, device byte size,
         device parity, device stop bits, device timeout)
        all returned values are serial.py constants.
        You must create such tuple!!!
        """
        self.master.tempBuffor = (self.deviceFileName, self.deviceBaudRate,
                                  self.deviceStopBits, self.deviceByteSize,
                                  self.deviceParity, self.deviceTimeout)


if __name__ == '__main__':

    def openDeviceConfig():
        win = tk.Toplevel()
        win.tempBuffor = ()  # such python trick -> add new varialbe to old cl
        ConfigSubFrame(win).pack()
        win.focus_set()
        win.focus_get()
        win.wait_window()
        msb.showinfo(title='Captured config tuple', message=win.tempBuffor)

    ot = tk.Tk()
    tk.Button(ot, text='CONFIG', command=openDeviceConfig).pack()
    ot.mainloop()
