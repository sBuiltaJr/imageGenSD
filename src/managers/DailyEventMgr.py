#Manages daily event timers and triggers.  Interfaces with the DB if needed.


#####  Imports  #####

import datetime as dt
import logging as log
import pathlib as pl
import sched
import time


#####  Manager Class  #####

class DailyEventManager:

    def __init__(self
                 options : dict):
        """Schedules daily events for the system, like daily roll resets.

           Input: self - Pointer to the current object instance.
                  options - a dict of options for this class.

           Output: None - Throws exceptions on error.
        """
        self.db_log = log.getLogger('daily')
        self.db_log.setLevel(options['log_lvl'])
        log_path = pl.Path(options['log_name_daily'])

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
        
        self.sch = sched.scheduler(time.monotonic, time.sleep)

    #TODO: manage persistent state information.
    def Start(self):
        """Creates the initial events for the system.

           Input: self - Pointer to the current object instance.

           Output: None - Throws exceptions on error.
        """
        
        
        
    def DailyRollReset():
        """Resets the daily roll tracker for all users.

           Input: self - Pointer to the current object instance.

           Output: None.
        """