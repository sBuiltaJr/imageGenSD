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
import tests.CharactersTests as ct
import tests.DbTests as dt
import tests.ManagersTests as mt
import tests.UiTests as uit
import tests.UtilitiesTests as ut

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

    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=dt.TestMariadbIfc))

    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=mt.TestDailyEventManager))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=mt.TestQueueManager))
    
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ct.TestCharacterJobsClass))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ct.TestProfileGenerator))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ct.TestRarityClass))
    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ct.TestStatsClass))

    suite.addTest(unt.defaultTestLoader.loadTestsFromTestCase(testCaseClass=ut.TestJobFactory))
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
