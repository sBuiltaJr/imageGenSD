#Defines the shared mock interfaces used by unit tests.

from .utilities import JobFactory as jf
from .utilities import ProfileGenerator as pg
import discord as dis
from typing import Callable, Optional, Any
import unittest
from unittest.mock import MagicMock

DEFAULT_GUILD_ID   = 1111111111
DEFAULT_PROFILE_ID = 1234567890


#####  Mock Database Interface Class  #####

class MockDb():

    class MockCursor():

        def __init__(self,
                     buffered : bool):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      buffered - If the cursor should be buffered or not.

               Output: none.
            """

            self.buffered = buffered
            self.last_cmd = ""

        def execute(self,
                    cmd : Optional[str] = None):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      cmd - What command to execute.

               Output: none.
            """

            self.last_cmd = cmd
            return

        def fetchone(self):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.

               Output: none.
            """

            return self.last_cmd

    class MockConnection():

        def __init__(self):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      content - What data to post to the channel.
                      embed - An optional embed to add to the message.
                      file - An optional fileadd to the message.

               Output: none.
            """

            self.auto_reconnect = False
            self.database       = ""
            self.cursor         = MockCursor(buffered=False)

        def execute(self,
                    cmd : Optional[str] = None) -> str :
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      cmd - What command to execute.

               Output: none.
            """

            return input

    def connect(self,
                host       : str,
                port       : int,
                user       : str,
                password   : str,
                autocommit : bool) -> MockConnection:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  autocommit - Whether to automatically publish results or not.
                  host - The DB's URL.
                  password - the db user's password.
                  port - The DB's port.
                  user - The user to add to DB commands.

           Output: MockConnection - a fake DB connection.
        """
        return MockConnection()

class MockDbInterface():

    def dailyDone(self,
                  id : int) ->bool:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  id - the Discord user id for the command author.

           Output: bool - if the user has already rolled a daily
        """

        return (id != DEFAULT_PROFILE_ID)

    def getInstance(self,
                    options : dict) ->bool:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  options - options to initialize the db.

           Output: N/A
        """

        pass

    def getProfile(self,
                   profile_id : Optional[str] = DEFAULT_PROFILE_ID) -> pg.Profile:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  profile_id - the IGSD character profile to show.

           Output: bool - if the user has already rolled a daily
        """

        if profile_id != None and profile_id == DEFAULT_PROFILE_ID:

            return pg.getDefaultProfile()

        else:

            return None

    def getImage(self,
                 profile_id : Optional[str] = DEFAULT_PROFILE_ID) -> Optional[str]:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  profile_id - the IGSD character profile to show.

           Output: bool - if the user has already rolled a daily
        """

        if profile_id != None and profile_id == DEFAULT_PROFILE_ID:

            return "iVBORw0KGgoAAAANSUhEUgAABAAA"

        else:

            return None

    def resetDailyRoll(self,
                       options : dict) ->bool:
        """A bare minimum mock to ensure test compatability.
           Note: a quick of the current implementation requires throwing an
                 exception to exit the 'while True' loop in the function.

           Input: self - Pointer to the current object instance.

           Output: N/A
        """

        raise NotImplementedError

    def saveRoll(self,
                 id      : int,
                 img     : str,
                 info    : dict,
                 profile : pg.Profile):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  id - the Discord user id for the command author.
                  img - the image string to save.
                  info - the SD info used to generate the image.
                  profile - the profile associated with the image.

           Output: bool - if the user has already rolled a daily
        """

        pass


#####  Mock GetPage Class  #####

class MockGetPage():

    async def get_page(self,
                       index : int):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  index - which page to get.

           Output: dis-Embed - a default Eiscord embed object.
                   int - a valid value of pages for a menu.
        """

        return dis.Embed(), index


#####  Mock Interaction Class  #####

class MockInteraction():

    class InteractionChannel():

        async def send(self,
                       content : Optional[str]       = None,
                       embed   : Optional[dis.Embed] = None,
                       file    : Optional[dis.File]  = None):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      content - Waht data to post to the channel.
                      embed - An optional embed to add to the message.
                      file - An optional fileadd to the message.

               Output: none.
            """

            pass

    class InteractionMessage():

        async def edit(self,
                       view : Optional[Any] = None):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      view - Which discord view to edit.

               Output: none.
            """

            pass

    class InteractionResponse():

        async def send_message(self,
                               delete_after : Optional[float]     = None,
                               embed        : Optional[dis.Embed] = None,
                               ephemeral    : Optional[bool]      = None,
                               view         : Optional[Any]       = None):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      delete_after - How long to display the message if ephemeral.
                      embed - An optional embed to add to the message.
                      ephemeral - If the message should be automatically deleted.
                      view - Which discord view to edit.

               Output: none.
            """

            pass

        async def edit_message(self,
                               embed        : Optional[dis.Embed] = None,
                               view         : Optional[Any]       = None):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      embed - An optional embed to add to the message.
                      view - Which discord view to edit.

               Output: none.
            """

            pass

    class InteractionUser():

        def __init__(self):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.

               Output: none.
            """

            self.id = DEFAULT_PROFILE_ID

    def __init__(self):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.channel     = self.InteractionChannel()
        self.guild_id    = DEFAULT_GUILD_ID
        self.interaction = 0
        self.message     = self.InteractionMessage()
        self.response    = self.InteractionResponse()
        self.user        = self.InteractionUser()

    async def original_response(self):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: message - a mock Discord message.
        """

        return self.message

#####  Mock Loop Class  #####

class MockLoop():

    def create_task(self,
                    coro : Any,
                    name : Optional[str] = None):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  coro - the coroutine to run.
                  name - task name for the coroutine.

           Output: message - a mock Discord message.
        """

        pass


#####  Mock Post  #####
def post(job      : jf.Job,
         metadata : dict):
    """A bare minimum mock to ensure test compatability.

       Input: N/A.

       Output: N/A.
    """

    pass


#####  Mock Queue Class  #####

class MockQueue():

    def put(self):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: json - A string formatted like a json file.
        """

        pass

    def get(self):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: json - A string formatted like a json file.
        """

        nr.getRandomName              = MagicMock()
        nr.getRandomName.return_value = "Default Sally"

        return jf.JobFactory.getJob(type=jf.JobTypeEnum.TESTGET,
                                    ctx=self.metadata['ctx'])


#####  Mock Result Class  #####

class MockResult():

    def json(self):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: json - A string formatted like a json file.
        """

        return {'info'   : '{"info":{"empty":"0"},"prompt":"good","negative_prompt":"bad","steps":"10","height":"256","width":"256","sampler_name":"Euler a","seed":"-1","subseed":"-1","cfg_scale":"1.0"}',
                'images' : ["iVBORw0KGgoAAAANSUhEUgAABAAA"]}


#####  Mock Tag Source Class  #####

class MockTagSource():

    def getRandomTags(self,
                      tag_src : int):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: N.A
        """

        return ("Default,Tag",2)


#####  Mock Button Class  #####

class MockUiButton():

    def __init__(self,
                 emoji: Optional[Any]       = None,
                 style: Optional[Any]       = None):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        pass

    async def button(self):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: N.A
        """

        pass


#####  Mock View Class  #####

class MockView():

    class MockMenuChild():

        def __init__(self):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.

               Output: none.
            """

            self.disabled = False
            self.emoji    = ""

    def __init__(self):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.children  = [self.MockMenuChild(),
                          self.MockMenuChild(),
                          self.MockMenuChild()]