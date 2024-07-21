#Encapsulates the-specific featuers of the Assign Work Target Dropdown UI type.


#####  Imports  #####
import discord as dis
import src.characters.StatsClass as sc
import src.ui.DropDownFactory as ddf
import src.ui.DynamicDropdown as dd
from typing import Optional

#####  Assign Key Gen Drop Down Class  ####

class AssignKeyGenDropdown(dd.DynamicDropdown):


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

        self.choices     = choices if choices else econ.getAllWorkTargetChoices(user=ctx.user.id)
        self.db          = metadata['db_ifc']
        self.interaction = ctx
        self.metadata    = metadata
        self.tier        = int(opts['tier']) if 'tier' in opts else 0

        slice = range(0, len(self.choices) - self.offset)

        options = [dis.SelectOption(label=self.choices[self.offset + x].name,value=self.choices[self.offset + x].id) for x in slice]
        options.insert(0, dis.SelectOption(label='Next',   value=ddf.FORWARD_NAV_VALUE))
        options.insert(0, dis.SelectOption(label='Back',   value=ddf.BACKWARD_NAV_VALUE))
        options.insert(0, dis.SelectOption(label='Cancel', value=ddf.CANCEL_NAV_VALUE))

        select_limit = self.limit - self.active_workers

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

        if str(ddf.CANCEL_NAV_VALUE) in self.values :

            self.db.putDropdown(state   = False,
                                user_id = self.interaction.user.id)
            message = await self.interaction.original_response()
            await message.edit(view=None)

        elif str(ddf.FORWARD_NAV_VALUE) in self.values or str(ddf.BACKWARD_NAV_VALUE) in self.values:

            opts = {'tier' : self.tier}
            next = 

            new_view = DropdownView(ctx      = self.interaction,
                                    type     = DropDownTypeEnum.ASSIGN_WORK_TARGET,
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

            result = self.db.assignKeyGenWork(count       = self.active_workers,
                                              profile_ids = self.values,
                                              tier        = self.tier,
                                              user_id     = self.interaction.user.id,
                                              workers     = self.workers)

            self.db.putDropdown(state   = False,
                                user_id = self.interaction.user.id)

            await interaction.response.edit_message(content=f"Assigned the chosen characters: {names}to keygen work in tier {self.tier + 1}!", view=None)

#econ obj with data and setters
#Only offer a 'save' button to users?  Only at end?
#Filter by 'best' in next update.