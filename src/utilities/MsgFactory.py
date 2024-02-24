#encapsualtes different message types and post functions based on the specific
#message type requested.


#####  Imports  #####

from abc import ABC, abstractmethod
import asyncio as asy
import base64 as b64
from ..db import MariadbIfc as mdb
import discord as dis
from enum import IntEnum, verify, UNIQUE
import io
import json
import pickle as pic
from . import ProfileGenerator as pg
import requests as req
from . import TagRandomizer as tr
from typing import Literal, Optional
from urllib.parse import urljoin

#####  Package Variables  #####

#####  Abstract Casses  #####
class Message(ABC):

    @abstractmethod
    def DoWork(self,
               web_url: str):
        """Does whatever work the message is requesting, like generating images
           from the Stable Diffusion URL.

           Input: self - Pointer to the current object instance.
                  web_url - a URL to a place to do work.

           Output: N/A.
           
           Note: This function is called in the Job Queue, meaning *only*
                 picklable data is available to it.
        """
        pass

    def GetGuild(self) -> int:
        """Returns the Guild (Discord Server) ID originating this request.

           Input: self - Pointer to the current object instance.

           Output: int - the numeric representation of a Guild.
        """

        return self.guild

    def GetReason(self) -> str:
        """Returns the HTTP Reason string associated with this request.

           Input: self - Pointer to the current object instance.

           Output: str - Textual reason of a HTTP Status response.
        """

        return self.result.reason

    def GetStatusCode(self) -> int:
        """Returns the HTTP status code associated with this request.

           Input: self - Pointer to the current object instance.

           Output: int - the numeric response to a HTTP request.
        """

        return self.result.status_code

    def GetUserId(self) -> int:
        """Returns the (Discord) user ID that originated this request.

           Input: self - Pointer to the current object instance.

           Output: int - the numeric representation of a user.
        """

        return self.user_id

    @abstractmethod
    async def Post(self,
                   metadata : dict):
        """Posts the message's response data to Discord, including handling
           command-specific formatting.

           Input: self - Pointer to the current object instance.
                  metadata - Context from the command needed to post correctly.

           Output: N/A.
        """
        pass

    @abstractmethod
    def Randomize(self):
        """Performs randomization functions for the request, if applicable.
           For example, adds randomized tags to a request if a 'randomized'
           flag is set true.

           Input: self - Pointer to the current object instance.

           Output: int - N/A.
        """
        pass

#####  Enum Casses  #####

@verify(UNIQUE)
class MessageTypeEnum(IntEnum):

    GENERATE     =    0
    LISTPROFILES =    1
    ROLL         =    2
    SHOWPROFILE  =    3
    TESTPOST     =    4
    TESTGET      =    5
    TESTROLL     =    6
    TESTSHOW     =    7

#####  Message Casses  #####

class GenerateMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        pass

    def DoWork(self,
               web_url : str):
        pass

    async def Post(self,
                   ctx  : dis.Interaction):
        pass

    def Randomize(self):
        pass

class ListProfilesMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        pass

    def DoWork(self,
               web_url : str):
        pass

    async def Post(self,
                   metadata : dict):
        pass

    def Randomize(self):
        pass

class RollMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        pass

    def DoWork(self,
               web_url : str):
        pass

    async def Post(self,
                   metadata : dict):

        """if msg['cmd'] == 'roll':

            info_dict = json.loads(msg['info'])
            db_ifc.SaveRoll(id=msg['id'],
                            img=msg['images'][0],
                            info=info_dict,
                            profile=self.profile)"""
        pass

    def Randomize(self):
        pass

class ShowProfileMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        """Creates a message object for the /showprofile command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.

           Output: N/A.
        """

        self.guild              = ctx.guild_id
        self.result             = req.Response()
        self.result.reason      = "OK"
        self.result.status_code = 200
        self.user_id            = ctx.user.id

    def DoWork(self,
               web_url: str):
        pass

    async def Post(self,
                   metadata : dict):

        self.profile = metadata['db_ifc'].GetProfile(metadata['id'])

        if not self.profile:

            embed = dis.Embed(title="Error",
                              description=f"User A character with the ID `{metadata['id']}` does not exist!",
                              color=0xec1802)
            await metadata['ctx'].channel.send(content=f"<@{self.user_id}>", embed=embed)

        else:
            embed        = dis.Embed()
            self.db_img  = metadata['db_ifc'].GetImage(profile_id=metadata['id'])
            favorite     = f"<@{self.profile.favorite}>" if self.profile.favorite != 0 else "None. You could be here!"

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

            image = io.BytesIO(b64.b64decode(self.db_img))

            await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                               file=dis.File(fp=image,
                                                             filename='image.png'),
                                               embed=embed)

    def Randomize(self):
        pass

class TestGetMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        """Creates a message object for the /testget command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.

           Output: N/A.
        """

        self.guild   = ctx.guild_id
        self.result  = req.Response()
        self.user_id = ctx.user.id

    def DoWork(self,
               web_url : str):

        self.result = req.get(url=urljoin(web_url, '/sdapi/v1/memory'), timeout=5)

    async def Post(self,
                   metadata : dict):

        embed = dis.Embed(title='Test GET successful:',
                          description=f"Status code: {self.result.status_code} Reason: {self.result.reason}",
                          color=0x008000)

        await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                           embed=embed)

    def Randomize(self):
        pass

class TestPostMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        """Creates a message object for the /testpost command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.

           Output: N/A.
        """

        self.guild   = ctx.guild_id
        self.post    = pg.GetDefaultJobData()
        self.result  = req.Response()
        self.user_id = ctx.user.id

    def DoWork(self,
               web_url : str):

        self.result = req.post(url=urljoin(web_url, '/sdapi/v1/txt2img'), json=self.post)

    async def Post(self,
                   metadata : dict):

        embed = dis.Embed()
        json_result = self.result.json()
        info_dict   = json.loads(json_result['info'])

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
        embed.add_field(name='Randomized', value=False)
        embed.add_field(name='Tags Added to Prompt', value="None")

        for i in json_result['images']:
            image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))

        await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                           file=dis.File(fp=image,
                                                         filename='image.png'),
                                           embed=embed)

    def Randomize(self):
        pass

class TestRollMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        """Creates a message object for the /testroll command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.

           Output: N/A.
        """

        self.guild   = ctx.guild_id
        self.post    = pg.GetDefaultJobData()
        self.profile = pg.GetDefaultProfile()
        self.result  = req.Response()
        self.user_id = ctx.user.id

    def DoWork(self,
               web_url : str):

        self.result = req.post(url=urljoin(web_url, '/sdapi/v1/txt2img'), json=self.post)

    async def Post(self,
                   metadata : dict):

        embed = dis.Embed()
        json_result = self.result.json()
        info_dict   = json.loads(json_result['info'])
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

        for i in json_result['images']:
            image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))

        await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                            file=dis.File(fp=image,
                                                          filename='image.png'),
                                            embed=embed)

    def Randomize(self):
        pass

class TestShowMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        """Creates a message object for the /testshowprofile command.

           Input: self - Pointer to the current object instance.
                  ctx - the Discord context from the user's slash command.

           Output: N/A.
        """

        self.guild              = ctx.guild_id
        self.result             = req.Response()
        self.result.reason      = "OK"
        self.result.status_code = 200
        self.user_id            = ctx.user.id

    def DoWork(self,
               web_url : str):
        pass

    async def Post(self,
                   metadata : dict):

        embed        = dis.Embed()
        self.profile = metadata['db_ifc'].GetProfile()
        self.db_img  = metadata['db_ifc'].GetImage()
        favorite     = f"<@{self.profile.favorite}>" if self.profile.favorite != 0 else "None. You could be here!"

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

        image = io.BytesIO(b64.b64decode(self.db_img))

        await metadata['ctx'].channel.send(content=f"<@{self.user_id}>",
                                           file=dis.File(fp=image,
                                                         filename='image.png'),
                                           embed=embed)

    def Randomize(self):
        pass


##### Post Message Factory Class  #####

class MsgFactory:

    def GetMsg(type : MessageTypeEnum,
               ctx  : dis.Interaction) -> Message:
        """Returns an instance of a message type with appropriate options set.
           Note that no message can contain unpicklable data.

           Input: self - Pointer to the current object instance.

           Output: msg - The appropriate message type.
        """

        match type:

            case MessageTypeEnum.GENERATE:
                return GenerateMessage(ctx)

            case MessageTypeEnum.LISTPROFILES:
                return ListProfilesMessage(ctx)

            case MessageTypeEnum.ROLL:
                return RollMessage(ctx)

            case MessageTypeEnum.SHOWPROFILE:
                return ShowProfileMessage(ctx)

            case MessageTypeEnum.TESTPOST:
                return TestPostMessage(ctx)

            case MessageTypeEnum.TESTGET:
                return TestGetMessage(ctx)

            case MessageTypeEnum.TESTROLL:
                return TestRollMessage(ctx)

            case MessageTypeEnum.TESTSHOW:
                return TestShowMessage(ctx)

            case _:
                return ( 0,   1)