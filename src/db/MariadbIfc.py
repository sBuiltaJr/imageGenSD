#This file manages interfacing to a maraidb server of at least version 10.
#It may work with older mariadb versions, though they are untested.

#The current table definitions have the following maximums:
#Created profiles: ~4,294,967,296 (limit of UUID size)
#Owned profiles: ~134,210,000 (with JSON formatting of UUIDs)

#####  Imports  #####

import json
import logging as log
import logging.handlers as lh
import mariadb
from mariadb.constants import *
import os
import pathlib as pl
import pickle as pic
import src.utilities.ProfileGenerator as pg
import src.utilities.RarityClass as rc
import src.utilities.StatsClass as sc
import sys
import threading as th
from typing import Literal, Optional

#####  Package Variables  #####

#####  Mariadb Interface Class  #####

class MariadbIfc:
    """Acts as the dabase interface for MariaDB SQL servers.  Also creates
        tables, users, and fields as needed.
    """
    __instance = None
    __lock = th.Lock()

    @staticmethod
    def getInstance(options : dict):
        """Returns an instance of the singletion, or makes a new instance if
           one doesn't exist, using the provided options parameter.

           Input: self - Pointer to the current object instance.
                  options - a dict of options for this class.

           Output: MariadbIfc - an instance of the interface.
        """

        if MariadbIfc.__instance == None:

            with MariadbIfc.__lock :

                if MariadbIfc.__instance == None:

                    MariadbIfc(options)

        return MariadbIfc.__instance

    def __init__(self,
                 options : dict):
        """Reads the included json config for db parameters, like username and
           login information.  Verification is handled in a different function.
           Also instantiates a logger specifically for this class.

           Input: self - Pointer to the current object instance.
                  options - a dict of options for this class.

           Output: None - Throws exceptions on error.
        """

        if MariadbIfc.__instance != None:

            return

        else:

            MariadbIfc.__instance = self

            self.args      = options
            self.cmds      = {}
            self.con       = None

            self.db_log = log.getLogger('mariadb')
            self.db_log.setLevel(options['log_lvl'])
            log_path = pl.Path(options['log_name_db'])

            logHandler = lh.RotatingFileHandler(filename=log_path.absolute(),
                                                encoding=options['log_encoding'],
                                                maxBytes=int(options['max_bytes']),
                                                backupCount=int(options['log_file_cnt']),
            )
            formatter = log.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}',
                                      options['date_fmt'],
                                      style='{'
            )
            logHandler.setFormatter(formatter)
            self.db_log.addHandler(logHandler)

            try:
                paths = { 'db'   : pl.Path('src/db/db_commands.json').absolute(),
                          'econ' : pl.Path('src/db/queries/economy_queries.json').absolute(),
                          'inv'  : pl.Path('src/db/queries/inventory_queries.json').absolute(),
                          'keyg' : pl.Path('src/db/queries/keygen_queries.json').absolute(),
                          'pic'  : pl.Path('src/db/queries/picture_queries.json').absolute(),
                          'prof' : pl.Path('src/db/queries/profile_queries.json').absolute(),
                          'user' : pl.Path('src/db/queries/user_queries.json').absolute()}
                self.db_log.debug(f"paths are: {paths['db']} {paths['econ']} {paths['inv']} {paths['keyg']} {paths['pic']} {paths['prof']} {paths['user']}")
                json_file         = open(paths['db'])
                self.db_cmds      = json.load(json_file)
                json_file         = open(paths['econ'])
                self.cmds['econ'] = json.load(json_file)
                json_file         = open(paths['inv'])
                self.cmds['inv']  = json.load(json_file)
                json_file         = open(paths['keyg'])
                self.cmds['keyg'] = json.load(json_file)
                json_file         = open(paths['pic'])
                self.cmds['pic']  = json.load(json_file)
                json_file         = open(paths['prof'])
                self.cmds['prof'] = json.load(json_file)
                json_file         = open(paths['user'])
                self.cmds['user'] = json.load(json_file)

            #Sure, it's more pythonic to use with and limit exceptions cases,
            #but making a case here for every possible exception type is dumb.
            except Exception as err:

                self.db_log.error(f"Unable to get MariaDB commands: {err=}")
                raise  FileNotFoundError(f"Error opening the mariaDB command files: {err=}")

            if not self.validateInstall() :

                self.db_log.error(f"Unable to access mariaDB server! {options['host']} {options['port']} {options['user_name']} {options['password']}")
                raise PermissionError(f"Unable to access mariaDB server!")

            self.db_log.info(f"Successfully connected to database: host: {options['host']} port: {options['port']} username: {options['user_name']} db: {options['database']}")
            self.db_log.debug(f"Loaded commands: {self.db_cmds} {self.cmds['pic']} {self.cmds['econ']} {paths['inv']} {self.cmds['keyg']} {self.cmds['prof']} {self.cmds['user']}")

    def assignKeyGenWork(self,
                         count       : int,
                         profile_ids : list,
                         tier        : int,
                         tier_data   : dict,
                         user_id     : int):
        """Assigns a given list of profile IDs to the 'KeyGen' work action,
           including updating the relevant profile and econ table entries.

            Input: self - Pointer to the current object instance.
                   count - the User's total worker count of this type of work.
                   profile_ids - a (verified) lsit of IDs to assign to work.
                   tier - what level of work is being assigned.
                   tier_data - the worker data for this tier.
                   user_id - The Discord user assocaited with the action.

            Output: N/A.
        """
        cmd        = ""
        cursor     = self.con.cursor(buffered=False)
        key        = f'put_tier_{tier}'
        #This is a workaround to the cursor interpreting None as 'None'
        new_entry  = [INDICATOR.NULL,INDICATOR.NULL,INDICATOR.NULL,INDICATOR.NULL,INDICATOR.NULL, user_id]
        worker_cnt = count

        #The remove function ensures that any existing workers always occupy
        #the front slots (and that empty slots are at the end)
        for worker in range(0, tier_data['count']):

            new_entry[worker] = tier_data['workers'][worker]
            worker_cnt += 1

        for slot in range(0, len(profile_ids)) :

            new_entry[slot + tier_data['count']] = profile_ids[slot]
            worker_cnt += 1

            cmd = (self.cmds['prof']['put_occupied']) % (True, profile_ids[slot])
            self.db_log.debug(f"Preparing to mark a profile as occupied: {cmd}")
            cursor.execute(cmd)

        data = tuple(new_entry)

        cmd  = (self.cmds['keyg'][key]) % (new_entry[0], new_entry[1], new_entry[2], new_entry[3], new_entry[4], user_id)
        self.db_log.debug(f"Updating user's keygen work list for tier {tier}: {cmd}")
        #This must be done as implemented due to how the mariadb python cursor
        #handles (or rather, doesn't handle) NULL entries. See
        #https://mariadb-corporation.github.io/mariadb-connector-python/usage.html#using-indicators
        cursor.execute(self.cmds['keyg'][key], data)

        cmd = (self.cmds['econ']['put_keygen_count']) % (worker_cnt, user_id)
        self.db_log.debug(f"Updating user's econ keygen count: {cmd}")
        cursor.execute(cmd)

    def createNewUser(self,
                      id : str) -> bool:
        """Creates a new user profile in all assocaited tables, if needed.

            Input: self - Pointer to the current object instance.
                   id - The user's Discord ID, to act as their DB key.

            Output: bool - True if a user was created.
        """
        cmd    = ""
        cursor = self.con.cursor(buffered=False)
        result = False

        #TODO: Better user/profile management.
        self.db_log.info(f"Checking if user {id} exists")
        cmd = (self.cmds['user']['get_user']) % (id)
        self.db_log.debug(f"Executing get user command: {cmd}")
        cursor.execute(cmd)
        user_profile = cursor.fetchone()

        if user_profile == None:

            cmd = (self.cmds['user']['put_new']) % (id)
            self.db_log.debug(f"Preparing to create user: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Created user")

            cmd = (self.cmds['econ']['put_new']) % (id)
            self.db_log.debug(f"Preparing to create user econ entry: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Updated user's economy entries.")

            cmd = (self.cmds['inv']['put_new']) % (id)
            self.db_log.debug(f"Creating user {id}'s ivnentory table: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Creatied user {id}'s inventory table")

            cmd = (self.cmds['keyg']['put_new']) % (id)
            self.db_log.debug(f"Preparing to create user keygen entry: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Updated user's keygen worker entries.")

            result = True

        return result

    def dailyDone(self,
                  id  : Optional[str] = "x'fffffffffffffffffffffffffffffffe'") -> bool:
        """Returns whether a user has already completed their daily actions.

            Input: self - Pointer to the current object instance.
                   id - The user to look-up, defaults to the test user.

            Output: bool - True if the user has already done their dailies.
        """
        cmd    = ""
        cursor = self.con.cursor(buffered=False)
        result = False

        if not self.createNewUser(id) :

            cmd = (self.cmds['user']['get_user']) % (id)
            self.db_log.debug(f"Executing get user command: {cmd}")
            cursor.execute(cmd)
            user_profile = cursor.fetchone()

            result = bool(user_profile[int(self.cmds['user']['daily_index'])])
            self.db_log.debug(f"User's daily value: {result}")

        return result

    def getImage(self,
                 picture_id : Optional[str] = None,
                 profile_id : Optional[str] = "ffffffff-ffff-ffff-ffff-fffffffffffe") -> str:
        """Returns a given profile for a given user.

            Input: self - Pointer to the current object instance.
                   picture_id - optional picture ID to find, defaults to the ID
                                linked to the profile_id provided.
                   profile_id - optional profile ID for the picture, defaults
                                to the test image.

            Output: The image associated with the profile, if any.
        """
        cmd    = ""
        cursor = self.con.cursor(buffered=False)
        result = None
        pic_id = 0

        if picture_id == None:

            self.db_log.info(f"Getting picture ID")

            cmd = (self.cmds['prof']['get_profile']) % (profile_id)
            self.db_log.debug(f"Executing get profile command {cmd}")
            cursor.execute(cmd)

            profile = cursor.fetchone()

            if profile == None:

                self.db_log.warn(f"Could not find the profile {profile_id} in the DB!")
                return ""

        self.db_log.info(f"Getting picture.")
        cmd = (self.cmds['pic']['get_image']) % (picture_id if picture_id != None else profile[int(self.cmds['prof']['pic_id_index'])])
        self.db_log.debug(f"Executing get picture command {cmd}")
        cursor.execute(cmd)
        #The cursor object doesn't appear to actually provide a better way
        #to determine if the cursor has a result.
        img = cursor.fetchone()

        if (img == None):

            self.db_log.warning(f"Picture ID {profile[int(self.cmds['prof']['pic_id_index'])]} not found!")
            return ""

        else:

            self.db_log.debug(f"Got picture: {img[0]}")
            return img[0]

    def getProfile(self,
                   id : Optional[str] = "ffffffff-ffff-ffff-ffff-fffffffffffe") -> Optional[pg.Profile]:
        """Returns a given profile for a given user.

            Input: self - Pointer to the current object instance.
                   id - The profile to get, defaults to the test profile.

            Output: str - The profile object found by the search, if any.
        """
        cmd     = ""
        cursor  = self.con.cursor(buffered=False)
        profile = None
        result  = None

        self.db_log.info(f"Getting profile")
        cursor.execute((self.cmds['prof']['get_profile']) % id)
        #The cursor object doesn't appear to actually provide a better way
        #to determine if the cursor has a result.
        result = cursor.fetchone()

        if (result == None):

            self.db_log.warning(f"Profile not found!: {id}")

        else:

            self.db_log.debug(f"Got profile: {result}")
            profile=self.mapQueryToProfile(query=result)

        return profile

    def getProfiles(self,
                    user_id : int) -> list:
        """Returns all profiles for a given user.

            Input: self - Pointer to the current object instance.
                   user_id - user ID to interrogate for profiles.

            Output: list - A list of all profiles found, if any.  None if not.
        """
        cmd     = ""
        cursor  = self.con.cursor(buffered=False)
        results = []

        self.db_log.info(f"Getting profiles for user {user_id}")
        cmd = (self.cmds['prof']['get_owned_profs']) % (user_id)
        self.db_log.debug(f"Executing command: {cmd}")
        cursor.execute(cmd)

        for x in cursor:

            self.db_log.debug(f"Adding result: {x}")
            results.append(self.mapQueryToProfile(query=x))

        self.db_log.debug(f"Got results: {results}")

        return results

    def getKeyGenParams(self,
                        user_id : int) -> dict:
        """Returns the Keygen parameters and current assigned workers for a
           given user (limit, count, worker ids, etc).

            Input: self - Pointer to the current object instance.
                   user_id - user ID to interrogate for their keygen limit.

            Output: dict - the current user keygen stats.
        """
        cmd    = ""
        cursor = self.con.cursor(buffered=False)
        results = {}

        self.db_log.info(f"Getting keygen worker limit for user {user_id}")
        cmd = (self.cmds['econ']['get_keygen_params']) % (user_id)
        self.db_log.debug(f"Executing command: {cmd}")
        cursor.execute(cmd)

        result = cursor.fetchone()
        self.db_log.debug(f"Got result: {result}")

        if result:

            #This mapping is to minimize code changes if the paramaters change.
            results = {'total'        : result[0],
                       'current_tier' : result[1],
                       'limit_t0'     : result[2],
                       'limit_t1'     : result[3],
                       'limit_t2'     : result[4],
                       'limit_t3'     : result[5],
                       'limit_t4'     : result[6],
                       'limit_t5'     : result[7]}

        prof = {}

        cmd = (self.cmds['keyg']['get_tier_all']) % (user_id)
        self.db_log.debug(f"Getting current user keygen worker allocation: {cmd}")
        cursor.execute(cmd)
        #This is returned as a tuple, so either way it has to be converted to a
        #dict at some point.
        result = cursor.fetchone()
        self.db_log.debug(f"Current user keygen allocation is: {result}")
        prof['workers'] = self.mapQueryToKeyGenInfo(query=result)
        self.db_log.debug(f"Worker stats are: {prof['workers']}")

        results |= prof

        return results

    def getKeyGenProfiles(self,
                          tier_data : dict,
                          user_id   : int) -> list:
        """Returns all profiles assigned to key gen work for a given user.

            Input: self - Pointer to the current object instance.
                   tier_data - the key gen parameters for the user.
                   user_id - user ID to interrogate for profiles.

            Output: list - A list of all profiles found, if any.  None if not.
        """
        cmd     = ""
        cursor  = self.con.cursor(buffered=False)
        #This is a workaround to the cursor interpreting None as 'None'.
        ids    = [INDICATOR.NULL for x in range(0, int(self.cmds['keyg']['max_workers']))]
        index   = 0
        results = []

        #It would be nice if I could give the cursor a list as if it were a
        #SELECT statement or JOIN.
        for tier in tier_data['workers'].values():

            for id in range(0, int(tier['count'])):

                ids[index] = tier['workers'][id]

                #The downside of actually using the object as an iterable is
                #the the loop has to manually track its current position.
                index += 1

        data = tuple(ids)
        self.db_log.debug(f"IDs are: {ids}")

        cmd  = (self.cmds['prof']['get_all_workers']) % data
        self.db_log.debug(f"Getting all of a user's keygen profiles: {cmd}")
        #This must be done as implemented due to how the mariadb python cursor
        #handles (or rather, doesn't handle) NULL entries. See
        #https://mariadb-corporation.github.io/mariadb-connector-python/usage.html#using-indicators
        cursor.execute(self.cmds['prof']['get_all_workers'], data)

        for x in cursor:

            self.db_log.debug(f"Adding result: {x}")
            results.append(self.mapQueryToProfile(query=x))

        self.db_log.debug(f"Got results: {results}")

        return results

    def getUnoccupiedProfiles(self,
                              user_id : int) -> list:
        """Returns all profiles not marked as 'occupied' for a given user.

            Input: self - Pointer to the current object instance.
                   user_id - user ID to interrogate for profiles.

            Output: list - A list of all profiles found, if any.  None if not.
        """
        cmd     = ""
        cursor  = self.con.cursor(buffered=False)
        results = []

        self.db_log.info(f"Getting unoccupied profiles for user {user_id}")
        cmd = (self.cmds['prof']['get_unoccupied_profs']) % (user_id)
        self.db_log.debug(f"Executing command: {cmd}")
        cursor.execute(cmd)

        for x in cursor:

            self.db_log.debug(f"Adding result: {x}")
            results.append(self.mapQueryToProfile(query=x))

        self.db_log.debug(f"Got results: {results}")

        return results

    def mapQueryToKeyGenInfo(self,
                             query : tuple) -> dict:
        """Maps the elements of a key gen row to a managable dictionary.  This
           is to help higher-level code parse the row data easier.

           Input: self - Pointer to the current object instance.
                  query - a tuple representing a single keygen row from the DB.

           Output: dict - a dict of the results grouped by tier.
        """
        workers = {'tier_0' : {'workers' : [query[ 0], query[ 1],query[ 2],query[ 3],query[ 4]]},
                   'tier_1' : {'workers' : [query[ 5], query[ 6],query[ 7],query[ 8],query[ 9]]},
                   'tier_2' : {'workers' : [query[10], query[11],query[12],query[13],query[14]]},
                   'tier_3' : {'workers' : [query[15], query[16],query[27],query[28],query[29]]},
                   'tier_4' : {'workers' : [query[20], query[21],query[22],query[23],query[24]]},
                   'tier_5' : {'workers' : [query[25], query[26],query[27],query[28],query[29]]}}
        workers['tier_0']['count'] = len(workers['tier_0']['workers']) - workers['tier_0']['workers'].count(None)
        workers['tier_1']['count'] = len(workers['tier_1']['workers']) - workers['tier_1']['workers'].count(None)
        workers['tier_2']['count'] = len(workers['tier_2']['workers']) - workers['tier_2']['workers'].count(None)
        workers['tier_3']['count'] = len(workers['tier_3']['workers']) - workers['tier_3']['workers'].count(None)
        workers['tier_4']['count'] = len(workers['tier_4']['workers']) - workers['tier_4']['workers'].count(None)
        workers['tier_5']['count'] = len(workers['tier_5']['workers']) - workers['tier_5']['workers'].count(None)

        return workers

    def mapQueryToProfile(self,
                          query : tuple) -> pg.Profile:
        """Maps the full return of a profile query to a Profile object.  This is
           required because the DB stores profiles as their individual elements.

           Input: self - Pointer to the current object instance.
                  query - a tuple representing a single profile from the DB.

           Output: Profile - the query converted into a Profile, or the default
                             profile.
        """
        self.db_log.debug(f"Preparing to map query: {query}")
        stat_opts              = sc.getDefaultOptions()
        stat_opts['agility']   = query[5]
        stat_opts['average']   = float(query[24])
        stat_opts['defense']   = query[6]
        stat_opts['endurance'] = query[7]
        stat_opts['luck']      = query[8]
        stat_opts['strength']  = query[9]

        stats = sc.Stats(rarity=rc.RarityList(int(query[21])),
                         opts=stat_opts)
        self.db_log.debug(f"Stats map output was: {pic.dumps(stats)}")
        prof_opts             = pg.getDefaultOptions()
        prof_opts['affinity'] = query[10]
        prof_opts['battles']  = query[11]
        prof_opts['creator']  = query[3]
        prof_opts['desc']     = query[12]
        prof_opts['exp']      = query[13]
        prof_opts['favorite'] = query[14]
        prof_opts['history']  = query[15]
        prof_opts['id']       = query[0]
        prof_opts['img_id']   = query[1]
        prof_opts['info']     = query[16]
        prof_opts['level']    = query[17]
        prof_opts['losses']   = query[18]
        prof_opts['missions'] = query[19]
        prof_opts['name']     = query[20]
        prof_opts['owner']    = query[4]
        prof_opts['rarity']   = rc.RarityList(int(query[21]))
        prof_opts['stats']    = stats
        prof_opts['wins']     = query[22]
        prof_opts['occupied'] = query[23]
        profile=pg.Profile(opts=prof_opts)
        self.db_log.debug(f"Profile map output was: {profile}")

        return profile

    def removeKeyGenWork(self,
                         count       : int,
                         profile_ids : list,
                         tier        : int,
                         tier_data   : dict,
                         user_id     : int):
        """Remvoes a given list of profile IDs to the 'KeyGen' work action,
           including updating the relevant profile and econ table entries.

            Input: self - Pointer to the current object instance.
                   count - the User's total worker count of this type of work.
                   profile_ids - a (verified) lsit of IDs to remove from work.
                   tier - what level of work is being removed from.
                   tier_data - the worker data for this tier.
                   user_id - The Discord user assocaited with the action.

            Output: N/A.
        """
        cmd        = ""
        cursor     = self.con.cursor(buffered=False)
        key        = f'put_tier_{tier}'
        new_entry  = tier_data['workers']

        #This sorting is necessary to ensure only the lowest slots are filled.
        for id in profile_ids:

            new_entry.remove(id)

        for null in range(0, len(profile_ids)) :

            #This is a workaround to the cursor interpreting None as 'None'
            new_entry.append(INDICATOR.NULL)

        new_entry.append(user_id)

        data = tuple(new_entry)

        cmd  = (self.cmds['keyg'][key]) % (new_entry[0], new_entry[1], new_entry[2], new_entry[3], new_entry[4], user_id)
        self.db_log.debug(f"Updating user's keygen work list for tier {tier}: {cmd}")
        #This must be done as implemented due to how the mariadb python cursor
        #handles (or rather, doesn't handle) NULL entries. See
        #https://mariadb-corporation.github.io/mariadb-connector-python/usage.html#using-indicators
        cursor.execute(self.cmds['keyg'][key], data)

        cmd = (self.cmds['econ']['put_keygen_count']) % (count - len(profile_ids), user_id)
        self.db_log.debug(f"Updating user's econ keygen count: {cmd}")

        #Only update occupied after clearing the work table in case the command
        #fails somehow, ensuring that the table won't have ghost workers.
        for slot in range(0, len(profile_ids)) :

            cmd = (self.cmds['prof']['put_occupied']) % (False, profile_ids[slot])
            self.db_log.debug(f"Preparing to mark a profile as unoccupied: {cmd}")
            cursor.execute(cmd)

    def resetDailyRoll(self):
        """Resets the 'daily' boolean for all user profiles, allowing them to
           perform another round of daily actions.

            Input: N/A

            Output: N/A.
        """
        cmd    = ""
        cursor = self.con.cursor(buffered=False)
        result = None

        self.db_log.warning(f"Preparing to reset daily rolls.")
        cmd = (self.cmds['user']['reset_daily'])
        self.db_log.debug(f"Executing daily roll reset command: {cmd}")

        try:

            cursor.execute(cmd)

        except Exception as err:

            self.db_log.error(f"Failed to reset daily value!: {err=}")

    def saveRoll(self,
                 id      : Optional[str] = "x'fffffffffffffffffffffffffffffffe'",
                 img     : Optional[str] = None,
                 info    : dict          = None,
                 profile : str           = None):
        """Created a UUID for the given profile.  Assumes daily limits have
           already been verified before calling.

            Input: self - Pointer to the current object instance.
                   id - user ID to link the profile to.
                   info - the picture metadata to store.
                   profile - The profile to link the image to.

            Output: N/A.
        """
        cmd        = ""
        cursor     = self.con.cursor(buffered=False)
        entry      = profile
        entry.info = info
        owned      = None
        result     = None


        cursor.execute((self.cmds['prof']['get_profile']) % id)
        #The cursor object doesn't appear to actually provide a better way
        #to determine if the cursor has a result.
        for x in cursor:

            result = x
            self.db_log.debug(f"Cursor Response in loop: {x}")

        if (result != None):

            #Is this is a test command?
            if (x[0] == self.db_cmds['default_id']):

                self.db_log.warning(f"Rolled the test profile: {x}")

            #Somehow the the roll is linked to an existing, non-test profile?
            else:

                #TODO: post an error message to the user to try again.
                self.db_log.warning(f"Found an existing non-test profile: {x}  For roll {info}")

        else:

            cmd = (self.cmds['prof']['put_new']) % (self.db_cmds['default_id'], id, entry.creator, entry.stats.agility, entry.stats.defense, entry.stats.endurance, entry.stats.luck, entry.stats.strength, entry.desc, entry.favorite, json.dumps(entry.info), entry.name, entry.rarity.value, entry.stats.average)
            self.db_log.debug(f"Preparing to add profile: {cmd}")
            cursor.execute(cmd)
            #We don't actually know the GUID until we get it back from the DB.
            pr_uid=cursor.fetchone()
            profile.id = pr_uid[0]
            self.db_log.info(f"Stored profile with UID {pr_uid}")

            cmd = (self.cmds['pic']['put_new']) % ('0x' + str(pr_uid[0]).replace('-',''), pr_uid[1], json.dumps(entry.info), img)
            self.db_log.debug(f"Preparing to add picture: {cmd}")
            cursor.execute(cmd)
            pi_uid=cursor.fetchone()
            self.db_log.info(f"Stored picture with UID {pi_uid}")

            #It's only possible to link the picture to the profile after its
            #UUID is generated.
            cmd = (self.cmds['prof']['put_img_id']) % (pi_uid[0], pr_uid[0])
            self.db_log.debug(f"Updating Profile to reference picture UUID: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Linked picture id {pi_uid[0]} to profile {pr_uid[0]}")

            #This needs to be last to get both UIDs.
            cmd = (self.cmds['user']['get_owned']) % (id)
            self.db_log.debug(f"Getting user {id}'s owned dict: {cmd}")
            cursor.execute(cmd)
            str_owned = cursor.fetchone()

            try:

                self.db_log.debug(f"Got user {id}'s owned dict: {str_owned}")
                owned=json.loads(str_owned[0])

            except Exception as err:

                self.db_log.debug(f"User {id}'s had no valid owned profiles: {str_owned}")
                #This is a user's first roll, or they wiped all their characters.
                owned= {}

            self.db_log.info(f"Got user {id}'s owned dict")

            #This allows for easy looping over (keys) to get all profiles.
            key = f"{pr_uid[0]}"
            owned[key] = pi_uid[0]
            self.db_log.debug(f"Associated profile {pr_uid[0]} with user {id} as: {owned[key]}")

            cmd = (self.cmds['user']['set_owned']) % (json.dumps(owned), id)
            self.db_log.debug(f"Updating user {id} owned dict: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Updated user {id}'s owned dict")

            #Finally, now that the roll has been fully saved and connected to
            #the user's profile, mark their daily roll as complete.
            cmd = (self.cmds['user']['set_daily_roll']) % (id)
            self.db_log.debug(f"Updating user {id} owned dict: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Updated user {id}'s owned dict")

    def updateDailyKeyGenWork(self):
        """Creates keys for all users that have assigned workers to keygen
           creation before daily reset.

            Input: N/A

            Output: N/A.
        """
        cmd    = ""
        cursor = self.con.cursor(buffered=False)
        result = None

        self.db_log.warning(f"Preparing to update daily Key Gen counts.")

        try:

            #TODO: find the sordid single-line statement capable of doing this,
            #instead of by-user.  The current user list is small enough that
            #the waste is okay, but it should be corrected.
            cmd = (self.cmds['keyg']['get_dailys'])
            self.db_log.debug(f"Executing update daily Key Gen counts command: {cmd}")
            cursor.execute(cmd)

            #Yes, this must be done this way because the subsequent cursor
            #interactions will delete the query results.
            results = cursor.fetchall()
            self.db_log.debug(f"Found users to udpate: {results}")

            #Reminder that the cursor returns all results as tuples.
            for usr in results:


                cmd = (self.cmds['keyg']['get_tier_all']) % (usr[0])
                self.db_log.debug(f"Getting current user keygen worker allocation: {cmd}")
                cursor.execute(cmd)

                result = cursor.fetchone()
                self.db_log.debug(f"Current user keygen allocation is: {result}")
                workers = self.mapQueryToKeyGenInfo(query=result)
                self.db_log.debug(f"Worker stats are: {workers}")

                cmd = (self.cmds['inv']['put_daily']) % (workers['tier_0']['count'], workers['tier_1']['count'], workers['tier_2']['count'], workers['tier_3']['count'], workers['tier_4']['count'], workers['tier_5']['count'], usr[0])
                self.db_log.debug(f"Updating users keys with new values: {cmd}")
                cursor.execute(cmd)
                self.db_log.info(f"Updated user {usr[0]}'s keys")

        except Exception as err:

            self.db_log.error(f"Failed to update daily Keygen List!: {err=}")

    def validateInstall(self) -> bool:
        """Validates all the database components are accessable and usable by
           the script.

            Input: self - Pointer to the current object instance.

            Output: bool - True if install is valid and usable.
        """
        all_ok = False

        #These are separarte try statements for better error debugging.  The
        #idea of creating missing DBs was scrapped due to implementation
        #complexity.
        #(The script would need to invoke mariadb as sudo with root).
        try:
            #TODO: convert to a threadpool
            self.con = mariadb.connect(host=self.args['host'],
                                       port=int(self.args['port']),
                                       user=self.args['user_name'],
                                       password=self.args['password'],
                                       autocommit=True)

            self.con.auto_reconnect = bool(self.args['auto_reconnect'])

        except mariadb.Error as err:

            self.db_log.error(f"Error connecting to mariadb: {err}")
            return all_ok

        try:

            #The interface requries the cursor.
            cursor = self.con.cursor(buffered=False)
            cursor.execute((self.db_cmds['create_db']) % self.args['database'])
            self.con.database = self.args['database']

            for table in self.cmds.values():

                #The script actually interacts with the Tables to confirm the
                #permissions, instead of just relying on the GRANT table, to
                #avoid parsing it and having to guess some of the parameters.
                cursor.execute(self.db_cmds['create_table'] + table['table_fmt'])
                cursor.execute(table['del_default'])
                cursor.execute(table['make_def_tst'])

        except mariadb.OperationalError as err:

            self.db_log.error(f"Unable to access database: {err}")
            return all_ok

        except mariadb.ProgrammingError as err:

            self.db_log.error(f"Unable to access tables in database: {err}")
            return all_ok

        except mariadb.Error as err:

            self.db_log.error(f"Error running mariadb commands: {err=}")
            return all_ok

        all_ok = True;

        return all_ok