#Encapsulates different job types and post functions based on the specific
#job type requested.


#####  Imports  #####

from abc import ABC, abstractmethod
import base64 as b64
from ..db import MariadbIfc as mdb
import discord as dis
from enum import IntEnum, verify, UNIQUE
import io
import json
from . import ProfileGenerator as pg
import requests as req
from typing import Optional
from urllib.parse import urljoin

#####  Package Variables  #####

#####  Abstract Classes  #####
class Job(ABC):

    @abstractmethod
    def doWork(self,
               web_url: str):
        """Does whatever work the job is requesting, like generating images
           from the Stable Diffusion URL.

           Input: self - Pointer to the current object instance.
                  web_url - a URL to a place to do work.

           Output: N/A.

           Note: This function is called in the Job Queue, meaning *only*
                 picklable data is available to it.
        """
        pass

    @abstractmethod
    def doRandomize(self,
                    tag_src):
        """Performs randomization functions for the request, if applicable.
           For example, adds randomized tags to a request if a 'randomized'
           flag is set true.

           Input: self - Pointer to the current object instance.

           Output: int - N/A.
        """
        pass

    def _getEmbedBaseForGenerate(self,
                                 info : dict) -> dis.Embed:
        """Returns a Dsicord embed object formatted for generate-style posts.

           Input: self - Pointer to the current object instance.
                  info - a dict of all the relevent embed parameters.

           Output: embed - A formatted Embed object.
        """
        embed = dis.Embed()

        embed.add_field(name='Prompt', value=info['prompt'])
        embed.add_field(name='Negative Prompt', value=info['negative_prompt'])
        embed.add_field(name='Steps', value=info['steps'])
        embed.add_field(name='Height', value=info['height'])
        embed.add_field(name='Width', value=info['width'])
        embed.add_field(name='Sampler', value=info['sampler_name'])
        embed.add_field(name='Seed', value=info['seed'])
        embed.add_field(name='Subseed', value=info['subseed'])
        embed.add_field(name='CFG Scale', value=info['cfg_scale'])
        #Randomized and co are special because they're not a parameter sent to SD.
        embed.add_field(name='Randomized', value=info['random'])
        embed.add_field(name='Tags Added to Prompt', value=info['tags_added'])

        return embed

    def _getEmbedBaseForProfiles(self) -> dis.Embed:
        """Returns a Dsicord embed object formatted for profile-style posts.

           Input: self - Pointer to the current object instance.
                  info - a dict of all the relevent embed parameters.

           Output: embed - A formatted Embed object.
        """
        embed = dis.Embed()

        favorite = f"<@{self.profile.favorite}>" if self.profile.favorite != 0 else "None. You could be here!"

        embed.add_field(name='Creator', value=f"<@{self.profile.creator}>")
        embed.add_field(name='Owner', value=f"<@{self.profile.owner}>")
        embed.add_field(name='Name', value=self.profile.name)
        embed.add_field(name='Rarity', value=self.profile.rarity.name)
        embed.add_field(name='Agility', value=self.profile.stats.agility)
        embed.add_field(name='Defense', value=self.profile.stats.defense)
        embed.add_field(name='Endurance', value=self.profile.stats.endurance)
        embed.add_field(name='Luck', value=self.profile.stats.luck)
        embed.add_field(name='Strength', value=self.profile.stats.strength)
        embed.add_field(name='Description', value=self.profile.desc)
        embed.add_field(name='Favorite', value=f"{favorite}")

        return embed

    def getGuild(self) -> int:
        """Returns the Guild (Discord Server) ID originating this request.

           Input: self - Pointer to the current object instance.

           Output: int - the numeric representation of a Guild.
        """

        return self.guild

    def getRandomize(self) -> bool:
        """Returns whether this request should have randomized tags added.

           Input: self - Pointer to the current object instance.

           Output: bool - Whether or not the job needs randomized tags added.
        """

        return self.randomize

    def getReason(self) -> str:
        """Returns the HTTP Reason string associated with this request.

           Input: self - Pointer to the current object instance.

           Output: str - Textual reason of a HTTP Status response.
        """

        return self.result.reason

    def getStatusCode(self) -> int:
        """Returns the HTTP status code associated with this request.

           Input: self - Pointer to the current object instance.

           Output: int - the numeric response to a HTTP request.
        """

        return self.result.status_code

    def getUserId(self) -> int:
        """Returns the (Discord) user ID that originated this request.

           Input: self - Pointer to the current object instance.

           Output: int - the numeric representation of a user.
        """

        return self.user_id

    @abstractmethod
    async def post(self,
                   metadata : dict):
        """Posts the job's response data to Discord, including handling
           command-specific formatting.

           Input: self - Pointer to the current object instance.
                  metadata - Context from the command needed to post correctly.

           Output: N/A.
        """
        pass

#####  Enum Classes  #####

@verify(UNIQUE)
class JobTypeEnum(IntEnum):

    GENERATE     =    0
    ROLL         =    1
    SHOWPROFILE  =    2
    TESTPOST     =    3
    TESTGET      =    4
    TESTROLL     =    5
    TESTSHOW     =    6

#####  Job Classes  #####

class GenerateJob(Job):

    def __init__(self,
                 ctx     : dis.Interaction,
                 options : Optional[dict] = None):
        """Creates a job object for the /generate command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of configs for this job.

           Output: N/A.
        """

        self.guild                  = ctx.guild_id
        self.post_data              = pg.getDefaultJobData()
        self.post_data['cfg_scale'] = options['cfg_scale']
        self.post_data['height']    = options['height']
        self.post_data['n_prompt']  = options['n_prompt']
        self.post_data['prompt']    = options['prompt']
        self.post_data['random']    = options['random']
        self.post_data['sampler']   = options['sampler']
        self.post_data['seed']      = options['seed']
        self.post_data['steps']     = options['steps']
        self.post_data['tag_cnt']   = options['tag_cnt']
        self.post_data['width']     = options['width']
        self.randomize              = bool(options['random'])
        self.result                 = req.Response()
        self.user_id                = ctx.user.id
        self.profile                = pg.Profile(self.user_id)

    def doWork(self,
               web_url : str):

        self.result = req.post(url=urljoin(web_url, '/sdapi/v1/txt2img'), json=self.post_data)

    async def post(self,
                   metadata : dict):

        json_result             = self.result.json()
        info_dict               = json.loads(json_result['info'])
        info_dict['random']     = self.randomize
        info_dict['tags_added'] = self.post_data['tags_added']
        embed                   = self._getEmbedBaseForGenerate(info=info_dict)

        for i in json_result['images']:
            image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))

        await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                           file=dis.File(fp=image,
                                                         filename='image.png'),
                                           embed=embed)

    def doRandomize(self,
                    tag_src):

        tag_data = tag_src.getRandomTags(int(self.post_data['tag_cnt']))
        self.post_data['prompt']     += tag_data[0]
        self.post_data['tags_added']  = tag_data[1]

class RollJob(Job):

    def __init__(self,
                 ctx     : dis.Interaction,
                 options : dict):
        """Creates a job object for the /roll command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of configs for this job.

           Output: N/A.
        """
        self.guild               = ctx.guild_id
        self.post_data           = pg.getDefaultJobData()
        self.post_data['prompt'] = options['prompt']
        self.post_data['seed']   = options['seed']
        self.randomize           = bool(options['random'])
        self.result              = req.Response()
        self.user_id             = ctx.user.id
        self.profile             = pg.Profile(self.user_id)

    def doWork(self,
               web_url : str):

        self.result = req.post(url=urljoin(web_url, '/sdapi/v1/txt2img'), json=self.post_data)

    async def post(self,
                   metadata : dict):

        json_result = self.result.json()
        info_dict   = json.loads(json_result['info'])

        #This is a cheating protection check to prevent a user that spamms the
        #/roll command cross different servers while the image is being
        #generated.  It's non-atomic so there's still a small window for
        #duplicate rolls, but is acceptable for now.
        if not metadata['db_ifc'].dailyDone(self.user_id):

            metadata['db_ifc'].saveRoll(id=self.user_id,
                                        img=json_result['images'][0],
                                        info=info_dict,
                                        profile=self.profile)

            embed = self._getEmbedBaseForProfiles()

            for i in json_result['images']:
                image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))

            await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                               file=dis.File(fp=image,
                                                             filename='image.png'),
                                               embed=embed)

    def doRandomize(self,
                    tag_src):

        tag_data = tag_src.getRandomTags(int(self.post_data['tag_cnt']))
        self.post_data['prompt']     += tag_data[0]
        self.post_data['tags_added']  = tag_data[1]

class ShowProfileJob(Job):

    def __init__(self,
                 ctx     : dis.Interaction,
                 options : dict):
        """Creates a job object for the /showprofile command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of configs for this job.

           Output: N/A.
        """

        self.id                 = options['id']
        self.guild              = ctx.guild_id
        self.randomize          = False
        self.result             = req.Response()
        self.result.reason      = "OK"
        self.result.status_code = 200
        self.user_id            = ctx.user.id

    def doWork(self,
               web_url: str):
        pass

    async def post(self,
                   metadata : dict):

        self.profile = metadata['db_ifc'].getProfile(self.id)

        if not self.profile:

            embed = dis.Embed(title="Error",
                              description=f"User A character with the ID `{self.id}` does not exist!",
                              color=0xec1802)
            await metadata['ctx'].channel.send(content=f"<@{self.user_id}>", embed=embed)

        else:
            embed       = self._getEmbedBaseForProfiles()
            self.db_img = metadata['db_ifc'].getImage(profile_id=self.id)

            image = io.BytesIO(b64.b64decode(self.db_img))

            await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                               file=dis.File(fp=image,
                                                             filename='image.png'),
                                               embed=embed)

    def doRandomize(self,
                    tag_src):
        pass

class TestGetJob(Job):

    def __init__(self,
                 ctx     : dis.Interaction,
                 options : Optional[dict] = None):
        """Creates a job object for the /testget command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of optional configs for this job.

           Output: N/A.
        """

        self.guild     = ctx.guild_id
        self.randomize = False
        self.result    = req.Response()
        self.user_id   = ctx.user.id

    def doWork(self,
               web_url : str):

        self.result = req.get(url=urljoin(web_url, '/sdapi/v1/memory'), timeout=5)

    async def post(self,
                   metadata : dict):

        embed = dis.Embed(title='Test GET successful:',
                          description=f"Status code: {self.result.status_code} Reason: {self.result.reason}",
                          color=0x008000)

        await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                           embed=embed)

    def doRandomize(self,
                    tag_src):
        pass

class TestPostJob(Job):

    def __init__(self,
                 ctx     : dis.Interaction,
                 options : Optional[dict] = None):
        """Creates a job object for the /testpost command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of optional configs for this job.

           Output: N/A.
        """

        self.guild     = ctx.guild_id
        self.post_data = pg.getDefaultJobData()
        self.randomize = False
        self.result    = req.Response()
        self.user_id   = ctx.user.id

    def doWork(self,
               web_url : str):

        self.result = req.post(url=urljoin(web_url, '/sdapi/v1/txt2img'), json=self.post_data)

    async def post(self,
                   metadata : dict):

        json_result             = self.result.json()
        info_dict               = json.loads(json_result['info'])
        info_dict['random']     = False
        info_dict['tags_added'] = ""
        embed                   = self._getEmbedBaseForGenerate(info=info_dict)

        for i in json_result['images']:
            image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))

        await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                           file=dis.File(fp=image,
                                                         filename='image.png'),
                                           embed=embed)

    def doRandomize(self,
                    tag_src):
        pass

class TestRollJob(Job):

    def __init__(self,
                 ctx     : dis.Interaction,
                 options : Optional[dict] = None):
        """Creates a job object for the /testroll command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of optional configs for this job.

           Output: N/A.
        """

        self.guild     = ctx.guild_id
        self.post_data = pg.getDefaultJobData()
        self.profile   = pg.getDefaultProfile()
        self.randomize = False
        self.result    = req.Response()
        self.user_id   = ctx.user.id

    def doWork(self,
               web_url : str):

        self.result = req.post(url=urljoin(web_url, '/sdapi/v1/txt2img'), json=self.post_data)

    async def post(self,
                   metadata : dict):

        embed       = self._getEmbedBaseForProfiles()
        json_result = self.result.json()

        for i in json_result['images']:
            image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))

        await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                           file=dis.File(fp=image,
                                                         filename='image.png'),
                                           embed=embed)

    def doRandomize(self,
                    tag_src):
        pass

class TestShowJob(Job):

    def __init__(self,
                 ctx     : dis.Interaction,
                 options : Optional[dict] = None):
        """Creates a job object for the /testshowprofile command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of optional configs for this job.

           Output: N/A.
        """

        self.guild              = ctx.guild_id
        self.profile            = ""
        self.result             = req.Response()
        self.randomize          = False
        self.result.reason      = "OK"
        self.result.status_code = 200
        self.user_id            = ctx.user.id

    def doWork(self,
               web_url : str):
        pass

    async def post(self,
                   metadata : dict):

        self.profile = metadata['db_ifc'].getProfile()
        self.db_img  = metadata['db_ifc'].getImage()
        embed        = self._getEmbedBaseForProfiles()

        image = io.BytesIO(b64.b64decode(self.db_img))

        await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                           file=dis.File(fp=image,
                                                         filename='image.png'),
                                           embed=embed)

    def doRandomize(self,
                    tag_src):
        pass


##### Post Job Factory Class  #####

class JobFactory:

    def getJob(type    : JobTypeEnum,
               ctx     : dis.Interaction,
               options : Optional[dict] = None) -> Job:
        """Returns an instance of a job type with appropriate options set.
           Note that no job can contain unpicklable data.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.
                  options - a dict of optional configs for this job.

           Output: msg - The appropriate job type.
        """

        match type:

            case JobTypeEnum.GENERATE:
                return GenerateJob(ctx,
                                   options)

            case JobTypeEnum.ROLL:
                return RollJob(ctx,
                               options)

            case JobTypeEnum.SHOWPROFILE:
                return ShowProfileJob(ctx,
                                      options)

            case JobTypeEnum.TESTPOST:
                return TestPostJob(ctx,
                                   options)

            case JobTypeEnum.TESTGET:
                return TestGetJob(ctx,
                                  options)

            case JobTypeEnum.TESTROLL:
                return TestRollJob(ctx,
                                   options)

            case JobTypeEnum.TESTSHOW:
                return TestShowJob(ctx,
                                   options)

            case _:
                raise NotImplementedError
