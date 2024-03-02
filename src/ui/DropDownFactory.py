#Encapsulates different modal types used in various jobs.


#####  Imports  #####
from ..db import MariadbIfc as mdb
from abc import ABC, abstractmethod
import base64 as b64
import discord as dis
from enum import IntEnum, verify, UNIQUE
import io
import src.utilities.JobFactory as jf
from typing import Callable, Optional
import traceback

#####  Package Variables  #####

#Imposed by Discord
DROPDOWN_ITEM_LIMIT          = 25
#limit minus the 3 nav buttons (forward, back, and cancel)
DROPDOWN_ITEM_LIMIT_WITH_NAV = DROPDOWN_ITEM_LIMIT - 3
FORWARD_NAV_VALUE            =  1
BACKWARD_NAV_VALUE           = -1
CANCEL_NAV_VALUE             =  0

#####  Enum Classes  #####

@verify(UNIQUE)
class DropDownTypeEnum(IntEnum):

    SHOW    =    0
    FACTORY =    1
    DUNGEON =    2

#####  Abstract Classes  #####
class DynamicDropdown(ABC, dis.ui.Select):

    @abstractmethod
    async def getPage(self,
                      page: int):
        pass

    async def on_timeout(self):
        """Handles the timeout interaction inherent to discord interactions.

           Input : self - a pointer to the current object.

           Output : None.
        """
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def getTotalPages(total_items    : int) -> int:
        """Calculates the total number of pages for a given object.

           Input : total_items - the total number of items in the menu.

           Output : int - How many pages are required for this list.
        """
        return ((total_items - 1) // DROPDOWN_ITEM_LIMIT) + 1


#####  Modeal Factory  Class  ####

class ShowDropdown(DynamicDropdown):


    def __init__(self,
                 ctx      : dis.Interaction,
                 metadata : dict,
                 opts     : Optional[dict],
                 choices  : Optional[list] = None):

        self.choices  = choices
        self.ctx      = ctx
        self.metadata = metadata
        self.offset   = 0 if opts == None else int(opts['offset'])

        if choices != None:

            self.pages = self.getTotalPages(total_items=len(choices))
            options    = [dis.SelectOption(label=choices[x].name,value=choices[x].id) for x in range(0, DROPDOWN_ITEM_LIMIT_WITH_NAV)]
            options.append(dis.SelectOption(label='Next',value=FORWARD_NAV_VALUE))
            options.append(dis.SelectOption(label='Back',value=BACKWARD_NAV_VALUE))
            options.append(dis.SelectOption(label='Cancel',value=CANCEL_NAV_VALUE))

        super().__init__(placeholder='Select a character to display.', min_values=1, max_values=1, options=options)

    async def getPage(self,
                      page: int):
        pass

    async def callback(self,
                       interaction: dis.Interaction):

        if self.values[0] == str(FORWARD_NAV_VALUE) :

            opts = {}
            choices = self.choices[5:DROPDOWN_ITEM_LIMIT_WITH_NAV+5]
            opts['offset'] = 5

            new_view = DropdownView(ctx      = self.ctx,
                                    type     = DropDownTypeEnum.SHOW,
                                    metadata = self.metadata,
                                    choices  = choices,
                                    options  = opts)

            await interaction.response.edit_message(view=new_view)

        elif self.values[0] == str(CANCEL_NAV_VALUE) :

            message = await self.ctx.original_response()
            await message.edit(view=None)

        elif self.values[0] == str(BACKWARD_NAV_VALUE) :

            opts = {}
            choices = self.choices[0:DROPDOWN_ITEM_LIMIT_WITH_NAV]
            opts['offset'] = 0

            new_view = DropdownView(ctx      = self.ctx,
                                    type     = DropDownTypeEnum.SHOW,
                                    metadata = self.metadata,
                                    choices  = choices,
                                    options  = opts)

            await interaction.response.edit_message(view=self.view)

        elif self.values != None:

            opts = {'id' : self.values[0]}

            job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.SHOWPROFILE,
                                       ctx     = self.ctx,
                                       options = opts)
            result = self.metadata['queue'].add(metadata = self.metadata,
                                                job      = job)
            await interaction.response.edit_message(content=result)


class DropdownView(dis.ui.View):

    def __init__(self,
                 ctx      : dis.Interaction,
                 type     : DropDownTypeEnum,
                 choices  : Optional[list] = None,
                 metadata : Optional[dict] = None,
                 options  : Optional[list] = None):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(DropDownFactory.getDropDown(ctx      = ctx,
                                                  type     = type,
                                                  choices  = choices,
                                                  metadata = metadata,
                                                  options  = options))

class DropDownFactory:

    def getDropDown(ctx      : dis.Interaction,
                    type     : DropDownTypeEnum,
                    choices  : Optional[list] = None,
                    metadata : Optional[dict] = None,
                    options  : Optional[dict] = None) -> DynamicDropdown:
        """Returns an instance of a drop down type with appropriate options set.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of optional configs for this drop down.

           Output: dropdown - The appropriate dropdown type.
        """

        match type:

            case DropDownTypeEnum.SHOW:
                return ShowDropdown(ctx      = ctx,
                                    metadata = metadata,
                                    choices  = choices,
                                    opts     = options)

            case DropDownTypeEnum.FACTORY:
                raise NotImplementedError

            case DropDownTypeEnum.DUNGEON:
                raise NotImplementedError

            case _:
                raise NotImplementedError
