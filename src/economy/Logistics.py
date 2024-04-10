#Encapsulates all Logistics-related economy functions.


#####  Imports  #####
from dataclasses import dataclass, field
from enum import Enum, verify, UNIQUE

#####  Package Variables  #####

#####  Helper Classes  #####
@dataclass
class LogisticsInfoMixin:
    order        : int
    cost         : int
    display_name : str

@verify(UNIQUE)
class LogisticsListEnum(LogisticsInfoMixin, Enum):

    #These are numbered in recommended order, individual tiers are expected to
    #filter as required for a given user.
    LOGISTICS_0 =  0, 100, "Base Logistics Expansion Slot 1"
    LOGISTICS_1 =  1, 100, "Base Logistics Expansion Slot 2"
    TEAM_0      =  2, 100, "Dungeon Exploration Team Expansion Slot 1"
    HOSPITAL_0  =  3, 100, "Unit Recovery Center Expansion Slot 1"
    KEY_GEN_0   =  4, 100, "Dungeon Key Generation Expansion Slot 1"
    CRAFTER_0   =  5, 100, "Equipment Crafting Team Expansion Slot 1"
    BUILDER_0   =  6, 100, "Base Building Team Expansion Slot 1"
    LOGISTICS_2 =  7, 100, "Base Logistics Expansion Slot 3"
    LOGISTICS_3 =  8, 100, "Base Logistics Expansion Slot 4"
    LOGISTICS_4 =  9, 100, "Base Logistics Expansion Slot 5"
    RESEARCH_0  = 10, 100, "Dungeon Tier Research Expansion Slot 1"
    HOSPITAL_1  = 11, 100, "Unit Recovery Center Expansion Slot 2"
    HOSPITAL_2  = 12, 100, "Unit Recovery Center Expansion Slot 3"
    KEY_GEN_1   = 13, 100, "Dungeon Key Generation Expansion Slot 2"
    KEY_GEN_2   = 14, 100, "Dungeon Key Generation Expansion Slot 3"
    TEAM_1      = 15, 100, "Dungeon Exploration Team Expansion Slot 2"
    CRAFTER_1   = 16, 100, "Equipment Crafting Team Expansion Slot 2"
    CRAFTER_2   = 17, 100, "Equipment Crafting Team Expansion Slot 3"
    BUILDER_1   = 18, 100, "Base Building Team Expansion Slot 2"
    HOSPITAL_3  = 19, 100, "Unit Recovery Center Expansion Slot 4"
    TEAM_2      = 20, 100, "Dungeon Exploration Team Expansion Slot 3"
    KEY_GEN_3   = 21, 100, "Dungeon Key Generation Expansion Slot 4"
    CRAFTER_3   = 22, 100, "Equipment Crafting Team Expansion Slot 4"
    BUILDER_2   = 23, 100, "Base Building Team Expansion Slot 3"
    BUILDER_3   = 24, 100, "Base Building Team Expansion Slot 4"
    HOSPITAL_4  = 25, 100, "Unit Recovery Center Expansion Slot 5"
    KEY_GEN_4   = 26, 100, "Dungeon Key Generation Expansion Slot 5"
    CRAFTER_4   = 27, 100, "Equipment Crafting Team Expansion Slot 5"
    TEAM_3      = 28, 100, "Dungeon Exploration Team Expansion Slot 4"
    BUILDER_4   = 29, 100, "Base Building Team Expansion Slot 5"
    TEAM_4      = 30, 100, "Dungeon Exploration Team Expansion Slot 5"
    RESEARCH_1  = 31, 100, "Dungeon Tier Research Expansion Slot 2"
    RESEARCH_2  = 32, 100, "Dungeon Tier Research Expansion Slot 3"
    RESEARCH_3  = 33, 100, "Dungeon Tier Research Expansion Slot 4"
    RESEARCH_4  = 34, 100, "Dungeon Tier Research Expansion Slot 5"
    NOTHING     = 99, 100, "No target set (or no valid target available)"

def getNextLevelsList(self,
                      stats : list) -> list:
    """Returns the next available logistics targets given a list of current
       capabilities.  This list is assumed to be read directly from the DB,
       meaning current capabilities are provided as an integer list and not a
       set of LogisticsEnums.

       Input: self - A class instance reference.

       Output: List - An iterable list of rarities.
    """
    pass

def getNextTargetInprogression(self,
                               current : int) -> int:
    """Returns the enum value of the next research target, meant for handling
       excess work in a research tier during daily resets.

       Input: self - A class instance reference.

       Output: List - An iterable list of rarities.
    """
    pass


# Read econ data into an obj and return right key/value pairs.

#Focus log in a tier, back, next, finish
#only ahve targets in tier
#In daily, check if complete, then automatically apply balance to next log in tree (avoid stale data abuse)
#have automatic progression between types to avoid work loss.
#Re-apply any sapre progress to a new research if moved by the user.
#Different currencies by tier.