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
import time
from typing import Literal, Optional

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
        
        self.disLog.debug(f"Syncing Guild Tree to Global.")
        
        await self.tree.sync()
        
    def GetLoop(self):
        """Returns a reference to this client's asyncio event loop.

            Input  : self - a reference to the current object.

            Output : loop - the client's event loop.
        """
        return self.loop;

intents = dis.Intents.default()
IGSD_client = IGSDClient(intents=intents)

#####  Package Functions  #####
def BannedWordsFound(prompt: str, banned_words: str) -> bool:
    """Tests if banded words exist in the provided parameters.  This is written
       as a separate function to allow future updates to the banned word list
       without restarting the bot.

       Input  : None.

       Output : None.
    """
    result = False;
    
    #The default prompt is assumed to not be banned.
    if banned_words != None and prompt != None:
        #re-sanatize the word list in case spaces/separators snuck in
        word_list = (banned_words.replace(" ", "")).split(",")
        result    = any(word in prompt for word in word_list)
    
    return result

@IGSD_client.event
async def on_ready():
    global job_queue
    global worker
    
        
    queLog = log.getLogger('queue')
    queLog.setLevel(params['log_lvl'])

    logHandler = lh.RotatingFileHandler(
        filename=params['log_name_queue'],
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
    queLog.addHandler(logHandler)
    queLog.info(f'Logged in as {IGSD_client.user} (ID: {IGSD_client.user.id})')
    
    queLog.debug(f"Creating Queue Manager.")
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
    await interaction.response.send_message(f'Hi, {interaction.user.mention}', ephemeral=True, delete_after=9.0)

#This is commented until the failed inheritance issue can be resolved.
#@IGSD_client.tree.command()
#async def testclear(interaction: dis.Interaction):
#    """A test HTTP GET command to verify basic connection to the webui page.
#       Also tests the internal data path.
#
#       Input  : None.
#
#       Output : None.
#    """
#    disLog = log.getLogger('discord')
#    rng    = range(1,10)
#
#    msg = [{ 'metadata' : {
#                'ctx'    : interaction,
#                'loop'   : IGSD_client.GetLoop(),
#                'poster' : Post
#           },
#           'data' : {
#                #Requests are sorted by guild for rate-limiting
#                'guild'  : interaction.guild_id,
#                #This should really be metadata but the rest of the metadata
#                #can't be pickeled, so this must be passed with the work.
#                'id'     : x,
#                'post'   : {'empty'},
#                'reply'  : "test msg"
#            }
#        } for x in rng]
#    disLog.debug(f"trying to clear the queue.") 
#    
#    for m in rng:
#        result = job_queue.Add(msg[m -1])
#
#    job_queue.Flush()
#    
#    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

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
    
    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

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
    
    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

@IGSD_client.tree.command()
@dac.describe(prompt=f"The prompt(s) for generating the image, up to {params['options']['max_prompt_len']} characters.",
              negative_prompt=f"Prompts to filter out of results, up to {params['options']['max_prompt_len']} characters.",
              height=f"Image height, rounded down to a {params['options']['step_size']} pixel size.",
              width=f"Image width, rounded down to a {params['options']['step_size']} pixel size.",
              steps=f"Number of steps, from {params['options']['min_steps']} to {params['options']['max_steps']}.",
              seed="Use a seed for more repeatable results on a given image.",
              cfg_scale="how much weight to give your prompts.",
              sampler="Sampling method (like 'Euler').")
async def generate(interaction: dis.Interaction,
                   prompt          : Optional[dac.Range[str, 0, int(params['options']['max_prompt_len'])]]                                 = params['options']['prompts'],
                   negative_prompt : Optional[dac.Range[str, 0, int(params['options']['max_prompt_len'])]]                                 = params['options']['negatives'],
                   height          : Optional[dac.Range[int, int(params['options']['min_height']), int(params['options']['max_height'])]]  = int(params['options']['height']),
                   width           : Optional[dac.Range[int, int(params['options']['min_width']), int(params['options']['max_width'])]]    = int(params['options']['width']),
                   steps           : Optional[dac.Range[int, int(params['options']['min_steps']), int(params['options']['max_steps'])]]    = int(params['options']['steps']),
                   seed            : Optional[dac.Range[int, -(pow(2,53) - 1), (pow(2,53) - 1)]]                                           = int(params['options']['seed']), #These are limits imposed by Discord.
                   cfg_scale       : Optional[dac.Range[float, 0.0, 30.0]]                                                                 = float(params['options']['cfg']),
                   sampler         : Optional[Literal["Euler a","Euler","LMS","Heun","DPM2","DM2 a","DPM++ 2S a","DPM++ 2M","DPM++ SDE","DPM fast","DPM adaptive","LMS Karras","DPM2 Karras","DPM2 a Karras","DPM++ 2M Karras","DPM++ SDE Karras","DDIM","PLMS"]]  = params['options']['sampler']):
                   #Yes, I am disappoitned I can't wrangle this into a config parameter.  Thanks PEP 586.
    """Generates a image based on user-supplied prompts, if provided.  Provides
       defaults if not.  Enforces any parameter limits, including an optional
       banned word filter.

        Input  : prompt - what the user wants to append to the default prompt.
                 negative_prompt - what the user wants to append to the default.
                 height - How tall to make the pre-scaled image.
                 width - How wide to make the pre-scaled image.
                 steps - How many steps to itterate in the SD process.
                 seed - What seed value to use (-1 is random).
                 cfg_scale - How much weight to give prompts in generation.
                 sampler - Which algorithm to use.

        Output : N/A.
    """
    disLog = log.getLogger('discord')
    error = False;
    
    if BannedWordsFound(prompt, params['options']['banned_words']) or BannedWordsFound(negative_prompt, params['options']['banned_neg_words']):
        result = f"Job ignored.  Please do not use words containing: {params['options']['banned_words']} in the positive prompt or {params['options']['banned_neg_words']} in the negative prompt."
    else:
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
                    'id'     :  interaction.user.id,
                    'post'   : job_queue.GetDefaultJobData()},
                    'reply'  : ""
                }

        #And probably blacklist people who try to bypass X times.
        msg['data']['post']['prompt']          = prompt
        msg['data']['post']['negative_prompt'] = negative_prompt
        msg['data']['post']['height']          = (height - (height % int(params['options']['step_size'])))
        msg['data']['post']['width']           = (width  - (width  % int(params['options']['step_size'])))
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
        
    elif msg['id'] == 'testgetid' or ((type(msg['id']) != str) and (msg['id'] < 10)):
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
    
    if int(params['options']['step_size']) <= 1:
    
        disLog.error(f"Image dimension step size must be greater than 1!")
        exit(1)
        
    #This will be modified in the future to accept user-supplied paths.
    try:
        with open(default_params['cred']) as json_file:
            creds = json.load(json_file)

    except OSError as err:
        disLog.critical(f"Can't load file from path {default_params['cred']}")
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