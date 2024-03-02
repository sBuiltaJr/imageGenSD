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
            self.db_cmds   = {}
            self.con       = None
            self.pict_cmds = {}
            self.prof_cmds = {}
            self.user_cmds = {}

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

                self.db_log.debug(f"paths are: {pl.Path('src/db/db_commands.json').absolute()} {pl.Path('src/db/queries/picture_queries.json').absolute()} {pl.Path('src/db/queries/profile_queries.json').absolute()} {pl.Path('src/db/queries/user_queries.json').absolute()}")
                json_file      = open(pl.Path("src/db/db_commands.json").absolute())
                self.db_cmds   = json.load(json_file)
                json_file      = open(pl.Path("src/db/queries/picture_queries.json").absolute())
                self.pict_cmds = json.load(json_file)
                json_file      = open(pl.Path("src/db/queries/profile_queries.json").absolute())
                self.prof_cmds = json.load(json_file)
                json_file      = open(pl.Path("src/db/queries/user_queries.json").absolute())
                self.user_cmds = json.load(json_file)

            #Sure, it's more pythonic to use with and limit exceptions cases,
            #but making a case here for every possible exception type is dumb.
            except Exception as err:

                self.db_log.error(f"Unable to get MariaDB commands: {err=}")
                raise  FileNotFoundError(f"Error opening the mariaDB command files: {err=}")

            if not self.validateInstall() :

                self.db_log.error(f"Unable to access mariaDB server! {options['host']} {options['port']} {options['user_name']} {options['password']}")
                raise PermissionError(f"Unable to access mariaDB server!")

            self.db_log.info(f"Successfully connected to database: host: {options['host']} port: {options['port']} username: {options['user_name']} db: {options['database']}")
            self.db_log.debug(f"Loaded commands: {self.db_cmds} {self.pict_cmds} {self.prof_cmds} {self.user_cmds}")

    def dailyDone(self,
                  id  : Optional[str] = "x'fffffffffffffffffffffffffffffffe'") -> bool:
        """Returns whether a user has already completed their daily actions.

            Input: self - Pointer to the current object instance.
                   id - The user to look-up, defaults to the test user.

            Output: bool - True if the user has already done their dailies.
        """
        cursor = self.con.cursor(buffered=False)
        cmd    = ""
        result = False

        #TODO: Better user/profile management.
        self.db_log.info(f"Checking if user {id} exists")
        cmd = (self.user_cmds['get_user']) % (id)
        self.db_log.debug(f"Executing get user command: {cmd}")
        cursor.execute(cmd)
        user_profile = cursor.fetchone()

        if user_profile == None:

            cmd = (self.user_cmds['put_new']) % (id)
            self.db_log.debug(f"Preparing to create user: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Created user")

        else:

            result = bool(user_profile[int(self.user_cmds['daily_index'])])
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
        cursor     = self.con.cursor(buffered=False)
        cmd        = ""
        result     = None
        pic_id     = 0

        if picture_id == None:

            self.db_log.info(f"Getting picture ID")

            cmd = (self.prof_cmds['get_profile']) % (profile_id)
            self.db_log.debug(f"Executing get profile command {cmd}")
            cursor.execute(cmd)

            profile = cursor.fetchone()

            if profile == None:

                self.db_log.warn(f"Could not find the profile {profile_id} in the DB!")
                return ""

        self.db_log.info(f"Getting picture.")
        cmd = (self.pict_cmds['get_image']) % (picture_id if picture_id != None else profile[int(self.prof_cmds['pic_id_index'])])
        self.db_log.debug(f"Executing get picture command {cmd}")
        cursor.execute(cmd)
        #The cursor object doesn't appear to actually provide a better way
        #to determine if the cursor has a result.
        img = cursor.fetchone()

        if (img == None):

            self.db_log.warning(f"Picture ID {profile[int(self.prof_cmds['pic_id_index'])]} not found!")
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
        cursor     = self.con.cursor(buffered=False)
        cmd        = ""
        profile    = None
        result     = None

        self.db_log.info(f"Getting profile")
        cursor.execute((self.prof_cmds['get_profile']) % id)
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
        """Returns a given profile for a given user.

            Input: self - Pointer to the current object instance.
                   user_id - user ID to interrogate for profiles.

            Output: N/A.
        """
        cursor     = self.con.cursor(buffered=False)
        cmd        = ""
        results    = []

        self.db_log.info(f"Getting profiles for user {user_id}")
        cmd = (self.prof_cmds['get_owned_profs']) % (user_id)
        self.db_log.debug(f"Executing command: {cmd}")
        cursor.execute(cmd)

        for x in cursor:

            self.db_log.debug(f"Adding result: {x}")
            results.append(self.mapQueryToProfile(query=x))

        self.db_log.debug(f"Got results: {results}")

        return results

    def mapQueryToProfile(self,
                          query : list) -> pg.Profile:
        """Maps the full return of a profile query to a Profile object.  This is
           required because the DB stores profiels as their individual elements.

           Input: self - Pointer to the current object instance.
                  query - a list representing a single profile from the DB.

           Output: Profile - the query converted into a Profile, or the default
                             profile.
        """
        self.db_log.debug(f"Preparing to map query: {query}")
        stat_opts              = sc.getDefaultOptions()
        stat_opts['agility']   = query[5]
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
        profile=pg.Profile(opts=prof_opts)
        self.db_log.debug(f"Profile map output was: {profile}")
        
        return profile

    def resetDailyRoll(self):
        """Resets the 'daily' boolean for all user profiles, allowing them to
           perform another round of daily actions.

            Input: N/A

            Output: N/A.
        """
        cursor     = self.con.cursor(buffered=False)
        cmd        = ""
        result     = None

        self.db_log.warning(f"Preparing to reset daily rolls.")
        cmd = (self.user_cmds['reset_daily'])
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
        cursor     = self.con.cursor(buffered=False)
        cmd        = ""
        entry      = profile
        entry.info = info
        owned      = None
        result     = None


        cursor.execute((self.prof_cmds['get_profile']) % id)
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

            cmd = (self.prof_cmds['put_new']) % (self.db_cmds['default_id'], id, entry.creator, entry.stats.agility, entry.stats.defense, entry.stats.endurance, entry.stats.luck, entry.stats.strength, entry.desc, entry.favorite, json.dumps(entry.info), entry.name, entry.rarity.value)
            self.db_log.debug(f"Preparing to add profile: {cmd}")
            cursor.execute(cmd)
            #We don't actually know the GUID until we get it back from the DB.
            pr_uid=cursor.fetchone()
            self.db_log.info(f"Stored profile with UID {pr_uid}")

            cmd = (self.pict_cmds['put_new']) % ('0x' + str(pr_uid[0]).replace('-',''), pr_uid[1], json.dumps(entry.info), img)
            self.db_log.debug(f"Preparing to add picture: {cmd}")
            cursor.execute(cmd)
            pi_uid=cursor.fetchone()
            self.db_log.info(f"Stored picture with UID {pi_uid}")

            #It's only possible to link the picture to the profile after its
            #UUID is generated.
            cmd = (self.prof_cmds['put_img_id']) % (pi_uid[0], pr_uid[0])
            self.db_log.debug(f"Updating Profile to reference picture UUID: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Linked picture id {pi_uid[0]} to profile {pr_uid[0]}")

            #This needs to be last to get both UIDs.
            cmd = (self.user_cmds['get_owned']) % (id)
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

            cmd = (self.user_cmds['set_owned']) % (json.dumps(owned), id)
            self.db_log.debug(f"Updating user {id} owned dict: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Updated user {id}'s owned dict")

            #Finally, now that the roll has been fully saved and connected to
            #the user's profile, mark their daily roll as complete.
            cmd = (self.user_cmds['set_daily_roll']) % (id)
            self.db_log.debug(f"Updating user {id} owned dict: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Updated user {id}'s owned dict")

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

            #It does pain me a little to write out a loop.
            cursor.execute(self.db_cmds['create_table'] + self.pict_cmds['table_fmt'])
            cursor.execute(self.db_cmds['create_table'] + self.prof_cmds['table_fmt'])
            cursor.execute(self.db_cmds['create_table'] + self.user_cmds['table_fmt'])

            #The script actually interacts with the Tables to truly confirm the
            #permissions, instead of just relying on the GRANT table, to avoid
            #having to parse the output and guess some of the parameters.
            cursor.execute(self.pict_cmds['del_default'])
            cursor.execute(self.pict_cmds['make_def_tst'])
            cursor.execute(self.prof_cmds['del_default'])
            cursor.execute(self.prof_cmds['make_def_tst'])
            cursor.execute(self.user_cmds['del_default'])
            cursor.execute(self.user_cmds['make_def_tst'])

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