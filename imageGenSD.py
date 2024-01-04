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
import pathlib as pl
import pickle as pic
import requests as req
import src.db.MariadbIfc as mdb
import src.managers.QueueMgr as qm
import src.utilities.NameRandomizer as nr
import src.utilities.ProfileGenerator as pg
import threading as th
import time
from typing import Literal, Optional

#####  Package Variables  #####

#The great thing about package-level dictionaries is their global (public-like)
#capability, avoiding constant passing down to 'lower' defs.
#Static data only, no file objects or similar (or else!).
creds = {}
#These can be specified as POSIX style since the using call will normalize them.
default_params = {'cfg'       : 'src/config/config.json',
                  'cred'      : 'src/config/credentials.json',
                  'bot_token' : ''}
db_ifc = None
dict_path = ["","",""]
IGSD_version = '0.3.5'
#This will be modified in the future to accept user-supplied paths.
#This file must be loaded prior to the logger to allow for user-provided
#options to be passed to the Logger.  Thus it must have special error
#handling outside of the logger class.
cfg_path = pl.Path(default_params['cfg'])

try:
    #The .absoltue call normalizes the path in case the user had slashing
    #issues.  Obviously can't solve all potential problems.
    with open(cfg_path.absolute()) as json_file:
        params = json.load(json_file)

    dict_path[0] = pl.Path(params['queue_opts']['rand_dict_path'])
    dict_path[1] = pl.Path(params['profile_opts']['fn_dict_path'])
    dict_path[2] = pl.Path(params['profile_opts']['ln_dict_path'])

    for dir in range(len(dict_path)):
        #This is just an access check and is done early to allow for an exit if
        #the file has read/access issues.  The using classes will separately
        #open a copy when needed with a more read-efficent module.
        if not dict_path[dir].is_file():
            raise FileNotFoundError

    #This is to guarantee there's no confusion about where the dict is.
    #If run across computers, this will need to be changed.
    params['queue_opts']['rand_dict_path'] = dict_path[0].absolute()
    params['profile_opts']['fn_dict_path'] = dict_path[1].absolute()
    params['profile_opts']['ln_dict_path'] = dict_path[2].absolute()

    #While it would be ideal to simply rely on a user-supplied size, we
    #can't assume the user will think to do this nor give an accurate
    #value, hence we have to scan ourselves.
    params['queue_opts']['dict_size']      = sum(1 for line in open(params['queue_opts']['rand_dict_path']))
    params['profile_opts']['fn_dict_size'] = sum(1 for line in open(params['profile_opts']['fn_dict_path']))
    params['profile_opts']['ln_dict_size'] = sum(1 for line in open(params['profile_opts']['ln_dict_path']))

    if int(params['queue_opts']['dict_size']) < int(params['queue_opts']['max_rand_tag_cnt']) or \
       int(params['queue_opts']['max_rand_tag_cnt']) <= int(params['queue_opts']['min_rand_tag_cnt']):
        raise IndexError

except OSError as err:
    print(f"Can't load the config file from path: {cred_path.absolute()}!")
    exit(-3)

except FileNotFoundError as err:
    print(f"Can't load one of the dictionaries dictionaries: {dict_path[0]} {dict_path[1]} {dict_path[2]}")
    exit(-4)

except IndexError as err:
    print(f"The tag dictionary is {params['queue_opts']['dict_size']} lines long, shorter than the tag randomizer max size of {params['queue_opts']['max_rand_tag_cnt']} OR Max tags {params['queue_opts']['max_rand_tag_cnt']} is less than min tags {params['queue_opts']['min_rand_tag_cnt']}!")
    exit(-5)

job_queue   = None
worker      = None

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
    """Performs post-login setup for the bot.

       Input  : None.

       Output : None.
    """
    global db_ifc
    global job_queue
    global profile_gen
    global worker


    disLog = log.getLogger('discord')
    disLog.setLevel(params['log_lvl'])
    log_path = pl.Path(params['log_name'])

    logHandler = lh.RotatingFileHandler(filename=log_path.absolute(),
                                        encoding=params['log_encoding'],
                                        maxBytes=int(params['max_bytes']),
                                        backupCount=int(params['log_file_cnt'])
    )

    formatter = log.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}',
                              params['date_fmt'],
                              style='{'
    )
    logHandler.setFormatter(formatter)
    disLog.addHandler(logHandler)
    #TODO: get propagate to properly disable.
    #disLog.propagate=False

    queLog = log.getLogger('queue')
    queLog.setLevel(params['log_lvl'])
    log_path = pl.Path(params['log_name_queue'])

    logHandler = lh.RotatingFileHandler(filename=log_path.absolute(),
                                        encoding=params['log_encoding'],
                                        maxBytes=int(params['max_bytes']),
                                        backupCount=int(params['log_file_cnt'])
    )

    formatter = log.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}',
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

    queLog.debug(f"Creating DB Interface.")
    db_ifc = mdb.MariadbIfc(options=params['db_opts'])

    #Only start the job queue once all otehr tasks are ready.
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
#    """A test flood of requests to verify the flush command works.
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
                'post'   : {'random': False, 'tags_added':'', 'tag_cnt':0},
                'profile' : "",
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
                'guild'   : interaction.guild_id,
                #This should really be metadata but the rest of the metadata
                #can't be pickeled, so this must be passed with the work.
                'id'      :  "testpostid",
                'post'    : pg.GetDefaultJobData(),
                'profile' : pic.dumps(pg.GetDefaultProfile())},
                'reply'   : ""
            }
    disLog.debug(f"Posting test PUT job {msg} to the queue.")
    result = job_queue.Add(msg)

    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

@IGSD_client.tree.command()
async def testroll(interaction: dis.Interaction):
    """Verifies a profile can be added to a test image.

       Input  : None.

       Output : None.

       Note: All slash commands *MUST* respond in 3 seconds or be terminated.
    """
    disLog = log.getLogger('discord')
    msg = { 'metadata' : {
                'ctx'     : interaction,
                'loop'    : IGSD_client.GetLoop(),
                'poster'  : Post
           },
           'data' : {
                #Requests are sorted by guild for rate-limiting
                'guild'   : interaction.guild_id,
                #This should really be metadata but the rest of the metadata
                #can't be pickeled, so this must be passed with the work.
                'id'      : "testroll",
                'post'    : pg.GetDefaultJobData(),
                'profile' : pic.dumps(pg.GetDefaultProfile())},
                'reply'   : ""
            }

    #disLog.debug(f"Creating a new profile.")
    #msg['data']['profile'] = pic.dumps(pg.Profile(id=interaction.user.id))
    #disLog.debug(f"Profile complete: {msg['data']['profile']}")

    disLog.debug(f"Posting test ROLL job {msg} to the queue.")
    result = job_queue.Add(msg)

    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

@IGSD_client.tree.command()
@dac.describe(random=f"A flag to add between {params['queue_opts']['min_rand_tag_cnt']} and {params['queue_opts']['max_rand_tag_cnt']} random tags to the user prompt.  Does not count towards the maximum prompt length.",
              tag_cnt=f"If 'random' is enabled, an exact number of tags to add to the prompt, up to params['queue_opts']['max_rand_tag_cnt']",
              prompt=f"The prompt(s) for generating the image, up to {params['options']['max_prompt_len']} characters.",
              negative_prompt=f"Prompts to filter out of results, up to {params['options']['max_prompt_len']} characters.",
              height=f"Image height, rounded down to a {params['options']['step_size']} pixel size.",
              width=f"Image width, rounded down to a {params['options']['step_size']} pixel size.",
              steps=f"Number of steps, from {params['options']['min_steps']} to {params['options']['max_steps']}.",
              seed="Use a seed for more repeatable results on a given image.",
              cfg_scale="how much weight to give your prompts.",
              sampler="Sampling method (like 'Euler').")
async def generate(interaction: dis.Interaction,
                   random          : Optional[bool]                                                                                        = False,
                   tag_cnt         : Optional[dac.Range[int, 0, int(params['queue_opts']['max_rand_tag_cnt'])]]                            = 0,
                   prompt          : Optional[dac.Range[str, 0, int(params['options']['max_prompt_len'])]]                                 = params['options']['prompts'],
                   negative_prompt : Optional[dac.Range[str, 0, int(params['options']['max_prompt_len'])]]                                 = params['options']['negatives'],
                   height          : Optional[dac.Range[int, int(params['options']['min_height']), int(params['options']['max_height'])]]  = int(params['options']['height']),
                   width           : Optional[dac.Range[int, int(params['options']['min_width']), int(params['options']['max_width'])]]    = int(params['options']['width']),
                   steps           : Optional[dac.Range[int, int(params['options']['min_steps']), int(params['options']['max_steps'])]]    = int(params['options']['steps']),
                   seed            : Optional[dac.Range[int, -(pow(2,53) - 1), (pow(2,53) - 1)]]                                           = int(params['options']['seed']), #These are limits imposed by Discord.
                   cfg_scale       : Optional[dac.Range[float, 0.0, 30.0]]                                                                 = float(params['options']['cfg']),
                   sampler         : Optional[Literal["Euler a","Euler","LMS","Heun","DPM2","DM2 a","DPM++ 2S a","DPM++ 2M","DPM++ SDE","DPM fast","DPM adaptive","LMS Karras","DPM2 Karras","DPM2 a Karras","DPM++ 2M Karras","DPM++ SDE Karras","DDIM","PLMS"]]  = params['options']['sampler']):
                   #Yes, I am disappointed I can't wrangle the sampler list into a config parameter.  Thanks PEP 586.
    """Generates a image based on user-supplied prompts, if provided.  Provides
       defaults if not.  Enforces any parameter limits, including an optional
       banned word filter.

        Input  : random - Adds a random number of random tags to the prompt input if True.
                 tag_cnt - A specific number of random tags to add to a prompt.
                 prompt - What the user wants to append to the default prompt.
                 negative_prompt - What the user wants to append to the default.
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
                    'guild'   : interaction.guild_id,
                    #This should really be metadata but the rest of the metadata
                    #can't be pickeled, so this must be passed with the work.
                    'id'      : interaction.user.id,
                    'post'    : pg.GetDefaultJobData(),
                    'profile' : pic.dumps(pg.GetDefaultProfile())},
                    'reply'   : ""
                }

        #And probably blacklist people who try to bypass prompt filters X times.
        #Also nearly all input sanitization is done by the function call.
        msg['data']['post']['random']          = random
        msg['data']['post']['tag_cnt']         = tag_cnt
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

    elif msg['id'] == 'testroll':

        info_dict = json.loads(msg['info'])

        #TODO: Move to a non-test function.  Users will always get their roll
        #so it's always appropriate to save the output.  Other commands may
        #differ.
        db_ifc.SaveRoll(msg['profile'], info_dict)

        embed = dis.Embed()
        profile = pic.loads(msg['profile'])
        embed.add_field(name='Creator', value=f"<@{profile.creator}>")
        embed.add_field(name='Owner', value=f"<@{profile.owner}>")
        embed.add_field(name='Name', value=profile.name)
        embed.add_field(name='Rarity', value=profile.rarity.name)
        embed.add_field(name='Agility', value=profile.stats.agility)
        embed.add_field(name='Defense', value=profile.stats.defense)
        embed.add_field(name='Endurance', value=profile.stats.endurance)
        embed.add_field(name='Luck', value=profile.stats.luck)
        embed.add_field(name='Strength', value=profile.stats.strength)
        embed.add_field(name='Description', value=profile.desc)
        embed.add_field(name='Range', value=profile.stats.range)

        for i in msg['images']:
            image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))

        await msg['ctx'].channel.send(content=f"<@{msg['ctx'].user.id}>",
                                      file=dis.File(fp=image,
                                      filename='image.png'), embed=embed)
    else:
        info_dict = json.loads(msg['info'])
        db_ifc.SaveRoll(msg['profile'], info_dict)
        
        embed = dis.Embed()
        embed.add_field(name='Prompt', value=info_dict['prompt'])
        embed.add_field(name='Negative Prompt', value=info_dict['negative_prompt'])
        embed.add_field(name='Steps', value=info_dict['steps'])
        embed.add_field(name='Height', value=info_dict['height'])
        embed.add_field(name='Width', value=info_dict['width'])
        embed.add_field(name='Sampler', value=info_dict['sampler_name'])
        embed.add_field(name='Seed', value=info_dict['seed'])
        embed.add_field(name='Subseed', value=info_dict['subseed'])
        embed.add_field(name='CFG Scale', value=info_dict['cfg_scale'])
        #Randomized and co are special because they're not a parameter sent to SD.
        embed.add_field(name='Randomized', value=msg['random'])
        embed.add_field(name='Tags Added to Prompt', value=msg['tags_added'])

        for i in msg['images']:
            image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))

        await msg['ctx'].channel.send(content=f"<@{msg['ctx'].user.id}>",
                                      file=dis.File(fp=image,
                                      filename='image.png'), embed=embed)

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

    if int(params['options']['step_size']) <= 1:

        print(f"Image dimension step size must be greater than 1!")
        exit(-1)

    #This will be modified in the future to accept user-supplied paths.
    try:
        cred_path = pl.Path(default_params['cred'])

        with open(cred_path.absolute()) as json_file:
            creds = json.load(json_file)

    except OSError as err:
        print(f"Can't load file from path {cred_path.absolute()}")
        exit(-2)

    nr.init(params['profile_opts'])

    #Start manager tasks
    try:
        IGSD_client.run(creds['bot_token'])
    except Exception as err:
        print(f"Caught exception {err} when trying to run IGSD client!")


if __name__ == '__main__':
    Startup()

#Supported commands:
#/flush:   clear queue and kill active jobs (if possible).  Needs Owner/Admin to run.
#/Restart: Flush + recreates the queue objects.  Effectively restarts the script.  Also requires Owner.
#/Cancel:  Kills most recent request from the poster, if possible.