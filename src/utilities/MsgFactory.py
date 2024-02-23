#encapsualtes different message types and post functions based on



#####  Imports  #####


import .ProfileGenerator as pg
import .MenuPagination as mp
import .TagRandomizer as tr
from abc import ABC, abstractmethod
import base64 as b64
import discord as dis
from enum import IntEnum, verify, UNIQUE
import io
import pickle as pic
import requests as req
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
    def GetResult(self) -> str:
        pass

    @abstractmethod
    def GetId(self) -> int:
        pass

    @abstractmethod
    def GetStatusCode(self) -> int:
        pass

    @abstractmethod
    def Post(self):
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
                 options : dict):

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetId(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def Post(self):
        pass

    def Randomize(self):
        pass

class ListProfilesMessage(Message):

    def __init__(self,
                 options : dict):

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetId(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def Post(self):
        pass

    def Randomize(self):
        pass

class RollMessage(Message):

    def __init__(self,
                 options : dict):

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetId(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def Post(self):
        pass

    def Randomize(self):
        pass

class ShowProfileMessage(Message):

    def __init__(self,
                 options : dict):

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetId(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def Post(self):
        pass

    def Randomize(self):
        pass

class TestGetMessage(Message):

    def __init__(self,
                 options : dict)

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetId(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def Post(self):
        pass

    def Randomize(self):
        pass

class TestPostMessage(Message):

    def __init__(self,
                 options : dict):

        self.ctx      = options['ctx']
        self.embed    = dis.Embed()
        self.guild    = self.ctx.guild_id
        self.loop     = options['loop']
        self.post_fn  = options['post_fn']
        self.post     = pg.GetDefaultJobData()
        self.post     = pg.GetDefaultProfile()
        self.reply    = ""
        self.result   = req.Response()
        self.user_id  = self.ctx.user.id

    def DoWork(self,
               web_url: str):
        self.result = req.get(url=urljoin(web_url, '/sdapi/v1/memory'), timeout=5)

    def GetGuild(self) -> int:
        return self.guild
        
    def GetResult(self) -> str:
        return self.result.status_code

    def GetUserId(self) -> int:
        return self.ctx.user.id

    def GetStatusCode(self) -> int:
        pass

    def Post(self):
    
        info_dict = json.loads(msg['info'])

        self.embed.add_field(name='Prompt', value=info_dict['prompt'])
        self.embed.add_field(name='Negative Prompt', value=info_dict['negative_prompt'])
        self.embed.add_field(name='Steps', value=info_dict['steps'])
        self.embed.add_field(name='Height', value=info_dict['height'])
        self.embed.add_field(name='Width', value=info_dict['width'])
        self.embed.add_field(name='Sampler', value=info_dict['sampler_name'])
        self.embed.add_field(name='Seed', value=info_dict['seed'])
        self.embed.add_field(name='Subseed', value=info_dict['subseed'])
        self.embed.add_field(name='CFG Scale', value=info_dict['cfg_scale'])
        #Randomized and co are special because they're not a parameter sent to SD.
        self.embed.add_field(name='Randomized', value=msg['random'])
        self.embed.add_field(name='Tags Added to Prompt', value=msg['tags_added'])

        for i in msg['images']:
            image = io.BytesIO(b64.b64decode(i.split(",", 1)[0]))

        await msg['ctx'].channel.send(content=f"<@{msg['ctx'].user.id}>",
                                      file=dis.File(fp=image,
                                      filename='image.png'),
                                      embed=embed)

    def Randomize(self):
        pass

class TestRollMessage(Message):

    def __init__(self,
                 options : dict):

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetId(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def Post(self):
        pass

    def Randomize(self):
        pass

class TestShowMessage(Message):

    def __init__(self,
                 options : dict):

    def DoWork(self,
               web_url: str):
        pass

    def GetGuild(self) -> int:
        pass

    def GetId(self) -> int:
        pass

    def GetStatusCode(self) -> int:
        pass

    def Post(self):
        pass

    def Randomize(self):
        pass


##### Post Message Factory Class  #####

class MsgFactory:

    def GetMsg(self,
               type    : MessageTypeEnum,
               options : dict) -> Message:
        """Returns an instance of a message type with appropriate options set.

           Input: self - Pointer to the current object instance.

           Output: msg - The appropriate message type.
        """

        match type:

            case MessageTypeEnum.GENERATE:
                return GenerateMessage(options)

            case MessageTypeEnum.LISTPROFILES:
                return ListProfilesMessage(options)

            case MessageTypeEnum.ROLL:
                return RollMessage(options)

            case MessageTypeEnum.SHOWPROFILES:
                return ShowProfilesMessage(options)

            case MessageTypeEnum.TESTPOST:
                return TestPostMessage(options)

            case MessageTypeEnum.TESTGET:
                return TestGetMessage(options)

            case MessageTypeEnum.TESTROLL:
                return TestRollMessage(options)

            case MessageTypeEnum.TESTSHOW:
                return TestShowMessage(options)

            case _:
                return ( 0,   1)