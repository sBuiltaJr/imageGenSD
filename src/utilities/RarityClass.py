#A helper class to encapsulate rarity properties.


#####  Imports  #####
from enum import Enum, verify, UNIQUE
import random as rand

#####  Helper Classes  #####

@verify(UNIQUE)
class RarityList(Enum):

    SPECIAL    =    0
    LEGENDARY  = 1000
    ULTRA_RARE = 2000
    SUPER_RARE = 3000
    RARE       = 4000
    UNCOMMON   = 5000
    COMMON     = 6000
    CUSTOM     = 4294967296

    @classmethod
    def getStandardNameList(cls) -> list:
        """Returns the rarities as an iterable list starting wtih the rarest.

           Input: self - A class instance reference.

           Output: List - An iterable list of rarities.
        """
        return [cls.LEGENDARY, cls.ULTRA_RARE, cls.SUPER_RARE, cls.RARE, cls.UNCOMMON, cls.COMMON]

    @classmethod
    def getProbabilityList(cls) -> list:
        """Returns the probabilities of each rarity as an iterable list,
           starting wtih the rarest.

           Input: self - A class instance reference.

           Output: List - An iterable list of cumulative rarity probabilities.
        """
        #55% common 35% uncommon, 8.25% rare, 1.35% SR, .35% UR, .05% Legendary
        #Or, listed as summs from common to Legendary:
        #[65.0, 90.0, 98.25, 99.60, 99.95, 100.0]
        return [0.0005, 0.0035, 0.0135, 0.0825, 0.25, 0.65]


#####  Rarity Class  #####

class Rarity:

    def GenerateRarity(self) -> RarityList:
        """Generates a random rarity level for the profile.

           Input: self - Pointer to the current object instance.

           Output: enum - A randomly selected rarity from the distribution.
        """

        #This is a quirk of choices returning the output as a list.
        return rand.choices(population = RarityList.getStandardNameList(),
                            weights    = RarityList.getProbabilityList())[0]