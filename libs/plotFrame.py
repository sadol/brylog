#!/usr/bin/env python
"""
serial device plotting class
"""
import matplotlib as mpl
mpl.use('TkAgg')
from collections import deque
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk


QUANTITY = {'=V': ('DC Voltage plot', '[V]'),
            '~V': ('AC Voltage plot', '[V]'),
            ' A': ('Current plot', '[A]'),
            ' O': ('Resistance plot', r'$[\Omega]$'),
            ' F': ('Capacitance plot', '[F]'),
            ' H': ('Inductance plot', '[H]'),
            ' C': ('Temperature plot', r'$[^\circ C]$')}

class PlotFrame(tk.Frame):
    def __init__(self, root, queueObj, delay, **rest):
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
        return [mi - (0.1 * mi), ma + (0.1 * ma)]

    def _setTitle(self, quantity):
        """sets proper plot title according to raw data physical quantity

        Arguments:
            quantity -> string, quantipy postfix

        Returns:
            string, updated waveform plot title"""
        return QUANTITY[quantity][0]

    def _setLabel(self, label):
        """sets proper plot`s y axis label  according to raw data

        Arguments:
            label  -> string, label

        Returns:
            string, updated waveform plot`s y axis label"""
        return QUANTITY[label][1]

    def plot(self):
        """ploting function using matplotlib and tkinter objects"""
        buf = self.queueObj.get()
        self.myAxes.set_title(self._setTitle(buf[2]))   # change title
        self.myAxes.set_ylabel(self._setLabel(buf[2]))  # change label
        self.plotBuffer.popleft()                     # remove leftmost element
        self.plotBuffer.append(buf[1])                # add to right new el
        self.myLine.set_data(range(100), self.plotBuffer)
        lim = self._setLimits(self.plotBuffer)
        self.myAxes.axis([1, 100, lim[0], lim[1]])
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
