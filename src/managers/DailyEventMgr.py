#Manages daily event timers and triggers.  Interfaces with the DB if needed.


#####  Imports  #####

import datetime as dt
import logging as log
import logging.handlers as lh
import pathlib as pl
import sched
import src.db.MariadbIfc as mdb
import threading as th
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
        self.db_log = log.getLogger('daily')
        self.db_log.setLevel(opts['log_lvl'])
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
        self.db_log.addHandler(logHandler)
        
        self.db_log.info(f"Creating Daily Reset thread.")
        self.daily_reset_thread = th.Thread(target=DailyEventManager.DailyRollReset,
                                            name="Daily Reset Thread",
                                            daemon=True)
        
        self.sch = sched.scheduler(time.monotonic, time.sleep)

    #TODO: manage persistent state information.
    def Start(self):
        """Creates the initial events for the system.

           Input: self - Pointer to the current object instance.

           Output: None - Throws exceptions on error.
        """
        self.daily_reset_thread.start()
        
    def DailyRollReset():
        """Resets the daily roll tracker for all users.

           Input: self - Pointer to the current object instance.

           Output: None.
        """
        pass