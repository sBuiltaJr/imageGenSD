#Creates a base profile for an IGSD-generated image.


#####  Imports  #####
from enum import Enum
import logging as log
from . import NameRandomizer as nr
from . import RarityClass as rc
from . import StatsClass as sc
from typing import Literal, Optional


#####  Package Variables  #####

DEFAULT_OWNER = 170331989436661760
DEFAULT_ID    = "ffffffff-ffff-ffff-ffff-fffffffffffe"

#####  Profile Class  #####

#This definition must come before GetDefaultProfile so it can be referenced.
class Profile:

    #Optional Name?  description?
    def __init__(self,
                 opts : dict):
        """Creates a profile intended to attaching to an IGSD-generated image.

           Input: self - Pointer to the current object instance.
                  opts - a dict of values to set in the profile.

           Output: None - Throws exceptions on error.
        """

        self.affinity = int(opts['affinity']) if opts['affinity'] != None else 0
        self.battles  = int(opts['battles'])  if opts['battles']  != None else 0
        self.exp      = int(opts['exp'])      if opts['exp']      != None else 0
        self.favorite = int(opts['favorite']) if opts['favorite'] != None else 0
        self.history  = opts['history']       if opts['history']  != None else None
        self.id       = str(opts['id'])       if opts['id']       != None else DEFAULT_ID
        self.img_id   = str(opts['img_id'])   if opts['img_id']   != None else None #Separate to prevent laoded profiles from eating memory
        self.info     = opts['info']          if opts['info']     != None else None
        self.level    = int(opts['level'])    if opts['level']    != None else 0
        self.losses   = int(opts['losses'])   if opts['losses']   != None else 0
        self.missions = int(opts['missions']) if opts['missions'] != None else 0
        self.name     = nr.getRandomName()    if opts['name']     == None else opts['name']
        self.owner    =  int(opts['owner'])   if opts['owner']    != None else DEFAULT_OWNER
        self.rarity   = rc.Rarity.generateRarity(self) if opts['rarity'] == None else opts['rarity']
        self.wins     = int(opts['wins'])     if opts['wins']     != None else 0
        #The items below rely on items above.
        self.stats    = sc.Stats(rarity=self.rarity, opts=sc.getDefaultOptions()) if opts['stats'] == None else opts['stats']
        self.creator  = int(opts['creator'])  if opts['creator'] != None else self.owner
        self.desc     = opts['desc']          if opts['desc']    != None else sc.getDescription(self.rarity)

#####  Package Functions  #####

def getDefaultJobData() -> dict:
    """Returns the default job settings that can be provided to an empty
       query (or to reinitialize an object).

       Input: None.

       Output: opts - a dictionary of the default queue arguments.
    """

    return {
    'enable_hr'           : True,
    'denoising_strength'  : 0.35,
    'firstphase_width'    : 0,
    'firstphase_height'   : 0,
    'hr_scale'            : 2,
    'hr_upscaler'         : "4x-AnimeSharp",
    'hr_second_pass_steps': 10,
    'hr_resize_x'         : 1024,
    'hr_resize_y'         : 1536,
    'prompt'              : "detailed background, masterpiece, best quality, 1girl, white dress, dress, short sleeves, strapless dress, frills, thighhigh stockings, black thighhighs, boots, red hair, long hair, medium breasts, blush, slight smile, painting, paintbrush, eyebrows visible through hair, standing, easel, paint, blue eyes, brown shoes, bangs, canvas \(object\), holding paintbrush, braid, braided hair, painting \(object\), bow, yellow bow, hands up, hair ornament, indoors, cute,",
    'styles'              : ["string"],
    'seed'                : 2920639719,
    'subseed'             : -1,
    'subseed_strength'    : 0,
    'seed_resize_from_h'  : -1,
    'seed_resize_from_w'  : -1,
    'sampler_name'        : "",
    'batch_size'          : 1,
    'n_iter'              : 1,
    'steps'               : 50,
    'cfg_scale'           : 22.0,
    'width'               : 512,
    'height'              : 768,
    'restore_faces'       : False,
    'tiling'              : False,
    'do_not_save_samples' : False,
    'do_not_save_grid'    : False,
    'negative_prompt'     : "(low quality, worst quality:1.4), (bad anatomy), extra digit, fewer digits, (extra arms:1.2), bad hands, by (bad-artist:0.6), bad-image-v2-39000, NSFW, nipples, loli, child, children, shota, boy, male, men, man",
    'eta'                 : 0,
    's_churn'             : 0,
    's_tmax'              : 0,
    's_tmin'              : 0,
    's_noise'             : 1,
    'override_settings'   : {},
    'override_settings_restore_afterwards': True,
    'script_args'         : [],
    'sampler_index'       : "DPM++ 2M Karras",
    'script_name'         : "",
    'send_images'         : True,
    'save_images'         : False,
    'tags_added'          :'', #Custom parameter not for SD POST
    'tag_cnt'             : 0, #Custom parameter not for SD POST
    'alwayson_scripts'    : {}
    }

def getDefaultProfile() -> Profile:
    """Returns the default profile, intended for test functions.

       Input: None.

       Output: Profile - a profile with set defaults.
    """

    default = Profile(opts = getMascotOptions())

    return default

def getDefaultOptions() -> dict:
    """Returns a default dictionary of options accepted by the Profile class.

       Input: None

       Output: dict - a complete dictionary of default options.
    """
    opts = {'affinity' : None,
            'battles'  : None,
            'creator'  : None,
            'desc'     : None,
            'exp'      : None,
            'favorite' : None,
            'history'  : None,
            'id'       : None,
            'img_id'   : None,
            'info'     : None,
            'level'    : None,
            'losses'   : None,
            'missions' : None,
            'name'     : None,
            'owner'    : None,
            'rarity'   : None,
            'stats'    : None,
            'wins'     : None
           }

    return opts

def getMascotOptions() -> dict:
    """Returns a default dictionary of options suited for the Mascot profile.

       Input: None

       Output: dict - a complete dictionary of default options.
    """
    base_stats = sc.getDefaultOptions()
    base_stats.update((x,1) for x in iter(base_stats))

    opts = {'affinity' : None,
            'battles'  : None,
            'creator'  : DEFAULT_OWNER,
            'desc'     : "A poor defenseless bot doing its best.",
            'exp'      : None,
            'favorite' : DEFAULT_OWNER,
            'history'  : None,
            'id'       : DEFAULT_OWNER,
            'img_id'   : DEFAULT_ID,
            'info'     : None,
            'level'    : None,
            'losses'   : None,
            'missions' : None,
            'name'     : "IGSD Mascot",
            'owner'    : DEFAULT_OWNER,
            'rarity'   : rc.RarityList.CUSTOM,
            'stats'    : sc.Stats(rarity=rc.RarityList.CUSTOM,
                                  opts=base_stats),
            'wins'     : None
           }

    return opts