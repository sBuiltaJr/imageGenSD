#Manages the job queue for processing IGSD images. Also handles reate limits
#nad other checks, including tracking guilds.
#
#A seaprate manager is reqruied by Discord becuase all slash commands have a
#Hard 3-second timeout.  Even modern HW is not yet able to meet this demand.


#####  Imports  #####

import asyncio as asy
import logging as log
import multiprocessing as mp

jobs       = {}
#####  Package Functions  #####

"""    def getDefaultJobData() -> dict:
        Returns the default job settings that can be provided to an empty
           query (or to reinitialize an object).

           Input: None.

           Output: opts - a dictionary of the default queue arguments.
        
        return {
        'enable_hr'           : params['options']['HDR'],
        'denoising_strength'  : 0,
        'firstphase_width'    : 0,
        'firstphase_height'   : 0,
        'hr_scale'            : 2,
        'hr_upscaler'         : "string",
        'hr_second_pass_steps': 0,
        'hr_resize_x'         : 0,
        'hr_resize_y'         : 0,
        'prompt'              : params['options']['prompts'],
        'styles'              : ["string"],
        'seed'                : int(params['options']['seed']),
        'subseed'             : -1,
        'subseed_strength'    : 0,
        'seed_resize_from_h'  : -1,
        'seed_resize_from_w'  : -1,
        'sampler_name'        : "",
        'batch_size'          : 1,
        'n_iter'              : 1,
        'steps'               : int(params['options']['steps']),
        'cfg_scale'           : float(params['options']['cfg']),
        'width'               : int(params['options']['width']),
        'height'              : int(params['options']['height']),
        'restore_faces'       : False,
        'tiling'              : False,
        'do_not_save_samples' : False,
        'do_not_save_grid'    : False,
        'negative_prompt'     : params['options']['negatives'],
        'eta'                 : 0,
        's_churn'             : 0,
        's_tmax'              : 0,
        's_tmin'              : 0,
        's_noise'             : 1,
        'override_settings'   : {},
        'override_settings_restore_afterwards': True,
        'script_args'         : [],
        'sampler_index'       : "Euler",
        'script_name'         : "",
        'send_images'         : True,
        'save_images'         : params['options']['save_imgs'],
        'alwayson_scripts'    : {}
        }
"""    
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
        self.disLog     = log.getLogger('discord')
        self.id         = manager_id
        self.keep_going = True
        self.post_loop  = loop
        #It's possible all opts are provided directly from config.json,
        #requiring them to be cast appropriately for the manager.  This also
        #allows the caller to never have to worry about casting the types
        #correctly for a config file and definition it doesn't own.
        self.depth          = int(opts['depth'])
        self.job_cooldown   = float(opts['job_cooldown'])
        self.max_guilds     = int(opts['max_guilds'])
        self.max_guild_reqs = int(opts['max_guild_reqs'])
        self.post_cooldown  = float(opts['post_cooldown'])
        self.web_url        = opts['webui_URL']
        
        #This may eventually be implemented as a concurrent futures ProcessPool
        #to allow future versions to invoke workers across computers (e.g.
        #subprocess_exec with TCP/UDP data to/from a set of remote terminals).
        self.queue = mp.Queue(self.depth)
        
    def add(self, request : dict):
        """Passes queued jobs to the worker tasks.  Is effectively the 'main'
           of the class.  Workers return the image prompt and queue object id
           when compelte.  The Manager should post the result to the main thread
           via a pipe to allow simultaneous handling of commands and responses.

           Input: self - Pointer to the current object instance.
                  request - sanitized data to potentially add to the queue.
              
           Output: None - Results are posted to a pipe.
        """
        global jobs
        
        if request['data']['id'] not in jobs:
            jobs[request['data']['id']] = request
            self.disLog.debug(f"Added new request to id {request['data']['id']}.")
        else :
            self.disLog.debug(f"Request id {request['data']['id']} alraedy exists!")
            return
        
            #Else rate limit
        self.queue.put(request['data'])
    
    def PutRequest(self) :
        """Should be instantiated as an independent proecss for putting and
           getting data from the SD werver.  Results are provided back to the
           main IGSD thread viathe supplied event loop.  Has no knowledge of
           Guilds or how to post the provided image to the requestor.

            Input: pipe - where to return the SD image gen result.
                  
            Output: None - Throws exceptions on error.
        """
        global jobs
        
        while self.keep_going:
            self.disLog.info(f"Starting put to SD server at {self.web_url}.")
            result = self.queue.get()
            #actually put the job.
            job     = jobs.pop(result['id'])
            result |= job['metadata']
            job['metadata']['loop'].create_task(job['metadata']['ctx'].channel.send(result['reply']), name="reply")
            #job['metadata']['loop'].call_soon_threadsafe(job['metadata']['poster'], result, context=None)#Put response here instread
        return
        
    def run(self):
        """SHould spawn the process that puts job requests to the SD server.
           The job task uses the provided pipe to post results, the manager 
           only needs to wait for completion before starting another job.  Is
           the freamework for multiple concurrent jobs, but will need to be
           modified to actually support them.

           Input: self - Pointer to the current object instance.
              
           Output: None - Results are posted to a pipe.
        """
        self.disLog.info(f"Queue Manager {self.id} starting workers.")
        #This may, someday, need to be a proper multiprocessing queue.
        #jobs = [QueueObject(x) for x in range(self.depth)], in a loop

