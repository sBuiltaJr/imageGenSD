#Manages user requests through Discord to generate images with a Stable
#Diffusion model filepath supplied in the config.json file.  Cannot prevent
#Specific types of images, like NSFW, from being generated.


#####  Imports  #####

import asyncio as asy
import base64 as b64
import discord as dis
from discord import app_commands as dac
import io
import logging as log
import logging.handlers as lh
import json
import multiprocessing as mp
import os
import QueueMgr as qm
import requests as req
import threading as th
from typing import Optional

#####  Package Variables  #####

#The great thing about package-level dictionaries is their global (public-like)
#capability, avoiding constant passing down to 'lower' defs. 
#Static data only, no file objects or similar (or else!).
creds = {}
default_params = {'cfg'       : 'config.json',
                  'cred'      : 'credentials.json',
                  'bot_token' : ''}
IGSD_version = '0.1.0'    
#This will be modified in the future to accept user-supplied paths.
#This file must be loaded prior to the logger to allow for user-provided
#options to be passed to the Logger.  Thus it must have special error
#handling outside of the logger class.
with open(default_params['cfg']) as json_file:
    params = json.load(json_file)
job_queue = None
worker = None

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

intents = dis.Intents.default()
IGSD_client = IGSDClient(intents=intents)

#####  Package Functions  #####

@IGSD_client.event
async def on_ready():
    global job_queue
    global worker
    
    disLog = log.getLogger('discord')
    disLog.info(f'Logged in as {IGSD_client.user} (ID: {IGSD_client.user.id})')
    
    disLog.debug(f"Creating Queue Manager.")
    job_queue = qm.Manager(loop=IGSD_client.GetLoop(),
                           manager_id=1,
                           opts=params['queue_opts'])
    worker    = th.Thread(target=job_queue.PutRequest,
                          name="Queue mgr",
                          daemon=True)
    worker.start()
    
    print('------')
    
@IGSD_client.tree.command()
async def hello(interaction: dis.Interaction):
    """A test echo command to verify basic discord functionality.

       Input  : None.

       Output : None.
    """
    await interaction.response.send_message(f'Hi, {interaction.user.mention}', ephemeral=True, delete_after=45.0)
    
        
@IGSD_client.tree.command()
async def testget(interaction: dis.Interaction):
    """A test HTTP GET command to verify basic connection to the webui page.
       Also tests the internal data path.

       Input  : None.

       Output : None.
    """
    disLog = log.getLogger('discord')

    msg = { 'metadata' : {
                'ctx'    : interaction,
                'loop'   : IGSD_client.GetLoop(),
                'poster' : Post
           },
           'data' : {
                #Requests are sorted by guild for rate-limiting
                'guild'  : interaction.guild_id,
                #This should really be metadata but the rest of the metadata
                #can't be pickeled, so this must be passed with the work.
                'id'     : "testgetid",
                'post'   : {'empty'},
                'reply'  : "test msg"
            }
        }
    disLog.debug(f"Posting test GET job {msg} to the queue.") 
    result = job_queue.Add(msg)
    
    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=45.0)

@IGSD_client.tree.command()
async def testpost(interaction: dis.Interaction):
    """A test HTTP PUT command to verify basic connection to the webui page.

       Input  : None.

       Output : None.
       
       Note: All slash commands *MUST* respond in 3 seconds or be terminated.
    """
    disLog = log.getLogger('discord')
    msg = { 'metadata' : {
                'ctx'    : interaction,
                'loop'   : IGSD_client.GetLoop(),
                'poster' : Post
           },
           'data' : {
                #Requests are sorted by guild for rate-limiting
                'guild'  : interaction.guild_id,
                #This should really be metadata but the rest of the metadata
                #can't be pickeled, so this must be passed with the work.
                'id'     :  "testpostid",
                'post'   : job_queue.GetDefaultJobData()},
                'reply'  : ""
            }
    disLog.debug(f"Posting test PUT job {msg} to the queue.") 
    result = job_queue.Add(msg)
    
    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=45.0)

"""@dac.option("height",
        choices=[x for x in range(params['options']['min_height'], params['options']['max_height'] + 64, 64)])
@dac.option("width",
        choices=[x for x in range(params['options']['min_width'], params['options']['max_width'] + 64, 64)])
@dac.option("steps",
        choices=[x for x in range(params['options']['min_steps'], params['options']['max_steps'] + params['options']['step_step'], params['options']['step_step'])])
@dac.option("sampler",
        choices=((params['options']['samplers']).split(','))):"""
@IGSD_client.tree.command(nsfw=True)
@dac.describe(prompt="The prompt(s) for generating the image.",
              negative_prompt="Prompts to filter out of results.",
              height="Image height.",
              width="Image width.",
              steps="Number of steps.",
              seed="Use a seed for more repeatable results on a given iamge.",
              cfg_scale="how much weight to give your prompts.",
              sampler="Sampling method (like 'Euler').")
#@dac.AppCommand.nsfw(True) #Enabled until the word filter and user blacklsiting is implemented.
#@dac.Command(nsfw=True) #Enabled until the word filter and user blacklsiting is implemented.
async def generate(interaction: dis.Interaction,
                   prompt          : Optional[str]   = params['options']['prompts'],
                   negative_prompt : Optional[str]   = params['options']['negatives'],
                   height          : Optional[int]   = int(params['options']['height']),
                   width           : Optional[int]   = int(params['options']['width']),
                   steps           : Optional[int]   = int(params['options']['steps']),
                   seed            : Optional[int]   = int(params['options']['seed']),
                   cfg_scale       : Optional[float] = float(params['options']['cfg']),
                   sampler         : Optional[str]   = params['options']['sampler']):
    disLog = log.getLogger('discord')
    msg = { 'metadata' : {
                'ctx'    : interaction,
                'loop'   : IGSD_client.GetLoop(),
                'poster' : Post
           },
           'data' : {
                #Requests are sorted by guild for rate-limiting
                'guild'  : interaction.guild_id,
                #This should really be metadata but the rest of the metadata
                #can't be pickeled, so this must be passed with the work.
                'id'     :  "testpostid",
                'post'   : job_queue.GetDefaultJobData()},
                'reply'  : ""
            }

    #Add prompt filter checking.
    #And probably blacklist people who try to bypass X times.
    msg['data']['post']['prompt']          = prompt
    msg['data']['post']['negative_prompt'] = negative_prompt
    msg['data']['post']['height']          = height
    msg['data']['post']['width']           = width
    msg['data']['post']['steps']           = steps
    msg['data']['post']['seed']            = seed
    msg['data']['post']['cfg_scale']       = cfg_scale
    msg['data']['post']['sampler']         = sampler
    
    disLog.debug(f"Posting user job {msg} to the queue.") 
    result = job_queue.Add(msg)
    
    await interaction.response.send_message(f'{result}', ephemeral=True)


async def Post(msg):
    """Posts the query's result to Discord.  Runs in the main asyncio loop so
       the manager can start the next job concurrently.

        Input  : msg - a reference to the completed job.

        Output : N/A.
    """
    embed = None
    image = None
    
    if msg['status_code'] != 200:
        embed = dis.Embed(title='Job Error:',
                          description=f"Status code: {msg['status_code']} Reason: {msg['reason']}",
                          color=0xec1802)
                          
        await msg['ctx'].channel.send(content=f"<@{msg['ctx'].user.id}>",
                                      embed=embed)
        
    elif msg['id'] == 'testgetid':
        #Maybe a future version will have a generic image to return and eliminate this clause.
        embed = dis.Embed(title='Test GET successful:',
                          description=f"Status code: {msg['status_code']} Reason: {msg['reason']}",
                          color=0x008000)

        await msg['ctx'].channel.send(content=f"<@{msg['ctx'].user.id}>",
                                      embed=embed)
        
    else:
        embed = dis.Embed()
        embed.add_field(name='Prompt', value=msg['parameters']['prompt'])
        embed.add_field(name='Negative Prompt', value=msg['parameters']['negative_prompt'])
        embed.add_field(name='Steps', value=msg['parameters']['steps'])
        embed.add_field(name='Height', value=msg['parameters']['height'])
        embed.add_field(name='Width', value=msg['parameters']['width'])
        embed.add_field(name='Sampler', value=msg['parameters']['sampler_index'])
        embed.add_field(name='Seed', value=msg['parameters']['seed'])
        embed.add_field(name='CFG Scale', value=msg['parameters']['cfg_scale'])
        embed.add_field(name='Highres Fix', value=msg['parameters']['enable_hr'])

        for i in msg['images']:
            image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))
        
        await msg['ctx'].channel.send(content=f"<@{msg['ctx'].user.id}>",
                                      file=dis.File(fp=image,
                                      filename='image.png') ,embed=embed)

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
    
    try:
        IGSD_client.run(creds['bot_token'])
    except Exception as err:
        disLog.error(f"Caught exception {err} when trynig to run IGSD client!")


if __name__ == '__main__':
    Startup()

#Supported commands:
#/flush:   clear queue and kill active jobs (if possible).  Needs Owner/Admin to run.
#/Restart: Flush + recreates the queue objects.  Effectively restarts the script.  Also requires Owner.
#/Cancel:  Kills most recent request from the poster, if possible. 