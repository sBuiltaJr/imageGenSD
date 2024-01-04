#Creates a randomized name from a dictionary of first and last names. Created
#as a non-class utility due to expected low request volume and to allow for
#implementation changes without affecting the parent.
#
#A dictionary-style format is used for user convenience and compatibility.


#####  Imports  #####

import linecache as lc
import logging as log
import os
import random as rand

#####  Package Variables  #####

fn_dict_path = None
fn_dict_size = 0
ln_dict_path = None
ln_dict_size = 0
name_log     = None

#####  Package Functions  #####

def init(options : dict):
    """Saves relevant settings to avoid repetitive reads to dictionaries.
       It gets all relevant parameters from the parent and assumes they
       have already been sanitized.

       Input: self - Pointer to the current object instance.
              fn_dict_path - where to find the first name dictionary.
              fn_dict_size - number of new-line separated names in the dictionary.
              ln_dict_path - where to find the last name dictionary.
              ln_dict_size - number of new-line separated names in the dictionary.

       Output: None - Throws exceptions on error.
    """
    global name_log
    global fn_dict_path
    global fn_dict_size
    global ln_dict_path
    global ln_dict_size

    #Maybe this should be a separate log at some point.
    name_log  = log.getLogger('discord')
    #This is deliberately not a Path, like in the parent, to allow linecache
    #to read the file in case the user decided to provide a large file.
    #Also, apparently Pathlib is missing methods that cachelib is using
    #(probably for sanitization), causing exceptions if you give it a Path.
    fn_dict_path = os.path.abspath(options['fn_dict_path'])
    fn_dict_size = int(options['fn_dict_size'])
    ln_dict_path = os.path.abspath(options['ln_dict_path'])
    ln_dict_size = int(options['ln_dict_size'])

    #TODO: add a RNG initializer if this is ever split into its own thread.

    name_log.info(f"Initializing the Name RNG class with: first name dict path: {fn_dict_path} fn_dict_size: {fn_dict_size} last name dict path: {ln_dict_path} ln_dict_size: {ln_dict_size}.")

def getRandomName() -> str:
    """Creates a randomized name from the name dictionaries provided during
       initialization.

       Input: self - Pointer to the current object instance.

       Output: str - A space-separated full name in Western order.
    """
    global name_log
    global fn_dict_path
    global fn_dict_size
    global ln_dict_path
    global ln_dict_size
    first_name = "Default"
    last_name  = "Sally"

    #Consider adding the ability for a variable length name string return.

    first_name = (lc.getline(fn_dict_path, rand.randint(0, fn_dict_size))).rstrip()
    last_name  = (lc.getline(ln_dict_path, rand.randint(0, ln_dict_size))).rstrip()

    name_log.debug(f"Generated name {first_name + ' ' + last_name} from {fn_dict_path} {ln_dict_path}")

    return first_name + ' ' + last_name
