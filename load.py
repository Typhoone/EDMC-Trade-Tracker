import os
import sys
import logging
import tkinter as tk
import threading
import requests
import json
import traceback
from functools import partial


# local imports
import Helpers
from Views import *
from Models import *


# EDMC imports
import myNotebook as nb
from ttkHyperlinkLabel import HyperlinkLabel
from config import config, appname
from EDMCLogging import get_main_logger
from theme import theme



# System Vars
this = sys.modules[__name__]  # For holding module globals
this.version = 'v0.0.1'
plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f'{appname}.{plugin_name}')

# Page Vars
this.currentPage = None

# Loop Vars
this.shouldFetchLoop = threading.Event()
this.fetchedCommodities = threading.Event()
this.loops = []
this.shownLoops = []
this.commoditiesDict = dict()
this.currentLoop = None

# For compatibility with pre-5.0.0
if not hasattr(config, 'get_int'):
    config.get_int = config.getint
if not hasattr(config, 'get_str'):
    config.get_str = config.get
if not hasattr(config, 'get_bool'):
    config.get_bool = lambda key: bool(config.getint(key))
if not hasattr(config, 'get_list'):
    config.get_list = config.get

# EDMC Funcs
def plugin_start3(plugin_dir):
    """Start the plugin"""
    logger.info('Starting worker threads...')
    this.stopThreads = threading.Event()
    this.threads = [
        threading.Thread(
            target=loopFetchThread,
            args=(this.stopThreads, ),
            name='Loop Fetching worker',
            daemon=True
        ),
        threading.Thread(
            target=fetchCommodities,
            args=(this.stopThreads, ),
            name='Commodity Update Worker',
            daemon=True
        )
    ]
    [thread.start() for thread in this.threads] # start all the threads
    logger.debug('Done.')
    loadConfigVars()

    return "Trade Tracker"

def plugin_app(parent):
    # Adds to the main page UI
    this.frame = tk.Frame(parent)
    initPages()
    load("home")
    return this.frame


def plugin_prefs(parent, cmdr, is_beta):
    """Plugin Preferences UI hook."""
    x_padding = 10

    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)

    HyperlinkLabel(
        frame, text='Trade Tracker', background=nb.Label().cget('background'), url="https://github.com/Typhoone/route-tracker", underline=True
    ).grid(row = 0, columnspan=2, padx=x_padding, sticky=tk.W) 


    return frame

def plugin_stop() -> None:
    """Stop this plugin."""
    logger.debug('Signalling threads to stop...')
    # Signal threads to close and wait for them to stop
    this.stopThreads.set()
    [thread.join() for thread in this.threads]
    this.threads = None
    logger.debug('Done.')

# Paging

def initPages():
    this.pages = {}

    # Home
    loop_btn = tk.Button(this.frame, text="Loop Route", command= lambda : load("loadLoops"))
    buttons = [loop_btn]
    this.pages["home"] = HomeView(buttons)

    # Loading Page
    loadingLabel = tk.Label(this.frame, text="Loading...")
    this.pages['loading'] = LoadingView(loadingLabel)

    # Loops Page
    this.pages['loops'] = LoopsView()

    # Loop Page

    # Test Page
    category = Category(5, "test")
    categories = [category]
    view = TestView(logger)
    view.setTest(categories)
    this.pages['test'] = view

def showPage(page, includeFooter = False):
    if(this.currentPage):
        this.pages[this.currentPage].hide()
    this.currentPage = page
    logger.debug(f'Showing Page: {page}')
    this.pages[page].show()

def load(state):
    this.state = state
    if state == 'home':
        showPage(state)
    elif state == 'loadLoops':
        showPage('loading')
        this.shouldFetchLoop.set()
    elif state == 'loops':
        showPage('loops')

def tester():
    logger.info("Working")
    showPage("test")

def loadConfigVars():
	this.includePlanetary = tk.IntVar(value=config.get_int("Trade-Tracker_includePlanetary", default = 1))
	this.minSupplyInt = tk.DoubleVar(value=config.get_str("Trade-Tracker_MinSupply", default = 1.5))
	this.hopDistInt = tk.IntVar(value=config.get_int("Trade-Tracker_hopDist", default = 0))
	this.priceAgeInt = tk.IntVar(value=config.get_int("Trade-Tracker_priceAge", default = 1))
	this.minDemandInt = tk.IntVar(value=config.get_int("Trade-Tracker_minDemand", default = 0))
	this.minProfitInt = tk.IntVar(value=config.get_int("Trade-Tracker_minProfit", default = 20000))

	this.currentSystem = config.get_str("Trade-Tracker_CurrentSystem", default = 'Sol')

	this.currentStation = config.get_str("Trade-Tracker_CurrentStation", default = "Abraham Lincoln")

# Loop Route
def lookupLoops(minSupply, systemId, includePlanetary, hopDist=50, priceAge=30, minDemand=0, minProfit=9500):
    url = 'https://eddb.io/route/search/loops'
    postData = {
                "loopsSettings": {
                    "implicitCommodities": [],
                    "ignoredCommodities": [],
                    "hopDistance": hopDist,
                    "minSupply": minSupply,
                    "minDemand": minDemand,
                    "priceAge": priceAge,
                    "minProfit": minProfit,
                    "systemId": systemId,
                    "sort": "profit"
                },
                "systemFilter": {
                    "skipPermit": False,
                    "powers": []
                },
                "stationFilter": {
                    "landingPad": 30,
                    "governments": [],
                    "allegiances": [],
                    "states": [],
                    "economies": [],
                    "distance": None,
                    "loopDistance": 0,
                    "singleRouteDistance": 0,
                    "includePlanetary": includePlanetary,
                    "includeFleetCarriers": False
                }
            }

    jsonOb = json.dumps(postData, indent = 4)
    logger.debug(jsonOb)
    logger.debug("Begin Fetch")
    jsonData = requests.post(url, json=postData).json()
    logger.debug("End Fetch")

    # logger.debug(jsonData)

    loops = []

    for loop in jsonData:
        newLoop = Loop(**loop) 
        loops.append(newLoop)

    return loops

def updateLoops(loops):
    loopNum = 5
    loopsToProcess = loops[:loopNum]
    for indx, loop in enumerate(loopsToProcess):
        logger.debug(loop.oneStation.type_id)
        logger.debug(loop.twoStation.type_id)
        showLoopFunc = partial(showLoop, indx)
        if indx < len(this.shownLoops):
            # update loop
            this.shownLoops[indx].updateLine(loop, indx, showLoopFunc)
        else:
            # create loop and append
            loopInfoLine = LoopInfoLine(loop, this.frame, str(indx + 1), showLoopFunc)
            this.shownLoops.append(loopInfoLine)
    this.pages['loops'].setLoops(this.shownLoops)
   
def showLoop(indx):
    this.currentLoop = this.loops[indx]
    logger.debug(this.currentLoop)

# Thread Stuff
def fetchCommodities(stopThread):
    """Worker thread for fetching commodities"""
    logger.debug("Fetching cmmodities...")
    try:
        for commodity in requests.get('https://eddb.io/archive/v6/commodities.json').json():
            newCommodity = Commodity(**commodity)
            this.commoditiesDict[newCommodity.id] = newCommodity
        logger.info(f"Fetched {len(commoditiesDict)} commodities")
        this.fetchedCommodities.set()
    except Exception as err:
        logger.error(err)
        logger.error(traceback.format_exc())

def loopFetchThread(stopThread):
    logger.debug('Loop thread starting...')
    try:
        stop_or_fetch = Helpers.OrEvent(stopThread, this.shouldFetchLoop)
        while not stopThread.is_set():  # exit loop if the stopThread event is called
            if this.shouldFetchLoop.is_set():
                this.shouldFetchLoop.clear()
                logger.info("Fetching Loop Data")
                this.fetchedCommodities.wait() # wait until commodity list is fetched at least once before fetching loops
                # systemId = getSystemId(this.currentSystem) if this.currentSystem else 17072
                systemId = 17072

                # logger.info(f'Fetching Loop Data - {systemId}: {this.currentSystem}')
                maxHopDist = 23
                minSup = round(this.minSupplyInt.get() * 640)
                includePlanet = this.includePlanetary.get() == 1
                this.loops = lookupLoops(minSup, 
											systemId, 
											includePlanet, 
											maxHopDist, 
											this.priceAgeInt.get(), 
											this.minDemandInt.get(), 
											this.minProfitInt.get()
											)
                logger.info("Loop Data Fetched")
                # for loop in this.loops:
                #     logger.debug(loop.profit())
                # showPage(this.currentPage)
                updateLoops(this.loops)
                load("loops")
            stop_or_fetch.wait() # wait until either stopThread or shouldFetchLoop events fire
    except Exception as err:
        logger.error(err)
        logger.error(traceback.format_exc())