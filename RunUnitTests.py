#Defines the different unit test sets available for the IGSD project.  Notably,
#most files use relative includes, so the test framework needs to be in the
#same root package as IGSD main to allow pathing to work correctly (or at least
#no lower than /src).
#
#This has forced all test classes to be written into the /src folder.
#
#TODO: consider migrating IGSD main and /src all down a layer to allow for
#better UT separation, at least as much as unittest allows.

#####  Imports  #####

import coverage
import unittest as unt
#https://coverage.readthedocs.io/en/7.4.3/faq.html#q-why-do-the-bodies-of-functions-show-as-executed-but-the-def-lines-do-not
cov = coverage.Coverage()
cov.start()
from src import DbTests as dt
from src import ManagersTests as mt
from src import UiTests as uit
from src import UtilitiesTests as ut

#####  Test Class  #####

def testUtilities():
    """Performs setup for and runs all unit tests defined in the project.

       Input: N/A.

       Output: N/A.
    """

    suite  = unt.TestSuite()
    result = unt.TestResult()
    runner = unt.TextTestRunner()

    #TODO: convert name randomizer into an instantiated class to avoid mock destroying the package
    #for all tests post-mock.
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestNameRandomizer))

    #TODO: find a nice way to handle the cursor interface not having ways to
    #easily distinguish between different commands.
    #suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=dt.TestMariadbIfc))

    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=mt.TestDailyEventManager))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=mt.TestQueueManager))

    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestJobFactory))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestProfileGenerator))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestRarityClass))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestStatsClass))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestTagRandomizer))

    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=uit.TestMenuPagination))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=uit.TestDropdownFactory))

    print(runner.run(suite))


if __name__ == '__main__':
    testUtilities()
    cov.stop()
    cov.html_report(directory='covhtml')
    cov.save()
    cov.report()