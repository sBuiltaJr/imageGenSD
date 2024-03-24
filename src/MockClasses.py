#Defines the shared mock interfaces used by unit tests.

from .utilities import JobFactory as jf
from .utilities import ProfileGenerator as pg
from .utilities import RarityClass as rc
import discord as dis
from typing import Callable, Optional, Any
import unittest
from unittest.mock import MagicMock

DEFAULT_DISPLAY_NAME = "UNIT TESTER 9000"
DEFAULT_GUILD_ID     = 1111111111
DEFAULT_PROFILE_ID   = 1234567890
DEFAULT_USER_ID      = 999999999999999999
DEFAULT_USER_NAME    = "DEFAULT_USER_NAME"
DEFAULT_UUID         = "ffffffff-ffff-ffff-ffff-fffffffffffe"


#####  Mock Database Interface Class  #####

class MockDb():

    class MockConnection():

        class cursor():

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

        return self.MockConnection()

class MockDbInterface():

    def assignKeyGenWork(self,
                         count       : int,
                         profile_ids : list,
                         tier        : int,
                         tier_data   : dict,
                         user_id     : int):
        """A bare minimum mock to ensure test compatability.
           Note: a quick of the current implementation requires throwing an
                 exception to exit the 'while True' loop in the function.

           Input: self - Pointer to the current object instance.
                  count - the User's total worker count of this type of work.
                  profile_ids - a (verified) lsit of IDs to assign to work.
                  tier - what level of work is being assigned.
                  tier_data - the worker data for this tier.
                  user_id - The Discord user assocaited with the action.

           Output: N/A
        """
        pass

    def dailyDone(self,
                  id : int) ->bool:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  id - the Discord user id for the command author.

           Output: bool - if the user has already rolled a daily
        """

        return (id != DEFAULT_PROFILE_ID)

    def getDropdown(self,
                    user_id : int) :
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  state - the state to put the boolean.

           Output: N/A
        """

        pass

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

    def getSummaryCharacters(self,
                             user_id : int) -> dict:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  user_id - the user_id to query. -1 means return error.

           Output: N/A
        """

        results = {}

        if user_id < 0:

            return None

        else :

            rarities = rc.RarityList.getStandardValueList()

            for x in rarities :

                results[f'{x}'] = {'avg_stat'       : 1.1,
                                   'avg_std'        : 1.1,
                                   'wins'           : 1,
                                   'losses'         : 1,
                                   'total_value'    : 1,
                                   'equipped'       : 1,
                                   'armed'          : 1,
                                   'avg_health'     : 1.1,
                                   'made_and_owned' : 1,
                                   'owned'          : 1,
                                   'occupied'       : 1}

            results['equipped']       = 1
            results['armed']          = 1
            results['highest_rarity'] = rc.RarityList.COMMON.value
            results['losses']         = 1
            results['made_and_owned'] = 1
            results['occupied']       = 1
            results['owned']          = 1
            results['total_value']    = 1
            results['wins']           = 1

        return results

    def getSummaryEconomy(self,
                          user_id : int) -> dict:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  user_id - the user_id to query. -1 means return error.

           Output: N/A
        """

        categories = ['builder', 'crafter', 'hospital', 'keygen', 'research', 'team', 'worker']
        results    = {}

        if user_id < 0:

            return None

        else :

            for key in categories:

                results[key] = {}
                results[key]['count']  = 1
                results[key]['tier']   = 1
                results[key]['tier_0'] = 1
                results[key]['tier_1'] = 1
                results[key]['tier_2'] = 1
                results[key]['tier_3'] = 1
                results[key]['tier_4'] = 1
                results[key]['tier_5'] = 1

        return results

    def getSummaryInventory(self,
                            user_id : int) -> dict:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  user_id - the user_id to query. -1 means return error.

           Output: N/A
        """

        results = {}

        if user_id < 0:

            return None

        else :

            results['dust'] = 1

            for tier in range(0,6):

                results[f'tier_{tier}'] = {}
                results[f'tier_{tier}']['armor_count']  = 1
                results[f'tier_{tier}']['key_count']    = 1
                results[f'tier_{tier}']['weapon_count'] = 1

        return results

    def putDropdown(self,
                    state : bool,
                    user_id : int) :
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.
                  state - the state to put the boolean.

           Output: N/A
        """

        pass

    def resetDailyRoll(self) ->bool:
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: N/A
        """

        pass

    def updateDailyKeyGenWork(self) ->bool:
        """A bare minimum mock to ensure test compatability.
           Note: a quick of the current implementation requires throwing an
                 exception to exit the 'while True' loop in the function.

           Input: self - Pointer to the current object instance.

           Output: N/A
        """

        pass

    def removeKeyGenWork(self,
                             count       : int,
                             profile_ids : list,
                             tier        : int,
                             tier_data   : dict,
                             user_id     : int):
        """A bare minimum mock to ensure test compatability.
           Note: a quick of the current implementation requires throwing an
                 exception to exit the 'while True' loop in the function.

           Input: self - Pointer to the current object instance.
                  count - the User's total worker count of this type of work.
                  profile_ids - a (verified) lsit of IDs to remove from work.
                  tier - what level of work is being removed from.
                  tier_data - the worker data for this tier.
                  user_id - The Discord user assocaited with the action.

           Output: N/A
        """
        pass

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


#####  Mock Interaction Class  #####

class MockInteraction():

    class InteractionChannel():

        async def send(self,
                       content          : Optional[str]       = None,
                       embed            : Optional[dis.Embed] = None,
                       allowed_mentions : Optional[Any]       = None,
                       file             : Optional[dis.File]  = None):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      content - Waht data to post to the channel.
                      embed - An optional embed to add to the message.
                      allowed_mentions - Which users can be mentioned in this reply.
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
                               content          : Optional[str]       = None,
                               delete_after     : Optional[float]     = None,
                               embed            : Optional[dis.Embed] = None,
                               allowed_mentions : Optional[Any]       = None,
                               ephemeral        : Optional[bool]      = None,
                               view             : Optional[Any]       = None):
            """A bare minimum mock to ensure test compatability.

               Input: self - Pointer to the current object instance.
                      delete_after - How long to display the message if ephemeral.
                      embed - An optional embed to add to the message.
                      allowed_mentions - Which users can be mentioned in this reply.
                      ephemeral - If the message should be automatically deleted.
                      view - Which discord view to edit.

               Output: none.
            """

            pass

        async def edit_message(self,
                               content : Optional[str]       = None,
                               embed   : Optional[dis.Embed] = None,
                               view    : Optional[Any]       = None):
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

            self.id           = DEFAULT_PROFILE_ID
            self.display_name = DEFAULT_DISPLAY_NAME

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

    async def edit_original_response(self,
                                     content     : Optional[str]       = None,
                                     embed       : Optional[dis.Embed] = None,
                                     attachments : Optional[Any]       = None):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: message - a mock Discord message.
        """

        pass

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


#####  Mock User Class  #####

class MockUser():

    def __init__(self,
                 id           : Optional[int] = DEFAULT_USER_ID,
                 display_name : Optional[str] = DEFAULT_DISPLAY_NAME,
                 name         : Optional[str] = DEFAULT_USER_NAME):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.id           = id
        self.display_name = DEFAULT_DISPLAY_NAME
        self.name         = name

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