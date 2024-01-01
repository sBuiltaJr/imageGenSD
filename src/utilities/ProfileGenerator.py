#Creates a base profile for an IGSD-generated image.


#####  Imports  #####
from enum import Enum
import logging as log
from . import RarityClass as rc
from . import StatsClass as sc
from typing import Literal, Optional



#####  Helper Classes  #####

#####  Profile Class  #####

class Profile:

    #Optional Name?  description?
    def __init__(self,
                 id     : int,
                 #info   : Optional[info],
                 owner  : Optional[int]           = None,
                 rarity : Optional[rc.RarityList] = None,
                 stats  : Optional[sc.Stats]      = None):
        """Creates a profile intended to attaching to an IGSD-generated image.

           Input: self - Pointer to the current object instance.

           Output: None - Throws exceptions on error.
        """

        self.creator = id
        self.owner   = id if owner == None else owner
        self.rarity  = rc.Rarity.GenerateRarity(self) if rarity == None else rarity
        self.name    = "test"
        self.stats   = sc.Stats(self.rarity) if stats == None else stats
        self.info    = None #Get IGSD image info before profile?

