#Creates the Discord class for the IGSD bot and passes it to the function
#definition class for initialization and connection to Discord.

#####  Imports  #####

import asyncio as asy
import discord as dis
from discord import app_commands as dac
import logging as log

#####  Package Classes  #####

class Client(dis.Client):
    def __init__(self, *, intents: dis.Intents):
        """This command copies the global command set to a given Guild instance.

            Input  : self - a reference to the current object.
                     intents - what Discord intents are required to run the bot.

            Output : None
        """

        self.dis_log = log.getLogger('discord')
        self.dis_log.debug(f"Intents are: {intents}")

        super().__init__(intents=intents)
        self.tree = dac.CommandTree(self)

    async def setup_hook(self):
        """Copies the global command set to a given Guild instance.

            Input  : self - a reference to the current object.

            Output : None
        """

        #Replies should be managed in a separate task to allow the main UI to
        #always be responsive, and allow the backend to process work independent
        #of message posting.  It's more efficent and better separated.
        self.loop = asy.get_running_loop()

        self.dis_log.debug(f"Syncing Guild Tree to Global.")
        await self.tree.sync()

    def getLoop(self):
        """Returns a reference to this client's asyncio event loop.

            Input  : self - a reference to the current object.

            Output : loop - the client's event loop.
        """

        return self.loop;


intents = dis.Intents.default()
client  = Client(intents=intents)