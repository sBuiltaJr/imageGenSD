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
import threading as th
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
job_queue = ()
worker = ()

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

    async def setup_hook(self):
        """Copies the global command set to a given Guild instance.

            Input  : self - a reference to the current object.

            Output : None
        """
        
        #Replies should be managed in a separate task to allow the main UI to
        #always be responsive, and allow the backend to process work independent
        #of message posting.  It's more efficent and better separated.
        self.loop = asy.get_running_loop()
        
        self.tree.copy_global_to(guild=dis.Object(creds['guild_id']))
        self.disLog.debug(f"Syncing Guild Tree to {creds['guild_id']}.")
        
        await self.tree.sync(guild=dis.Object(creds['guild_id']))
        
    def GetLoop(self):
        """Returns a reference to this client's asyncio event loop.

            Input  : self - a reference to the current object.

            Output : loop - the client's event loop.
        """
        return self.loop;
        
    def Post(self, msg : dict):
        """Posts the provided message to the specified discord channel. Invoked
           by the Queue Manager since all these asyncio tasks fall under a
           single event loop that will hang if waiting for a pipe, thus hanging
           all active tasks (and the thread).

            Input  : self - a reference to the current object.
                     msg - what to post, where, and whom to notify.

            Output : None.
        """
        self.disLog.debug(f"Posting the message {msg}")
        #Evaluate the message and identify any quit requests.
        #await msg['ctx'].channel.send(msg['reply'])
        self.loop.create_task(msg['ctx'].channel.send(msg['reply']), name="reply")

intents = dis.Intents.default()
IGSD_client = IGSDClient(intents=intents)

#####  Package Functions  #####

@IGSD_client.event
async def on_ready():
    global job_queue
    global worker
    
    disLog = log.getLogger('discord')
    disLog.info(f'Logged in as {IGSD_client.user} (ID: {IGSD_client.user.id})')
    
    disLog.debug(f"Creating Queue Manager)")
    job_queue = qm.Manager(IGSD_client.GetLoop(), 1, params['queue_opts'])
    worker    = th.Thread(target=job_queue.PutRequest, name="worker")
    worker.start()
    
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
async def testinternalloop(interaction: dis.Interaction):
    """Pushes a test message through internal pipes only, no PUT to the SD server.

       Input  : None.

       Output : None.
       
       Note: All slash commands *MUST* respond in 3 seconds or be terminated.
    """
    disLog = log.getLogger('discord')

    #url = urljoin(params['webui_URL'], '/sdapi/v1/txt2img')
    #disLog.info(f'URL is: {url}')
    #disLog.debug(f'test parameters are: {test_params}')
    msg = { 'metadata' : {
            'ctx' : interaction,
            'loop' : IGSD_client.GetLoop(),
            'poster' : IGSD_client.Post
            },
        'data' : {
            'id' : 'testpostid',
            'reply' : "test msg"
            }
        }
    disLog.debug(f"Posting job {msg} to the queue") 
    job_queue.add(msg)
    
    #Discord slash commands have a hard 3-second timeout.  Thus this must be
    #routed to a queue maanger.
    await interaction.response.send_message(f'Posted Test Message to work queue.')

@IGSD_client.tree.command()
async def testpost(interaction: dis.Interaction):
    """A test HTTP PUT command to verify basic connection to the webui page.

       Input  : None.

       Output : None.
       
       Note: All slash commands *MUST* respond in 3 seconds or be terminated.
    """
    await interaction.response.send_message(f'Posted Test Message to work queue.')
       
#####  main  #####

def Startup():
    """Updates the global dictionary with the supplied configuration, if it
       exists, and starts the program.

       Input : None (yet).

       Output : None.
    """
    global params
    global creds
    global job_queue
    
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
    
    #Start manager tasks
    disLog.debug(f"Starting Bot client")
    IGSD_client.run(creds['bot_token'])


if __name__ == '__main__':
    Startup()

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