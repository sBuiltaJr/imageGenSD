#Creates a base profile for an IGSD-generated image.


#####  Imports  #####
from enum import Enum
import logging as log
from . import NameRandomizer as nr
from . import RarityClass as rc
from . import StatsClass as sc
from typing import Literal, Optional


#####  Package Variables  #####

#####  Profile Class  #####

#This definition must come before GetDefaultProfile so it can be referenced.
class Profile:

    #Optional Name?  description?
    def __init__(self,
                 owner    : int,
                 #TODO: combine the options into the options dictionary
                 #in a way to avoid key errors.
                 affinity : Optional[int]           = None,
                 battles  : Optional[int]           = None,
                 creator  : Optional[int]           = None,
                 desc     : Optional[str]           = None,
                 exp      : Optional[int]           = None,
                 favorite : Optional[int]           = None,
                 history  : Optional[dict]          = None,
                 id       : Optional[int]           = None,
                 img_id   : Optional[int]           = None,
                 info     : Optional[dict]          = None,
                 level    : Optional[int]           = None,
                 losses   : Optional[int]           = None,
                 missions : Optional[int]           = None,
                 name     : Optional[str]           = None,
                 rarity   : Optional[rc.RarityList] = None,
                 stats    : Optional[sc.Stats]      = None,
                 wins     : Optional[int]           = None):
        """Creates a profile intended to attaching to an IGSD-generated image.

           Input: self - Pointer to the current object instance.

           Output: None - Throws exceptions on error.
        """

        self.affinity = affinity if affinity != None else 0
        self.battles  = battles if battles != None else 0
        self.creator  = creator if creator != None else owner
        self.exp      = exp if exp != None else 0
        self.favorite = favorite if favorite != None else 0
        self.id       = id if id != None else "ffffffff-ffff-ffff-ffff-fffffffffffe"
        self.img_id   = img_id if img_id != None else None #Separate to prevent laoded profiles from eating memory
        self.info     = info if info != None else None #Get IGSD image info before profile?
        self.level    = level if level != None else 0
        self.losses   = losses if losses != None else 0
        self.history  = history if history != None else None
        self.missions = missions if missions != None else 0
        self.name     = nr.GetRandomName() if name == None else name
        self.owner    = owner
        self.rarity   = rc.Rarity.GenerateRarity(self) if rarity == None else rarity
        self.stats    = sc.Stats(self.rarity) if stats == None else stats
        self.wins     = wins if wins != None else 0
        #The items below rely on items above.
        self.desc     = desc if desc != None else sc.GetDescription(self.rarity)

#####  Package Functions  #####

def GetDefaultJobData() -> dict:
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
    'random'              : False, #Custom parameter not for SD POST
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

def GetDefaultProfile() -> Profile:
    """Returns the default profile, intended for test functions.

       Input: None.

       Output: Profile - a profile with set defaults.
    """
    default = Profile(id=170331989436661760,
                      info=None,
                      affinity=0,
                      battles=0,
                      creator=170331989436661760,
                      desc="A poor defenseless bot doing its best.",
                      exp=0,
                      favorite=170331989436661760,
                      losses=0,
                      name="IGSD Mascot",
                      owner=170331989436661760,
                      rarity=rc.RarityList.CUSTOM,
                      stats=sc.Stats(rarity=rc.RarityList.CUSTOM,
                                     agility=1,
                                     defense=1,
                                     endurance=1,
                                     luck=1,
                                     strength=1),
                      wins=0)

    return default


