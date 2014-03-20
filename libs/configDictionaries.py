#!/usr/bin/env python
"""
this file contains some config dicts used by widgets in home lab app
"""
import tkinter as tk
from tkinter import font as fnt

#frame config------------------------------------------------------------------
frConf = {'relief': tk.RIDGE, 'borderwidth': 2, 'padx': 10, 'pady': 2}

#label config------------------------------------------------------------------
lbConf = {'font': (fnt.BOLD, 16, fnt.ROMAN)}

#small label config------------------------------------------------------------
lbConfSmall = {'font': (fnt.BOLD, 12, fnt.ROMAN), 'foreground': 'black'}

#small label config------------------------------------------------------------
lbConfSmallRed = {'font': (fnt.BOLD, 12, fnt.ROMAN), 'foreground': 'red'}

#all buttons config------------------------------------------------------------
allBut = {'height': 1, 'width': 10}
#ok button config--------------------------------------------------------------
okbConf = {'font': (fnt.BOLD, 10, fnt.ROMAN)}
okbConf.update(allBut)

#cancel button config
clbConf = {'font': (fnt.BOLD, 10, fnt.ROMAN)}
clbConf.update(allBut)
