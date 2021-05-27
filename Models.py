from dataclasses import dataclass
import tkinter as tk
import time
import math
from functools import partial
from tkinter import ttk

import logging
from EDMCLogging import get_main_logger
logger = logging.getLogger('EDMC-Trade-Tracker.Modules')

@dataclass
class Category:
    id: int
    name: str

@dataclass
class Commodity:
    id: int
    name: str
    category_id: int
    average_price: int
    is_rare: bool
    max_buy_price: int
    max_sell_price: int
    min_buy_price: int
    min_sell_price: int
    buy_price_lower_average: int
    sell_price_upper_average: int
    is_non_marketable: bool
    ed_id: int
    category: Category  = None

    def __post_init__(self):
        if not self.category:  # Lookup category if not set
            logger.error(f'mising category: {self.id}')
        elif self.category and not isinstance(self.category, Category):
            self.category = Category(**self.category)

@dataclass
class Listing:
    """Listing class"""
    id: int
    station_id: int
    commodity_id: int
    supply: int
    supply_bracket: int
    buy_price: int
    sell_price: int
    demand: int
    demand_bracket: int
    collected_at: int
    LEFT: str = "Left"
    RIGHT: str = "RIGHT"

    def timeAgo(self): # changeto datetime.timedelta
        now = round(time.time())
        listingTime = self.collected_at
        timeDiff = now - listingTime

        if timeDiff < 60: #
            return f"{timeDiff}sec "
        elif timeDiff < 3600:
            return f"{round(timeDiff/60)}min"
        elif timeDiff < 86400:
            return f"{round(timeDiff/60/60)}hrs"
        else:
            return f"{round(timeDiff/60/60/24)}day"


@dataclass
class BuyListing(Listing):
    """BuyListing subclass"""

@dataclass
class SellListing(Listing):
    """SellListing subclass"""

@dataclass
class Station:
    id: int
    name: str
    system_id: int
    max_landing_pad_size: str
    distance_to_star: int
    faction: str
    type_id: int
    has_blackmarket: bool
    has_refuel: bool
    has_repair: bool
    has_rearm: bool
    has_outfitting: bool
    has_shipyard: bool
    has_docking: bool
    has_commodities: bool
    has_material_trader: bool
    has_technology_broker: bool
    has_carrier_vendor: bool
    has_carrier_administration: bool
    has_interstellar_factors: bool
    has_universal_cartographics: bool
    has_social_space: bool
    updated_at: int
    shipyard_updated_at: int
    outfitting_updated_at: int
    market_updated_at: int

    def getTypeIcon(self):
        if self.type_id in range(13, 18):
            return "🪐"
        else:
            return " "

@dataclass
class System:
    id: int
    name: str
    x: float
    y: float
    z: float
    faction: str
    population: int
    allegiance_id: int
    government_id: int
    needs_permit: bool
    updated_at: int
    simbad_ref: str
    is_populated: bool

@dataclass
class Point:
    x: float
    y: float
    z: float

    def distance(self, point):
        dx = self.x - point.x
        dy = self.y - point.y
        dz = self.z - point.z
        return round(math.hypot(dx, dy, dz))


@dataclass
class Loop:
    oneBuyListing: BuyListing
    twoBuyListing: BuyListing
    oneSellListing: SellListing
    twoSellListing: SellListing
    oneStation: Station
    twoStation: Station
    oneSystem: System
    twoSystem: System
    oneCommodity: Commodity
    twoCommodity: Commodity
    distance: float
    userSystem: System
    tradeLoopId: int

    def __post_init__(self):
        self.oneBuyListing = BuyListing(**self.oneBuyListing)
        self.twoBuyListing = BuyListing(**self.twoBuyListing)
        self.oneSellListing = SellListing(**self.oneSellListing)
        self.twoSellListing = SellListing(**self.twoSellListing)
        self.oneStation = Station(**self.oneStation)
        self.twoStation = Station(**self.twoStation)
        self.oneSystem = System(**self.oneSystem)
        self.twoSystem = System(**self.twoSystem)
        self.oneCommodity = Commodity(**self.oneCommodity)
        self.twoCommodity = Commodity(**self.twoCommodity)
        self.userSystem = System(**self.userSystem)
        self.distance = round(self.distance)

    def min_distance(self):
        userPoint = Point(self.userSystem.x, self.userSystem.y, self.userSystem.z)
        oneSystemPoint = Point(self.oneSystem.x, self.oneSystem.y, self.oneSystem.z)
        twoSystemPoint = Point(self.twoSystem.x, self.twoSystem.y, self.twoSystem.z)
        dist1 = userPoint.distance(oneSystemPoint)
        dist2 = userPoint.distance(twoSystemPoint)
        return min(dist1, dist2)
    
    def min_distance_str(self):
        return f'{self.min_distance()} ly'

    def loop_length_str(self):
        return f'{self.distance} ly'

    def profit(self):
        oneProfit = self.twoSellListing.sell_price - self.oneBuyListing.buy_price
        twoProfit = self.oneSellListing.sell_price - self.twoBuyListing.buy_price
        return oneProfit + twoProfit
    
    def profit_str(self):
        return f'{self.profit()}Cr'

@dataclass
class LabelHolder:
    label: tk.Label
    alignment: str = tk.W

@dataclass
class LoopInfoLine:
    """This is used to store the tk variables for displaying an entire loop in the loops view"""
    loop: Loop
    frame: tk.Frame
    indx: str
    buttonFunc: partial
    indxVar: tk.StringVar = None
    list1TimeAgo: tk.StringVar = None
    list2TimeAgo: tk.StringVar = None
    station1Icon: tk.StringVar = None
    station2Icon: tk.StringVar = None
    distTo: tk.StringVar = None
    loopDist: tk.StringVar = None
    profit: tk.StringVar = None
    supply1: tk.StringVar = None
    supply2: tk.StringVar = None
    line1Labels: list[tk.Label] = None
    line2Labels: list[tk.Label] = None
    selectButton: tk.Button = None
    separator: ttk.Separator = None
    # probably want to add a separator here

    def __post_init__(self):
        self.indxVar = tk.StringVar(value=self.indx)
        logger.debug(self.loop)
        logger.debug(self.loop.oneBuyListing)
        self.list1TimeAgo = tk.StringVar(value=self.loop.oneBuyListing.timeAgo())
        self.list2TimeAgo = tk.StringVar(value=self.loop.twoBuyListing.timeAgo())
        self.station1Icon = tk.StringVar(value=self.loop.oneStation.getTypeIcon())
        self.station2Icon = tk.StringVar(value=self.loop.twoStation.getTypeIcon())        
        self.distTo = tk.StringVar(value=self.loop.min_distance_str())
        self.loopDist = tk.StringVar(value=self.loop.loop_length_str())
        self.profit = tk.StringVar(value=self.loop.profit())
        self.supply1 = tk.StringVar(value=self.loop.oneBuyListing.supply)
        self.supply2 = tk.StringVar(value=self.loop.twoBuyListing.supply)
        self.line1Labels =  self.createLine1Labels()
        self.line2Labels =  self.createLine2Labels()
        self.selectButton = tk.Button(self.frame, text="Select", command=self.buttonFunc)
        self.separator = ttk.Separator(self.frame, orient=tk.HORIZONTAL)

    def updateLine(self, loop, indx, commandFunc):
        self.loop = loop
        self.indxVar.set(indx)
        self.list1TimeAgo.set(self.loop.oneBuyListing.timeAgo())
        self.list2TimeAgo.set(self.loop.twoBuyListing.timeAgo())
        self.station1Icon.set(self.loop.oneStation.getTypeIcon())
        self.station2Icon.set(self.loop.twoStation.getTypeIcon())
        self.distTo.set(self.loop.min_distance_str())
        self.loopDist.set(self.loop.loop_length_str())
        self.profit.set(self.loop.profit())
        self.supply1.set(self.loop.oneBuyListing.supply)
        self.supply2.set(self.loop.twoBuyListing.supply)
        self.selectButton.configure(command=commandFunc)
    
    def createLine1Labels(self):
        labels = []
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.indxVar)))
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.station1Icon)))
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.list1TimeAgo), tk.E))
        labels.append(LabelHolder(tk.Label(self.frame, text="⮀")))
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.list2TimeAgo)))
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.station2Icon)))
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.distTo), tk.E))
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.profit), tk.E))
        return labels

    def createLine2Labels(self):
        labels = []
        labels.append(LabelHolder(tk.Label(self.frame, text=""), tk.E))
        labels.append(LabelHolder(tk.Label(self.frame, text=""), tk.E))
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.supply1), tk.E))
        labels.append(LabelHolder(tk.Label(self.frame, text="⮀")))
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.supply2)))
        labels.append(LabelHolder(tk.Label(self.frame, text=""), tk.E))
        labels.append(LabelHolder(tk.Label(self.frame, textvariable=self.loopDist), tk.E))
        return labels
       

        



@dataclass
class Route:
    system: System
    station: Station
    commodity: Commodity
    supply: int
    cost: int