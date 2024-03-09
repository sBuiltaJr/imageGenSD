#A helper class to encapsulate stat properties.


#####  Imports  #####
from . import RarityClass as rc
import logging as log
import random as rand
import statistics as stat
from typing import Literal, Optional


#####  Package Variables  #####

#####  Package Functions  #####

def getStatRange(rarity : rc.RarityList) -> tuple:
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


def getDescription(rarity : rc.RarityList = rc.RarityList.COMMON) -> str:
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

def getDefaultOptions() -> dict:
    """Returns a default dictionary of options accepted by the Stats class.

       Input: None

       Output: dict - a complete dictionary of default options.
    """
    opts = {'agility'   : None,
            'average'   : None,
            'defense'   : None,
            'endurance' : None,
            'luck'      : None,
            'strength'  : None
           }

    return opts

#####  Helper Classes  #####

#####  Stats Class  #####

class Stats:

    def __init__(self,
                 rarity : rc.RarityList,
                 opts   : dict):
        """Creates a  stats object based on rarity.

           Input: self - Pointer to the current object instance.
                  rarity - Which rarity value to use for generation.

           Output: None - Throws exceptions on error.
        """
        #Starting simple for now, future versions should have luck influence stats?
        self.range     = getStatRange(rarity)

        self.agility   = int(opts['agility'])   if opts['agility']   != None else rand.randint(self.range[0], self.range[1])
        self.defense   = int(opts['defense'])   if opts['defense']   != None else rand.randint(self.range[0], self.range[1])
        self.endurance = int(opts['endurance']) if opts['endurance'] != None else rand.randint(self.range[0], self.range[1])
        self.luck      = int(opts['luck'])      if opts['luck']      != None else rand.randint(self.range[0], self.range[1])
        self.strength  = int(opts['strength'])  if opts['strength']  != None else rand.randint(self.range[0], self.range[1])
        #The items below rely on items above.
        self.average   = float(opts['average']) if opts['average']   != None else stat.mean(self.getStatsList())

    def getStatsList(self) -> list:
        """Returns the object's stats as a list.

           Input: self - Pointer to the current object instance.

           Output: list - A lsit of stats sorted alphabetically.
        """
        return [self.agility, self.defense, self.endurance, self.luck, self.strength]
