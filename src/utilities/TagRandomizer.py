#Selects a set of random tags to add to a given IGSD prompt.  Useful for
#pseudo-randomization of the output images given generic user prompts.  Also
#enables image generation of just randomized prompts.
#
#A dictionary-style format is used for user convenience and compatability.


#####  Imports  #####
import linecache as lc


class TagRandomizer:

    def __init__(self):
        """Manages job request queueing and tracks relevant discord context,
           such as poster, Guild, channel, etc.  The Manager gets this from the
           caller so different Managers could have different settings.

           Input: self - Pointer to the current object instance.
                  loop - The asyncio event loop this manager posts to.
                  manager_id - The current Manager's ID, assigned by the caller.
                  opts - A dictionary of options, like cooldowns.
              
           Output: None - Throws exceptions on error.
        """