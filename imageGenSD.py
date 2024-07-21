#Manages user requests through Discord to generate images with a Stable
#Diffusion model filepath supplied in the config.json file.  Cannot prevent
#Specific types of images, like NSFW, from being generated.


#####  Imports  #####

import asyncio as asy
import discord as dis
from discord import app_commands as dac
from enum import Enum, IntEnum, verify, UNIQUE
import logging as log
import logging.handlers as lh
import json
import multiprocessing as mp
import os
import pathlib as pl
import requests as req
import src.characters.CharacterJobs as cj
import src.characters.ProfileGenerator as pg
import src.characters.RarityClass as rc
import src.db.MariadbIfc as mdb
import src.managers.DailyEventMgr as dem
import src.managers.QueueMgr as qm
import src.ui.DropDownFactory as ddf
import src.ui.MenuPagination as mp
import src.utilities.JobFactory as jf
import src.utilities.NameRandomizer as nr
import src.utilities.TagRandomizer as tr
import string
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
IGSD_version   = '0.3.89'
job_queue      = None
job_worker     = None
show_queue     = None
show_worker    = None
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

    dis_log = log.getLogger('discord')

    await interaction.response.send_message(f"This is bot version {IGSD_version}!  Invite me to your server with [this link](https://discord.com/api/oauth2/authorize?client_id=1084600126913388564&permissions=534723816512&scope=bot)!  Code found [on GitHub](https://github.com/sBuiltaJr/imageGenSD).", ephemeral=True, delete_after=30.0)

@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
@dac.describe(tier="Which tier to manage character assignments in.  1 means 'Base', 6 means 'Master'.") #TODO: cycle through the tiers?
@dac.describe(type="Where to assign work.  Defaults to Exploration_Team.")
async def assign(interaction : dis.Interaction,
                 tier        : Optional[dac.Range[int, 1, 6]] = 1,
                 type        : Optional[cj.AssignChoices] = cj.AssignChoices.Exploration_Team):
    """Assigns selected characters to a type of work.

        Input  : interaction - the interaction context from Discord.
                 tier - what rarity tier to assign for (1-based for the average user)
                 type - what type of work to assign the characters to.

        Output : N/A.

        Note: This function intentionally bundles several disparate commands
              together for user convenience.
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
    dis_log.debug(f"Got profiles for Assign: {profiles}.")

    options = db_ifc.getWorkerCountsInTier(user_id = interaction.user.id)
    dis_log.debug(f"Got worker counts for Assign: {options}.")

    options |= db_ifc.getSummaryEconomy(user_id    = interaction.user.id)
    dis_log.debug(f"Got Assign parameters: {options}.")

    if db_ifc.getDropdown(user_id = interaction.user.id) :

        await interaction.response.send_message(f'Please close your existing dropdown menu or wait for it to time out.', ephemeral=True, delete_after=9.0)

    elif not profiles or not options:

        await interaction.response.send_message('You need a character first!  Use the /roll command to get one, or free existing profiles from their assignments!', ephemeral=True, delete_after=9.0)

    elif int(options[type.value]['tier']) < tier:

        await interaction.response.send_message(f"You don't have access to this tier yet!  Right now you can access tier {options[type.value]['tier'] + 1}. Start some research and building with /assign to upgrade!", ephemeral=True, delete_after=9.0)

    elif int(options['counts'][type.value + tier]) >= int(options[type.value][f'tier_{tier}']):

        await interaction.response.send_message(f"You've assigned all possible workers for tier {tier + 1}!  Either remove a worker or research more slots.", ephemeral=True, delete_after=9.0)

    else:

        options['active_workers'] = options['counts'][type.value + tier]
        options['limit']          = options[type.value][f'tier_{tier}']
        options['tier']           = tier
        options['workers']        = db_ifc.getWorkersInJob(job     = type.value + tier,
                                                           user_id = interaction.user.id)

        match type:

            case cj.AssignChoices.Dungeon_Keys:

                dis_log.debug(f"Creating a ASSIGN KEY GEN view for user {interaction.user.id}.")

                view = ddf.DropdownView(ctx      = interaction,
                                        type     = ddf.DropDownTypeEnum.ASSIGN_KEY_GEN,
                                        choices  = profiles,
                                        metadata = metadata,
                                        options  = options)

                await interaction.response.send_message(f"Select profile(s) to assign to {type.name} for tier {tier + 1}:",view=view)

            case _:

                await interaction.response.send_message("This interaction is not yet implemented!", ephemeral=True, delete_after=9.0)

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
@dac.describe(name="A name, or fragment of, used to filter the profile list (case insensitive).")
@dac.describe(rarity="Which rarity to search.  If none, if defaults to showing all rarities.")
@dac.describe(user="The Discord user owning the profiles lsited by the command.  If none, it defaults to you.")
async def listprofiles(interaction : dis.Interaction,
                       name        : Optional[dac.Range[str, 0, 36]] = None,
                       rarity      : Optional[rc.RarityList]         = None,
                       user        : Optional[dis.User]              = None,):
    """Returns a pagenated list of profile names and IDs owned by the caller.

        Input  : interaction - the interaction context from Discord.
                 user - optional, the discord user whose profiles to list
                 rarity - optional, a rarity to filter results on
                 name - optional, a name or fragment thereof to filter the profile list

        Output : N/A.
    """

    dis_log       = log.getLogger('discord')
    error_desc    = ""
    profiles      = []
    rarity_values = None if rarity == None else int(rarity.value)
    title         = "Owned characters" + f" in tier {rarity.name}" if isinstance(rarity_values, int) else ""
    #This has to be in the function body because an arg can't be used to assign
    #another arg in the function call.
    user_id       = interaction.user.id if user == None else user.id
    user_dis      = interaction.user if user == None else user

    if rarity == None :

        rarities      = [str(x.value) for x in rc.RarityList]
        rarity_values = ','.join(rarities)

    if name == None:
        profiles      = db_ifc.getUsersProfiles(rarity  = rarity_values,
                                                user_id = user_id)
        error_desc    = f"User <@{user_id}> does not own any characters" + f" in tier {rarity.name}!" if isinstance(rarity_values, int) else "!"
    else:
        profiles      = db_ifc.getProfiles(name    = name.strip(string.punctuation),
                                           rarity  = rarity_values,
                                           user_id = user_id)
        error_desc    = f"Found no characters owned by user <@{user_id}> that have a name similar to {name}" + f" in tier {rarity.name}." if isinstance(rarity_values, int) else "."
        title         = f"Owned characters with name like {name}" + f" in tier {rarity.name}" if isinstance(rarity_values, int) else f""
    dis_log.debug(f"Got profiles for list profile: {profiles}.")

    if not profiles:
        
        embed = dis.Embed(title       = title,
                          description = error_desc,
                          color       = 0xec1802)
        await interaction.response.send_message(content=f"<@{interaction.user.id}>", embed=embed)

    else:

        short_profiles = [(profiles[x].name,profiles[x].id) for x in range(0,len(profiles))]

        await mp.MenuPagination(interaction = interaction,
                                profiles    = short_profiles,
                                title       = title,
                                user        = user_dis).navigate()

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
    global show_queue
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

    dis_log.debug(f"Creating Job Queue Manager.")
    job_queue = qm.Manager(manager_id = 0,
                           opts       = params['queue_opts'])
    job_worker = th.Thread(target = job_queue.putJob,
                           name   = "Job Queue mgr",
                           daemon = True)

    dis_log.debug(f"Creating Show Queue Manager.")
    show_queue = qm.Manager(manager_id = 1,
                            opts       = params['queue_opts'])
    show_worker = th.Thread(target = show_queue.putJob,
                            name   = "Show Queue mgr",
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
    job_worker.start()
    show_worker.start()

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
@dac.describe(tier="Which tier to manage character assignments in.  1 means 'Base', 6 means 'Master'.") #TODO: cycle through the tiers?
@dac.describe(type="Where to assign work.  Defaults to Exploration_Team.")
async def remove(interaction : dis.Interaction,
                 tier        : Optional[dac.Range[int, 1, 6]] = 1,
                 type        : Optional[cj.AssignChoices] = cj.AssignChoices.Exploration_Team):
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

    profiles = db_ifc.getWorkersInJob(job     = type.value + tier,
                                      user_id = interaction.user.id)
    dis_log.debug(f"Got profiles for Remove: {profiles}.")

    options = db_ifc.getWorkerCountsInTier(user_id = interaction.user.id)
    dis_log.debug(f"Got worker counts for Remove: {options}.")

    options |= db_ifc.getSummaryEconomy(user_id = interaction.user.id)
    dis_log.debug(f"Got Remove parameters: {options}.")

    if db_ifc.getDropdown(user_id = interaction.user.id) :

        await interaction.response.send_message(f'Please close your existing dropdown menu or wait for it to time out.', ephemeral=True, delete_after=9.0)

    elif not profiles or not options:

        await interaction.response.send_message('You need to create or assign a character to this kind of work first!  Use the /roll command to get one, or /assign to add workers!', ephemeral=True, delete_after=9.0)

    elif int(options[type.value]['tier']) < tier:

        await interaction.response.send_message(f"You don't have access to this tier yet!  Right now you can access tier {options[type.value]['tier'] + 1}. Start some research and building with /assign to upgrade!", ephemeral=True, delete_after=9.0)

    else:

        options['active_workers'] = options['counts'][type.value + tier]
        options['tier']           = tier

        match type:

            case cj.AssignChoices.Dungeon_Keys:

                dis_log.debug(f"Creating a REMOVE KEY GEN view for user {interaction.user.id}.")

                view = ddf.DropdownView(ctx      = interaction,
                                        type     = ddf.DropDownTypeEnum.REMOVE_KEY_GEN,
                                        choices  = profiles,
                                        metadata = metadata,
                                        options  = options)

                await interaction.response.send_message(f'Select a profile to remove from keygen work for tier {tier + 1}:',view=view)

            case _:

                await interaction.response.send_message("This interaction is not yet implemented!", ephemeral=True, delete_after=9.0)

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
@dac.describe(name="A name of the profile to view. Will find all similar names (case insensitive).")
@dac.describe(profile_id="The profile ID of the character.  Use /listprofiles to find the ID.")
@dac.describe(rarity="Which rarity to search.  If none, if defaults to showing all rarities.")
@dac.describe(user="The Discord user owning the profiles.  If none, it defaults to you.")
async def showprofile(interaction : dis.Interaction,
                      name        : Optional[dac.Range[str, 0, 36]] = None,
                      profile_id  : Optional[dac.Range[str, 0, 36]] = None,  #The length of a UUID
                      rarity      : Optional[rc.RarityList]         = None,
                      user        : Optional[dis.User]              = None):
    """Displays a profile or a dropdown of matching profiles.

        Input  : interaction - the interaction context from Discord.
                 name - A name that will be used to search the profiles.
                 profile_id - the profile ID to retrieve.
                 rarity - optional, a rarity to search in.
                 user - which user's profiles to show; defaults to the author.

        Output : N/A.
    """

    dis_log       = log.getLogger('discord')
    metadata      = {'ctx'     : interaction,
                     'db_ifc'  : db_ifc,
                     'loop'    : IGSD_client.getLoop(),
                     'post_fn' : post,
                     'queue'   : show_queue
                    }
    rarity_values = None if rarity == None else int(rarity.value)


    if rarity == None :

        rarities      = [str(x.value) for x in rc.RarityList]
        rarity_values = ','.join(rarities)

    user_id  = interaction.user.id if user == None else user.id

    if profile_id != None:
        #The profile id was provided, prioritize that over everything else

        opts = {'id' : profile_id}

        dis_log.debug(f"Creating a job with metadata {metadata} and options {opts}.")
        job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.SHOW_PROFILE,
                                   ctx     = interaction,
                                   options = opts)
        dis_log.debug(f"Posting SHOW job {job} to the queue.")
        result = show_queue.add(metadata = metadata,
                                job      = job)

        await interaction.response.send_message(f'{result}')
    else:
        #get profiles from the database using user and name

        if db_ifc.getDropdown(user_id = interaction.user.id) :

            await interaction.response.send_message(f'Please close your existing dropdown menu or wait for it to time out.', ephemeral=True, delete_after=9.0)

        else:

            dis_log.debug(f"Creating a SHOW PROFILE view for user {interaction.user.id}.")
            empty_error  = "";
            many_message = "";

            if name == None:

                profiles     = db_ifc.getUsersProfiles(rarity  = rarity_values,
                                                       user_id = user_id)
                empty_error  = f"<@{user_id}> does't own any profiles" + f" in tier {rarity.name}!" if isinstance(rarity_values, int) else "!"
                many_message = f'Select a profile to view:'

            else:

                dis_log.debug(f"Looking for profiles of name {name} and rarity {rarity}.")
                profiles     = db_ifc.getProfiles(name    = name.strip(string.punctuation), 
                                                  rarity  = rarity_values,
                                                  user_id = user_id)
                empty_error  = f"Found no characters owned by <@{user_id}> that have a name similar to {name}" + f" in tier {rarity.name}!" if isinstance(rarity_values, int) else "!"
                many_message = f"Select a profile with name like '{name}' to view:"

            if len(profiles) == 0:

                dis_log.debug(f"Looking for name, Found none {name} with rarity {rarity_values}")
                embed = dis.Embed(title="Error",
                                  description=empty_error,
                                  color=0xec1802)
                await interaction.response.send_message(content=f"<@{interaction.user.id}>", embed=embed)

            elif len(profiles) == 1:

                dis_log.debug(f"Looking for name, Found one {name} {rarity_values} {profiles[0].id}")
                opts = {'id' : profiles[0].id}

                dis_log.debug(f"Creating a job with metadata {metadata} and options {opts}.")
                job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.SHOW_PROFILE,
                                           ctx     = interaction,
                                           options = opts)
                dis_log.debug(f"Posting SHOW job {job} to the queue.")
                result = show_queue.add(metadata = metadata,
                                        job      = job)

                await interaction.response.send_message(f'{result}')

            else:

                dis_log.debug(f"Looking for name, Found many {len(profiles)}")
                view = ddf.DropdownView(ctx      = interaction,
                                        type     = ddf.DropDownTypeEnum.SHOW,
                                        choices  = profiles,
                                        metadata = metadata)

                await interaction.response.send_message(many_message,view=view)

@verify(UNIQUE)
class SummaryChoices(Enum):
    #lower case since it's user-facing
    Characters = 0
    Economy    = 1
    Inventory  = 2

@IGSD_client.tree.command()
@dac.checks.has_permissions(use_application_commands=True)
@dac.describe(user="The Discord user owning the profiles listed by the command.  If none, it defaults to you.")
@dac.describe(type="What kind of summary to show (characters, economy, or inventory).  Defaults to inventory.")
async def showsummary(interaction : dis.Interaction,
                      type        : Optional[SummaryChoices] = SummaryChoices.Inventory,
                      user        : Optional[dis.User] = None):
    """Displays various kinds of summaries for a particular player.  Defaults
       to showing the user's inventory.

        Input  : interaction - the interaction context from Discord.
                 type - what kind of summary to show.
                 user - which user's profiles to show; defaults to the author.

        Output : N/A.
    """

    dis_log  = log.getLogger('discord')
    metadata = {'ctx'     : interaction,
                'db_ifc'  : db_ifc,
                'loop'    : IGSD_client.getLoop(),
                'post_fn' : post,
                'queue'   : show_queue
               }


    opts = {'user_id' : interaction.user.id if user == None else user.id}

    if db_ifc.getDropdown(user_id = interaction.user.id) :

        await interaction.response.send_message(f'Please close your existing dropdown menu or wait for it to time out.', ephemeral=True, delete_after=9.0)

    else :

        match type:

            case SummaryChoices.Characters:

                dis_log.debug(f"Creating a job with metadata {metadata}.")
                job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.SHOW_SUMMARY_CHARACTERS,
                                           ctx     = interaction,
                                           options = opts)

                dis_log.debug(f"Posting CHARACTERS SUMMARY job {job} to the queue.")
                result = show_queue.add(metadata = metadata,
                                        job      = job)

            case SummaryChoices.Economy:

                dis_log.debug(f"Creating a job with metadata {metadata}.")
                job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.SHOW_SUMMARY_ECONOMY,
                                           ctx     = interaction,
                                           options = opts)

                dis_log.debug(f"Posting ECONOMY SUMMARY job {job} to the queue.")
                result = show_queue.add(metadata = metadata,
                                        job      = job)

            case SummaryChoices.Inventory:

                dis_log.debug(f"Creating a INVENTORY SUMMARY job with metadata {metadata}.")
                job = jf.JobFactory.getJob(type    = jf.JobTypeEnum.SHOW_SUMMARY_INVENTORY,
                                           ctx     = interaction,
                                           options = opts)

                dis_log.debug(f"Posting INVENTORY SUMMARY job {job} to the queue.")
                result = show_queue.add(metadata = metadata,
                                        job      = job)

            case _:

                dis_log.Error(f"Given an invalid type of showsummary job {type}!")
                result = "Error, this is an invalid choice!"

        await interaction.response.send_message(f'{result}', ephemeral=True, delete_after=9.0)

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
    job = jf.JobFactory.getJob(type = jf.JobTypeEnum.TEST_GET,
                               ctx  = interaction)

    dis_log.debug(f"Posting test GET job {job} to the queue.")
    result = show_queue.add(metadata = metadata,
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
    job = jf.JobFactory.getJob(type = jf.JobTypeEnum.TEST_POST,
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
    job = jf.JobFactory.getJob(type = jf.JobTypeEnum.TEST_ROLL,
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
    job = jf.JobFactory.getJob(type = jf.JobTypeEnum.TEST_SHOW,
                               ctx  = interaction)
    dis_log.debug(f"Posting test SHOW job {job} to the queue.")
    result = show_queue.add(metadata = metadata,
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


#/shop
