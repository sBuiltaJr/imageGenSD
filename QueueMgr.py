#Manages the job queue for processing IGSD images. Also handles reate limits
#nad other checks, including tracking guilds.
#
#A seaprate manager is reqruied by Discord becuase all slash commands have a
#Hard 3-second timeout.  Even modern HW is not yet able to meet this demand.



#####  Queue Object Class  #####
#The queue object is included since it's fairly small and probably won't change
#independently of the manager.  No reason to add a new file, yet.
class QueueObject:

    def __init__(self, object_id: int):
    """Queue Objects contain the prompt data passed by a slash command.  Their
       contents are passed to the Stable Diffusion engine when ready.

       Input: self - Pointer to the current object instance.
              id - A unique ID assigned by the manager for tracking.

       Output: None - Throws exceptions on error.

    """
        self.job_data = {}
        self.id       = object_id
        
# d|= args with args initially set to default Job Data
        
    def getDefaultJobData() -> dict:
    """Returns the default job settings that can be provided to an empty query
       (or to reinitialize an object).

       Input: None.

       Output: opts - a dictionary of the default queue arguments.
    """
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
    
#####  Manager Class  #####
class Manager:

    """Manages job request queueing and tracks relevant discord context, such
       as poster, guild, channel, etc.  The manager gets this from the caller
       so different managers could have different settings.

       Input: self - Pointer to the current object instance.
              manager_id - The current maanger's ID, assigned by the caller.
              opts - A dictionary of options, like cooldowns.
              
       Output: None - Throws exceptions on error.

    """
    def __init__(self, manager_id: int, opts: dict):
        self.id = manager_id
        #It's possible all opts are provided directly from config.json,
        #requriing them to be cast appropriately for the manager.  This also
        #allows the caller to never have to worry about casting the types
        #correctly for a config file and definition it doesn't own.
        self.depth          = int(opts['depth'])
        self.job_cooldown   = float(['job_cooldown'])
		self.max_guilds     = int(opts['max_guilds'])
		self.max_guild_reqs = int(opts['max_guild_reqs'])
		self.post_cooldown  = int(opts['post_cooldown'])
        
    def add(self, opts : dict) -> bool:
    
    def run(self):
    
        #This may, someday, need to be a proepr multiprocessing queue.
        jobs = [QueueObject(x) for x in range(self.depth)]
        
#Manager spawned as a separate task that does the managing.
    #Manager has a pipe to get jobs from main task (allowing 'await' to work)
    #Manager pends on pipe in add and adds to queue
        #Need to verify taht pipe and job processes don't lock eachother
#Jobs submitted as a separate process Manager awaits.
    #Concurrent futures to allow for multiple jobs.
    #Needs to not block add feature.
    