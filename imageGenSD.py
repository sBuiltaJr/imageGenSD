#Manages user requests through Discord to generate images with a Stable
#Diffusion model filepath supplied in the config.json file.  Cannot prevent
#Specific types of images, like NSFW, from being generated.


#####  Imports  #####

import asyncio
import discord as dis
from discord import app_commands as dac
import gzip
from PIL import Image as img
import logging as log
import logging.handlers as lh
import json
import requests as req
import os
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

#####  Package Classes  #####

class IGSDClient(dis.Client):
    def __init__(self, *, intents: dis.Intents):
        super().__init__(intents=intents)
        self.tree = dac.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=dis.Object(creds['guild_id']))
        await self.tree.sync(guild=dis.Object(creds['guild_id']))

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

       Input : None.

       Output : None.
    """
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')
    
        
@IGSD_client.tree.command()
async def testapiget(interaction: dis.Interaction):
    """A test HTTP GET command to verify basic connection to the webui page.

       Input : None.

       Output : None.
    """
    
    try:
        response = req.get(url=params['webui_URL'], timeout=5)
    except Exception as err:
        await interaction.response.send_message(f'Error sending GET request, got {err}!')
        return
    await interaction.response.send_message(f'GET got back: {response.status_code}, {response.reason}')
    
@IGSD_client.tree.command()
async def testapiput(interaction: dis.Interaction):
    """A test HTTP PUT command to verify basic connection to the webui page.

       Input : None.

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

    url = urljoin(params['webui_URL'], '/sdapi/v1/txt2img')
    disLog.info(f'URL is: {url}')
    disLog.debug(f'test parameters are: {test_params}')
    
    try:
        time.sleep(1)
        #response = req.post(url=url, json=test_params)
        #resp_img = response.json()
        
    except Exception as err:
        await interaction.response.send_message(f'Error sending PUT request, got {err}, {resp_img}!')
        return
    
    #Discord slash commands have a hard 3-second timeout.  Thus this must be
    #routed to a queue maanger.
    await interaction.response.send_message(f'Woo')#PUT got: {response.status_code}, {response.reason}')
    
#####  main  #####

def startup():
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

    disLog.debug(f'Starting Bot client')
    IGSD_client.run(creds['bot_token'])


if __name__ == '__main__':
    startup()
#asyncio.run(startup())

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