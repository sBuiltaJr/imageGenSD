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
from typing import Literal, Optional

#####  Package Variables  #####


#####  Mariadb Interface Class  #####

class MariadbIfc:
    """Acts as the dabase interface for MariaDB SQL servers.  Also creates
        tables, users, and fields as needed.
    """

    def __init__(self, options : dict):
        """Reads the included json config for db parameters, like username and
            login information.  Verification is handled in a different function.
            Also instantiates a logger specifically for this class.

            Input: self - Pointer to the current object instance.

            Output: None - Throws exceptions on error.
        """

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

            self.db_log.debug(f"paths are: {pl.Path("src/db/db_commands.json").absolute()} {pl.Path("src/db/queries/picture_queries.json").absolute()} {pl.Path("src/db/queries/profile_queries.json").absolute()} {pl.Path("src/db/queries/user_queries.json").absolute()}")
            json_file      = open(pl.Path("src/db/db_commands.json").absolute())
            self.db_cmds   = json.load(json_file)
            json_file      = open(pl.Path("src/db/queries/picture_queries.json").absolute())
            self.pict_cmds = json.load(json_file)
            json_file      = open(pl.Path("src/db/queries/profile_queries.json").absolute())
            self.prof_cmds = json.load(json_file)
            json_file      = open(pl.Path("src/db/queries/user_queries.json").absolute())
            self.user_cmds = json.load(json_file)
        #Sure, it's more pythonic to use with and only catch limited exceptions,
        #but making a case here for every possible exception type is dumb.
        except Exception as e:

            self.db_log.error(f"Unable to get MariaDB commands: {e=}")
            raise  FileNotFoundError(f"Error opening the mariaDB command files: {e=}")

        if not self.ValidateInstall() :

            self.db_log.error(f"Unable to access mariaDB server! {options['host']} {options['port']} {options['user_name']} {options['password']}")
            raise PermissionError(f"Unable to access mariaDB server!")

        self.db_log.info(f"Successfully connected to database: host: {options['host']} port: {options['port']} username: {options['user_name']} db: {options['database']}")
        self.db_log.debug(f"Loaded commands: {self.db_cmds} {self.pict_cmds} {self.prof_cmds} {self.user_cmds}")

    def ValidateInstall(self) -> bool:
        """Validates all the database components are accessable and usable by the
            script.

            Input: self - Pointer to the current object instance.

            Output: bool - True if install is valid and usable.
        """
        all_ok = False

        #These are separarte try statements for better error debugging.  The idea
        #of creating missing DBs was scrapped due to implementation complexity.
        #(The script would need to invoke mariadb as sudo with root).
        try:
            #TODO: convert to a threadpool
            self.con = mariadb.connect(host=self.args['host'],
                                       port=int(self.args['port']),
                                       user=self.args['user_name'],
                                       password=self.args['password'])

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

    def GetImage(self,
                 picture_id : Optional[str] = 'ffffffff-ffff-ffff-ffff-fffffffffffe',
                 profile_id : Optional[str] = 'ffffffff-ffff-ffff-ffff-fffffffffffe') -> str:
        """Returns a given profile for a given user.

            Input: self - Pointer to the current object instance.
                   id - user ID to link the profile to.
                   info - the picture metadata to store.
                   profile - The profile to link the image to.

            Output: N/A.
        """
        cursor     = self.con.cursor()
        cmd        = ""
        result     = None
        pic_id     = 0
        
        self.db_log.info(f"Getting picture ID")
        
        cmd = (self.prof_cmds['get_profile']) % (profile_id)
        self.db_log.debug(f"Executing get profile command {cmd}")
        cursor.execute(cmd)
        
        profile = cursor.fetchone()
        
        if profile == None:

            self.db_log.error(f"Could not find default profile in the DB!")
            return ""
        
        self.db_log.info(f"Getting picture.")
        cmd = (self.pict_cmds['get_image']) % (profile[int(self.prof_cmds['pic_id_index'])])
        self.db_log.debug(f"Executing get picture command {cmd}")
        cursor.execute(cmd)
        #The cursor object doesn't appear to actually provide a better way
        #to determine if the cursor has a result.
        img = cursor.fetchone()

        if (img == None):

            self.db_log.warn(f"Picture not found!")
            return ""
        
        else:
        
            self.db_log.debug(f"Got picture: {img[0]}")
            return img[0]

    def GetProfile(self,
                 id         : Optional[str] = 'ffffffff-ffff-ffff-ffff-fffffffffffe',
                 profile_id : Optional[str] = 'ffffffff-ffff-ffff-ffff-fffffffffffe') -> str:
        """Returns a given profile for a given user.

            Input: self - Pointer to the current object instance.
                   id - user ID to link the profile to.
                   info - the picture metadata to store.
                   profile - The profile to link the image to.

            Output: N/A.
        """
        cursor     = self.con.cursor()
        cmd        = ""
        result     = None

        self.db_log.info(f"Getting profile")
        cursor.execute((self.prof_cmds['get_profile']) % id)
        #The cursor object doesn't appear to actually provide a better way
        #to determine if the cursor has a result.
        result = cursor.fetchone()

        if (result == None):

            self.db_log.warn(f"Profile not found!: {id}")
        
        else:
        
            self.db_log.debug(f"Got profile: {result}")
            #Since profiles are stored as individual elements in the DB for
            #statistical analysis, the actual profile object needs to be
            #re-created before it can be returned (since the rest of the code
            #expects to interact with an object).
            stats=sc.Stats(rarity=rc.RarityList(int(result[21])),
                           agility=result[5],
                           defense=result[6],
                           endurance=result[7],
                           luck=result[8],
                           strength=result[9])
            self.db_log.debug(f"Made stats: {pic.dumps(stats)}")
             #TODO: find a way to better map these.  Blah blah factory.
            profile=pg.Profile(id=result[0],
                              img_id=result[1],
                              creator=result[3],
                              owner=result[4],
                              affinity=result[10],
                              battles=result[11],
                              desc=result[12],
                              exp=result[13],
                              favorite=result[14],
                              history=result[15],
                              info=result[16],
                              level=result[17],
                              losses=result[18],
                              missions=result[19],
                              name=result[20],
                              rarity=rc.RarityList(int(result[21])),
                              stats=stats,
                              wins=result[22])
            self.db_log.debug(f"Made profile: {pic.dumps(profile)}")
            return profile

    def SaveRoll(self,
                 id      : Optional[str] = 'ffffffff-ffff-ffff-ffff-fffffffffffe',
                 img     : Optional[str] = None,
                 info    : dict          = None,
                 profile : str           = None):
        """Created a UUID for the given profile.

            Input: self - Pointer to the current object instance.
                   id - user ID to link the profile to.
                   info - the picture metadata to store.
                   profile - The profile to link the image to.

            Output: N/A.
        """
        cursor     = self.con.cursor()
        cmd        = ""
        entry      = pic.loads(profile)
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

                self.db_log.warn(f"Found an existing non-test profile: {x}  For roll {info}")

        else:

            #TODO: find a better way of updating user properties; right now
            #both caller and here have to know the state parameters to update
            #something.  Maybe a dict of only the keys to update, with
            #f-strings on the commands to update without parsing names?  Has
            #issues with knowing how to update (e.g. increment a count).  Maybe
            #a dict of commands instead of values?
            result = None

            for x in cursor:

                result = x
                self.db_log.debug(f"User entry found: {x}")

            if (result != None):

                cmd = (self.user_cmds['put_new']) % (id, id)
                self.db_log.debug(f"Preparing to create user: {cmd}")
                cursor.execute(cmd)
                self.db_log.info(f"Created user")

            else:

                cmd = (self.user_cmds['inc_cmd_ct']) % (id)
                self.db_log.debug(f"Preparing to update user cmd count {cmd}")
                cursor.execute(cmd)
                self.db_log.info(f"Incremented user {id}'s command count.")

            cmd = (self.prof_cmds['put_new']) % (self.db_cmds['default_id'], id, entry.creator, entry.stats.agility, entry.stats.defense, entry.stats.endurance, entry.stats.luck, entry.stats.strength, entry.desc, entry.favorite, json.dumps(entry.info), entry.name, entry.rarity.value)
            self.db_log.debug(f"Preparing to add profile: {cmd}")
            cursor.execute(cmd)
            #We don't actually know the guid until we get it back from the DB.
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

            if str_owned != None:

                self.db_log.debug(f"Got user {id}'s owned dict: {str_owned}")
                owned=json.loads(str_owned[0])

            else:

                #This is a user's first roll, or they wiped all their characters.
                owned= {}

            self.db_log.info(f"Got user {id}'s owned dict")

            #This allows for easy looping over (keys) to get all profiles.
            owned['{pr_uid[0]}'] = pi_uid[0]
            self.db_log.debug(f"Associated profile {pr_uid[0]} with user {id} as: {owned['{pr_uid[0]}']}")

            cmd = (self.user_cmds['put_owned']) % (json.dumps(owned), id)
            self.db_log.debug(f"Updating user {id} owned dict: {cmd}")
            cursor.execute(cmd)
            self.db_log.info(f"Updated user {id}'s owned dict")


#Forge waifus via combination?
#
#Daily rolls measured on UTC for days

#TODO: define how a user is suppose to make the IGSD bot account and give access to the bogus and IGSD tables.
#CREATE DATABASE IGSD;
#CREATE USER IF NOT EXISTS 'IGSD_Bot'@'%' IDENTIFIED BY 'password';
#GRANT ALL PRIVILEGES ON IGSD.* TO 'IGSD_Bot'@'%';
#Set the max_allowed_packet=4G in my.ini or ~/.my.cnf