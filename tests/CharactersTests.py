#Defines all unit tests for the files under the /characters folder.  This file
#must be defiend at a Package level that encapsulates all includes for the
#characters Pacakges.

#####  Imports  #####

from . import MockClasses as mc
import json
import src.characters.CharacterJobs as cj
import src.characters.ProfileGenerator as pg
import src.characters.RarityClass as rc
import src.characters.StatsClass as sc
import src.utilities.NameRandomizer as nr
import statistics as stat
import unittest
from unittest import IsolatedAsyncioTestCase as iatc
from unittest.mock import MagicMock


#####  Character Jobs Class  #####

class TestCharacterJobsClass(unittest.TestCase):

    def testGetEmptyJobTypeList(self):
        """Verifies that the getEmptyJobTypeList function returns a valid
           values of empty job list type.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        empty = cj.CharacterJobTypeEnum.getEmptyJobTypeList()

        self.assertEqual(len(empty), len(cj.CharacterJobTypeEnum))
        
        for key in cj.CharacterJobTypeEnum:
            
            self.assertEqual(0, empty[key])

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

    def testGetStandardNameList(self):
        """Verifies that the getStandardNameList function returns the specific
           list of standard expected names for the rarity class.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        rarity_list = rc.RarityList.getStandardNameList()

        self.assertIn(rc.RarityList.COMMON,     rarity_list)
        self.assertIn(rc.RarityList.UNCOMMON,   rarity_list)
        self.assertIn(rc.RarityList.RARE,       rarity_list)
        self.assertIn(rc.RarityList.SUPER_RARE, rarity_list)
        self.assertIn(rc.RarityList.ULTRA_RARE, rarity_list)
        self.assertIn(rc.RarityList.LEGENDARY,  rarity_list)

    def testGetProbabilityList(self):
        """Verifies that the getProbabilityList function returns the specific
           list of standard probabilities for the rarity class.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        rarity_list = rc.RarityList.getProbabilityList()

        self.assertIn(0.65,   rarity_list)
        self.assertIn(0.25,   rarity_list)
        self.assertIn(0.0825, rarity_list)
        self.assertIn(0.0135, rarity_list)
        self.assertIn(0.0035, rarity_list)
        self.assertIn(0.0005, rarity_list)

    def testGetStandardValueList(self):
        """Verifies that the getStandardValueList function returns the specific
           list of standard rarity values for the rarity class.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        value_list = rc.RarityList.getStandardValueList()

        self.assertEqual(rc.RarityList.COMMON.value,     value_list[0])
        self.assertEqual(rc.RarityList.UNCOMMON.value,   value_list[1])
        self.assertEqual(rc.RarityList.RARE.value,       value_list[2])
        self.assertEqual(rc.RarityList.SUPER_RARE.value, value_list[3])
        self.assertEqual(rc.RarityList.ULTRA_RARE.value, value_list[4])
        self.assertEqual(rc.RarityList.LEGENDARY.value,  value_list[5])

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

            stats_range = stats.getStatsList()

            for stat in stats_range:

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

           stats_range = sc.getStatRange(rarity = rarity)

           self.assertTrue(isinstance(stats_range, tuple))
           self.assertTrue(isinstance(stats_range[0], int))
           self.assertTrue(isinstance(stats_range[1], int))
           self.assertLess(stats_range[0], stats_range[1])

    def testGetValidDescription(self):
        """Verifies that the GetValidDescription function returns valid values
           for all possible values of the rarity class Enum.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        for rarity in rc.RarityList:

           rarity_range = sc.getDescription(rarity = rarity)

           self.assertTrue(isinstance(rarity_range, str))

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

    def testStatsClassGetRangeAverageList(self):
        """Verifies that the getRangeAverageList function returns valid values
           for all possible values of the rarity class Enum.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        expected_averages = []

        for rarity in rc.RarityList.getStandardNameList():

            rarity_range = sc.getStatRange(rarity)
            expected_averages.append(stat.mean(rarity_range))

        averages = sc.getRangeAverageList()

        self.assertEqual(len(expected_averages), len(averages))

        for index in range(0, len(averages)) :

            self.assertAlmostEqual(averages[index], expected_averages[index], places=2)
