#Defines all unit tests for the files under the /ui folder.  This file must be
#defiend at a Package level that encapsulates all includes for the ui Pacakges.

#####  Imports  #####

from . import MockClasses as mc
from .ui import MenuPagination as mp
from .utilities import ProfileGenerator as pg
import discord as dis
from typing import Callable, Optional, Any
import unittest
from unittest import IsolatedAsyncioTestCase as iatc
from unittest.mock import patch
from unittest.mock import MagicMock





#####  Menu Pagination Class  #####

class TestMenuPagination(iatc):


    async def asyncSetUp(self):
        """Method called to prepare the test fixture. This is called after
           setUp(). This is called immediately before calling the test method;
           other than AssertionError or SkipTest, any exception raised by this
           method will be considered an error rather than a test failure. The
           default implementation does nothing.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.interaction = mc.MockInteraction()
        profile          = pg.getDefaultProfile()

        with patch('discord.ui.View') as mc.MockView, patch('discord.ui.Button') as mc.MockUiButton:

            self.uut = mp.MenuPagination(interaction = self.interaction,
                                         profiles    = [(profile.name, profile.id) for x in range(0,25)])

    async def testInteractionCheckPasses(self):
        """Verifies that the interaction_check function verifies only the post
           author is allowed to interact with menu buttons.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        result = await self.uut.interaction_check(interaction=self.interaction)

        self.assertTrue(result)

    async def testInteractionCheckFails(self):
        """Verifies that the interaction_check function verifies that users
           other than the author are not allowed to interact with menu buttons.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        uut_interaction = mc.MockInteraction()

        result = await self.uut.interaction_check(interaction=uut_interaction)

        self.assertFalse(result)

    async def testNavigatePassesOnOnePage(self):
        """Verifies that the navigate function works for a 1-page navigation.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        self.uut.index = 1

        await self.uut.navigate()

        self.assertTrue(True)

    async def testNavigatePassesOnManyPages(self):
        """Verifies that the navigate function works for a >1-page navigation.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        self.uut.index = 10

        await self.uut.navigate()

        self.assertTrue(True)

    async def testEditPagePasses(self):
        """Verifies that the editPage function works.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        uut_interaction = mc.MockInteraction()

        await self.uut.editPage(interaction=uut_interaction)

        self.assertTrue(True)

    async def testUpdateButtonsSinglePasses(self):
        """Verifies that the updateButtons function works with a single page.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.uut.total_pages = 1
        self.uut.index       = 1
        self.uut.updateButtons()

        self.assertTrue(self.uut.children[0].disabled)
        self.assertTrue(self.uut.children[1].disabled)
        self.assertTrue(self.uut.children[2].emoji.name == "⏮️")

    async def testUpdateButtonsSinglePassesWithDifferentIndex(self):
        """Verifies that the updateButtons function works with a single page
           but not an equal number of total pages.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.uut.total_pages = 1
        self.uut.index       = 0
        self.uut.updateButtons()

        self.assertFalse(self.uut.children[0].disabled)
        self.assertFalse(self.uut.children[1].disabled)
        self.assertTrue(self.uut.children[2].emoji.name == "⏭️")

    async def testOnTimeoutPasses(self):
        """Verifies that the on_timeout function works.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        await self.uut.on_timeout()

        self.assertTrue(True)

    async def testGetTotalPagesGivesValidValues(self):
        """Verifies that the getTotalPages function returns valid values of the
           correct type when given valid inputs.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        pages = self.uut.getTotalPages(total_items    = 0,
                                       items_per_page = 1)
        self.assertEqual(pages, 0)

        pages = self.uut.getTotalPages(total_items    = 1,
                                       items_per_page = 1)
        self.assertEqual(pages, 1)

        pages = self.uut.getTotalPages(total_items    = 10,
                                       items_per_page = 1)
        self.assertEqual(pages, 10)

        pages = self.uut.getTotalPages(total_items    = 100,
                                       items_per_page = 10)
        self.assertEqual(pages, 10)
