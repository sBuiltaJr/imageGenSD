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


def GetDescription(rarity : rc.RarityList = rc.RarityList.COMMON) -> str:
    """Generates a random rarity level for the profile.

       Input: self - Pointer to the current object instance.

       Output: enum - A randomly selected rarity from the distribution.
    """

    match rarity:

        case rc.RarityList.LEGENDARY:
            return "The highest tier, rarest, and best kind of character!  Take that!"

        case rc.RarityList.ULTRA_RARE:
            return "The second-highest tier of character!  So close!"

        case rc.RarityList.SUPER_RARE:
            return "The thrid-higest tier of character!  Able to trounce their lessers."

        case rc.RarityList.RARE:
            return "The fourth-higest tier of character!  What a rare find!"

        case rc.RarityList.UNCOMMON:
            return "The fifth-highest tier of character!  Better than the lowest, but not by much."

        case rc.RarityList.COMMON:
            return "The most common kind of character.  It is the thought that counts, right?"

        case rc.RarityList.CUSTOM:
            return "A custom kind of character not bound by the rules of this world!"

        case _:
            return "A description so bland it shouldn't exist!"

#####  Helper Classes  #####

#####  Stats Class  #####

class Stats:

    def __init__(self,
                 rarity : rc.RarityList,
                 #TODO: combine the options into the options dictionary
                 #in a way to avoid key errors.
                 agility   : Optional[int] = None,
                 defense   : Optional[int] = None,
                 endurance : Optional[int] = None,
                 luck      : Optional[int] = None,
                 strength  : Optional[int] = None):
        """Creates a  stats object based on rarity.

           Input: self - Pointer to the current object instance.
                  rarity - Which rarity value to use for generation.

           Output: None - Throws exceptions on error.
        """
        #Starting simple for now, future versions should have luck influence stats?
        self.range     = GetStatRange(rarity)

        self.agility   = agility if agility != None else rand.randint(self.range[0], self.range[1])
        self.defense   = defense if defense != None else rand.randint(self.range[0], self.range[1])
        self.endurance = endurance if endurance != None else rand.randint(self.range[0], self.range[1])
        self.luck      = luck if luck != None else rand.randint(self.range[0], self.range[1])
        self.strength  = strength if strength != None else rand.randint(self.range[0], self.range[1])

    def GetStatsList(self) -> list:
        """Returns the object's stats as a list.

           Input: self - Pointer to the current object instance.

           Output: list - A lsit of stats sorted alphabetically.
        """
        return [self.agility, self.defense, self.endurance, self.luck, self.strength]
