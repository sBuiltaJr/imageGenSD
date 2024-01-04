#This file manages interfacing to a maraidb server of at least version 10.
#It may work with older mariadb versions, though they are untested.

#####  Imports  #####

import json
import logging as log
import logging.handlers as lh
import mariadb
import os
import pathlib as pl
import pickle as pic
import sys

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

        self.args = options
        self.cmds = {}
        self.con  = None

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

            json_file = open(options['db_cmds'])
            self.cmds = json.load(json_file)
        #Sure, it's more pythonic to use with and only catch limited exceptions,
        #but making a case here for every possible exception type is dumb.
        except Exception as e:

            self.db_log.error(f"Unable to get MariaDB commands: {e=}")
            raise  FileNotFoundError(f"Error opening the mariaDB config files: {e=}")

        if not self.ValidateInstall() :

            self.db_log.error(f"Unable to access mariaDB server! {options['host']} {options['port']} {options['user_name']} {options['password']}")
            raise PermissionError(f"Unable to access mariaDB server!")

        self.db_log.info(f"Successfully connected to database: host: {options['host']} port: {options['port']} username: {options['user_name']} db: {options['database']}")

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
            cursor = self.con.cursor()
            cursor.execute((self.cmds['create_db']) % self.args['database'])
            self.con.database = self.args['database']

            for db in self.args['tables'].values():
                #The script actually interacts with the Tables to truly confirm the
                #permissions, instead of just relying on the GRANT table, to avoid
                #having to parse the output and guess some of the parameters.
                cursor.execute(f"{self.cmds['create_bogus']}")
                cursor.execute(f"{self.cmds['insert_bogus']}")
                cursor.execute(f"{self.cmds['update_bogus']}")
                cursor.execute(f"{self.cmds['delete_bogus']}")
                #Delete also intentionally omits the 'IF EXIST' component for the
                #same reason.
                cursor.execute(f"{self.cmds['drop_bogus']}")

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
                 profile : str,
                 info    : dict):
        """Created a UUID for the given profile .

            Input: self - Pointer to the current object instance.

            Output: bool - True if install is valid and usable.
        """
        entry = pic.loads(profile)
        entry.info = info

#UUID added to profile when saved  HEX(UUID_TO_BIN(@uuid))
#Randgen profiles save in DB and linked to owner later
#No owner link in the profile, only in users
#Users unique by discord ID
#Store stats as pickled instead of columns?


#Waifu tracking:
#DB to track users and owned waifus (and image)
#Forge waifus via combination?
#
#Daily rolls measured on UTC for days
#Table to track?  Annoying in Mongo.  Internal dict okay?  Handling scale?
#Store all data to the DB post generation.

#TODO: define how a user is suppose to make the IGSD bot account and give access to the bogus and IGSD tables.
#"CREATE USER IF NOT EXISTS 'IGSD_Bot'@'%' IDENTIFIED BY 'password';
#GRANT ALL PRIVILEGES ON IGSD.* TO 'IGSD_Bot'@'%';