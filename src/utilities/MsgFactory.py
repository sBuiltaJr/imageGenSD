#encapsualtes different message types and post functions based on



#####  Imports  #####

from abc import ABC, abstractmethod
import asyncio as asy
import base64 as b64
import discord as dis
from enum import IntEnum, verify, UNIQUE
import io
#import MenuPagination as mp
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

    @abstractmethod
    def GetGuild(self) -> int:
        pass

    @abstractmethod
    def GetReason(self) -> str:
        pass

    @abstractmethod
    def GetStatusCode(self) -> int:
        pass

    @abstractmethod
    def GetUserId(self) -> int:
        pass

    @abstractmethod
    async def Post(self):
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
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetReason(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def GetUserId(self) -> int:
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
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetReason(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def GetUserId(self) -> int:
        pass

    async def Post(self,
                   ctx  : dis.Interaction):
        pass

    def Randomize(self):
        pass

class RollMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        pass

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self):
        pass

    def GetReason(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def GetUserId(self) -> int:
        pass

    async def Post(self,
                   ctx  : dis.Interaction):
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

    def GetGuild(self) -> int:
        pass

    def GetReason(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def GetUserId(self) -> int:
        pass

    async def Post(self,
                   ctx  : dis.Interaction):
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
        self.reply   = ""
        self.result  = req.Response()
        self.user_id = ctx.user.id

    def DoWork(self,
               web_url: str):

        self.result = req.get(url=urljoin(web_url, '/sdapi/v1/memory'), timeout=5)

    def GetGuild(self) -> int:

        return self.guild

    def GetReason(self) -> int:

        return self.result.reason

    def GetStatusCode(self) -> int:

        return self.result.status_code

    def GetUserId(self) -> int:

        return self.user_id

    async def Post(self,
                   ctx  : dis.Interaction):

        embed = dis.Embed(title='Test GET successful:',
                          description=f"Status code: {self.result.status_code} Reason: {self.result.reason}",
                          color=0x008000)

        await ctx.channel.send(content=f"<@{self.user_id}>",
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
        self.profile = pg.GetDefaultProfile()
        self.reply   = ""
        self.result  = req.Response()
        self.user_id = ctx.user.id

    def DoWork(self,
               web_url: str):

        self.result = req.post(url=urljoin(web_url, '/sdapi/v1/txt2img'), json=self.post)

    def GetGuild(self) -> int:

        return self.guild

    def GetReason(self) -> int:

        return self.result.reason

    def GetStatusCode(self) -> int:

        return self.result.status_code

    def GetUserId(self) -> int:

        return self.user_id

    async def Post(self,
                   ctx  : dis.Interaction):

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

        await ctx.channel.send(content=f"<@{self.user_id}>",
                               file=dis.File(fp=image,
                                             filename='image.png'),
                               embed=embed)

    def Randomize(self):
        pass

class TestRollMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        pass

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetReason(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def GetUserId(self) -> int:
        pass

    async def Post(self,
                   ctx  : dis.Interaction):
        pass

    def Randomize(self):
        pass

class TestShowMessage(Message):

    def __init__(self,
                 ctx  : dis.Interaction):
        pass

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetReason(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def GetUserId(self) -> int:
        pass

    async def Post(self,
                   ctx  : dis.Interaction):
        pass

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