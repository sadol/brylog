#!/usr/bin/env python
"""
serial device plotting class
"""
import matplotlib as mpl
mpl.use('TkAgg')
from collections import deque
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import re


QUANTITY = {'=V': ('DC Voltage Plot', '[V]'),
            '~V': ('AC Voltage Plot', '[V]'),
            ' V': ('Voltage Plot', '[V]'),
            '=A': ('DC Current Plot', '[A]'),
            '~A': ('AC Current Plot', '[A]'),
            ' A': ('Current Plot', '[A]'),
            '  ': ('Plot', '[-]'),
            ' O': ('Resistance Plot', r'$[\Omega]$'),
            ' F': ('Capacitance Plot', '[F]'),
            ' H': ('Frequency Plot', '[Hz]'),
            ' E': ('Electric Field Detection', '[E.F.]'),
            ' C': ('Celsius Temperature Plot', r'$[^\circ C]$'),
            ' f': ('Fahrenheit Temperature Plot', r'$[^\circ F]$')}

class PlotFrame(tk.Frame):
    def __init__(self, root, queueObj, delay, valueL, displayL, infoL, **rest):
        """Arguments:
            root        -> parent object
            queueObj    -> queue.Queue object which services serial dev
            **rest      -> kwargs{} for tkinter.Frame"""
        tk.Frame.__init__(self, master=root, **rest)
        self.grid()
        self.root = root
        neutral = self.root.cget('background')       # neutral color of widgets
        # data tuple index to plot(unique for each device)
        self.plotBuffer = deque([0] * 100)           # 100 points plot buffer
        self.queueObj = queueObj
        self.delay = delay
        self.valueL = valueL
        self.displayL = displayL
        self.infoL = infoL
        self.myFigure = mpl.figure.Figure(facecolor=neutral, edgecolor=neutral)
        self.myFigure.subplots_adjust(left=0.15, right=0.85)
        self.myAxes = self.myFigure.add_subplot(1, 1, 1)
        self.myAxes.grid(True)
        self.myAxes.set_title("Realtime Waveform Plot")
        self.myLine, = self.myAxes.plot(range(100), self.plotBuffer, '-',
                                        linewidth=2)
        self.canvas = FigureCanvasTkAgg(self.myFigure, master=self.root)
        self.canvas.get_tk_widget().grid()

    def _setLimits(self, dequeObj):
        """sets y range limits for self.plotObj

        Aruments:
            dequeObj -> collections.deque object filled with data to plot

        Returns:
            [min, max] list"""
        mi = min(dequeObj)
        ma = max(dequeObj)
        diff = ma - mi
        adjust = 0.1 * diff
        adjust = (mi if 0 < mi else (-mi if mi < 0 else 1)) * 0.1 if adjust == 0 else adjust
        return [mi - adjust, ma + adjust]

    def _setInfo(self, states):
        infoLine = ''
        if 'AUTO' in states:
            infoLine = infoLine + ', Auto-range'
        if 'Beep' in states:
            infoLine = infoLine + ', Beep'
        if 'Low-Battery' in states:
            infoLine = infoLine + ', Low-Battery'
        if 'Low-Impedance' in states:
            infoLine = infoLine + ', Low-Impedance'
        if 'dBm' in states:
            infoLine = infoLine + ', dBm'
        return re.sub(r'^, ', '', infoLine)

    def _setTitle(self, quantity, states):
        """sets proper plot title according to raw data physical quantity

        Arguments:
            quantity -> string, quantipy postfix

        Returns:
            string, updated waveform plot title"""
        headLine = QUANTITY[quantity][0]
        detailsLine = ''
        if 'Hold' in states:
            detailsLine = detailsLine + ', Hold'
        if 'Relative-Zero' in states:
            detailsLine = detailsLine + ', Relative'
        if 'Crest' in states:
            detailsLine = detailsLine + ', Crest'
        if('MIN' in states and 'MAX' in states):
            detailsLine = detailsLine + ', Min-max'
        else:
            if 'MIN' in states:
                detailsLine = detailsLine + ', Min'
            if 'MAX' in states:
                detailsLine = detailsLine + ', Max'
        detailsLine = re.sub(r'^, ', '', detailsLine)
        return headLine + (('\n' + detailsLine) if detailsLine else '')

    def _setLabel(self, label):
        """sets proper plot`s y axis label  according to raw data

        Arguments:
            label  -> string, label

        Returns:
            string, updated waveform plot`s y axis label"""
        return QUANTITY[label][1]

    def plot(self):
        """ploting function using matplotlib and tkinter objects"""
        (time, value, names, display, states) = self.queueObj.get()
        self.myAxes.set_title(self._setTitle(names, states))  # change title
        self.myAxes.set_ylabel(self._setLabel(names))         # change label
        self.displayL.config(text=display)
        self.infoL.config(text=self._setInfo(states))
        if (value is not None):
            self.valueL.config(text=value)
            self.plotBuffer.popleft()                     # remove leftmost element
            self.plotBuffer.append(value)                 # add to right new el
            self.myLine.set_data(range(100), self.plotBuffer)
            lim = self._setLimits(self.plotBuffer)
            self.myAxes.axis([1, 100, lim[0], lim[1]])
        else:
            self.valueL.config(text='N/A')
        self.canvas.draw()
        self.master.after(self.delay, self.plot)      # recursive!!!

if __name__ == '__main__':
    import brymen257 as br
    import queue
    import threading
    multimetr = br.Brymen257('/dev/ttyUSB0')
    root = tk.Tk()
    myQueue = queue.Queue()

    def func(device, queue):
        while True:
            queue.put(device.getData())

    thr = threading.Thread(target=func, args=(multimetr, myQueue), daemon=True)
    root.protocol(name='WM_DELETE_WINDOW', func=quit)
    p = PlotFrame(root, queueObj=myQueue, delay=25)
    p.grid()
    thr.start()
    p.plot(25)
    root.mainloop()
