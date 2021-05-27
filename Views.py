
import logging
import tkinter as tk
from functools import partial
import logging
from tkinter.ttk import Button
from EDMCLogging import get_main_logger
logger = logging.getLogger('EDMC-Trade-Tracker.Views')


class View:
    def __init__(self) -> None:
        pass

    def show(self):
        pass

    def hide(self):
        pass

class HomeView:
    def __init__(self, buttons) -> None:
        self.buttons = buttons
        self.rowWidth = 3

    def show(self):
        for indx, button in enumerate(self.buttons):
            button.grid(row=int(indx / self.rowWidth), column= indx % self.rowWidth, sticky=tk.W)

    def hide(self):
        for button in self.buttons:
            button.grid_forget()

class LoadingView:
    def __init__(self, loadingLabel) -> None:
        self.loadingLabel = loadingLabel

    def show(self):
        self.loadingLabel.grid(row = 0, column = 0)

    def hide(self):
        self.loadingLabel.grid_forget()

class LoopsView:
    # TOD: handle when ttal loops decreas
    def __init__(self):
        self.loops = []
        self.currentLoops = 0
        logger.info("Creating loops page")

    def show(self):
        rowPos = 0
        for loopIndx, loop in enumerate(self.loops):
            # First Line
            for labelIndx1, widget in enumerate(loop.line1Labels):
                widget.label.grid(row = rowPos, column = labelIndx1, sticky=widget.alignment)
            rowPos = rowPos + 1
            # Second Line
            for labelIndx2, widget in enumerate(loop.line2Labels):
                widget.label.grid(row = rowPos, column = labelIndx2, sticky=widget.alignment)
            loop.selectButton.grid(row=rowPos, column=len(loop.line2Labels), sticky=tk.E)
            rowPos = rowPos + 1
            loop.separator.grid(columnspan=10, sticky=tk.EW, row=rowPos)
            rowPos = rowPos + 1

    def hide(self):
        for loop in enumerate(self.loops):
            for widget in enumerate(loop.line1Labels):
                widget.label.grid_forget()
            for widget in enumerate(loop.line2Labels):
                widget.label.grid_forget()
            loop.selectButton.grid_forget()
            loop.separator.grid_forget()
        pass

    def setLoops(self, loops):
        self.loops = loops

class TestView:
    def __init__(self, logger) -> None:
        self.testArray = []
        self.logger = logger

    def show(self):
        self.logger.debug(self.testArray[0])
        pass

    def hide(self):
        pass

    def setTest(self, testArray):
        self.testArray = testArray