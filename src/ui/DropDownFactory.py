#Encapsulates different modal types used in various jobs.


#####  Imports  #####
from ..db import MariadbIfc as mdb
from abc import ABC, abstractmethod
import base64 as b64
import discord as dis
from enum import IntEnum, verify, UNIQUE
import io
import src.utilities.JobFactory as jf
import src.utilities.StatsClass as sc
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

    ASSIGN_KEY_GEN = 0
    DUNGEON        = 1
    REMOVE_KEY_GEN = 2
    SHOW           = 3

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

#####  Drop Down Factory  Class  ####

class KeyGenDropdown(DynamicDropdown):


    def __init__(self,
                 choices  : list,
                 ctx      : dis.Interaction,
                 metadata : dict,
                 opts     : dict):
        """Creates a Dropdown with a slices of choices from a provided choice
           list, including adding navigation via menu options.

           Input : self - a pointer to the current object.
                   ctx - the Discord context to associate with this dropdown.
                   choices - an optional list of choices for the dropdown.
                   metadata - Where to make Post request, among other things.
                   options - Dropdown-specific options.

           Output : None.
        """

        self.db          = metadata['db_ifc']
        self.interaction = ctx
        self.metadata    = metadata
        self.offset      = 0 if 'count' not in opts else int(opts['count'])
        self.tier        = int(opts['tier']) if 'tier' in opts else 0
        self.limit_key   = f'limit_t{self.tier}'
        self.limit       = int(opts[self.limit_key])
        self.tier_count  = opts['total']
        self.tier_key    = f'tier_{self.tier}'
        self.tier_data   = opts['workers'][self.tier_key]

        self.trimByGatingCriteria(choices=choices)

        #Note: this check isn't part of an __init__ mixin because the Select
        #__init__ doesn't pass arguments through Super, and because the 'slice'
        #variable needs to be defined before Select's __init__ is called.
        if len(self.choices) <= DROPDOWN_ITEM_LIMIT_WITH_NAV :

            slice = range(0, len(self.choices))

        elif self.offset + DROPDOWN_ITEM_LIMIT_WITH_NAV <= len(self.choices) :

            slice = range(0, DROPDOWN_ITEM_LIMIT_WITH_NAV)

        else :

            slice = range(0, len(self.choices) - self.offset)

        options = [dis.SelectOption(label=self.choices[self.offset + x].name,value=self.choices[self.offset + x].id) for x in slice]
        options.append(dis.SelectOption(label='Next',   value=FORWARD_NAV_VALUE))
        options.append(dis.SelectOption(label='Back',   value=BACKWARD_NAV_VALUE))
        options.append(dis.SelectOption(label='Cancel', value=CANCEL_NAV_VALUE))

        select_limit = self.limit - self.tier_data['count']

        super().__init__(placeholder=f'Select at most {select_limit} characters to assign to key generation work for tier {self.tier}.', min_values=1, max_values=select_limit, options=options)

    async def callback(self,
                       interaction: dis.Interaction):
        """Process options selected by a user when they click off the dropdown.
           If needing to present new options, it will delete and replace the
           existing Discord post with a new version.

           Input : self - a pointer to the current object.
                   interaction - the Discord context for the dropdown.

           Output : None.
        """

        if str(CANCEL_NAV_VALUE) in self.values :

            message = await self.interaction.original_response()
            await message.edit(view=None)
            
        elif str(FORWARD_NAV_VALUE) in self.values or str(BACKWARD_NAV_VALUE) in self.values:

            opts          = {'total'        : self.tier_count,
                             self.limit_key : self.limit,
                             'tier'         : self.tier,
                             'workers'      : {self.tier_key : self.tier_data}}
            next          = self.offset + DROPDOWN_ITEM_LIMIT_WITH_NAV * int(self.values[0])
            opts['count'] = next if next >= 0 and next < len(self.choices) else self.offset

            new_view = DropdownView(ctx      = self.interaction,
                                    type     = DropDownTypeEnum.ASSIGN_KEY_GEN,
                                    metadata = self.metadata,
                                    choices  = self.choices,
                                    options  = opts)

            await interaction.response.edit_message(view=new_view)

        elif self.values != None :

            names = ""

            for choice in self.choices :

                #If only the select object also tracked choice labels.
                if choice.id in self.values :

                    names += choice.name + ", "

            result = self.db.assignKeyGenWork(count       = self.tier_count,
                                              profile_ids = self.values,
                                              tier        = self.tier,
                                              tier_data   = self.tier_data,
                                              user_id     = self.interaction.user.id)

            await interaction.response.edit_message(content=f"Assigned the chosen characters: {names}to keygen work in tier {self.tier + 1}!",view=None)

    #Note: this view gates by occupied == True and stats_avg >= range average
    def trimByGatingCriteria(self,
                             choices : Optional[list] = None,
                             opts    : Optional[dict] = None):

        self.choices = []

        for choice in choices:

            if not choice.occupied and choice.stats.average >= sc.getRangeAverageList()[self.tier] and choice not in self.choices :

                self.choices.append(choice)


class RemoveKeyGenDropdown(DynamicDropdown):


    def __init__(self,
                 choices  : list,
                 ctx      : dis.Interaction,
                 metadata : dict,
                 opts     : dict):
        """Creates a Dropdown with a slices of choices from a provided choice
           list, including adding navigation via menu options.

           Input : self - a pointer to the current object.
                   ctx - the Discord context to associate with this dropdown.
                   choices - an optional list of choices for the dropdown.
                   metadata - Where to make Post request, among other things.
                   options - Dropdown-specific options.

           Output : None.
        """

        self.choices     = choices
        self.db          = metadata['db_ifc']
        self.interaction = ctx
        self.metadata    = metadata
        self.tier        = int(opts['tier']) if 'tier' in opts else 0
        self.limit_key   = f'limit_t{self.tier}'
        self.limit       = int(opts[self.limit_key])
        self.tier_count  = opts['total']
        self.tier_key    = f'tier_{self.tier}'
        self.tier_data   = opts['workers'][self.tier_key]
        self.count       = int(self.tier_data['count']) #There can only ever be, at most, 5.

        options = [dis.SelectOption(label=self.choices[x].name,value=self.choices[x].id) for x in range (0, self.count)]
        options.append(dis.SelectOption(label='Cancel', value=CANCEL_NAV_VALUE))

        super().__init__(placeholder=f'Select at most {self.count} characters to remove.', min_values=1, max_values=self.count, options=options)

    async def callback(self,
                       interaction: dis.Interaction):
        """Process options selected by a user when they click off the dropdown.
           If asked to cancel the transaction, it will edit the message and
           delete the dropdown.

           Input : self - a pointer to the current object.
                   interaction - the Discord context for the dropdown.

           Output : None.
        """

        if str(CANCEL_NAV_VALUE) in self.values :

            message = await self.interaction.original_response()
            await message.edit(view=None)

        elif self.values != None :

            names = ""

            for choice in self.choices :

                #If only the select object also tracked choice labels.
                if choice.id in self.values :

                    names += choice.name + ", "

            result = self.db.removeKeyGenWork(count       = self.tier_count,
                                              profile_ids = self.values,
                                              tier        = self.tier,
                                              tier_data   = self.tier_data,
                                              user_id     = self.interaction.user.id)

            await interaction.response.edit_message(content=f"Removed the chosen characters: {names}from keygen work in tier {self.tier + 1}!",view=None)

    def trimByGatingCriteria(self,
                             choices : Optional[list] = None,
                             opts    : Optional[dict] = None):
        pass


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

        self.choices     = choices
        self.interaction = ctx
        self.metadata    = metadata
        self.offset      = 0 if opts == None else int(opts['count'])

        #Note: this check isn't part of an __init__ mixin because the Select
        #__init__ doesn't pass arguments through Super, and because the 'slice'
        #variable needs to be defined before Select's __init__ is called.
        if len(self.choices) <= DROPDOWN_ITEM_LIMIT_WITH_NAV :

            slice = range(0, len(self.choices))

        elif self.offset + DROPDOWN_ITEM_LIMIT_WITH_NAV <= len(self.choices) :

            slice = range(0, DROPDOWN_ITEM_LIMIT_WITH_NAV)

        else :

            slice = range(0, len(self.choices) - self.offset)

        options = [dis.SelectOption(label=self.choices[self.offset + x].name,value=self.choices[self.offset + x].id) for x in slice]
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
            opts['count'] = next if next >= 0 and next < len(self.choices) else self.offset

            new_view = DropdownView(ctx      = self.interaction,
                                    type     = DropDownTypeEnum.SHOW,
                                    metadata = self.metadata,
                                    choices  = self.choices,
                                    options  = opts)

            await interaction.response.edit_message(view=new_view)

        elif self.values[0] == str(CANCEL_NAV_VALUE) :

            message = await self.interaction.original_response()
            await message.edit(view=None)

        elif self.values != None:

            opts = {'id' : self.values[0]}

            job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.SHOWPROFILE,
                                       ctx     = self.interaction,
                                       options = opts)
            result = self.metadata['queue'].add(metadata = self.metadata,
                                                job      = job)
            await interaction.response.edit_message(content=result)

    def trimByGatingCriteria(self,
                             choices : Optional[list] = None,
                             opts    : Optional[dict] = None):
        pass

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
        self.interaction = ctx

        super().__init__(timeout=100)

        self.add_item(DropDownFactory.getDropDown(choices  = choices,
                                                  ctx      = ctx,
                                                  type     = type,
                                                  metadata = metadata,
                                                  options  = options))

    async def on_timeout(self):
        """Handles the timeout interaction inherent to discord interactions.

           Input : self - a pointer to the current object.

           Output : None.
        """
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    async def interaction_check(self,
                                interaction : dis.Interaction) -> bool:
        """Validates an interaction to ensure the message author is the only
           person attempting to navigate through the pages.

           Input : self - a pointer to the current object.
                   interaction - the interaction spawning this object.

           Output : bool - True if the author sent this interaction.
        """

        if interaction.user == self.interaction.user:

            return True

        else:

            emb = dis.Embed(description = f"Only the author of the command can perform this action.",
                            color       = 16711680)

            await interaction.response.send_message(embed=emb, ephemeral=True, delete_after=9.0)
            return False

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

            case DropDownTypeEnum.ASSIGN_KEY_GEN:
                return KeyGenDropdown(choices  = choices,
                                      ctx      = ctx,
                                      metadata = metadata,
                                      opts     = options)

            case DropDownTypeEnum.REMOVE_KEY_GEN:
                return RemoveKeyGenDropdown(choices  = choices,
                                            ctx      = ctx,
                                            metadata = metadata,
                                            opts     = options)

            case DropDownTypeEnum.DUNGEON:
                raise NotImplementedError

            case _:
                raise NotImplementedError