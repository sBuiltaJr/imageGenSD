#Manages user requests through Discord to generate images with a Stable
#Diffusion model filepath supplied in the config.json file.  Cannot prevent
#Specific types of images, like NSFW, from being generated.


#####  Imports  #####

import asyncio as asy
import discord as dis
from discord import app_commands as dac
#import gzip
import logging as log
import logging.handlers as lh
import json
import multiprocessing as mp
import os
from PIL import Image as img
import QueueMgr as qm
import requests as req
import shutil as sh
import time
from urllib.parse import urljoin

#####  Package Variables  #####

#The great thing about package-level dictionaries is their global (public-like)
#capability, avoiding constant passing down to 'lower' defs. 
#Static data only, no file objects or similar (or else!).
creds = {}
default_params = {'cfg'       : 'config.json',
                  'cred'      : 'credentials.json',
                  'bot_token' : ''}
IGSD_version = '0.0.2'
params = {}
#This should be expanded to allow multiple pipes (and thus managers) eventually.
pipes = ()

#####  Package Classes  #####

class IGSDClient(dis.Client):
    def __init__(self, *, intents: dis.Intents):
        """This command copies the global command set to a given Guild instance.

            Input  : self - a reference to the current object.
                     intents - what Discord intents are required to run the bot.

            Output : None
        """
        self.disLog = log.getLogger('discord')
        self.disLog.debug(f"Intents are: {intents}")
        
        super().__init__(intents=intents)
        self.tree = dac.CommandTree(self)
        
        #This pipe must be made here so it can be passed to the response task
        #as it's generaetd.  This init is called before IGSD's main and thus
        #can't be passed into the function at runtime.
        self.disLog.info(f"Creating the posting pipes.")
        self.post_pipes = mp.Pipe(False)
        self.disLog.debug(f"Created request pipes {self.post_pipes}.")

    async def setup_hook(self):
        """Copies the global command set to a given Guild instance.

            Input  : self - a reference to the current object.

            Output : None
        """
        
        #Replies are managed in a separate task to allow the main UI to always
        #be responsive, and allow the backend to process work independent of
        #message posting.  It's more efficent and better separated.
        self.disLog.info(f'"Starting response task.")
        #Pipe 1 is always the recieve pipe.
        self.poster = asy.create_task(self.Post(self.post_pipes[0]), name='Poster')
        self.disLog.debug(f"Created poster task {self.poster}.")
        
        self.tree.copy_global_to(guild=dis.Object(creds['guild_id']))
        
        await self.tree.sync(guild=dis.Object(creds['guild_id']))
        
    async def Post(self, rx_pipe):
        """Posts the provided message to the specified discord channel.  Runs as
            a asyncio subtask unber the main class to prevent hanging.

            Input  : self - a reference to the current object.
                     msg - what to post, where, and whom to notify.

            Output : None.
        """
        #Post is run as a separate task, requiring its own logger reference.
        disLog = log.getLogger('discord')
        keep_posting = True
        
        while keep_posting:
            msg = rx_pipe.recv()
            disLog.debug(f"got the message {msg}")
            #Evaluate the message and identify any quit requests.
            await interaction.response.send_message(f'lol')
        return
    
    def GetPipe(self):
        """Returns the message posting pipe for this object.  Each object must
           own its posting pipe due to inheritance issues. This should only need
           to be fetched once per object.

            Input  : self - a reference to the current object.

            Output : connection - the input pipe for passing messages to the task.
        """
        #Pipes are returned as a tuple with the first element as the input.
        return self.response_pipes[1]
        
    def __exit__(self, exec_type, exec_value, traceback):
        """Runs as one of the final calls befoer an object is destroyed. Explicitly
           implemented to ensure the Post task and pipes are properly disposed.

            Input  : self - a reference to the current object.
                     exec_type - the type of exception that caused this call.
                     exec_value - the value of the exception that caused this call.
                     traceback - the stack involved in the exception call.

            Output : connection - the input pipe for passing messages to the task.
        """
        #Empty the pipe, if not already empty.  This is to flush any items left
        #and avoid the deadlock mentioned in the multiprocessing.Pipe docs
        for pipe in self.post_pipes:
        
            while pipe.poll(0):
            
                trash = pipe.recv()
            pipe.close()
        
        #Ensure the post task is properly deleted.
        self.poster.cancel()

intents = dis.Intents.default()
IGSD_client = IGSDClient(intents=intents)

#####  Package Functions  #####

@IGSD_client.event
async def on_ready():
    disLog = log.getLogger('discord')
    disLog.info(f'Logged in as {IGSD_client.user} (ID: {IGSD_client.user.id})')
    print('------')
    
@IGSD_client.tree.command()
async def hello(interaction: dis.Interaction):
    """A test echo command to verify basic discord functionality.

       Input  : None.

       Output : None.
    """
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')
    
        
@IGSD_client.tree.command()
async def testapiget(interaction: dis.Interaction):
    """A test HTTP GET command to verify basic connection to the webui page.

       Input  : None.

       Output : None.
    """
    
    try:
        #This should proabbly be moved to a manager since there may eventually
        #be multiple IP addresses.
        response = req.get(url=params['queue_opts']['webui_URL'], timeout=5)
    except Exception as err:
        await interaction.response.send_message(f"Error sending GET request, got {err}!")
        return
    await interaction.response.send_message(f"GET got back: {response.status_code}, {response.reason}")
    
@IGSD_client.tree.command()
async def testpost(interaction: dis.Interaction):
    """A test HTTP PUT command to verify basic connection to the webui page.

       Input  : None.

       Output : None.
       
       Note: All slash commands *MUST* respond in 3 seconds or be terminated.
    """
    disLog = log.getLogger('discord')
    test_params = {
        'enable_hr'           : False,#bool(params['options']['HDR']),
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
        'save_images'         : True,
        'alwayson_scripts'    : {}
    }

    #url = urljoin(params['webui_URL'], '/sdapi/v1/txt2img')
    #disLog.info(f'URL is: {url}')
    #disLog.debug(f'test parameters are: {test_params}')
    
    try:
        #time.sleep(1)
        #response = req.post(url=url, json=test_params)
        #resp_img = response.json()
        
    except Exception as err:
        disLog.error(f"Exception posting mesasge to poster task: {err}")
        await interaction.response.send_message(f"Error sending message to poster task!")
        return
    
    #Discord slash commands have a hard 3-second timeout.  Thus this must be
    #routed to a queue maanger.
    await interaction.response.send_message(f'Woo')#PUT got: {response.status_code}, {response.reason}')

#####  main  #####

def Startup():
    """Updates the global dictionary with the supplied configuration, if it
       exists, and starts the program.

       Input : None (yet).

       Output : None.
    """
    global params
    global creds
    
    #This will be modified in the future to accept user-supplied paths.
    #This file must be loaded prior to the logger to allow for user-provided
    #options to be passed to the Logger.  Thus it must have special error
    #handling outside of the logger class.
    with open(default_params['cfg']) as json_file:
        params = json.load(json_file)
        
    disLog = log.getLogger('discord')
    disLog.setLevel(params['log_lvl'])

    logHandler = lh.RotatingFileHandler(
        filename=params['log_name'],
        encoding=params['log_encoding'],
        maxBytes=int(params['max_bytes']),
        backupCount=int(params['log_file_cnt']),
    )
    
    formatter = log.Formatter(
        '[{asctime}] [{levelname:<8}] {name}: {message}', 
        params['date_fmt'],
        style='{'
    )
    logHandler.setFormatter(formatter)
    disLog.addHandler(logHandler)
    
    #This will be modified in the future to accept user-supplied paths.
    try:
        with open(default_params['cred']) as json_file:
            creds = json.load(json_file)

    except OSError as err:
        disLog.critical(f"Can\'t load file from path {default_params['cred']}")
        exit(1)


    disLog.debug(f"Starting IPC (pipe)")
    #Currently there's no need to have a duplex pipe; put will throw an exception
    #on full and there's no other useful status to return.  This will need to
    #change if the assumption ever changes.
    pipes = mp.Pipe(False)
    
    #Start manager tasks
    disLog.debug(f"Starting Bot client")
    IGSD_client.run(creds['bot_token'])
    print(f"After client start")


if __name__ == '__main__':
    Startup()
#asy.run(startup())

#Supported commands:
#/flush:   clear queue and kill active jobs (if possible).  Needs Owern/Admin to run.
#/Restart: Flush + recreates the queue objects.  Effectively restarts teh script.  Also requries Owner.
#/Cancel:  Kills most recent request from the poster, if possible. 
#Have the slash command inherently check rate limit against user ID.
# Raete limiting:
    # 1) Limit per guild (X requests in X seconds and Y total requests).
        #Check limits before accepting job to queue.
        #respond error if full
        #Adds req. to guild dict (including making) and timestamp.
            #Only need 'last added' tiemstamp, limiting input not output. (jobs only produce one file)
        #Support X number of guidls in config.
    # 2) Allow configruable options later (Owner/inviter config commands, also in JSON)
    # 3) Check Guild limits against dict size storing data (unique dicts per guild)
    # 4) Queue msut be deep enough to handle guild sizes (multi-queue probably too painful)
    # 5) No limit on specific user spam (yet).  May not be neede dwit Guild limit.
    # 6) Worker pool(of 1 for now, ac nfarm with expansion) pops form queue and reports guild ID when complete.
    # 7) Handler deletes entries from guild dict.