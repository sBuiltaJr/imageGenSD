#Manages user requests through Discord to generate images with a Stable
#Diffusion model filepath supplied in the config.json file.  Cannot prevent
#Specific types of images, like NSFW, from being generated.


#####  Imports  #####

import asyncio as asy
import discord as dis
from discord import app_commands as dac
import logging as log
import logging.handlers as lh
import json
import multiprocessing as mp
import os
import pathlib as pl
import requests as req
import src.db.MariadbIfc as mdb
import src.managers.DailyEventMgr as dem
import src.managers.QueueMgr as qm
import src.ui.DropDownFactory as ddf
import src.ui.MenuPagination as mp
import src.utilities.JobFactory as jf
import src.utilities.NameRandomizer as nr
import src.utilities.ProfileGenerator as pg
import src.utilities.TagRandomizer as tr
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
daily_mgr      = None
daily_mgr_th   = None
db_ifc         = None
dict_path      = ["","",""]
IGSD_version   = '0.3.8'
tag_randomizer = None
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

    dict_path[0] = pl.Path(params['tag_rng_opts']['rand_dict_path'])
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
    params['tag_rng_opts']['rand_dict_path'] = dict_path[0].absolute()
    params['profile_opts']['fn_dict_path']   = dict_path[1].absolute()
    params['profile_opts']['ln_dict_path']   = dict_path[2].absolute()

    #While it would be ideal to simply rely on a user-supplied size, we
    #can't assume the user will think to do this nor give an accurate
    #value, hence we have to scan ourselves.
    params['tag_rng_opts']['dict_size']    = sum(1 for line in open(params['tag_rng_opts']['rand_dict_path']))
    params['profile_opts']['fn_dict_size'] = sum(1 for line in open(params['profile_opts']['fn_dict_path']))
    params['profile_opts']['ln_dict_size'] = sum(1 for line in open(params['profile_opts']['ln_dict_path']))

    if int(params['tag_rng_opts']['dict_size']) < int(params['tag_rng_opts']['max_rand_tag_cnt']) or \
       int(params['tag_rng_opts']['max_rand_tag_cnt']) <= int(params['tag_rng_opts']['min_rand_tag_cnt']):
        raise IndexError

except OSError as err:
    print(f"Can't load the config file from path: {cred_path.absolute()}!")
    exit(-3)

except FileNotFoundError as err:
    print(f"Can't load one of the dictionaries: {dict_path[0]} {dict_path[1]} {dict_path[2]}")
    exit(-4)

except IndexError as err:
    print(f"The tag dictionary is {params['tag_rng_opts']['dict_size']} lines long, shorter than the tag randomizer max size of {params['tag_rng_opts']['max_rand_tag_cnt']} OR Max tags {params['tag_rng_opts']['max_rand_tag_cnt']} is less than min tags {params['tag_rng_opts']['min_rand_tag_cnt']}!")
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
        self.dis_log = log.getLogger('discord')
        self.dis_log.debug(f"Intents are: {intents}")

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

        self.dis_log.debug(f"Syncing Guild Tree to Global.")
        await self.tree.sync()

    def getLoop(self):
        """Returns a reference to this client's asyncio event loop.

            Input  : self - a reference to the current object.

            Output : loop - the client's event loop.
        """
        return self.loop;

intents = dis.Intents.default()
IGSD_client = IGSDClient(intents=intents)

#####  Package Functions  #####

@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
async def about(interaction : dis.Interaction):
    """Displays the bot version and invite link.

        Input  : interaction - the interaction context from Discord.

        Output : N/A.
    """
    dis_log  = log.getLogger('discord')
    
    await interaction.response.send_message(f"This is bot version {IGSD_version}!  Invite me to your server with [this link](https://discord.com/api/oauth2/authorize?client_id=1084600126913388564&permissions=534723816512&scope=bot)!", ephemeral=True, delete_after=30.0)


@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
@dac.describe(tier="Which tier to manage character assignments in.  1 mean 'common', 6 means 'legendary'.") #TODO: cycle through the tiers?
async def assignkeygen(interaction : dis.Interaction,
                       tier        : Optional[dac.Range[int, 1, 6]] = 1):
    """Assigns selected characters to key generation.  Only characters wtih stats above the average for their can be assigned to work on this job.

        Input  : interaction - the interaction context from Discord.
                 tier - what rarity tier to assign for (1-based for the average user)

        Output : N/A.
    """
    dis_log  = log.getLogger('discord')
    metadata = {'ctx'     : interaction,
                'db_ifc'  : db_ifc,
                'loop'    : IGSD_client.getLoop(),
                'post_fn' : post,
                'queue'   : job_queue
               }
    #one-based counting is purely for user convenience.
    tier -= 1

    profiles = db_ifc.getUnoccupiedProfiles(user_id = interaction.user.id)
    dis_log.debug(f"Got profiles for assign Key Gen: {profiles}.")

    options = db_ifc.getKeyGenParams(user_id = interaction.user.id)
    dis_log.debug(f"Got Key Gen parameters: {options}.")

    if not profiles or 'total' not in options:

        await interaction.response.send_message('You need a character first!  Use the /roll command to get one, or free existing profiles from their assignments!', ephemeral=True, delete_after=9.0)

    elif int(options['current_tier']) < tier:

        await interaction.response.send_message(f"You don't have access to this tier yet!  Right now you can access tier {options['current_tier'] + 1}. Start some /research and /building to upgrade!", ephemeral=True, delete_after=9.0)

    elif int(options['workers'][f'tier_{tier}']['count']) >= int(options[f'limit_t{tier}']):

        await interaction.response.send_message(f"You've assigned all possible workers for tier {tier + 1}!  Either remove a worker or research more slots.", ephemeral=True, delete_after=9.0)

    else:

        options['tier'] = tier
        dis_log.debug(f"Creating a ASSIGN KEY GEN view for user {interaction.user.id}.")

        view = ddf.DropdownView(ctx      = interaction,
                                type     = ddf.DropDownTypeEnum.ASSIGN_KEY_GEN,
                                choices  = profiles,
                                metadata = metadata,
                                options  = options)

        await interaction.response.send_message(f'Select a profile to assign to keygen work for tier {tier + 1}:',view=view)

def bannedWordsFound(prompt: str, banned_words: str) -> bool:
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

@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
@dac.describe(random=f"A flag to add between {params['tag_rng_opts']['min_rand_tag_cnt']} and {params['tag_rng_opts']['max_rand_tag_cnt']} random tags to the user prompt.  Does not count towards the maximum prompt length.",
              tag_cnt=f"If 'random' is enabled, an exact number of tags to add to the prompt, up to params['tag_rng_opts']['max_rand_tag_cnt']",
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
                   tag_cnt         : Optional[dac.Range[int, 0, int(params['tag_rng_opts']['max_rand_tag_cnt'])]]                            = 0,
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
    dis_log = log.getLogger('discord')
    error   = False;

    if bannedWordsFound(prompt, params['options']['banned_words']) or bannedWordsFound(negative_prompt, params['options']['banned_neg_words']):
        result = f"Job ignored.  Please do not use words containing: {params['options']['banned_words']} in the positive prompt or {params['options']['banned_neg_words']} in the negative prompt."
    else:

        metadata = {'ctx'     : interaction,
                    'db_ifc'  : db_ifc,
                    'loop'    : IGSD_client.getLoop(),
                    'post_fn' : post,
                    'tag_rng' : tag_randomizer
                   }
        opts = {'cfg_scale' : cfg_scale,
                'height'    : (height - (height % int(params['options']['step_size']))),
                'n_prompt'  : negative_prompt,
                'prompt'    : prompt,
                'random'    : random,
                'sampler'   : sampler,
                'seed'      : seed,
                'steps'     : steps,
                'tag_cnt'   : tag_cnt,
                'width'     : (width  - (width  % int(params['options']['step_size'])))
               }
        dis_log.debug(f"Creating a job with metadata {metadata} and options {opts}.")
        job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.GENERATE,
                                   ctx     = interaction,
                                   options = opts)
        dis_log.debug(f"Posting GENERATE job {job} to the queue.")
        result = job_queue.add(metadata = metadata,
                               job      = job)

    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
async def hello(interaction: dis.Interaction):
    """A test echo command to verify basic discord functionality.

       Input  : interaction - the interaction context from Discord.

       Output : None.
    """
    await interaction.response.send_message(f'Hi, {interaction.user.mention}', ephemeral=True, delete_after=9.0)

@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
@dac.describe(user="The Discord user owning the profiles lsited by the command.  If none, it defaults to you.")
async def listprofiles(interaction : dis.Interaction,
                       user        : Optional[dis.User] = None):
    """Returns a pagenated list of profile names and IDs owned by the caller.

        Input  : interaction - the interaction context from Discord.

        Output : N/A.
    """
    dis_log  = log.getLogger('discord')
    #This has to be in the function body because an arg can't be used to assign
    #another arg in the function call.
    user_id = interaction.user.id if user == None else user.id
    profiles = db_ifc.getProfiles(user_id)
    dis_log.debug(f"Got profiles for list profile: {profiles}.")

    if not profiles:

        embed = dis.Embed(title       = "Owned characters",
                          description = f"User <@{user_id}> does not own any characters!",
                          color       = 0xec1802)
        await interaction.response.send_message(content=f"<@{interaction.user.id}>", embed=embed)

    else:

        short_profiles = [(profiles[x].name,profiles[x].id) for x in range(0,len(profiles))]
        await mp.MenuPagination(interaction, short_profiles).navigate()

@IGSD_client.event
async def on_ready():
    """Performs post-login setup for the bot.

       Input  : None.

       Output : None.
    """
    global daily_mgr
    global daily_mgr_th
    global db_ifc
    global job_queue
    global tag_randomizer
    global worker


    dis_log = log.getLogger('discord')
    dis_log.setLevel(params['log_lvl'])
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
    dis_log.addHandler(logHandler)
    #TODO: get propagate to properly disable.
    #dis_log.propagate=False

    dis_log.info(f'Logged in as {IGSD_client.user} (ID: {IGSD_client.user.id})')

    dis_log.debug(f"Instantiating the Tag Randomizer.")
    tag_randomizer = tr.TagRandomizer(opts=params['tag_rng_opts'])


    dis_log.debug(f"Creating Queue Manager.")
    job_queue = qm.Manager(manager_id = 1,
                           opts       = params['queue_opts'])
    worker    = th.Thread(target = job_queue.putJob,
                          name   = "Queue mgr",
                          daemon = True)

    dis_log.debug(f"Creating DB Interface.")
    db_ifc = mdb.MariadbIfc(options=params['db_opts'])

    dis_log.debug(f"Creating Daily Event Manager.")
    daily_mgr    = dem.DailyEventManager(opts=params['daily_opts'])
    daily_mgr_th = th.Thread(target = daily_mgr.start,
                             name   = "Daily Event mgr",
                             daemon = True)

    daily_mgr_th.start()
    #Only start the job queue once all other tasks are ready.
    worker.start()

    print('------')

async def post(job      : jf.Job,
               metadata : dict):
    """Posts the query's result to Discord.  Runs in the main asyncio loop so
       the manager can start the next job concurrently.

        Input  : job - a reference to the completed job.

        Output : N/A.
    """

    dis_log = log.getLogger('discord')
    embed = None
    image = None

    if job.getStatusCode() != 200:

        embed = dis.Embed(title       = 'Job Error:',
                          description = f"Status code: {job.getStatusCode()} Reason: {job.getReason()}",
                          color       = 0xec1802)

        await metadata['ctx'].channel.send(content = f"<@{job.getUserId()}>",
                                           embed   = embed)

    else:

        await job.post(metadata)

@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
@dac.describe(tier="Which tier to manage character assignments in.  1 mean 'common', 6 means 'legendary'.") #TODO: cycle through the tiers?
async def removekeygen(interaction : dis.Interaction,
                       tier        : Optional[dac.Range[int, 1, 6]] = 1):
    """Creates a dropdown for removing characters from the Key Generation job.

        Input  : interaction - the interaction context from Discord.
                 tier - what rarity tier to remove (1-based for the average user)

        Output : N/A.
    """
    dis_log  = log.getLogger('discord')
    metadata = {'ctx'     : interaction,
                'db_ifc'  : db_ifc,
                'loop'    : IGSD_client.getLoop(),
                'post_fn' : post,
                'queue'   : job_queue
               }
    #one-based counting is purely for user convenience.
    tier -= 1

    options = db_ifc.getKeyGenParams(user_id = interaction.user.id)
    dis_log.debug(f"Got Key Gen parameters: {options}.")

    profiles = db_ifc.getKeyGenProfiles(tier_data = options,
                                        user_id   = interaction.user.id)
    dis_log.debug(f"Got profiles for Remove Key Gen: {profiles}.")

    if not profiles or 'total' not in options:

        await interaction.response.send_message('You need a character first!  Use the /roll command to get one!', ephemeral=True, delete_after=9.0)

    elif int(options['current_tier']) < tier:

        await interaction.response.send_message(f"You don't have access to this tier yet!  Right now you can access tier {options['tier'] + 1}. Start some /research and /building to upgrade!", ephemeral=True, delete_after=9.0)

    elif int(options['workers'][f'tier_{tier}']['count']) == 0:

        await interaction.response.send_message(f"You have no workers assigned to tier {tier + 1}!  Use /assignkeygen to add workers!", ephemeral=True, delete_after=9.0)

    else:

        options['tier'] = tier
        dis_log.debug(f"Creating a REMOVE KEY GEN view for user {interaction.user.id}.")

        view = ddf.DropdownView(ctx      = interaction,
                                type     = ddf.DropDownTypeEnum.REMOVE_KEY_GEN,
                                choices  = profiles,
                                metadata = metadata,
                                options  = options)

        await interaction.response.send_message(f'Select a profile to remove from keygen work for tier {tier + 1}:',view=view)

@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
async def roll(interaction: dis.Interaction):
    """Generates a new character and saves them to the caller's character list.

       Input  : interaction - the interaction context from Discord.

       Output : None.

       Note: All slash commands *MUST* respond in 3 seconds or be terminated.
    """
    dis_log = log.getLogger('discord')

    if db_ifc.dailyDone(interaction.user.id) :

        await interaction.response.send_message(f"You have already claimed a daily character, please wait until the daily reset to claim another.", ephemeral=True, delete_after=30.0)

    else :
        metadata = {'ctx'     : interaction,
                    'db_ifc'  : db_ifc,
                    'loop'    : IGSD_client.getLoop(),
                    'post_fn' : post,
                    'tag_rng' : tag_randomizer
                   }
        opts = {'random' : True,
                'prompt' : params['options']['prompts'],
                'seed'   : -1
               }
        dis_log.debug(f"Creating a job with metadata {metadata} and options {opts}.")
        job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.ROLL,
                                   ctx     = interaction,
                                   options = opts)
        dis_log.debug(f"Posting ROLL job {job} to the queue.")
        result = job_queue.add(metadata = metadata,
                               job      = job)

        await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
@dac.describe(user="The Discord user owning the profiles lsited by the command.  If none, it defaults to you.")
@dac.describe(profile_id="The profile ID of the character you'd like to view.  Use /listprofiles to see the name and ID for profiles!")
async def showprofile(interaction : dis.Interaction,
                      user        : Optional[dis.User] = None,
                      profile_id  : Optional[dac.Range[str, 0, 36]] = None): #The length of a UUID
    """Displays the profile associated with the provided ID.

        Input  : interaction - the interaction context from Discord.
                 id - the profile ID to retrieve.

        Output : N/A.
    """
    dis_log  = log.getLogger('discord')
    metadata = {'ctx'     : interaction,
                'db_ifc'  : db_ifc,
                'loop'    : IGSD_client.getLoop(),
                'post_fn' : post,
                'queue'   : job_queue
               }

    if profile_id == None:

        dis_log.debug(f"Creating a SHOW PROFILE view for user {interaction.user.id}.")
        user_id  = interaction.user.id if user == None else user.id
        profiles = db_ifc.getProfiles(user_id)
        dis_log.debug(f"User {user_id} returned profile list {profiles}.")
        view = ddf.DropdownView(ctx      = interaction,
                                type     = ddf.DropDownTypeEnum.SHOW,
                                choices  = profiles,
                                metadata = metadata)

        await interaction.response.send_message('Select a profile to view:',view=view)

    else:

        opts = {'id' : profile_id}

        dis_log.debug(f"Creating a job with metadata {metadata} and options {opts}.")
        job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.SHOWPROFILE,
                                   ctx     = interaction,
                                   options = opts)
        dis_log.debug(f"Posting SHOW job {job} to the queue.")
        result = job_queue.add(metadata = metadata,
                               job      = job)

        await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

#This is commented until the failed inheritance issue can be resolved.
#@IGSD_client.tree.command()
#async def testclear(interaction: dis.Interaction):
#    """A test flood of requests to verify the flush command works.
#
#       Input  : None.
#
#       Output : None.
#    """
#    dis_log = log.getLogger('discord')
#    rng    = range(1,10)
#
#    job = [{ 'metadata' : {
#                'ctx'    : interaction,
#                'loop'   : IGSD_client.getLoop(),
#                'poster' : post
#           },
#           'data' : {
#                #Requests are sorted by guild for rate-limiting
#                'guild'  : interaction.guild_id,
#                #This should really be metadata but the rest of the metadata
#                #can't be pickeled, so this must be passed with the work.
#                'id'     : x,
#                'post'   : {'empty'},
#                'reply'  : "test job"
#            }
#        } for x in rng]
#    dis_log.debug(f"trying to clear the queue.")
#
#    for m in rng:
#        result = job_queue.add(job[m -1])
#
#    job_queue.flush()
#
#    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

@IGSD_client.tree.command()
@dac.checks.has_permissions(manage_guild=True) #The closest to 'be a mod' Discord has.
async def testget(interaction: dis.Interaction):
    """A test HTTP GET command to verify basic connection to the webui page.
       Also tests the internal data path.

       Input  : interaction - the interaction context from Discord.

       Output : None.
    """

    dis_log  = log.getLogger('discord')
    metadata = {'ctx'     : interaction,
                'loop'    : IGSD_client.getLoop(),
                'post_fn' : post
               }
    dis_log.debug(f"Creating a job with metadata {metadata}.")
    job = jf.JobFactory.getJob(type = jf.JobTypeEnum.TESTGET,
                               ctx  = interaction)

    dis_log.debug(f"Posting test GET job {job} to the queue.")
    result = job_queue.add(metadata = metadata,
                           job      = job)

    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)


@IGSD_client.tree.command()
@dac.checks.has_permissions(manage_guild=True) #The closest to 'be a mod' Discord has.
async def testpost(interaction: dis.Interaction):
    """A test HTTP PUT command to verify basic connection to the webui page.

       Input  : interaction - the interaction context from Discord.

       Output : None.

       Note: All slash commands *MUST* respond in 3 seconds or be terminated.
    """

    dis_log  = log.getLogger('discord')
    metadata = {'ctx'     : interaction,
                'loop'    : IGSD_client.getLoop(),
                'post_fn' : post
               }
    dis_log.debug(f"Creating a job with metadata {metadata}.")
    job = jf.JobFactory.getJob(type = jf.JobTypeEnum.TESTPOST,
                               ctx  = interaction)
    dis_log.debug(f"Posting test PUT job {job} to the queue.")
    result = job_queue.add(metadata = metadata,
                           job      = job)

    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

@IGSD_client.tree.command()
@dac.checks.has_permissions(manage_guild=True) #The closest to 'be a mod' Discord has.
async def testroll(interaction: dis.Interaction):
    """Verifies a profile can be added to a test image.

       Input  : interaction - the interaction context from Discord.

       Output : None.

       Note: All slash commands *MUST* respond in 3 seconds or be terminated.
    """

    dis_log  = log.getLogger('discord')
    metadata = {'ctx'     : interaction,
                'loop'    : IGSD_client.getLoop(),
                'post_fn' : post
               }
    dis_log.debug(f"Creating a job with metadata {metadata}.")
    job = jf.JobFactory.getJob(type = jf.JobTypeEnum.TESTROLL,
                               ctx  = interaction)
    dis_log.debug(f"Posting test ROLL job {job} to the queue.")
    result = job_queue.add(metadata = metadata,
                           job      = job)

    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

@IGSD_client.tree.command()
@dac.checks.has_permissions(manage_guild=True) #The closest to 'be a mod' Discord has.
async def testshowprofile(interaction: dis.Interaction):
    """Verifies a profile can be retrieved and shown to the user.

       Input  : interaction - the interaction context from Discord.

       Output : None.

       Note: All slash commands *MUST* respond in 3 seconds or be terminated.
    """

    dis_log  = log.getLogger('discord')
    metadata = {'ctx'     : interaction,
                'db_ifc'  : db_ifc,
                'loop'    : IGSD_client.getLoop(),
                'post_fn' : post
               }
    dis_log.debug(f"Creating a job with metadata {metadata}.")
    job = jf.JobFactory.getJob(type = jf.JobTypeEnum.TESTSHOW,
                               ctx  = interaction)
    dis_log.debug(f"Posting test SHOW job {job} to the queue.")
    result = job_queue.add(metadata = metadata,
                           job      = job)

    await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

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


#/assignresearch
#/assignCrafting?
#/assignWorker?
#/CreateTeam
#/assignDungeon
#/hospital
#/shop