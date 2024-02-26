#Defines the shared mock interfaces used by unit tests.

import discord as dis
from typing import Callable, Optional, Any

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

            self.id = 1234567890

    def __init__(self):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: none.
        """

        self.channel     = self.InteractionChannel()
        self.guild_id    = 111111111
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


#####  Mock GetPage Class  #####

class MockResult():

    def json(self):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: json - A string formatted like a json file.
        """
        return {'info'   : '{"info":{"empty":"0"},"prompt":"good","negative_prompt":"bad","steps":"10","height":"256","width":"256","sampler_name":"Euler a","seed":"-1","subseed":"-1","cfg_scale":"1.0"}',
                'images' : {"iVBORw0KGgoAAAANSUhEUgAABAAA":"0"}}


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



#####  Mock Tag Source Class  #####

class MockTagSource():

    def getRandomTags(self,
                      tag_src : int):
        """A bare minimum mock to ensure test compatability.

           Input: self - Pointer to the current object instance.

           Output: N.A
        """
        return ("Default,Tag",2)