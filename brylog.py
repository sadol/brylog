#!/usr/bin/env python
"""
Configuration subframe for serial device for home_lab_project
"""

import tkinter as tk
import libs.configSubFrame as csf
import libs.configDictionaries as cfd
from tkinter import messagebox as msb
import time
import os
import threading
import libs.plotFrame as plf
import queue


class ConfigFrame(tk.Frame):
    def __init__(self, root, device, delay, **rest):
        """Arguments:

            root -> root widget for config frame,
            device -> serial device object
            delay -> delay time (see plotFrame.py)
            **rest -> rest of dict arguments inherited from tkinter.Frame"""
        tk.Frame.__init__(self, master=root, **rest)
        self.serialPath = None
        self.serialBaud = None
        self.serialBsize = None
        self.serialParity = None
        self.serialSbits = None
        self.serialTimeout = None
        self.conEstablished = False
        self.delay = delay
        self.device = device
        #---------------------config section-----------------------------------
        self.conFr = tk.Frame(master=self, **cfd.frConf)
        self.conFr.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)
        tk.Label(master=self.conFr, text='CONF & CONN DEVICE',
                 **cfd.lbConf).grid(row=0, column=0, columnspan=2)
        self.confB = tk.Button(master=self.conFr, text='CONFIG',
                               command=self._configDevice, **cfd.okbConf)
        self.confB.grid(row=1, column=0, sticky=tk.W)
        self.quitB = tk.Button(self.conFr, text='QUIT', command=self._quit,
                               **cfd.clbConf)
        self.quitB.grid(row=1, column=1, sticky=tk.W)
        tk.Label(master=self.conFr, text='Device:',
                 **cfd.lbConfSmall).grid(row=2, column=0, sticky=tk.E)
        self.pathL = tk.Label(master=self.conFr, text='NONE', fg='red')
        self.pathL.grid(row=2, column=1, sticky=tk.W)
        tk.Label(master=self.conFr, text='Baud Rate:',
                 **cfd.lbConfSmall).grid(row=3, column=0, sticky=tk.E)
        self.baudL = tk.Label(master=self.conFr, text='NONE', fg='red')
        self.baudL.grid(row=3, column=1, sticky=tk.W)
        tk.Label(master=self.conFr, text='Byte Size:',
                 **cfd.lbConfSmall).grid(row=4, column=0, sticky=tk.E)
        self.bytesL = tk.Label(master=self.conFr, text='NONE', fg='red')
        self.bytesL.grid(row=4, column=1, sticky=tk.W)
        tk.Label(master=self.conFr, text='Parity:',
                 **cfd.lbConfSmall).grid(row=5, column=0, sticky=tk.E)
        self.parL = tk.Label(master=self.conFr, text='NONE', fg='red')
        self.parL.grid(row=5, column=1, sticky=tk.W)
        tk.Label(master=self.conFr, text='Stop Bits:',
                 **cfd.lbConfSmall).grid(row=6, column=0, sticky=tk.E)
        self.sbitsL = tk.Label(master=self.conFr, text='NONE', fg='red')
        self.sbitsL.grid(row=6, column=1, sticky=tk.W)
        tk.Label(master=self.conFr, text='Timeout (s):',
                 **cfd.lbConfSmall).grid(row=7, column=0, sticky=tk.E)
        self.timeL = tk.Label(master=self.conFr, text='NONE', fg='red')
        self.timeL.grid(row=7, column=1, sticky=tk.W)

        #--------------save section--------------------------------------------
        self.conectFr = tk.Frame(master=self, **cfd.frConf)
        self.conectFr.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)
        tk.Label(master=self.conectFr, text='SAVE OUTPUT TO FILE',
                 **cfd.lbConf).grid(row=1, column=0, columnspan=2,
                                    sticky=tk.EW)
        self.saveB = tk.Button(master=self.conectFr, text='SAVE',
                               command=self._saveToFile, **cfd.okbConf)
        self.saveB.grid(row=2, column=0, sticky=tk.W)
        self.stopB = tk.Button(self.conectFr, text='STOP',
                               command=self._stopSaving, **cfd.okbConf)
        self.stopB.grid(row=2, column=1, sticky=tk.W)
        tk.Label(master=self.conectFr, text='File name:',
                 **cfd.lbConfSmall).grid(row=3, column=0, sticky=tk.E)
        self.fileL = tk.Label(master=self.conectFr, text='NONE', fg='red')
        self.fileL.grid(row=3, column=1, sticky=tk.W)
        self.fileName = ''
        self.fo = None  # file object variable
        self.saveDir = os.path.join(os.getcwd(), 'save')

        #------------multithreading variables----------------------------------
        self.plotQueue = queue.Queue()
        self.saveQueue = queue.Queue()

        #---------plot section ------------------------------------------------
        self.plotFr = tk.Frame(master=self, **cfd.frConf)
        self.plotFr.grid(row=0, column=2, rowspan=2, sticky=tk.EW)
        self.plot = plf.PlotFrame(self.plotFr, self.plotQueue, self.delay)
        self.plot.grid()

    def _mainDataProducer(self):
        """main data producer thread"""
        while self.conEstablished:
            temp = self.device.getData()
            self.plotQueue.put(temp)
            if not self.saveQueue.full():  # saving check
                self.saveQueue.put(temp)

    def _quit(self):
        """quit button handler"""
        self.conEstablished = False
        self.savingStatus = False
        if self.fo:
            self.fo.close()
        self.master.destroy()

    def _saveToFile(self):
        """SAVE button handler"""
        if(not self.conEstablished):
            msb.showerror(message='Device not ready')
            return
        self.fileName = (time.strftime("%Y_%m_%d %H_%M_%S", time.gmtime()) +
                         ' ' + os.path.basename(self.device.port) + '.txt')
        #file operations require save dir
        if(not os.path.exists(self.saveDir)):
            os.mkdir(path=self.saveDir, mode=755)
        if(not self.fo is None):
            msb.showerror(message='SAVING IS PROCEEDING ALREADY')
            return
        self.fileL.config(text=self.fileName[:6] + '...', **cfd.lbConfSmall)
        self.savingStatus = True
        self.thr3 = threading.Thread(target=self._saving, args=(),
                                     daemon=True)  # daemon!!! very important
        self.thr3.start()

    def _saving(self):
        """saves data to file. File name=datetime.datetime() + self.file_Name.
        Format : time.time()\tvalue\tunit\n"""
        saveFile = os.path.join(self.saveDir, self.fileName)
        self.fo = open(saveFile, 'a')
        while True:
            try:
                temp = self.saveQueue.get()
                for i in temp:
                    self.fo.write(str(i) + '\t')
                self.fo.write('\n')
                self.fo.flush()  # don't buffer
                self.saveQueue.task_done()
            except AttributeError:
                break  # end thread silently (must be a daemon!!!)

    def _stopSaving(self):
        """kills saving thread"""
        if(not self.fo is None):
            self.fo.close()  # cleaning after nasty thread
            self.fo = None
            self.fileL.config(text='NONE', **cfd.lbConfSmallRed)
        else:
            msb.showerror(message='NO FILE TO CLOSE')

    def _configDevice(self):
        """populates internal data variables of the class"""
        win = tk.Toplevel()
        win.tempBuffor = ()  # python trick->add new varialbe on the fly
        sub = csf.ConfigSubFrame(win)
        sub.grid()
        win.focus_set()    # \
        win.focus_get()    # |->  lock the popup window
        win.wait_window()  # /
        #!!! caveat !!! ORDER MATTERS !!! (future improve:use dict in sep mod)
        try:
            (self.serialPath, self.serialBaud, self.serialSbits,
             self.serialBsize, self.serialParity,
             self.serialTimeout) = win.tempBuffor
            self._connectDevice()  # don't use separate button, connect asap
        except ValueError:  # cancel action
            pass

    def _connectDevice(self):
        """tries to connect to serial device"""
        if(self.serialPath is None or self.serialBaud is None or
           self.serialBsize is None or self.serialParity is None or
           self.serialSbits is None or self.serialTimeout is None):

            msb.showerror(message='Device not configured!')
            return

        self.device.port = self.serialPath        # \
        self.device.baudrate = self.serialBaud    # |
        self.device.bytesize = self.serialBsize   # |
        self.device.parity = self.serialParity    # |-> for info label
        self.device.stopbits = self.serialSbits   # |
        self.device.timeout = self.serialTimeout  # /
        self.device.close()
        self.device.open()
        time.sleep(0.3)
        tempData = self.device.getFrame()
        if(not tempData is None):
            self.conEstablished = True
            self.pathL.config(text=self.serialPath, **cfd.lbConfSmall)
            self.baudL.config(text=self.serialBaud, **cfd.lbConfSmall)
            self.bytesL.config(text=self.serialBsize, **cfd.lbConfSmall)
            self.parL.config(text=self.serialParity, **cfd.lbConfSmall)
            self.sbitsL.config(text=self.serialSbits, **cfd.lbConfSmall)
            self.timeL.config(text=self.serialTimeout, **cfd.lbConfSmall)
            msb.showinfo(message='Connection established')
            #start data producer thread asap
            self.thr = threading.Thread(target=self._mainDataProducer,
                                        args=())
            self.thr.start()
            #begin plotting immediately in the separate thread
            self.thr2 = threading.Thread(target=self.plot.plot, args=())
            self.thr2.start()
        else:
            self.conEstablished = False
            msb.showwarning(message='Connection failed!\nCheck your device.')


if __name__ == '__main__':
    import libs.brymen257 as br

    root = tk.Tk()
    multimeter = br.Brymen257(None)
    root.title('BRYMEN 257 MULTIMETER')
    #!!!!!!!!special code for custom icon!!!!!!!!!!!!!!!!!!!!!!!!!
    root.wm_iconbitmap('@' + 'libs/oscillator_noise_64.xbm')
    delay = 25
    mainPanel = ConfigFrame(root, device=multimeter, delay=delay)
    mainPanel.grid()
    root.protocol('WM_DELETE_WINDOW', mainPanel._quit)
    root.mainloop()
