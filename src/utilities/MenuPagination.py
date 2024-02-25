#Creates a paginated embed to allow a user to navigate a lsit of objects.

import discord as dis
from typing import Callable, Optional


class MenuPagination(dis.ui.View):
    """Creates a paginated view of a input list.  Allows the command author to
       navigate between individual pages or to the start/end of the page group.
    """

    def __init__(self, interaction: dis.Interaction, get_page: Callable):
        self.interaction                = interaction
        self.get_page                   = get_page
        self.total_pages: Optional[int] = None
        self.index                      = 1

        super().__init__(timeout=100)

    async def interaction_check(self,
                                interaction: dis.Interaction) -> bool:
        """Validates an interaction to ensure the message author is the only
           person attempting to navigate through the pages.

           Input : self - a pointer to the current object.
                   interaction - the interaction spawning this object.

           Output : bool - True if the author sent this interaction.
        """

        if interaction.user == self.interaction.user:

            return True

        else:

            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=16711680
            )

            await interaction.response.send_message(embed=emb, ephemeral=True, delete_after=9.0)
            return False

    async def navigate(self):
        """Moves between pages, if possible.

           Input : self - a pointer to the current object.

           Output : None.
        """
        emb, self.total_pages = await self.get_page(self.index)

        if self.total_pages == 1:

            await self.interaction.response.send_message(embed=emb)

        elif self.total_pages > 1:

            self.updateButtons()
            await self.interaction.response.send_message(embed=emb, view=self)

    async def editPage(self,
                       interaction: dis.Interaction):
        """Moves between pages, if possible.

           Input : self - a pointer to the current object.
                   interaction - the interaction spawning this object.

           Output : None.
        """
        emb, self.total_pages = await self.get_page(self.index)
        self.updateButtons()
        await interaction.response.edit_message(embed=emb, view=self)

    def updateButtons(self):
        """Updates the button state based on valid button interactions.

           Input : self - a pointer to the current object.

           Output : None.
        """
        if self.index > self.total_pages // 2:

            self.children[2].emoji = "⏮️"

        else:

            self.children[2].emoji = "⏭️"

        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == self.total_pages

    @dis.ui.button(emoji="◀️", style=dis.ButtonStyle.blurple)
    async def previous(self,
                       interaction: dis.Interaction,
                       button: dis.Button):
        """Handles the button interaction of moving back a page.

           Input : self - a pointer to the current object.
                   interaction - the interaction spawning this object.
                   button - the button pressed in this interaction.

           Output : None.
        """
        self.index -= 1
        await self.editPage(interaction)

    @dis.ui.button(emoji="▶️", style=dis.ButtonStyle.blurple)
    async def next(self,
                   interaction: dis.Interaction,
                   button: dis.Button):
        """Handles the button interaction of moving to the next page.

           Input : self - a pointer to the current object.
                   interaction - the interaction spawning this object.
                   button - the button pressed in this interaction.

           Output : None.
        """
        self.index += 1
        await self.editPage(interaction)

    @dis.ui.button(emoji="⏭️", style=dis.ButtonStyle.blurple)
    async def end(self,
                  interaction: dis.Interaction,
                  button: dis.Button):
        """Handles the button interaction of moving to the first or last page.

           Input : self - a pointer to the current object.
                   interaction - the interaction spawning this object.
                   button - the button pressed in this interaction.

           Output : None.
        """
        if self.index <= self.total_pages // 2:

            self.index = self.total_pages

        else:

            self.index = 1

        await self.editPage(interaction)

    async def on_timeout(self):
        """Handles the timeout interaction inherent to discord interactions.

           Input : self - a pointer to the current object.

           Output : None.
        """
        # remove buttons on timeout
        message = await self.interaction.original_response()
        await message.edit(view=None)

    @staticmethod
    def getTotalPages(total_items: int,
                      items_per_page: int) -> int:
        """Calculates the total number of pages for a given object.

           Input : total_items - the total number of items in the menu.
                   items_per_page - how many items to display on a page.

           Output : int - How many pages are required for this list.
        """
        return ((total_items - 1) // items_per_page) + 1