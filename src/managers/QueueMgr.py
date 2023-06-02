#Manages the job queue for processing IGSD images. Also handles rate limits and
#other checks, including tracking guilds.
#
#A seaprate manager is reqruied by Discord because all slash commands have a
#hard 3-second timeout.  Even modern HW is not yet able to meet this demand.


#####  Imports  #####

import logging as log
import multiprocessing as mp
#from multiprocessing.queues import Queue
#from multiprocessing import get_context
import queue
import requests as req
from urllib.parse import urljoin
from ..utilities import TagRandomizer as tr
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

    def __init__(self, loop, manager_id: int, opts: dict):
        """Manages job request queueing and tracks relevant discord context,
           such as poster, Guild, channel, etc.  The Manager gets this from the
           caller so different Managers could have different settings.

           Input: self - Pointer to the current object instance.
                  loop - The asyncio event loop this manager posts to.
                  manager_id - The current Manager's ID, assigned by the caller.
                  opts - A dictionary of options, like cooldowns.
              
           Output: None - Throws exceptions on error.
        """
        self.flush      = False
        self.id         = manager_id
        self.keep_going = True
        self.post_loop  = loop
        self.queLog     = log.getLogger('queue')
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
        
        #Currently it doesn't make sense for a queue to create multiple
        #randomizers since jobs are processed serially.  This may need to
        #change if the jobs are ever made parallel.
        #
        #This call also assumes opts['rand_dict_path'] has been sanitized by
        #the parent before being passed down.
        self.randomizer = tr.TagRandomizer(opts['rand_dict_path'],
                                           int(opts['dict_size']),
                                           int(opts['max_rand_tag_cnt']),
                                           int(opts['min_rand_tag_cnt']))

    def Flush(self):
        """Sets the 'flush' flag true to enable the job queue to flush jobs
           when able.  

           Input: self - Pointer to the current object instance.
              
           Output: none.
        """
        self.flush = True
        
    def Add(self, request : dict) -> str:
        """Passes queued jobs to the worker tasks.  Is effectively the 'main'
           of the class.  Workers return the image prompt and queue object id
           when complete.  The Manager should post the result to the main thread
           via a pipe to allow simultaneous handling of commands and responses.

           Input: self - Pointer to the current object instance.
                  request - Sanitized data to potentially add to the queue.
              
           Output: str - Result of the job scheduling attempt.
        """
        global jobs
        
        if request['data']['guild'] not in jobs:
        
            if len(jobs) >= self.max_guilds :
            
                self.queLog.warning(f"Trying to add guild {request['data']['guild']} goes over Guild limit {self.max_guilds}!")
                return "Bot is currently servicing the maximum number of allowed Guilds."
                
            else:
                #Asyncio and Threading are suppose to be GIL safe, making this
                #safe.  Change this if that changes.
                jobs[request['data']['guild']] = {}
        
        #This is a form of rate-limiting; limiting a guild to X posts instead
        #of attempting to track timing.
        if len(jobs[request['data']['guild']]) >= self.max_guild_reqs:
        
            self.queLog.warning(f"User {request['data']['id']}'s request excedded the Guild request limit {self.max_guild_reqs}!")
            
            if len(jobs[request['data']['guild']]) == 0:
            
                del jobs[request['data']['guild']]
            
            return "Unable to add your job, too many requests from this Guild are already in the queue."
            
        #This isn't an elif to avoid duplicating the contents. ID is also only
        #deleted after the job is done, so this function always loses the race.
        if request['data']['id'] not in jobs[request['data']['guild']]:
        
            (jobs[request['data']['guild']])[request['data']['id']] = request['metadata']
            self.queLog.debug(f"Added new request from Guild {request['data']['guild']} to ID {request['data']['id']}.")
            
        else :
        
            self.queLog.debug(f"Request id {request['data']['id']} alraedy exists!")
            #In the future, this can be modified by converting ID into a
            #snowflake, allowing users to post multiple jobs.
            return "You already have a job on the queue, please wait until it's finished."
        
            #Else rate limit
        try:
        
            #This is both the latest time possible to get the randomized tags
            #and the safest time, since a user's request is already recorded,
            #preventing them from spamming requests if the randomizer takes a
            #long time for some reason.
            if request['data']['post']['random'] == True:
                tags = tr.getRandomTags()
            
            #The Metadata can't be pickeled, meaning we can only send data
            #through the queue.
            self.queue.put(request['data'])
            
        except queue.Full as err:
        
            (jobs[request['data']['guild']]).pop(request['data']['id'])
            self.queLog.warning(f" Encountered a full queue for request with metadata: {request['data']}, {err}!")
            
            return "The work queue is currently full, please wait a bit before making another request."
            
        except Exception as err:
        
            (jobs[request['data']['guild']]).pop(request['data']['id'])
            self.queLog.error(f" Unable to add job to queue for request with metadata: {request['data']}, {err}!")
            
            return "Unable to add your job to the queue.  Are you sending more than text and numbers?"
            
        return "Your job was added to the queue.  Please wait for it to finish before posting another."
    
    def GetDefaultJobData(self) -> dict:
        """Returns the default job settings that can be provided to an empty
           query (or to reinitialize an object).

           Input: None.

           Output: opts - a dictionary of the default queue arguments.
        """
        return {
        'enable_hr'           : True,
        'denoising_strength'  : 0.35,
        'firstphase_width'    : 0,
        'firstphase_height'   : 0,
        'hr_scale'            : 2,
        'hr_upscaler'         : "4x-AnimeSharp",
        'hr_second_pass_steps': 10,
        'hr_resize_x'         : 1024,
        'hr_resize_y'         : 1536,
        'prompt'              : "detailed background, masterpiece, best quality, 1girl, white dress, dress, short sleeves, strapless dress, frills, thighhigh stockings, black thighhighs, boots, red hair, long hair, medium breasts, blush, slight smile, painting, paintbrush, eyebrows visible through hair, standing, easel, paint, blue eyes, brown shoes, bangs, canvas \(object\), holding paintbrush, braid, braided hair, painting \(object\), bow, yellow bow, hands up, hair ornament, indoors, cute,",
        'styles'              : ["string"],
        'seed'                : 2920639719,
        'subseed'             : -1,
        'subseed_strength'    : 0,
        'seed_resize_from_h'  : -1,
        'seed_resize_from_w'  : -1,
        'sampler_name'        : "",
        'batch_size'          : 1,
        'n_iter'              : 1,
        'steps'               : 50,
        'cfg_scale'           : 22.0,
        'width'               : 512,
        'height'              : 768,
        'random'              : False,
        'restore_faces'       : False,
        'tiling'              : False,
        'do_not_save_samples' : False,
        'do_not_save_grid'    : False,
        'negative_prompt'     : "(low quality, worst quality:1.4), (bad anatomy), extra digit, fewer digits, (extra arms:1.2), bad hands, by (bad-artist:0.6), bad-image-v2-39000, NSFW, nipples, loli, child, children, shota, boy, male, men, man",
        'eta'                 : 0,
        's_churn'             : 0,
        's_tmax'              : 0,
        's_tmin'              : 0,
        's_noise'             : 1,
        'override_settings'   : {},
        'override_settings_restore_afterwards': True,
        'script_args'         : [],
        'sampler_index'       : "DPM++ 2M Karras",
        'script_name'         : "",
        'send_images'         : True,
        'save_images'         : True, #Should probably limit ability to run test command
        'alwayson_scripts'    : {}
        }
        
    def PutRequest(self) :
        """Should be instantiated as an independent proecss for putting and
           getting data from the SD werver.  Results are provided back to the
           main IGSD thread via the supplied event loop.  Has no knowledge of
           Guilds or how to post the provided image to the requestor.

            Input: pipe - where to return the SD image gen result.
                  
            Output: None - Throws exceptions on error.
        """
        global jobs
        
        while self.keep_going:
        
            if self.flush:
#                self.queue.Flush()
                self.flush = False
                continue
            request            = self.queue.get()
            result             = req.Response()
            result.status_code = 404
            result.reason      = "Exception Running Job, try again later."
            jres               = {}
            
            #Have a special check for the GET test, which doesn't expect to get
            #any data from an actual job.
            if request['id'] == "testgetid" or ((not (isinstance(request['id'], str))) and (request['id'] < 10)):
            
                self.queLog.debug(f"Performing GET test of URL: {self.web_url}.")
                try:
                    result = req.get(url=urljoin(self.web_url, '/sdapi/v1/memory'), timeout=5)
                    
                except Exception as err:
                    self.queLog.error(f"Exception trying to GET: {err}.")
                
            else:

                self.queLog.info(f"Starting PUT to SD server at {self.web_url}.")
                try:
                    result = req.post(url=urljoin(self.web_url, '/sdapi/v1/txt2img'), json=request['post'])
                    jres   = result.json()
                    
                except Exception as err:
                    self.queLog.error(f"Exception trying to PUT: {err}.")
                    

            jres['status_code'] = result.status_code
            jres['reason']      = result.reason
            jres['id']          = request['id'] #TODO this shouldn't be necessary
            jres['random']      = request['post']['random']
            #Pop last to ensure a new request from the same ID can be added
            #only after their first request is completed.
            job     = (jobs[request['guild']]).pop(request['id'])
            jres   |= job
            
            if len(jobs[request['guild']]) == 0:
            
                self.queLog.debug(f"Removing empty Guild {request['guild']} from the list.")
                del jobs[request['guild']]
                
            job['loop'].create_task(job['poster'](msg=jres), name="reply")
            
            if self.job_cooldown > 0.0:
            
                time.sleep(self.job_cooldown)
        return
        
    def Run(self):
        """Should spawn the process that puts job requests to the SD server.
           Is the freamework for multiple concurrent jobs, but will need to be
           modified to actually support them.

           Input: self - Pointer to the current object instance.
              
           Output: None - Results are posted to a pipe.
        """
        self.queLog.info(f"Queue Manager {self.id} starting workers.")
        #This may, someday, need to be a proper multiprocessing queue.
        #jobs = [QueueObject(x) for x in range(self.depth)], in a loop
