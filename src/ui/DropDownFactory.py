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

    async def on_timeout(self):
        """Handles the timeout interaction inherent to discord interactions.

           Input : self - a pointer to the current object.

           Output : None.
        """
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)


#####  Modeal Factory  Class  ####

class ShowDropdown(DynamicDropdown):


    def __init__(self,
                 choices  : list,
                 ctx      : dis.Interaction,
                 metadata : dict,
                 opts     : dict):
        """Creates a Dropdown with a slices of choices from a provided choice
           list, including adding navigation via menu options.

           Input : self - a pointer to the current object.
                   ctx - the Discord context to associate wtih this dropdown.
                   choices - an optional list of choices to pu in the dropdown.
                   metadata - Where to make Post request, among other things.
                   options - Dropdown-specific options.

           Output : None.
        """

        self.choices  = choices
        self.ctx      = ctx
        self.metadata = metadata
        self.offset   = 0 if opts == None else int(opts['offset'])


        if len(self.choices) <= DROPDOWN_ITEM_LIMIT_WITH_NAV :

            slice = range(0, len(self.choices))

        elif self.offset + DROPDOWN_ITEM_LIMIT_WITH_NAV <= len(self.choices) :

            slice = range(0, DROPDOWN_ITEM_LIMIT_WITH_NAV)

        else :

            slice = range(0, len(self.choices) - self.offset)

        options = [dis.SelectOption(label=choices[self.offset + x].name,value=choices[self.offset + x].id) for x in slice]
        options.append(dis.SelectOption(label='Next',   value=FORWARD_NAV_VALUE))
        options.append(dis.SelectOption(label='Back',   value=BACKWARD_NAV_VALUE))
        options.append(dis.SelectOption(label='Cancel', value=CANCEL_NAV_VALUE))

        super().__init__(placeholder='Select a character to display.', min_values=1, max_values=1, options=options)

    async def callback(self,
                       interaction: dis.Interaction):
        """Process otpions selected by a user when they click off the dropdown.
           If needing to present new options, it will delete and replace the
           existing Discord post with a new version.

           Input : self - a pointer to the current object.
                   interaction - the Discord context for the dropdown.

           Output : None.
        """

        if self.values[0] == str(FORWARD_NAV_VALUE) or self.values[0] == str(BACKWARD_NAV_VALUE) :

            opts           = {}
            next           = self.offset + DROPDOWN_ITEM_LIMIT_WITH_NAV * int(self.values[0])
            opts['offset'] = next if next >= 0 and next < len(self.choices) else self.offset

            new_view = DropdownView(ctx      = self.ctx,
                                    type     = DropDownTypeEnum.SHOW,
                                    metadata = self.metadata,
                                    choices  = self.choices,
                                    options  = opts)

            await interaction.response.edit_message(view=new_view)

        elif self.values[0] == str(CANCEL_NAV_VALUE) :

            message = await self.ctx.original_response()
            await message.edit(view=None)

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
        """Creates a parent view for the requesed dropdown.

           Input : self - a pointer to the current object.
                   ctx - the Discord context to associate wtih this dropdown.
                   type - what kind of dropdown to make.
                   choices - an optional list of choices to pu in the dropdown.
                   metadata - IGSD data for the dropdown.
                   options - Dropdown-specific options.

           Output : None.
        """

        super().__init__(timeout=100)

        self.add_item(DropDownFactory.getDropDown(choices  = choices,
                                                  ctx      = ctx,
                                                  type     = type,
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
                  ctx - the Discord context to associate wtih this dropdown.
                  type - what kind of dropdown to make.
                  choices - an optional list of choices to pu in the dropdown.
                  metadata - IGSD data for the dropdown.
                  options - Dropdown-specific options.

           Output: dropdown - The appropriate dropdown type.
        """

        match type:

            case DropDownTypeEnum.SHOW:
                return ShowDropdown(choices  = choices,
                                    ctx      = ctx,
                                    metadata = metadata,
                                    opts     = options)

            case DropDownTypeEnum.FACTORY:
                raise NotImplementedError

            case DropDownTypeEnum.DUNGEON:
                raise NotImplementedError

            case _:
                raise NotImplementedError
