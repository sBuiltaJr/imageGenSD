#Manages the job queue for processing IGSD images. Also handles reate limits
#nad other checks, including tracking guilds.
#
#A seaprate manager is reqruied by Discord becuase all slash commands have a
#Hard 3-second timeout.  Even modern HW is not yet able to meet this demand.


#####  Imports  #####

import logging as log
import multiprocessing as mp
import requests as req
from urllib.parse import urljoin

jobs = {}
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
        
    def Add(self, request : dict):
        """Passes queued jobs to the worker tasks.  Is effectively the 'main'
           of the class.  Workers return the image prompt and queue object id
           when compelte.  The Manager should post the result to the main thread
           via a pipe to allow simultaneous handling of commands and responses.

           Input: self - Pointer to the current object instance.
                  request - sanitized data to potentially add to the queue.
              
           Output: None - Results are posted to a pipe.
        """
        global jobs
        
        if request['metadata']['id'] not in jobs:
            jobs[request['metadata']['id']] = request['metadata']
            self.disLog.debug(f"Added new request to id {request['metadata']['id']}.")
        else :
            self.disLog.debug(f"Request id {request['metadata']['id']} alraedy exists!")
            return
        
            #Else rate limit
        #The Metadata can't be pickeled, meaning we can only send data through the queue.
        self.queue.put(request['data'])
    
    def GetDefaultJobData(self) -> dict:
        """Returns the default job settings that can be provided to an empty
           query (or to reinitialize an object).

           Input: None.

           Output: opts - a dictionary of the default queue arguments.
        """
        return {
        'enable_hr'           : False,
        'denoising_strength'  : 0,
        'firstphase_width'    : 0,
        'firstphase_height'   : 0,
        'hr_scale'            : 2,
        'hr_upscaler'         : "string",
        'hr_second_pass_steps': 0,
        'hr_resize_x'         : 0,
        'hr_resize_y'         : 0,
        'prompt'              : "(exceptional, best aesthetic, best quality, masterpiece, extremely detailed:1.2), white dress, dress, short sleeves, strapless dress, frills, thighhigh stockings, black thighhighs, boots, red hair, long hair, medium breasts, blush, slight smile, painting, paintbrush, eyebrows visible through hair, standing, easel, paint, blue eyes, brown shoes, bangs, canvas (object), holding paintbrush, braid, braided hair, painting (object), bow, yellow bow, hands up, hair ornament, indoors, cute,",
        'styles'              : ["string"],
        'seed'                : -1, #Should really identify which seed IGSD used for itself.
        'subseed'             : -1,
        'subseed_strength'    : 0,
        'seed_resize_from_h'  : -1,
        'seed_resize_from_w'  : -1,
        'sampler_name'        : "",
        'batch_size'          : 1,
        'n_iter'              : 1,
        'steps'               : 70,
        'cfg_scale'           : 22.0,
        'width'               : 512,
        'height'              : 512,
        'restore_faces'       : False,
        'tiling'              : False,
        'do_not_save_samples' : False,
        'do_not_save_grid'    : False,
        'negative_prompt'     : " Negative prompt: lowres, ((bad anatomy)), ((bad hands)), text, missing finger, extra digits, fewer digits, blurry, ((mutated hands and fingers)), (poorly drawn face), ((mutation)), ((deformed face)), (ugly), ((bad proportions)), ((extra limbs)), extra face, (double head), (extra head), ((extra feet)), monster, logo, cropped, worst quality, jpeg, humpbacked, long body, long neck, ((jpeg artifacts)), deleted, old, oldest, ((censored)), ((bad aesthetic)), (mosaic censoring, bar censor, blur censor),  watermark, (low quality, worst quality:1.4), (bad anatomy), extra digit, fewer digits, (extra arms:1.2), bad hands, by (bad-artist:0.6), bad-image-v2-39000, NSFW, nipples, loli, child, children, shota, boy, male, men, man",
        'eta'                 : 0,
        's_churn'             : 0,
        's_tmax'              : 0,
        's_tmin'              : 0,
        's_noise'             : 1,
        'override_settings'   : {},
        'override_settings_restore_afterwards': True,
        'script_args'         : [],
        'sampler_index'       : "DPM++ SDE Karras",
        'script_name'         : "",
        'send_images'         : True,
        'save_images'         : True, #Should probably limit ability to run test command
        'alwayson_scripts'    : {}
        }
        
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
            request = self.queue.get()
            jres = {}
            
            #Have a special check for the GET test, which doesn't expect to get
            #any data from an actual job.
            if request['id'] == "testgetid":
                self.disLog.debug(f"Performing GET test of URL: {self.web_url}.")
                result = req.get(url=urljoin(self.web_url, '/sdapi/v1/memory'), timeout=5)
            
            else:
                self.disLog.info(f"Starting put to SD server at {self.web_url}.")
                result  = req.post(url=urljoin(self.web_url, '/sdapi/v1/txt2img'), json=request['post'])
                jres    = result.json()

            jres['status_code'] = result.status_code
            jres['reason']      = result.reason
            #Pop last to ensure a new request from the same ID can be added
            #only after their first request is completed.
            job     = jobs.pop(request['id'])
            jres   |= job
            job['loop'].create_task(job['poster'](msg=jres), name="reply")
        return
        
    def Run(self):
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

