#Manages the job queue for processing IGSD images. Also handles rate limits and
#other checks, including tracking guilds.
#
#A seaprate manager is reqruied by Discord because all slash commands have a
#hard 3-second timeout.  Even modern HW is not yet able to meet this demand.


#####  Imports  #####

from ..utilities import JobFactory as jf
import logging as log
import logging.handlers as lh
import multiprocessing as mp
#from multiprocessing.queues import Queue
#from multiprocessing import get_context
import pathlib as pl
import requests as req
import time

jobs = {}

#####  Manager Class  #####

#class ManagedQueue(Queue):
#    """This overloads the default MP class to add useful basic functions, like
#       Queue flushing.
#    """

#    def __init__(self, maxsize=0, *, ctx=None):
#        ctx = get_context()
#        super().__init__(maxsize=maxsize, ctx=ctx)

#    def Flush(self, block=True, timeout=None):
#        """Empties the base cpython Queue to add useful features from the
#           underlying dequeue class that weren't exposed for some reason.
#           Is unable to cancel the current job being processed by the webui.
#
#           Inputs: self - Pointer to the current object instance.
#
#           Output: None.
#        """
#        if self._closed:
#            raise ValueError(f"Queue {self!r} is closed")
#        if not self._sem.acquire(block, timeout):
#            raise Full

#        with self._notempty:
#            if self._thread is None:
#                self._start_thread()
#            self._buffer.clear()
#            print(f"Cleared! {self.empty()}")
#            self._notempty.notify()

#####  Package Functions  #####

#####  Manager Class  #####

class Manager:

    def __init__(self,
                 manager_id : int,
                 opts       : dict):
        """Manages job job queueing and tracks relevant discord context,
           such as poster, Guild, channel, etc.  The Manager gets this from the
           caller so different Managers could have different settings.

           Input: self - Pointer to the current object instance.
                  manager_id - The current Manager's ID, assigned by the caller.
                  opts - A dictionary of options, like cooldowns.

           Output: None - Throws exceptions on error.
        """

        self.queue_log = log.getLogger('queue')
        self.queue_log.setLevel(opts['log_lvl'])
        log_path = pl.Path(opts['log_name_queue'])

        logHandler = lh.RotatingFileHandler(filename=log_path.absolute(),
                                            encoding=opts['log_encoding'],
                                            maxBytes=int(opts['max_bytes']),
                                            backupCount=int(opts['log_file_cnt'])
        )

        formatter = log.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}',
                                  opts['date_fmt'],
                                  style='{'
        )
        logHandler.setFormatter(formatter)
        self.queue_log.addHandler(logHandler)

        self.flush      = False
        self.id         = manager_id
        self.keep_going = True
        self.flush      = False
        #It's possible all opts are provided directly from config.json,
        #requiring them to be cast appropriately for the manager.  This also
        #allows the caller to never have to worry about casting the types
        #correctly for a config file and definition it doesn't own.
        self.depth          = int(opts['depth'])
        self.job_cooldown   = float(opts['job_cooldown'])
        self.max_guilds     = int(opts['max_guilds'])
        self.max_guild_reqs = int(opts['max_guild_reqs'])
        self.web_url        = opts['webui_URL']

        #This may eventually be implemented as a concurrent futures ProcessPool
        #to allow future versions to invoke workers across computers (e.g.
        #subprocess_exec with TCP/UDP data to/from a set of remote terminals).
        self.queue = mp.Queue(self.depth)

    def flush(self):
        """Sets the 'flush' flag true to enable the job queue to flush jobs
           when able.

           Input: self - Pointer to the current object instance.

           Output: none.
        """
        self.flush = True

    def add(self,
            metadata : dict,
            job  : jf.Job) -> str:
        """Passes queued jobs to the worker tasks.  Is effectively the 'main'
           of the class.  Workers return the image prompt and queue object id
           when complete.  The Manager should post the result to the main thread
           via a pipe to allow simultaneous handling of commands and responses.

           Input: self - Pointer to the current object instance.
                  metadata - Unpicklable data needed to post a result to Discord.
                  job - Sanitized data to potentially add to the queue.

           Output: str - Result of the job scheduling attempt.
        """
        global jobs

        #TODO: consider removing to have a single dict of 1 action per user to
        #ensure users can't submit multiple rolls.
        #TODO2: consider having non-affect commands (like show) go to a
        #different queue to allow the commands to process in parallel.
        #TODO3: consider having a lock around 2 trackers, 1 per user and 1 for
        #jobs per guild, to ensure 1 global job per user and limit spam
        #from a server (including user/account flooding from a server).
        if job.getGuild() not in jobs:

            if len(jobs) >= self.max_guilds :

                self.queue_log.warning(f"Trying to add guild {job.getGuild()} goes over Guild limit {self.max_guilds}!")
                return "Bot is currently servicing the maximum number of allowed Guilds."

            else:
                #Asyncio and Threading are suppose to be GIL safe, making this
                #safe.  Change this if that changes.
                jobs[job.getGuild()] = {}

        #This is a form of rate-limiting; limiting a guild to X posts instead
        #of attempting to track timing.
        if len(jobs[job.getGuild()]) >= self.max_guild_reqs:

            self.queue_log.warning(f"User {job.getUserId()}'s job excedded the Guild job limit {self.max_guild_reqs}!")

            if len(jobs[job.getGuild()]) == 0:

                del jobs[job.getGuild()]

            return "Unable to add your job, too many jobs from this Guild are already in the queue."

        #This isn't an elif to avoid duplicating the contents. ID is also only
        #deleted after the job is done, so this function always loses the race.
        if job.getUserId() not in jobs[job.getGuild()]:

            (jobs[job.getGuild()])[job.getUserId()] = metadata
            self.queue_log.debug(f"Added new job from Guild {job.getGuild()} to ID {job.getUserId()}.")

        else :

            self.queue_log.debug(f"Job id {job.getUserId()} alraedy exists!")
            #In the future, this can be modified by converting ID into a
            #snowflake, allowing users to post multiple jobs.
            return "You already have a job on the queue, please wait until it's finished."

            #Else rate limit
        try:

            #This is both the latest time possible to get the randomized tags
            #and the safest time, since a user's job is already recorded,
            #preventing them from spamming jobs if the randomizer takes a
            #long time for some reason.
            if job.getRandomize() :

                job.doRandomize(metadata['tag_rng'])

            #The Metadata can't be pickeled, meaning we can only send data
            #through the queue.
            self.queue.put(job)

        except queue.Full as err:

            (jobs[job.getGuild()]).pop(job.getUserId())
            self.queue_log.warning(f" Encountered a full queue for job with metadata: {job}, {err}!")

            return "The work queue is currently full, please wait a bit before making another job."

        except Exception as err:

            (jobs[job.getGuild()]).pop(job.getUserId())
            self.queue_log.error(f" Unable to add job to queue for job with metadata: {job}, {err}!")

            return "Unable to add your job to the queue.  Are you sending more than text and numbers?"

        return "Your job was added to the queue.  Please wait for it to finish before posting another."

    def putJob(self) :
        """Should be instantiated as an independent proecss for putting and
           getting data from the SD server.  Results are provided back to the
           main IGSD thread via the supplied event loop.  Has no knowledge of
           Guilds or how to post the provided image to the jobor.

            Input: self - Pointer to the current object instance.

            Output: None - Throws exceptions on error.
        """
        global jobs

        while self.keep_going:

            if self.flush:
#                self.queue.flush()
                self.flush = False
                continue

            job = self.queue.get()

            self.queue_log.debug(f"Job is: {job}")
            try:
                job.doWork(web_url=self.web_url)

            except Exception as err:
                self.queue_log.error(f"Exception doing work for Job: {err}, {job}.")

            if len(jobs[job.getGuild()]) == 0:

                self.queue_log.debug(f"Removing empty Guild {job.getGuild()} from the list.")
                del jobs[job.getGuild()]

            metadata = (jobs[job.getGuild()]).pop(job.getUserId())
            self.queue_log.debug(f"Posting job result to Discord from metadata: {metadata}")
            metadata['loop'].create_task(metadata['post_fn'](job=job, metadata=metadata),
                                         name="reply")

            if self.job_cooldown > 0.0:

                time.sleep(self.job_cooldown)
        return

    def run(self):
        """Should spawn the process that puts job jobs to the SD server.
           Is the freamework for multiple concurrent jobs, but will need to be
           modified to actually support them.

           Input: self - Pointer to the current object instance.

           Output: None - Results are posted to a pipe.
        """
        self.queue_log.info(f"Queue Manager {self.id} starting workers.")
        #This may, someday, need to be a proper multiprocessing queue.
        #jobs = [QueueObject(x) for x in range(self.depth)], in a loop
