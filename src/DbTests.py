#Defines all unit tests for the files under the /db folder.  This file must be
#defiend at a Package level that encapsulates all includes for the utilities
#Pacakges.

#####  Imports  #####

from . import MockClasses as mc
from .db import MariadbIfc as mdb
from .utilities import ProfileGenerator as pg
import discord as dis
import json
import sys
#import mariadb
import pathlib as pl
from typing import Callable, Optional, Any
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock


#####  Daily Event Manager Class  #####

class TestMariadbIfc(unittest.TestCase):
    
    @patch('src.db.MariadbIfc.mariadb', new_callable=mc.MockDb)
    def setUp(self, tst):
        """Method called to prepare the test fixture. This is called
           immediately before calling the test method; other than
           AssertionError or SkipTest, any exception raised by this method will
           be considered an error rather than a test failure. The default
           implementation does nothing.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        #This section is intentionally written like the actual code in
        #imageGenSD.py.
        cfg_path = pl.Path('src/config/config.json')

        with open(cfg_path.absolute()) as json_file:
            params = json.load(json_file)

        mariadb      = mc.MockDb()
        self.options = params['db_opts']
        self.uut     = mdb.MariadbIfc.getInstance(options=self.options)

    def testGetInstanceNew(self):
        """Verifies that the getInstance function behaves correctly with valid
           input and a not-yet initialized instance of the singleton.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.uut.__instance = None
        instance            = self.uut.getInstance(options=self.options)

        self.assertNotEqual(instance, None)

    def testGetInstanceFromExisting(self):
        """Verifies that the getInstance function behaves correctly with valid
           input and an existing instance of the singleton.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        instance = self.uut.getInstance(options={})

        self.assertNotEqual(instance, None)

    def testDailyDoneWorks(self):
        """Verifies that the dailyDone function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        done = self.uut.dailyDone()

        self.assertFalse(done)

    def testGetImageWorks(self):
        """Verifies that the getImage function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        img = self.uut.getImage()

        self.assertNotEqual(img, "")

    def testGetProfileWorks(self):
        """Verifies that the getProfile function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        profile = self.uut.getProfile()

        self.assertNotEqual(profile, "")

    def testGetProfilesWorks(self):
        """Verifies that the getProfiles function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        profile = self.uut.getProfiles(user_id=170331989436661760)

        self.assertNotEqual(profile, "")

    def testResetDailyRollWorks(self):
        """Verifies that the resetDailyRoll function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.uut.resetDailyRoll()

        self.assertTrue(True)

    def testSaveRollWorks(self):
        """Verifies that the saveRoll function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.uut.saveRoll(info={},
                          profile=pg.getDefaultProfile())

        self.assertTrue(True)