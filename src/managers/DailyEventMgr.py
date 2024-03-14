#Manages daily event timers and triggers.  Interfaces with the DB if needed.


#####  Imports  #####

import datetime as dt
import logging as log
import logging.handlers as lh
import pathlib as pl
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
        #The options are empty because the interface is a singleton and should
        #already be initialized properly by the main thread.
        self.db_ifc      = mdb.MariadbIfc.getInstance(options={})
        self.keep_going  = True
        self.roll_thread = None

    #TODO: manage persistent state information.
    def start(self):
        """Creates the initial events for the system.

           Input: self - Pointer to the current object instance.

           Output: None - Throws exceptions on error.
        """

        self.dem_log.debug(f"Starting the Roll reset scheduler.")
        #Youd think I could just use sched, but sched.run() will immediately
        #run the queue contents, regardless of the actual delay time, making
        #the actual event scheduling pointless and quickly devolving into an
        #unblocked while loop.
        #So a separate thread with blunt sleep it is.
        self.roll_thread = th.Thread(target=self.dailyRollReset,
                                     name="Daily Roll Reset Thread",
                                     daemon=True)
        self.roll_thread.start()

    def dailyRollReset(self):
        """Resets the daily roll tracker for all users.

           Input: self - Pointer to the current object instance.

           Output: None.
        """

        while self.keep_going:
            #This MUST be first to prevent auto-reset of the flag on reset.
            #It does meam a restart spanning a UTC midnight will not reset
            #until the next day, but it's an acceptable edge case.
            #TODO: find a nice way to force a manual refresh command owned only
            #by the bot/DB owner.
            today      = dt.datetime.now(dt.timezone.utc)
            now        = dt.datetime.now(dt.timezone.utc)
            midnight   = now.replace(hour=0, minute=0, second=0, microsecond=0)
            delay_time = 60*60*24 - (now - midnight).seconds
            self.dem_log.debug(f"Calculated the following for the next reset: {now} {midnight} delay_time: {delay_time}.")
            time.sleep(delay_time)

            self.dem_log.warning(f"Resetting daily rolls!")
            try:

                self.db_ifc.resetDailyRoll()
                self.dem_log.info(f"Daily roll reset complete")

            except Exception as err:

                self.dem_log.error(f"Unable to reset the daily rolls!: {err=}")
                self.keep_going = False

            self.dem_log.info(f"Scheduling the next reset.")