#Defines all unit tests for the files under the /utilities folder.  This file
#must be defiend at a Package level that encapsulates all includes for the
#utilities Pacakges.

#####  Imports  #####

from .utilities import NameRandomizer as nr
from .utilities import ProfileGenerator as pg
from .utilities import RarityClass as rc
from .utilities import StatsClass as sc
from .utilities import TagRandomizer as tr
import json
import pathlib as pl
import re
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock


#####  Name Randomizer Class  #####

class TestNameRandomizer(unittest.TestCase):


    def setUp(self):
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
        cfg_path  = pl.Path('src/config/config.json')
        dict_path = ["","",""]

        with open(cfg_path.absolute()) as json_file:
            params = json.load(json_file)

        dict_path[0] = pl.Path(params['profile_opts']['fn_dict_path'])
        dict_path[1] = pl.Path(params['profile_opts']['ln_dict_path'])

        params['profile_opts']['fn_dict_path']   = dict_path[0].absolute()
        params['profile_opts']['ln_dict_path']   = dict_path[1].absolute()

        params['profile_opts']['fn_dict_size'] = sum(1 for line in open(params['profile_opts']['fn_dict_path']))
        params['profile_opts']['ln_dict_size'] = sum(1 for line in open(params['profile_opts']['ln_dict_path']))

        if int(params['profile_opts']['fn_dict_size']) <= 0 or \
           int(params['profile_opts']['ln_dict_size']) <= 0:
            raise IndexError

        options = { 'fn_dict_path' : params['profile_opts']['fn_dict_path'],
                    'fn_dict_size' : params['profile_opts']['fn_dict_size'],
                    'ln_dict_path' : params['profile_opts']['ln_dict_path'],
                    'ln_dict_size' : params['profile_opts']['ln_dict_size'],
                  }
        nr.init(options=options)


    def testGetRandomNames(self):
        """Verifies that the getRandomName function returns valid values of the
           correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        name   = nr.getRandomName()
        parts  = re.findall(r'\w+', name, re.UNICODE)

        self.assertTrue(isinstance(name, str))
        self.assertEqual(len(parts), 2)


#####  Profile Generator Class  #####

class TestProfileGenerator(unittest.TestCase):

    def testProfileGeneratorBuildsBasic(self):
        """A simple verification that the Profile Geneartor class will build
           correctly if given valid inputs.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"
        owner                         = 1234567890

        profile = pg.Profile(owner=owner)

        self.assertEqual(profile.name, "Default Sally")

    def testProfileGeneratorBuildsWithParams(self):
        """A simple verification that the Profile Geneartor class will build
           correctly if given valid inputs and all optional parameters.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        rarity  = rc.Rarity().generateRarity()
        profile = pg.Profile(owner    = 1234567890,
                             affinity = 1,
                             battles  = 1,
                             creator  = 1,
                             desc     = "Default Description",
                             exp      = 1,
                             favorite = 1,
                             history  = {},
                             id       = 1,
                             img_id   = 1,
                             info     = {},
                             level    = 1,
                             losses   = 1,
                             missions = 1,
                             name     = "Default Sally",
                             rarity   = rarity,
                             stats    = sc.Stats(rarity),
                             wins     = 1)

        self.assertTrue(True)

    def testGetDefaultJobData(self):
        """Verifies that the getDefaultJobData function returns valid values of
           the correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        profile = pg.getDefaultJobData()

        self.assertTrue(isinstance(profile, dict))

    def testGetDefaultProfile(self):
        """Verifies that the getDefaultProfile function returns valid values of
           the correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        profile = pg.getDefaultProfile()

        self.assertTrue(isinstance(profile, pg.Profile))

#####  Rarity Class  #####

class TestRarityClass(unittest.TestCase):

    def testGenerateRarity(self):
        """Verifies that the generateRarity function returns valid values of
           the correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        rarity = rc.Rarity()

        value = rarity.generateRarity()

        self.assertIn(value, rc.RarityList)

    def testRarityClassBuilds(self):
        """A simple verification that the Rarity class will build correctly if
           given valid inputs.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        rarity = rc.Rarity()

        self.assertTrue(True)

#####  Stats Class  #####

class TestStatsClass(unittest.TestCase):

    def testGetStatsList(self):
        """Verifies that the getStatsList function returns valid values of the
           correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        for rarity in rc.RarityList:

            stats = sc.Stats(rarity)

            range = stats.getStatsList()

            for stat in range:

                self.assertTrue(isinstance(stat, int))
                self.assertGreaterEqual(stat, sc.getStatRange(rarity)[0])
                self.assertLessEqual(stat, sc.getStatRange(rarity)[1])

    def testGetValidStatRange(self):
        """Verifies that the getStatRange function returns valid values for all
           possible values of the rarity class Enum.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        for rarity in rc.RarityList:

           range = sc.getStatRange(rarity)
           self.assertTrue(isinstance(range, tuple))
           self.assertTrue(isinstance(range[0], int))
           self.assertTrue(isinstance(range[1], int))
           self.assertLess(range[0], range[1])

    def testGetValidDescription(self):
        """Verifies that the GetValidDescriptiog function returns valid values
           for all possible values of the rarity class Enum.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        for rarity in rc.RarityList:

           range = sc.getDescription(rarity)
           self.assertTrue(isinstance(range, str))

    def testStatsClassBuildsBasic(self):
        """A simple verification that the Stats class will build correctly if
           given valid inputs.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        for rarity in rc.RarityList:

            stats = sc.Stats(rarity)
            self.assertTrue(True)

    def testStatsClassBuildsWithParams(self):
        """A simple verification that the Stats class will build correctly if
           given valid inputs and additional stat parameters.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        for rarity in rc.RarityList:

            stats = sc.Stats(rarity    = rarity,
                             agility   = 1,
                             defense   = 1,
                             endurance = 1,
                             luck      = 1,
                             strength  = 1)
            self.assertTrue(True)

class TestTagRandomizer(unittest.TestCase):

    options = {}

    def setUp(self):
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
        cfg_path  = pl.Path('src/config/config.json')
        dict_path = [""]

        with open(cfg_path.absolute()) as json_file:
            params = json.load(json_file)

        dict_path[0] = pl.Path(params['tag_rng_opts']['rand_dict_path'])

        params['tag_rng_opts']['rand_dict_path'] = dict_path[0].absolute()

        params['tag_rng_opts']['dict_size'] = sum(1 for line in open(params['tag_rng_opts']['rand_dict_path']))

        if int(params['tag_rng_opts']['dict_size']) < int(params['tag_rng_opts']['max_rand_tag_cnt']) or \
           int(params['tag_rng_opts']['max_rand_tag_cnt']) <= int(params['tag_rng_opts']['min_rand_tag_cnt']):
            raise IndexError

        self.options = params['tag_rng_opts']

    def testTagRandomizerBuilds(self):
        """A simple verification that the Tag Randomizer class will build
           correctly if given valid inputs.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        uut = tr.TagRandomizer(opts=self.options)

        self.assertTrue(True)

    def testGetRandomTags(self):
        """Verifies that the getRandomTags function returns valid values of the
           correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        uut                  = tr.TagRandomizer(opts=self.options)
        random_tags, tag_cnt = uut.getRandomTags()

        self.assertGreaterEqual(tag_cnt, int(self.options['min_rand_tag_cnt']))
        self.assertLessEqual(tag_cnt, int(self.options['max_rand_tag_cnt']))
        self.assertNotEqual(tag_cnt, 0)

        for tag in random_tags:

            self.assertTrue(re.findall(r'\w+', tag, re.UNICODE) != None)
            self.assertTrue(isinstance(tag, str))


    def testGetRandomTagsExact(self):
        """Verifies that the getRandomTags function returns valid values of the
           correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        uut                  = tr.TagRandomizer(opts=self.options)
        random_tags, tag_cnt = uut.getRandomTags(exact=10)

        self.assertEqual(tag_cnt, 10)

        for tag in random_tags:

            self.assertTrue(re.findall(r'\w+', tag, re.UNICODE) != None)
            self.assertTrue(isinstance(tag, str))