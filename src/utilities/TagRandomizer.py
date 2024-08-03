#Selects a set of random tags to add to a given IGSD prompt.  Useful for
#pseudo-randomization of the output images given generic user prompts.  Also
#enables image generation of just randomized prompts.
#
#A dictionary-style format is used for user convenience and compatibility.


#####  Imports  #####

import linecache as lc
import logging as log
import logging.handlers as lh
import os
import pathlib as pl
import random as rand

#####  Tag Randomizer Class  #####

class TagRandomizer:

    def __init__(self, opts : dict):
        """Saves relevant tag randomizer settings for the object.  The
           randomizer gets all relevant parameters from the parent and assumes
           they have already been sanitized.

           Input: self - Pointer to the current object instance.
                  opts - a dictionary of all options for this class.

           Output: None - Throws exceptions on error.
        """
        self.rng_log = log.getLogger('tagrng')
        self.rng_log.setLevel(opts['log_lvl'])
        log_path     = pl.Path(opts['log_name_tagrng'])

        logHandler = lh.RotatingFileHandler(filename=log_path.absolute(),
                                            encoding=opts['log_encoding'],
                                            maxBytes=int(opts['max_bytes']),
                                            backupCount=int(opts['log_file_cnt'])
        )

        formatter = log.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}',
                                  opts['date_fmt'],
                                  style='{'
        )
        logHandler.setFormatter(formatter)
        self.rng_log.addHandler(logHandler)
        #This is deliberately not a Path, like in the parent, to allow linecache
        #to read the file in case the user decided to provide a large file.
        #Also, apparently Pathlib is missing methods that cachelib is using
        #(probably for sanitization), causing exceptions if you give it a Path.
        self.dict_path     = os.path.abspath(opts['rand_dict_path'])
        self.dict_size     = opts['dict_size']
        self.max_tags      = int(opts['max_rand_tag_cnt'])
        self.min_tags      = int(opts['min_rand_tag_cnt'])
        #Discord's limit for the tag generation, minus the length of a prefix
        self.post_limit    = 1023 - 2
        self.rand_retries  = int(opts['tag_retry_limit'])

        try:
            #Note the possibility of IO exceptions if /dev/urandom (or similar)
            #is not initialized/empty on your machine.
            rand.seed(rand.getrandbits(64))
            self.rng_log.debug(f"Using rand state: {rand.getstate()}")

        except Exception as err:
            self.rng_log.error(f"Error setting the RNG seed for the tag randomizer! {err}")

        self.rng_log.info(f"Initializing the Tag RNG class with parameters: dict path: {self.dict_path} dict_size: {self.dict_size} max tags: {self.max_tags} min_tags{self.min_tags}.")

    def getRandomTags(self, exact=0) -> (str, int):
        """Generates a string of comma-separated random tags extracted from the
           provided source dictionary.  Selects a random number of tags between
           the specified min and max values, defaulting to the init values.

           Input: self - Pointer to the current object instance.
                  exact - an exact number of tags to return (instead of min/max).

           Output: str - A comma-separated string of tags, doesn't assume the
                         parent added its own leading comma.
                   int - How many random tags were added to the prompt.
        """
        tag_count = 0
        tag_list  = ""
        infix     = ""

        #Users trying to be cute will get the default result.
        if exact > 0:
            tag_count = exact
        else:
            tag_count = rand.randint(self.min_tags, self.max_tags)

        for word in range(0, tag_count):

            tag = lc.getline(self.dict_path, rand.randint(0, self.dict_size))

            if tag_list.find(tag) > -1:

                self.rng_log.debug(f"Found duplicate tag {tag} from tag_list {tag_list}, attempting to get another")

                for retry in range (0, self.rand_retries):

                    tag = lc.getline(self.dict_path, rand.randint(0, self.dict_size))

                    if tag_list.find(tag) == -1:

                        self.rng_log.debug(f"Found new unique tag")
                        break

                self.rng_log.debug(f"Exiting de-dupe loop with tag {tag}.")

            #The getline function includes getting the separator.
            tag_list += (infix + tag.rstrip(os.linesep))
            infix     = ', '

        #Note: Embedded fields (like how tags are displayed in the Discord post)
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
                self.rng_log.warning(f"Tag list lacks comma separators and was bluntly truncated to {self.post_limit}.  This may still fail to post!")

            else:
                tag_list = tag_list[0:index]
                self.rng_log.warning(f"Tag_list exceeded allowed tag size limit of {self.post_limit}, truncated to {len(tag_list)}.  This may still fail to post!")

        self.rng_log.info(f"Used {tag_count} tags to get prompt input: {tag_list} of len {len(tag_list)}")
        tag_list = ', ' + tag_list

        return tag_list, tag_count
