#Provides a base abstracted dropdown class to inherit across other dropdowns.


#####  Imports  #####
from abc import ABC, abstractmethod
import discord as dis
from typing import Optional


#####  Abstract Classes  #####

class DynamicDropdown(ABC, dis.ui.Select):

    async def getByRarity(self):
        pass

    async def getBySearchParameter(self):
        pass

    async def getFavorited(self):
        pass

    @abstractmethod
    def trimByGatingCriteria(self,
                             choices : Optional[list] = None,
                             opts    : Optional[dict] = None):
        """Trimms the existing choices list by some defined criteria.

           Input : self - a pointer to the current object.
                   options - what critera to trim by.

           Output : None.
        """
        pass
