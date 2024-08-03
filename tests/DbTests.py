#Defines the unit tests for the files under the src/db folder.

#####  Imports  #####

import json
import sys
import pathlib as pl
import src.characters.ProfileGenerator as pg
import src.db.MariadbIfc as mdb
import src.characters.RarityClass as rc
import src.characters.CharacterJobs as cj
import mariadb
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import PropertyMock

#####  Mariadb Interface Class  #####

class TestMariadbIfc(unittest.TestCase):
    
    @patch('mariadb.connect')
    def setUp(self, patch):
        """Method called to prepare the test fixture. This is called
           immediately before calling the test method; other than
           AssertionError or SkipTest, any exception raised by this method will
           be considered an error rather than a test failure. The default
           implementation does nothing.

           Input: self  - Pointer to the current object instance.
                  patch - The mock patch of mariadb.connect.

           Output: none.
        """

        cfg_path = pl.Path('src/config/config.json')

        with open(cfg_path.absolute()) as json_file:
            params = json.load(json_file)

        self.options = params['db_opts']
        self.uut     = mdb.MariadbIfc.getInstance(options=self.options)
        self.patch   = patch
        self.cursor  = self.uut.con.cursor()

    @patch('mariadb.connect')
    def testGetInstanceNew(self, db_patch):
        """Verifies that the getInstance function behaves correctly with valid
           input and a not-yet initialized instance of the singleton.

           Input: self     - Pointer to the current object instance.
                  db_patch - The mock patch of mariadb.connect.

           Output: none.
        """
        with patch.object(mdb.MariadbIfc, '_MariadbIfc__instance', new_callable=PropertyMock) as ipatch:
            ipatch.return_value = None
            db_patch.reset_mock()

            instance = mdb.MariadbIfc.getInstance(options=self.options)

            self.assertNotEqual(instance, None)
            db_patch.assert_called_once()

    @patch('mariadb.connect')
    def testGetInstanceThenConstructor(self, db_patch):
        """Verifies that the getInstance function behaves correctly with valid
           input and a not-yet initialized instance of the singleton.

           Input: self     - Pointer to the current object instance.
                  db_patch - The mock patch of mariadb.connect.

           Output: none.
        """
        db_patch.reset_mock()

        instance = mdb.MariadbIfc(options=self.options)

        self.assertNotEqual(instance, None)
        db_patch.assert_not_called()

    @patch('mariadb.connect')
    def testGetInstanceFromExisting(self, db_patch):
        """Verifies that the getInstance function behaves correctly with valid
           input and an existing instance of the singleton.

            Input: self - Pointer to the current object instance.

            Output: none.
        """
        db_patch.reset_mock()

        instance = self.uut.getInstance(options={})

        self.assertNotEqual(instance, None)
        db_patch.assert_not_called()

    @patch('mariadb.connect')
    def testFaultOnConnectError(self, db_patch):
        """Verifies that the getInstance function behaves correctly when
           mariadb raises an error on connect.

           Input: self     - Pointer to the current object instance.
                  db_patch - The mock patch of mariadb.connect.

           Output: none.
        """
        db_patch.reset_mock()
        db_patch.side_effect = mariadb.Error

        with patch.object(mdb.MariadbIfc, '_MariadbIfc__instance', new_callable=PropertyMock) as ipatch:
            with self.assertRaises(PermissionError):
                ipatch.return_value = None

                instance = mdb.MariadbIfc.getInstance(options=self.options)

            db_patch.assert_called_once()

    @patch('mariadb.connect')
    def testFaultOnExecuteProgrammingError(self, db_patch):
        """Verifies that the getInstance function behaves correctly when
           mariadb raises an error on execute.

           Input: self     - Pointer to the current object instance.
                  db_patch - The mock patch of mariadb.connect.

           Output: none.
        """
        db_patch().cursor().execute.side_effect = mariadb.ProgrammingError
        db_patch.reset_mock()

        with patch.object(mdb.MariadbIfc, '_MariadbIfc__instance', new_callable=PropertyMock) as ipatch:
            with self.assertRaises(PermissionError):
                ipatch.return_value = None

                instance = mdb.MariadbIfc.getInstance(options=self.options)

            db_patch.assert_called_once()

    @patch('mariadb.connect')
    def testFaultOnExecuteOperationalError(self, db_patch):
        """Verifies that the getInstance function behaves correctly when
           mariadb raises an error on execute.

           Input: self     - Pointer to the current object instance.
                  db_patch - The mock patch of mariadb.connect.

           Output: none.
        """
        db_patch().cursor().execute.side_effect = mariadb.OperationalError
        db_patch.reset_mock()

        with patch.object(mdb.MariadbIfc, '_MariadbIfc__instance', new_callable=PropertyMock) as ipatch:
            with self.assertRaises(PermissionError):
                ipatch.return_value = None

                instance = mdb.MariadbIfc.getInstance(options=self.options)

            db_patch.assert_called_once()

    @patch('mariadb.connect')
    def testFaultOnExecuteGenericError(self, db_patch):
        """Verifies that the getInstance function behaves correctly when
           mariadb raises an error on execute.

           Input: self     - Pointer to the current object instance.
                  db_patch - The mock patch of mariadb.connect.

           Output: none.
        """
        db_patch().cursor().execute.side_effect = mariadb.Error
        db_patch.reset_mock()

        with patch.object(mdb.MariadbIfc, '_MariadbIfc__instance', new_callable=PropertyMock) as ipatch:
            with self.assertRaises(PermissionError):
                ipatch.return_value = None

                instance = mdb.MariadbIfc.getInstance(options=self.options)

            db_patch.assert_called_once()

    @patch('json.load')
    def testFaultOnFileNotFoundError(self, jl_patch):
        """Verifies that the getInstance function behaves correctly when
           db init errors on trying to get the mariadb commands

           Input: self     - Pointer to the current object instance.
                  pl_patch - The mock patch of json.load.

           Output: none.
        """
        jl_patch.side_effect = json.JSONDecodeError

        with patch.object(mdb.MariadbIfc, '_MariadbIfc__instance', new_callable=PropertyMock) as ipatch:
            with self.assertRaises(FileNotFoundError):
                ipatch.return_value = None

                instance = mdb.MariadbIfc.getInstance(options=self.options)

    def testAssignKeyGenWorkWorks(self):
        """Verifies that the assignKeyGenWork function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()

        self.uut.assignKeyGenWork(count       = 1,
                                  profile_ids = ["id"],
                                  tier        = 0,
                                  user_id     = 0,
                                  workers     = [{0: "id"}])

        self.assertEqual(self.cursor.execute.call_count, 2)

    def testCreateNewUser(self):
        """Verifies that the createNewUser function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchone.return_value = None

        result = self.uut.createNewUser(id = "new_id")

        self.cursor.execute.assert_called()
        self.assertNotEqual(self.cursor.execute.call_count, 1)
        self.assertTrue(result)

    def testCreateNewUserWithExistingUser(self):
        """Verifies that the createNewUser function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchone.return_value = "existing_user"

        result = self.uut.createNewUser(id = "existing_id")

        self.cursor.execute.assert_called_once()
        self.assertFalse(result)


    def testDailyDoneReturnsFalseWhenSet(self):
        """Verifies that the dailyDone function behaves correctly when the
           database returns a falsy value

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        daily_index = int(self.uut.cmds['user']['daily_index'])
        self.cursor.fetchone.return_value = {daily_index : False}

        done = self.uut.dailyDone()

        self.assertFalse(done)
        self.cursor.execute.assert_called()

    def testDailyDoneReturnsTrueWhenAvailable(self):
        """Verifies that the dailyDone function behaves correctly when the
           database returns a truthy value

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        daily_index = int(self.uut.cmds['user']['daily_index'])
        self.cursor.fetchone.return_value = {daily_index : True}

        done = self.uut.dailyDone()

        self.assertTrue(done)
        self.cursor.execute.assert_called()

    def testGetAssignParamsWorks(self):
        """Verifies that the getAssignParams function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchone.return_value = [0, 1, 2, 3, 4, 5, 6, 7]
        self.cursor.fetchall.return_value = "allocation";

        with patch.object(self.uut, 'mapQueryToKeyGenInfo') as map_mock:
            results = self.uut.getAssignParams(user_id = 0)

            self.assertEqual(self.cursor.fetchall.return_value,
                             map_mock.call_args[1]['query'])

            self.assertEqual(results["total"]       ,          0)
            self.assertEqual(results["current_tier"],          1)
            self.assertEqual(results["limit_t0"]    ,          2)
            self.assertEqual(results["limit_t1"]    ,          3)
            self.assertEqual(results["limit_t2"]    ,          4)
            self.assertEqual(results["limit_t3"]    ,          5)
            self.assertEqual(results["limit_t4"]    ,          6)
            self.assertEqual(results["limit_t5"]    ,          7)
            self.assertEqual(results["workers"]     , map_mock())

            self.assertEqual(self.cursor.execute.call_count, 2)

    def testGetDropdownWorks(self):
        """Verifies that the getDropdown function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchone.return_value = {0 : True}

        results = self.uut.getDropdown(user_id = 0)

        self.assertTrue(results)
        self.cursor.execute.assert_called_once()

    def testGetImageReturnsImageFromPictureId(self):
        """Verifies that the getImage function behaves correctly with valid
           input. If picture id is provided, it should return the picture data

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        pic_index = int(self.uut.cmds['prof']['pic_id_index'])
        self.cursor.fetchone.return_value = {0         : "success",
                                             pic_index : "id"}
        self.cursor.execute.reset_mock()

        img = self.uut.getImage(picture_id = "id")

        self.cursor.execute.assert_called_once()
        self.assertEqual(img, "success")

    def testGetImageReturnsEmptyFromNoneWithPictureId(self):
        """Verifies that the getImage function behaves correctly with valid
           input. If picture id is provided, it should return the picture data
           If the database returns None, the empty string should be returned

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.fetchone.return_value = None
        self.cursor.execute.reset_mock()

        img = self.uut.getImage(picture_id = "invalid_id")

        self.cursor.execute.assert_called_once()
        self.assertEqual(img, "")

    def testGetImageReturnsImageGettingPictureId(self):
        """Verifies that the getImage function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        pic_index = int(self.uut.cmds['prof']['pic_id_index'])
        self.cursor.fetchone.return_value = {0         : "success",
                                             pic_index : "id"}
        self.cursor.execute.reset_mock()

        img = self.uut.getImage(profile_id = "id")

        self.assertEqual(self.cursor.execute.call_count, 2)
        self.assertEqual(img, "success")

    def testGetImageReturnsEmptyWithInvalidProfile(self):
        """Verifies that the getImage function behaves correctly with valid
           input. If the DB doesn't find a profile matching the provided id, it
           should return an empty string

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.fetchone.return_value = None
        self.cursor.execute.reset_mock()

        img = self.uut.getImage(profile_id = "invalid_id")

        self.cursor.execute.assert_called_once()
        self.assertEqual(img, "")

    def testGetProfileReturnsProfileWithValidId(self):
        """Verifies that the getProfile function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.fetchone.return_value = "Profile"
        self.cursor.execute.reset_mock()

        with patch.object(self.uut, 'mapQueryToProfile') as map_mock:
            map_mock.return_value = "valid_profile"
            profile = self.uut.getProfile(id = "id")

            self.cursor.execute.assert_called_once()
            self.assertEqual(profile, "valid_profile")
            self.assertEqual(self.cursor.fetchone.return_value,
                             map_mock.call_args[1]['query'])

    def testGetProfileReturnsNoneWithInvalidId(self):
        """Verifies that the getProfile function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.fetchone.return_value = None
        self.cursor.execute.reset_mock()

        profile = self.uut.getProfile(id = "invalid_id")

        self.cursor.execute.assert_called_once()
        self.assertEqual(profile, None)


    def testGetProfilesWorks(self):
        """Verifies that the getProfiles function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.__iter__ = MagicMock(return_value=iter([1, 2, 3]))

        with patch.object(self.uut, "mapQueryToProfile") as map_mock:
            profile = self.uut.getProfiles(name    = "name",
                                           rarity  = [],
                                           user_id = 0)

            self.assertEqual(len(profile), 3)
            self.assertEqual(map_mock.call_count, 3)
            self.assertEqual(map_mock.call_args_list[0][1]['query'], 1)
            self.assertEqual(map_mock.call_args_list[1][1]['query'], 2)
            self.assertEqual(map_mock.call_args_list[2][1]['query'], 3)

    def testGetKeyGenParamsWorks(self):
        """Verifies that the getAssignParams function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchone.return_value = [0, 1, 2, 3, 4, 5, 6, 7]
        self.cursor.fetchall.return_value = "allocation";

        with patch.object(self.uut, 'mapQueryToKeyGenInfo') as map_mock:
            results = self.uut.getKeyGenParams(user_id = 0)

            self.assertEqual(self.cursor.fetchall.return_value,
                             map_mock.call_args[1]['query'])

            self.assertEqual(results["total"]       ,          0)
            self.assertEqual(results["current_tier"],          1)
            self.assertEqual(results["limit_t0"]    ,          2)
            self.assertEqual(results["limit_t1"]    ,          3)
            self.assertEqual(results["limit_t2"]    ,          4)
            self.assertEqual(results["limit_t3"]    ,          5)
            self.assertEqual(results["limit_t4"]    ,          6)
            self.assertEqual(results["limit_t5"]    ,          7)
            self.assertEqual(results["workers"]     , map_mock())

            self.assertEqual(self.cursor.execute.call_count, 2)

    def testGetKeyGenProfilesWorks(self):
        """Verifies that the getKeyGenProfiles function behaves correctly
           with valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.__iter__ = MagicMock(return_value=iter([1, 2, 3]))
        tier_data_dict =  {"workers": {
                                    "tier1": {"workers": [0,1,2], "count": 3},
                                    "tier2": {"workers": [4,5]  , "count": 2}}}

        with patch.object(self.uut, "mapQueryToProfile") as map_mock:
            profile = self.uut.getKeyGenProfiles(tier_data = tier_data_dict,
                                                 user_id   = 0)

            self.cursor.execute.assert_called_once()
            self.assertEqual(len(profile), 3)
            self.assertEqual(map_mock.call_count, 3)
            self.assertEqual(map_mock.call_args_list[0][1]['query'], 1)
            self.assertEqual(map_mock.call_args_list[1][1]['query'], 2)
            self.assertEqual(map_mock.call_args_list[2][1]['query'], 3)

    @patch("src.characters.RarityClass.RarityList")
    def testGetSummaryCharactersWorks(self, rarity_mock):
        """Verifies that the getSummaryCharacters function behaves correctly
           with valid input.

           Input: self        - Pointer to the current object instance.
                  rarity_mock - Patch of the RarityList class

           Output: none.
        """

        self.cursor.execute.reset_mock()
        rarity_mock.CUSTOM.value = 10
        rarity_mock.getStandardValueList.return_value = [0, 5, 10]
        iter_mock = MagicMock(return_value=iter([[1, "ignored"],
                                                 range(0, 12)]))
        self.cursor.__iter__ = iter_mock

        result = self.uut.getSummaryCharacters(user_id = 0)

        self.cursor.execute.assert_called_once()
        self.assertNotEqual(result, None)

    def testGetSummaryEconomysWorks(self):
        """Verifies that the getSummaryEconomy function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchone.return_value = [*range(0, 9*len(cj.AssignChoices))]

        result = self.uut.getSummaryEconomy(user_id = 0)

        self.cursor.execute.assert_called_once()
        self.assertNotEqual(result, None)

    def testGetSummaryInventoryWorks(self):
        """Verifies that the getSummaryInventory function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchone.return_value = [*range(0, 20)]

        result = self.uut.getSummaryInventory(user_id = 0)

        self.cursor.execute.assert_called_once()
        self.assertNotEqual(result, None)

    def testGetUnoccupiedProfilesWorks(self):
        """Verifies that the getUnoccupiedProfiles function behaves correctly
           with valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.__iter__ = MagicMock(return_value=iter([1, 2, 3]))

        with patch.object(self.uut, "mapQueryToProfile") as map_mock:
            profile = self.uut.getUnoccupiedProfiles(user_id = 0)

            self.cursor.execute.assert_called_once()
            self.assertEqual(len(profile), 3)
            self.assertEqual(map_mock.call_count, 3)
            self.assertEqual(map_mock.call_args_list[0][1]['query'], 1)
            self.assertEqual(map_mock.call_args_list[1][1]['query'], 2)
            self.assertEqual(map_mock.call_args_list[2][1]['query'], 3)

    def testGetUsersProfilesWorks(self):
        """Verifies that the getUsersProfiles function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.__iter__ = MagicMock(return_value=iter([1, 2, 3]))

        with patch.object(self.uut, "mapQueryToProfile") as map_mock:
            profile = self.uut.getUsersProfiles(user_id = 0,
                                                rarity = [])

            self.cursor.execute.assert_called_once()
            self.assertEqual(len(profile), 3)
            self.assertEqual(map_mock.call_count, 3)
            self.assertEqual(map_mock.call_args_list[0][1]['query'], 1)
            self.assertEqual(map_mock.call_args_list[1][1]['query'], 2)
            self.assertEqual(map_mock.call_args_list[2][1]['query'], 3)


    def testGetWorkerCountsInTierWorks(self):
        """Verifies that the getWorkerCountsInTier function behaves correctly
           with valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchall.return_value = [[0, 1], [2, 3]]

        result = self.uut.getWorkerCountsInTier(user_id = 0)

        self.cursor.execute.assert_called_once()
        self.assertNotEqual(result, None)

    def testGetWorkersInJobWorks(self):
        """Verifies that the getWorkersInJob function behaves correctly with
            valid input.

            Input: self - Pointer to the current object instance.

            Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchall.return_value = [[0, 1], [2, 3]]

        result = self.uut.getWorkersInJob(user_id = 0,
                                            job = 0)

        self.cursor.execute.assert_called_once()
        self.assertEqual(result, self.cursor.fetchall.return_value)

    def testMapQueryToKeyGenInfoWorks(self):
        """Verifies that the mapQueryToKeyGenInfo function behaves correctly
            with valid input.

            Input: self - Pointer to the current object instance.

            Output: none.
        """

        workers = self.uut.mapQueryToKeyGenInfo(query = [([10], 20)])

        self.assertEqual(workers['tier_1']['workers'][0], 10)

    def testMapQueryToProfileWorks(self):
        """Verifies that the mapQueryToProfile function behaves correctly
            with valid input.

            Input: self - Pointer to the current object instance.

            Output: none.
        """

        query_value = [*range(0,31)]
        query_value[21] = 0

        profile = self.uut.mapQueryToProfile(query = query_value)

        self.assertNotEqual(profile, None)
        self.assertEqual(profile.wins, 22)

    def testPutDropdownWorks(self):
        """Verifies that the putDropdown function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()

        self.uut.putDropdown(user_id = 0,
                             state = True)

        self.cursor.execute.assert_called_once()

    def testRemoveKeyGenWorkWorks(self):
        """Verifies that the removeKeyGenWork function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        workers_value = [[0], [1], [2], [3]]

        self.uut.removeKeyGenWork(user_id     = 0,
                                  profile_ids = [1, 2],
                                  tier        = 0,
                                  workers     = workers_value)

        self.assertEqual(self.cursor.execute.call_count, 2)

    def testResetDailyRollWorks(self):
        """Verifies that the resetDailyRoll function behaves correctly with
           valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()

        self.uut.resetDailyRoll()

        self.cursor.execute.assert_called_once()
        self.cursor.execute.assert_called_with(self.uut.cmds['user']['reset_daily'])

    def testResetDailyRollFails(self):
        """Verifies that the resetDailyRoll function behaves correctly if the
           database throws an exception.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.execute.side_effect = mariadb.DatabaseError("Mock database error")

        self.uut.resetDailyRoll()

        self.cursor.execute.assert_called_once()
        self.cursor.execute.assert_called_with(self.uut.cmds['user']['reset_daily'])

        self.cursor.execute.side_effect = None

    def testSaveRollWorksWithDefaultResult(self):
        """Verifies that the saveRoll function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.__iter__ = MagicMock(return_value=iter([[self.uut.db_cmds['default_id']]]))
        profile_value = pg.getDefaultProfile()

        self.cursor.execute.reset_mock()

        self.uut.saveRoll(info = {},
                          profile = profile_value)

        self.cursor.execute.assert_called_once()

    def testSaveRollWorksWithNonDefaultResult(self):
        """Verifies that the saveRoll function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.__iter__ = MagicMock(return_value=iter([["not_default_id"]]))
        profile_value = pg.getDefaultProfile()

        self.uut.saveRoll(info = {},
                          profile = profile_value)

        self.cursor.execute.assert_called_once()


    def testSaveRollWorksWithNoneFromDatabase(self):
        """Verifies that the saveRoll function behaves correctly with valid
           input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.__iter__ = MagicMock(return_value=iter([None,None]))
        return_values = ["00", ["id"], '{"id" : 0 }']
        self.cursor.fetchone.side_effect = return_values

        profile_value = pg.getDefaultProfile()

        self.uut.saveRoll(info = {},
                          profile = profile_value)

        self.assertEqual(self.cursor.execute.call_count, 7)

        self.cursor.fetchone.side_effect = None

    def testUpdateDailyKeyGenWorkWorks(self):
        """Verifies that the updateDailyKeyGenWork function behaves correctly
           with valid input.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.fetchall.return_value = [[*range(0,7)],[*range(0,7)]]

        self.uut.updateDailyKeyGenWork()

        self.assertEqual(self.cursor.execute.call_count, 3)

    def testUpdateDailyKeyGenWorkHandlesException(self):
        """Verifies that the updateDailyKeyGenWork function behaves correctly
           with a database exception.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.cursor.execute.reset_mock()
        self.cursor.execute.side_effect = mariadb.DatabaseError("Mock database error")

        self.uut.updateDailyKeyGenWork()

        self.cursor.execute.assert_called_once()
        self.cursor.execute.side_effect = None
