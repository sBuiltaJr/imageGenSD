#encapsualtes different message types and post functions based on



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
        pass

    def GetGuild(self) -> int:

        return self.guild

    def GetReason(self) -> int:

        return self.result.reason

    def GetStatusCode(self) -> int:

        return self.result.status_code

    def GetUserId(self) -> int:

        return self.user_id

    @abstractmethod
    async def Post(self,
                   metadata : dict):
        pass

    @abstractmethod
    def Randomize(self):
        pass

#####  Enum Casses  #####

@verify(UNIQUE)
class MessageTypeEnum(IntEnum):

    GENERATE     =    0
    LISTPROFILES =    1
    ROLL         =    2
    SHOWPROFILES =    3
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
        pass

    def DoWork(self,
               web_url: str):
        pass

    async def Post(self,
                   metadata : dict):
        pass

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

        #self.db_img  = ""
        self.guild              = ctx.guild_id
        self.result             = req.Response()
        self.result.reason      = "OK"
        self.result.status_code = 200
        self.user_id            = ctx.user.id

    def DoWork(self,
               web_url : str):
        return

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

            case MessageTypeEnum.SHOWPROFILES:
                return ShowProfilesMessage(ctx)

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