#Defines all unit tests for the files for the main IGSD file.

#####  Imports  #####

#from discord import app_commands as dac
import tests.MockClasses as mc
import unittest
from unittest import IsolatedAsyncioTestCase as iatc
from unittest.mock import MagicMock
from unittest.mock import patch

with patch('discord.app_commands.CommandTree.command', new=mc.MockDecorator):
    with patch('discord.app_commands.checks.has_permissions', new=mc.MockDecorator):
        import imageGenSD as igsd

#####  Character Jobs Class  #####

class TestIgsdClass(iatc):

    async def testInitSucceedsWithGoodArguments(self):
        """Verifies that IGSD can be initialized given good arguments.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        await igsd.testshowprofile(interaction = mc.MockInteraction())

        self.assertEqual(True, True)