#!/usr/bin/env python
"""
serial device plotting class
"""
import matplotlib as mpl
mpl.use('TkAgg')
from collections import deque
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk


class PlotFrame(tk.Frame):
    """
    serial device plotting class
    """
    def __init__(self, root, queueObj, dataPointer, delay, **rest):
        """
        constructor : root-> parent object
                      queueObj -> queue.Queue object which services serial dev
                      dataPointer-> tuple index of serial data output
                      **rest-> kwargs{} for tkinter.Frame
        """
        tk.Frame.__init__(self, master=root, **rest)
        self.grid()
        # data tuple index to plot(unique for each device)
        self.deviceData = dataPointer
        self.plotObj = None  # matplotlib object
        self.plotBuffer = deque([0] * 100)  # 100 points plot buffer
        self.queueObj = queueObj
        self.delay = delay
        self.myFigure = mpl.figure.Figure()
        self.myAxes = self.myFigure.add_subplot(111)
        self.myAxes.grid(True)
        self.myAxes.set_title("Realtime Waveform Plot")
        self.myLine, = self.myAxes.plot(range(100), self.plotBuffer, '-')

        #tkinter -> matplotlib objects---------------------------------------
        self.canvas = FigureCanvasTkAgg(self.myFigure, master=root)
        #canvas.show()
        self.canvas.get_tk_widget().grid()

    def _setLimits(self, dequeObj):
        """
        sets y range limits for self.plotObj
        """
        mi = min(dequeObj)
        ma = max(dequeObj)
        return [mi - (0.1 * mi), ma + (0.1 * ma)]

    def plot(self, delay):  # dummy argument is required!!!!!!!
        """
        ploting function using matplotlib and tkinter objects at the same time
        """
        buf = self.queueObj.get()
        self.plotBuffer.popleft()  # remove leftmost element
        self.plotBuffer.append(buf[self.deviceData])  # add to right new el
        #load data
        self.myLine.set_data(range(100), self.plotBuffer)
        #set limits on both axes
        lim = self._setLimits(self.plotBuffer)
        self.myAxes.axis([1, 100, lim[0], lim[1]])
        self.canvas.draw()  # draw this shit
        # recursion -> strange !
        self.master.after(self.delay, self.plot, self.delay)
        self.queueObj.task_done()

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
    p = PlotFrame(root, queueObj=myQueue, dataPointer=1, delay=25)
    p.grid()
    thr.start()
    p.plot(25)
    root.mainloop()
