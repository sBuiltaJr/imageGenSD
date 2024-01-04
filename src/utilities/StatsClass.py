#A helper class to encapsulate stat properties.


#####  Imports  #####
import logging as log
import random as rand
from . import RarityClass as rc
from typing import Literal, Optional


#####  Package Variables  #####

#####  Package Functions  #####

def GetStatRange(rarity : rc.RarityList) -> tuple:
    """Returns a tuple of a minimum and maximum value for a range, given a rarity.

       Input: rarity - Which rarity value to use for range definitions.

       Output: tuple - a minimum and maximum range set.
    """

    match rarity:

        case rc.RarityList.LEGENDARY:
            return (70, 100)

        case rc.RarityList.ULTRA_RARE:
            return (55,  85)

        case rc.RarityList.SUPER_RARE:
            return (45,  70)

        case rc.RarityList.RARE:
            return (25,  50)

        case rc.RarityList.UNCOMMON:
            return ( 5,  35)

        case rc.RarityList.COMMON:
            return ( 0,  20)

        case _:
            return ( 0,   1)

#####  Helper Classes  #####

#####  Stats Class  #####

#TODO: find a way to create the default profile without advancing the RNG
class Stats:

    def __init__(self,
                 rarity : rc.RarityList):
        """Creates a  stats object based on rarity.

           Input: self - Pointer to the current object instance.
                  rarity - Which rarity value to use for generation.

           Output: None - Throws exceptions on error.
        """
        #Starting simple for now, future versions should have luck influence stats?
        self.range     = GetStatRange(rarity)

        self.agility   = rand.randint(self.range[0], self.range[1])
        self.defense   = rand.randint(self.range[0], self.range[1])
        self.endurance = rand.randint(self.range[0], self.range[1])
        self.luck      = rand.randint(self.range[0], self.range[1])
        self.strength  = rand.randint(self.range[0], self.range[1])

    def GetStatsList(self) -> list:
        """Returns the object's stats as a list.

           Input: self - Pointer to the current object instance.

           Output: list - A lsit of stats sorted alphabetically.
        """
        return [self.agility, self.defense, self.endurance, self.luck, self.strength]