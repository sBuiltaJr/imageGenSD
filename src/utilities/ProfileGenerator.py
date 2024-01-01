#Creates a base profile for an IGSD-generated image.


#####  Imports  #####
from enum import Enum
import logging as log
from . import RarityClass as rc
#import StatsClass as sc
from typing import Literal, Optional


#Stats generated with rarity bands (slight RNG around a base prob set.)


#####  Helper Classes  #####

class Stats:

    Agility   : int
    Defense   : int
    Endurance : int
    Luck      : int
    Strength  : int


#####  Profile Class  #####

class Profile:

    #Optional Name?  description?
    def __init__(self,
                 id     : int,
                 #info   : Optional[info],
                 owner  : Optional[int]       = None,
                 rarity : Optional[rc.Rarity] = None,
                 stats  : Optional[Stats]     = None):
        """Creates a profile intended to attaching to an IGSD-generated image.

           Input: self - Pointer to the current object instance.

           Output: None - Throws exceptions on error.
        """

        self.creator = id
        self.owner   = 0 #starts with creator.
        self.rarity  = rc.Rarity.GenerateRarity(self) if rarity == None else rarity
        self.name    = "test"
        #self.stats   = sc.Stats.GenerateStats(self.rarity) if stats == None else stats
        self.info    = None #Get IGSD image info before profile?

    def GenerateStats(self,
                      rarity : rc.Rarity) -> Stats:
        """Generates stats for the profile based on rarity.

           Input: self - Pointer to the current object instance.

           Output: None - Throws exceptions on error.
        """


