#Defines unit tests for the Stats Class.

#####  Imports  #####

import unittest as unt
from src import UtilitiesTests as ut

#####  Test Class  #####

def testUtilities():

    suite  = unt.TestSuite()
    result = unt.TestResult()
    runner = unt.TextTestRunner()

    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestNameRandomizer))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestProfileGenerator))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestRarityClass))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestStatsClass))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestTagRandomizer))

    print(runner.run(suite))

testUtilities()