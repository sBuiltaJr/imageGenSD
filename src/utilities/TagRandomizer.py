#Selects a set of random tags to add to a given IGSD prompt.  Useful for
#pseudo-randomization of the output images given generic user prompts.  Also
#enables image generation of just randomized prompts.
#
#A dictionary-style format is used for user convenience and compatability.


#####  Imports  #####
import linecache as lc
#import pathlib as pl


class TagRandomizer:

    def __init__(self, dict_path: str, min_tags: int, max_tags:int):
        """Saves relevant tag randomizer settings for the object.  The
           randomizer gets all relevant parameters from the parent and assumes
           #they have already been sanitized.

           Input: self - Pointer to the current object instance.
                  dict_path - where to find the tag dictionary.
                  max_tags - the maximum of random tags to add to a prompt.
                  mix_tags - the minimum of random tags to add to a prompt.
              
           Output: None - Throws exceptions on error.
        """
        #This is deliberatly not a Path, like in the parent, to allow linecache
        #to read the file in case the user decided to provide a large file.
        self.dict_path = dict_path
        self.max_tags  = max_tags
        self.min_tags  = min_tags
        
    def getRandomTags(self, exact=0) -> str:
        """Generates astring of comma-separated random tags extracted from the
           provided soruce dictionary.  Selects a random number of tags between
           the specified min and max values, defaulting to the init values.

           Input: self - Pointer to the current object instance.
                  exact - an exact number of tags to return (instead of min/max).
              
           Output: str - A comma-separated lsit of tags, assumes the parent
                         added its own leading comma.
        """
        tag_list = ""
        
        return tag_list
        