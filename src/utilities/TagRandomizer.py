#Selects a set of random tags to add to a given IGSD prompt.  Useful for
#pseudo-randomization of the output images given generic user prompts.  Also
#enables image generation of just randomized prompts.
#
#A dictionary-style format is used for user convenience and compatability.


#####  Imports  #####
import linecache as lc
import logging as log
import os
import random as rand


class TagRandomizer:

    def __init__(self, dict_path: str, dict_size: int, min_tags: int, max_tags:int, rand_retries: int):
        """Saves relevant tag randomizer settings for the object.  The
           randomizer gets all relevant parameters from the parent and assumes
           #they have already been sanitized.

           Input: self - Pointer to the current object instance.
                  dict_path - where to find the tag dictionary.
                  max_tags - the maximum of random tags to add to a prompt.
                  mix_tags - the minimum of random tags to add to a prompt.
                  rand_retries - How many times to try getting a new random tag.
              
           Output: None - Throws exceptions on error.
        """
        
        #Maybe this should be a separate log at some point.
        self.rngLog        = log.getLogger('queue')
        #This is deliberatly not a Path, like in the parent, to allow linecache
        #to read the file in case the user decided to provide a large file.
        #Also, apparently Paythlib is missing methods that cachelib is using
        #(probably for sanitization), causing exceptions if you give it a Path.
        self.dict_path     = os.path.abspath(dict_path)
        self.dict_size     = dict_size
        self.max_tags      = max_tags
        self.min_tags      = min_tags
        self.post_limit    = 1023
        self.rand_retries  = rand_retries
        
        try:
            #Note the possibility of IO exceptions if /dev/urandom (or similar)
            #is not initialized/empty on your machine.
            rand.seed(rand.getrandbits(64))
            self.rngLog.debug(f"Using rand state: {rand.getstate()}")
            
        except Exception as err:
            self.rngLog.error(f"Error setting the RNG seed for the tag randomizer! {err}")
        
        self.rngLog.info(f"Initializing the Tag RNG class with parameters: dict path: {self.dict_path} dict_size: {self.dict_size} max tags: {self.max_tags} min_tags{self.min_tags}.")
        
    def getRandomTags(self, exact=0) -> (str, int):
        """Generates a string of comma-separated random tags extracted from the
           provided soruce dictionary.  Selects a random number of tags between
           the specified min and max values, defaulting to the init values.

           Input: self - Pointer to the current object instance.
                  exact - an exact number of tags to return (instead of min/max).
              
           Output: str - A comma-separated string of tags, doesn't assume the
                         parent added its own leading comma.
                   int - How many random tags were added the the prompt.
        """
        tag_count = 0
        tag_list  = ""
        
        #Users trying to be cute will get the default result.
        if exact > 0:
            tag_count = exact
        else:
            tag_count = rand.randint(self.min_tags, self.max_tags)
            
        for word in range(0, tag_count):
             
             tag = lc.getline(self.dict_path, rand.randint(0, self.dict_size))
             
             if tag_list.find(tag) > -1:
             
                self.rngLog.debug(f"Found duplicate tag {tag} from tag_list {tag_list}, attemptiong to get another")
                
                for retry in range (0, self.rand_retries):
                
                    tag = lc.getline(self.dict_path, rand.randint(0, self.dict_size))
                    
                    if tag_list.find(tag) == -1:
                    
                        self.rngLog.debug(f"Found new unique tag")
                        break
                    
                self.rngLog.debug(f"Exiting de-dupe loop with tag {tag}.")
             #The getline function includes getting the separator.
             tag_list += (', ' + tag.rstrip(os.linesep))
        
        #Note: Embedded fields (like how tags are dispalyed in the Discord post)
        #only allow up to self.post_limit characters, meaning we must truncate
        #the list to avoid exceptions in post-processing.
        if len(tag_list) > self.post_limit:
            #Find the last instance of a comma before the limit, and remove
            #everything following.
            index = tag_list.rfind(',', 0, self.post_limit)
            
            #If no comma is found at all, somehow, then we're forced to do a
            #blunt truncate.
            if index == -1:
            
                tag_list = tag_list[0:self.post_limit]
                self.rngLog.warning(f"Tag list lacks comma separators and was bluntly truncated to {self.post_limit}.  This may still fail to post!")
                
            else:
                tag_list = tag_list[0:index]
                self.rngLog.warning(f"Tag_list exceeded allwoed tag size limit of {self.post_limit}, truncated to {len(tag_list)}.  This may still fail to post!")
        
        self.rngLog.info(f"Used {tag_count} tags to get prompt input: {tag_list} of len {len(tag_list)}")
        
        return tag_list, tag_count
        