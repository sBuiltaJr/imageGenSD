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

    def SaveRoll(self,
                 id      : Optional[str] = '0xfffffffffffffffffffffffffffffffe',
                 img     : Optional[str] = None,
                 info    : dict          = None,
                 profile : str           = None):
        """Created a UUID for the given profile .

            Input: self - Pointer to the current object instance.

            Output: bool - True if install is valid and usable.
        """
        cursor     = self.con.cursor()
        entry      = pic.loads(profile)
        entry.info = info
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

                self.db_log.warn(f"Rolled the test profile: {x}")

            #Somehow the the roll is linked to an existing, non-test profile?
            else:

                self.db_log.warn(f"Found an existing non-test profile: {x}  For roll {info}")

        else:

            self.db_log.debug(f"Preparing to add profile: {(self.prof_cmds['put_new']) % (self.db_cmds['default_id'], id, entry.desc, entry.favorite, '{"0":"0"}', entry.name, entry.rarity.value)}")
            #print(str(entry.info).replace("'",'"'))
            cursor.execute((self.prof_cmds['put_new']) % (self.db_cmds['default_id'], id, entry.desc, entry.favorite, str(entry.info).replace("'",'"'), entry.name, entry.rarity.value))
            #We don't actually know the guid until we get it back from the DB.
            uid=cursor.fetchone()
            self.db_log.info(f"Stored profile with UID {uid}")

            self.db_log.debug(f"Preparing to add picture: {(self.pict_cmds['put_new']) % ('0x' + str(uid[0]).replace('-',''), uid[1], str(entry.info).replace("'",'"'), img)}")
            cursor.execute((self.pict_cmds['put_new']) % ('0x' + str(uid[0]).replace('-',''), uid[1], str(entry.info).replace("'",'"'), img))
            uid=cursor.fetchone()
            self.db_log.info(f"Stored picture with UID {uid}")

#Waifu tracking:
#DB to track users and owned waifus (and image)
#Forge waifus via combination?
#
#Daily rolls measured on UTC for days
#Table to track?  Annoying in Mongo.  Internal dict okay?  Handling scale?
#Store all data to the DB post generation.

#TODO: define how a user is suppose to make the IGSD bot account and give access to the bogus and IGSD tables.
#"CREATE USER IF NOT EXISTS 'IGSD_Bot'@'%' IDENTIFIED BY 'password';
#"GRANT ALL PRIVILEGES ON IGSD.* TO 'IGSD_Bot'@'%'";
#Set the max_allowed_packet=4G in my.ini or ~/.my.cnf