#Defines all unit tests for the files under the /utilities folder.  This file
#must be defiend at a Package level that encapsulates all includes for the
#utilities Pacakges.

#####  Imports  #####

from . import MockClasses as mc
from .utilities import JobFactory as jf
from .utilities import NameRandomizer as nr
from .utilities import ProfileGenerator as pg
from .utilities import RarityClass as rc
from .utilities import StatsClass as sc
from .utilities import TagRandomizer as tr
import discord as dis
import json
import pathlib as pl
import re
import requests as req
from typing import Callable, Optional, Any
import unittest
from unittest import IsolatedAsyncioTestCase as iatc
from unittest.mock import patch
from unittest.mock import MagicMock

#####  Menu Pagination Class  #####

class TestJobFactory(iatc):


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
        self.web_url     = "http://127.0.0.1:7860/"

    def testJobFactoryRaisesErrorOnBadArgs(self):
        """A simple verification that the Job Factory class will throw the
           NotImplementedError if given a bad job type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        with self.assertRaises(NotImplementedError):
            job = jf.JobFactory.getJob(type=-1, ctx=self.interaction)

    async def testRunGenerateJobFlow(self):
        """Verifies that the GenerateJob object returned from the Job Factory
           can perform all its necessary job functions.  This could be broken
           into multiple UTs once the UT code is refactored.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        opts = {
                'cfg_scale' : 1.0,
                'height'    : 256,
                'n_prompt'  : "bad",
                'prompt'    : "good",
                'random'    : True,
                'sampler'   : "Euler a",
                'seed'      : -1,
                'steps'     : 10,
                'tag_cnt'   : 0,
                'width'     : 256
        }

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        job = jf.JobFactory.getJob(type=jf.JobTypeEnum.GENERATE,
                                   ctx=self.interaction,
                                   options=opts)
        self.assertNotEqual(job, None)

        mock_tag_src = mc.MockTagSource()
        job.doRandomize(tag_src=mock_tag_src)
        self.assertEqual(job.post_data['tags_added'], 2)

        req.post              = MagicMock()
        req.post.return_value = mc.MockResult()

        job.doWork(web_url=self.web_url)
        self.assertNotEqual(job.result, None)

        metadata = {'ctx' : self.interaction}

        await job.post(metadata=metadata)
        self.assertTrue(True)

    async def testRunRollJobFlow(self):
        """Verifies that the RollJob object returned from the Job Factory can
           perform all its necessary job functions.  This could be broken into
           multiple UTs once the UT code is refactored.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        opts = {
                'prompt'    : "good",
                'random'    : True,
                'seed'      : -1
        }

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        job = jf.JobFactory.getJob(type=jf.JobTypeEnum.ROLL,
                                   ctx=self.interaction,
                                   options=opts)
        self.assertNotEqual(job, None)

        mock_tag_src = mc.MockTagSource()
        job.doRandomize(tag_src=mock_tag_src)
        self.assertEqual(job.post_data['tags_added'], 2)

        req.post              = MagicMock()
        req.post.return_value = mc.MockResult()

        job.doWork(web_url=self.web_url)
        self.assertNotEqual(job.result, None)

        metadata    = {'ctx'    : self.interaction,
                       'db_ifc' : mc.MockDbInterface()}
        job.profile = pg.getDefaultProfile()

        await job.post(metadata=metadata)
        self.assertTrue(True)

    async def testRunShowProfileJobFlow(self):
        """Verifies that the ShowProfileJob object returned from the Job
           Factory can perform all its necessary job functions.  This could be
           broken into multiple UTs once the UT code is refactored.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        opts = {'id' : mc.DEFAULT_PROFILE_ID}

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        job = jf.JobFactory.getJob(type=jf.JobTypeEnum.SHOWPROFILE,
                                   ctx=self.interaction,
                                   options=opts)
        self.assertNotEqual(job, None)

        metadata = {'ctx'    : self.interaction,
                    'db_ifc' : mc.MockDbInterface()}

        await job.post(metadata=metadata)
        self.assertTrue(True)

    async def testRunShowProfileJobFlowNoProfile(self):
        """Verifies that the ShowProfileJob object returned from the Job
           Factory will follow the error path if the request profile isn't
           found.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        opts = {'id' : 1}

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        job = jf.JobFactory.getJob(type=jf.JobTypeEnum.SHOWPROFILE,
                                   ctx=self.interaction,
                                   options=opts)
        self.assertNotEqual(job, None)

        metadata    = {'ctx'    : self.interaction,
                       'db_ifc' : mc.MockDbInterface()}
        job.id = 1

        await job.post(metadata=metadata)
        self.assertTrue(True)

    async def testRunGetJobFlow(self):
        """Verifies that the GetJob object returned from the Job Factory can
           perform all its necessary job functions.  This could be broken into
           multiple UTs once the UT code is refactored.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        job = jf.JobFactory.getJob(type=jf.JobTypeEnum.TESTGET,
                                   ctx=self.interaction)
        self.assertNotEqual(job, None)

        req.post              = MagicMock()
        req.post.return_value = mc.MockResult()

        job.doWork(web_url=self.web_url)
        self.assertNotEqual(job.result, None)

        metadata    = {'ctx'    : self.interaction}

        await job.post(metadata=metadata)
        self.assertTrue(True)

    async def testRunTestPostJobFlow(self):
        """Verifies that the TestPostJob object returned from the Job Factory
           can perform all its necessary job functions.  This could be broken
           into multiple UTs once the UT code is refactored.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        job = jf.JobFactory.getJob(type=jf.JobTypeEnum.TESTPOST,
                                   ctx=self.interaction)
        self.assertNotEqual(job, None)

        mock_tag_src = mc.MockTagSource()
        job.doRandomize(tag_src=mock_tag_src)
        self.assertEqual(job.post_data['tags_added'], "")

        req.post              = MagicMock()
        req.post.return_value = mc.MockResult()

        job.doWork(web_url=self.web_url)
        self.assertNotEqual(job.result, None)

        metadata = {'ctx' : self.interaction}

        await job.post(metadata=metadata)
        self.assertTrue(True)

    async def testRunTestRollJobFlow(self):
        """Verifies that the TestRollJob object returned from the Job Factory
           can perform all its necessary job functions.  This could be broken
           into multiple UTs once the UT code is refactored.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        job = jf.JobFactory.getJob(type=jf.JobTypeEnum.TESTROLL,
                                   ctx=self.interaction)
        self.assertNotEqual(job, None)

        req.post              = MagicMock()
        req.post.return_value = mc.MockResult()

        job.doWork(web_url=self.web_url)
        self.assertNotEqual(job.result, None)

        metadata    = {'ctx'    : self.interaction}

        await job.post(metadata=metadata)
        self.assertTrue(True)

    async def testRunTestShowProfileJobFlow(self):
        """Verifies that the TestShowProfileJob object returned from the Job
           Factory can perform all its necessary job functions.  This could be
           broken into multiple UTs once the UT code is refactored.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        job = jf.JobFactory.getJob(type=jf.JobTypeEnum.TESTSHOW,
                                   ctx=self.interaction)
        self.assertNotEqual(job, None)

        metadata = {'ctx'    : self.interaction,
                    'db_ifc' : mc.MockDbInterface()}

        await job.post(metadata=metadata)
        self.assertTrue(True)


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

        profile = pg.Profile(opts=pg.getDefaultOptions())

        self.assertEqual(profile.name, "Default Sally")

    def testProfileGeneratorBuildsWithParams(self):
        """A simple verification that the Profile Geneartor class will build
           correctly if given valid inputs and all optional parameters.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        profile = pg.Profile(opts=pg.getMascotOptions())

        self.assertNotEqual(profile, None)

    def testGetDefaultJobData(self):
        """Verifies that the getDefaultJobData function returns valid values of
           the correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        profile = pg.getDefaultJobData()

        self.assertNotEqual(profile, None)
        self.assertTrue(isinstance(profile, dict))

    def testGetDefaultProfile(self):
        """Verifies that the getDefaultProfile function returns valid values of
           the correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        profile = pg.getDefaultProfile()

        self.assertNotEqual(profile, None)
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

        self.assertNotEqual(rarity, None)

#####  Stats Class  #####

class TestStatsClass(unittest.TestCase):

    def testGetStatsList(self):
        """Verifies that the getStatsList function returns valid values of the
           correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        for rarity in rc.RarityList:

            stats = sc.Stats(rarity = rarity,
                             opts   = sc.getDefaultOptions())

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

           range = sc.getStatRange(rarity = rarity)

           self.assertTrue(isinstance(range, tuple))
           self.assertTrue(isinstance(range[0], int))
           self.assertTrue(isinstance(range[1], int))
           self.assertLess(range[0], range[1])

    def testGetValidDescription(self):
        """Verifies that the GetValidDescription function returns valid values
           for all possible values of the rarity class Enum.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        for rarity in rc.RarityList:

           range = sc.getDescription(rarity = rarity)

           self.assertTrue(isinstance(range, str))

    def testStatsClassBuildsBasic(self):
        """A simple verification that the Stats class will build correctly if
           given valid inputs.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        for rarity in rc.RarityList:

            stats = sc.Stats(rarity = rarity,
                             opts   = sc.getDefaultOptions())
            self.assertTrue(True)

    def testStatsClassBuildsWithParams(self):
        """A simple verification that the Stats class will build correctly if
           given valid inputs and additional stat parameters.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        for rarity in rc.RarityList:

            opts   = sc.getDefaultOptions()
            opts.update((x,1) for x in iter(opts))

            stats = sc.Stats(rarity = rarity,
                             opts   = opts)
            self.assertTrue(True)


#####  Tag Randomizer Class  #####

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

        self.uut = tr.TagRandomizer(opts=self.options)

    def testTagRandomizerBuilds(self):
        """A simple verification that the Tag Randomizer class will build
           correctly if given valid inputs.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.assertNotEqual(self.uut, None)

    def testGetRandomTags(self):
        """Verifies that the getRandomTags function returns valid values of the
           correct type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        random_tags, tag_cnt = self.uut.getRandomTags()

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

        random_tags, tag_cnt = self.uut.getRandomTags(exact=10)

        self.assertEqual(tag_cnt, 10)

        for tag in random_tags:

            self.assertTrue(re.findall(r'\w+', tag, re.UNICODE) != None)
            self.assertTrue(isinstance(tag, str))