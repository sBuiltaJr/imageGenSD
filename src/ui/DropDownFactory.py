#Encapsulates different modal types used in various jobs.


#####  Imports  #####

import discord as dis
from enum import IntEnum, verify, UNIQUE
import src.ui.DynamicDropdown as dd
import src.ui.AssignKeyGenDropdown as akgd
import src.ui.RemoveKeyGenDropdown as rkgd
import src.ui.ShowDropdown as shd
from typing import Optional

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

    ASSIGN_KEY_GEN     = 0
    ASSIGN_WORK_TARGET = 1
    ASSIGN_WORKERS     = 2
    DUNGEON            = 3
    REMOVE_KEY_GEN     = 4
    REMOVE_WORKERS     = 5
    SHOW               = 6

#####  Drop Down Factory Class  ####

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
        self.db          = metadata['db_ifc']

        #This is fine for now since users aren't allowed to control the
        #dropdown enum provided to the function.
        self.db.putDropdown(state   = True,
                            user_id = self.interaction.user.id)

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

        self.db.putDropdown(state   = False,
                            user_id = self.interaction.user.id)
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
                    options  : Optional[dict] = None) -> dd.DynamicDropdown:
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

            case DropDownTypeEnum.ASSIGN_KEY_GEN:
                return akgd.AssignKeyGenDropdown(choices  = choices,
                                                 ctx      = ctx,
                                                 metadata = metadata,
                                                 opts     = options)

            case DropDownTypeEnum.ASSIGN_WORK_TARGET:
                return AssignWorkTargetDropdown(choices  = choices,
                                                ctx      = ctx,
                                                metadata = metadata,
                                                opts     = options)

            case DropDownTypeEnum.ASSIGN_WORKERS:
                return AssignWorkersDropdown(choices  = choices,
                                             ctx      = ctx,
                                             metadata = metadata,
                                             opts     = options)

            case DropDownTypeEnum.DUNGEON:
                raise NotImplementedError

            case DropDownTypeEnum.REMOVE_KEY_GEN:
                return rkgd.RemoveKeyGenDropdown(choices  = choices,
                                                 ctx      = ctx,
                                                 metadata = metadata,
                                                 opts     = options)

            case DropDownTypeEnum.REMOVE_WORKERS:
                return RemoveWorkersDropdown(choices  = choices,
                                             ctx      = ctx,
                                             metadata = metadata,
                                             opts     = options)

            case DropDownTypeEnum.SHOW:
                return shd.ShowDropdown(choices  = choices,
                                        ctx      = ctx,
                                        metadata = metadata,
                                        opts     = options)

            case _:
                raise NotImplementedError

#Add a 'recommend' option to fill slots
#Add an auto-assign for everything.
#Just creating a DDF for each kind of team and work.