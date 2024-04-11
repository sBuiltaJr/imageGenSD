#Encapsulates the-specific featuers of the Show Dropdown UI type.


#####  Imports  #####
import discord as dis
import src.characters.StatsClass as sc
import src.ui.DropDownFactory as ddf
import src.ui.DynamicDropdown as dd
import src.utilities.JobFactory as jf
from typing import Optional

class ShowDropdown(dd.DynamicDropdown):


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
        self.db          = metadata['db_ifc']
        self.interaction = ctx
        self.metadata    = metadata
        self.offset      = 0 if opts == None else int(opts['count'])

        #Note: this check isn't part of an __init__ mixin because the Select
        #__init__ doesn't pass arguments through Super, and because the 'slice'
        #variable needs to be defined before Select's __init__ is called.
        if len(self.choices) <= ddf.DROPDOWN_ITEM_LIMIT_WITH_NAV :

            slice = range(0, len(self.choices))

        elif self.offset + ddf.DROPDOWN_ITEM_LIMIT_WITH_NAV <= len(self.choices) :

            slice = range(0, ddf.DROPDOWN_ITEM_LIMIT_WITH_NAV)

        else :

            slice = range(0, len(self.choices) - self.offset)

        options = [dis.SelectOption(label=self.choices[self.offset + x].name,value=self.choices[self.offset + x].id) for x in slice]
        options.insert(0, dis.SelectOption(label='Next',   value=ddf.FORWARD_NAV_VALUE))
        options.insert(0, dis.SelectOption(label='Back',   value=ddf.BACKWARD_NAV_VALUE))
        options.insert(0, dis.SelectOption(label='Cancel', value=ddf.CANCEL_NAV_VALUE))

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

        if self.values[0] == str(ddf.FORWARD_NAV_VALUE) or self.values[0] == str(ddf.BACKWARD_NAV_VALUE) :

            opts           = {}
            next           = self.offset + ddf.DROPDOWN_ITEM_LIMIT_WITH_NAV * int(self.values[0])
            opts['count'] = next if next >= 0 and next < len(self.choices) else self.offset

            new_view = DropdownView(ctx      = self.interaction,
                                    type     = DropDownTypeEnum.SHOW,
                                    metadata = self.metadata,
                                    choices  = self.choices,
                                    options  = opts)

            await interaction.response.edit_message(view=new_view)

        elif self.values[0] == str(ddf.CANCEL_NAV_VALUE) :

            self.db.putDropdown(state   = False,
                                user_id = self.interaction.user.id)
            message = await self.interaction.original_response()
            await message.edit(view=None)

        elif self.values != None:

            opts = {'id' : self.values[0]}

            job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.SHOW_PROFILE,
                                       ctx     = self.interaction,
                                       options = opts)
            result = self.metadata['queue'].add(metadata = self.metadata,
                                                job      = job)
            await interaction.response.edit_message(content=result)

    def trimByGatingCriteria(self,
                             choices : Optional[list] = None,
                             opts    : Optional[dict] = None):
        pass