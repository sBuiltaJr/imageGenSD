#Encapsulates the-specific featuers of the Remove KeyGen Dropdown UI type.


#####  Imports  #####
import discord as dis
import src.characters.StatsClass as sc
import src.ui.DropDownFactory as ddf
import src.ui.DynamicDropdown as dd
from typing import Optional

#####  Remove Key Gen Drop Down Class  ####

class RemoveKeyGenDropdown(dd.DynamicDropdown):


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
        self.ID          = 0
        self.interaction = ctx
        self.metadata    = metadata
        self.NAME        = 1
        self.tier        = int(opts['tier']) if 'tier' in opts else 0
        self.count       = opts['active_workers'] #There can only ever be, at most, 5.

        options = [dis.SelectOption(label=self.choices[x][self.NAME],value=self.choices[x][self.ID]) for x in range (0, self.count)]
        options.append(dis.SelectOption(label='Cancel', value=ddf.CANCEL_NAV_VALUE))

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

        if str(ddf.CANCEL_NAV_VALUE) in self.values :

            self.db.putDropdown(state   = False,
                                user_id = self.interaction.user.id)
            message = await self.interaction.original_response()
            await message.edit(view=None)

        elif self.values != None :

            names = ""

            for choice in self.choices :

                #If only the select object also tracked choice labels.
                if choice[self.ID] in self.values :

                    names += choice[self.NAME] + ", "

            result = self.db.removeKeyGenWork(profile_ids = self.values,
                                              tier        = self.tier,
                                              user_id     = self.interaction.user.id,
                                              workers     = self.choices)

            self.db.putDropdown(state   = False,
                                user_id = self.interaction.user.id)

            await interaction.response.edit_message(content=f"Removed the chosen characters: {names}from keygen work in tier {self.tier + 1}!",view=None)

    def trimByGatingCriteria(self,
                             choices : Optional[list] = None,
                             opts    : Optional[dict] = None):
        pass
