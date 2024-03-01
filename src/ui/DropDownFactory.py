#Encapsulates different modal types used in various jobs.


#####  Imports  #####
from abc import ABC, abstractmethod
import discord as dis
from enum import IntEnum, verify, UNIQUE
from typing import Callable, Optional
import traceback

#####  Package Variables  #####

#Imposed by Discord
DROPDOWN_ITME_LIMIT = 25

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
        return ((total_items - 1) // DROPDOWN_ITME_LIMIT) + 1


#####  Modeal Factory  Class  ####

class ShowDropdown(DynamicDropdown):


    def __init__(self,
                 ctx  : dis.Interaction,
                 opts : Optional[list] = None):

        self.choices = opts
        self.ctx     = ctx

        if opts != None:

            self.pages = self.getTotalPages(total_items=len(opts))
            options    = [dis.SelectOption(label=opts[x][0],value=opts[x][1]) for x in range(0,23)]
            options.append(dis.SelectOption(label='Next',value=1))
            options.append(dis.SelectOption(label='Back',value=-1))

        super().__init__(placeholder='Select a character to display.', min_values=1, max_values=DROPDOWN_ITME_LIMIT, options=options)

    async def getPage(self,
                      page: int):
        pass

    async def callback(self,
                       interaction: dis.Interaction):

        if self.values[0] == '1':
            opts = self.choices[1:24]

            new_view = DropdownView(ctx=self.ctx,
                                    type = DropDownTypeEnum.SHOW,
                                    options=opts)

            await interaction.response.edit_message(view=new_view)

        elif self.values[0] == '-1':#-1 in self.values:

            #self.values = []
            init_list = [dis.SelectOption(label=self.choices[x][0],value=self.choices[x][1]) for x in range(0,12)]
            init_list.append(dis.SelectOption(label='Next',value=1))
            self._underlying.options = init_list
            self._underlying.options = []

            #for x in init_list:
            #    self.append_option(x)
            #self.options = init_list
            #super().__init__(placeholder='Select a character to display.', min_values=1, max_values=DROPDOWN_ITME_LIMIT, options=init_list)
            await interaction.response.edit_message(view=self.view)

        elif self.values != None:

            await interaction.response.send_message(f'You selected {self.values}')


class DropdownView(dis.ui.View):

    def __init__(self,
                 ctx     : dis.Interaction,
                 type    : DropDownTypeEnum,
                 options : Optional[list] = None):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(DropDownFactory.getDropDown(ctx=ctx,
                                                  type=type,
                                                  options=options))

class DropDownFactory:

    def getDropDown(ctx     : dis.Interaction,
                    type    : DropDownTypeEnum,
                    options : Optional[dict] = None) -> DynamicDropdown:
        """Returns an instance of a drop down type with appropriate options set.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of optional configs for this drop down.

           Output: dropdown - The appropriate dropdown type.
        """

        match type:

            case DropDownTypeEnum.SHOW:
                return ShowDropdown(ctx=ctx,
                                    opts=options)

            case DropDownTypeEnum.FACTORY:
                raise NotImplementedError

            case DropDownTypeEnum.DUNGEON:
                raise NotImplementedError

            case _:
                raise NotImplementedError

#Have user select which waifus they want to work in UI prior to jub creation.
#Create job as a callback option to the Lop and create job then
#Job updates DB and posts result to channel.