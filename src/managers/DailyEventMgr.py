#Manages daily event timers and triggers.  Interfaces with the DB if needed.


#####  Imports  #####

import datetime as dt
import logging as log
import logging.handlers as lh
import pathlib as pl
import sched
import src.db.MariadbIfc as mdb
#import threading as th
import time


#####  Manager Class  #####

class DailyEventManager:

    def __init__(self,
                 opts : dict):
        """Schedules daily events for the system, like daily roll resets.

           Input: self - Pointer to the current object instance.
                  opts - a dict of options for this class.

           Output: None - Throws exceptions on error.
        """
        self.dem_log = log.getLogger('daily')
        self.dem_log.setLevel(opts['log_lvl'])
        log_path = pl.Path(opts['log_name_daily'])

        logHandler = lh.RotatingFileHandler(filename=log_path.absolute(),
                                            encoding=opts['log_encoding'],
                                            maxBytes=int(opts['max_bytes']),
                                            backupCount=int(opts['log_file_cnt']),
        )
        formatter = log.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}',
                                  opts['date_fmt'],
                                  style='{'
        )
        logHandler.setFormatter(formatter)
        self.dem_log.addHandler(logHandler)
        
        self.dem_log.debug(f"Creating DB Interface.")
        #The options are empty because the itnerface is a singleton and should
        #alraedy be initialized properly by the main thread.
        self.db_ifc = mdb.MariadbIfc.GetInstance(options={})
        self.sch = sched.scheduler(time.monotonic, time.sleep)

    #TODO: manage persistent state information.
    def Start(self):
        """Creates the initial events for the system.

           Input: self - Pointer to the current object instance.

           Output: None - Throws exceptions on error.
        """
        #TODO: each reset event should probably be its own thread with
        #independent timers.
        self.DailyRollReset()
        
    def DailyRollReset(self):
        """Resets the daily roll tracker for all users.

           Input: self - Pointer to the current object instance.

           Output: None.
        """
        self.db_ifc.ResetDailyRoll()