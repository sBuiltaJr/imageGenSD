#Manages user requests through Discord to generate images with a Stable
#Diffusion model filepath supplied in the config.json file.  Cannot prevent
#Specific types of images, like NSFW, from being generated.


#####  imports  #####
import discord as dis
import logging as log
import os

#The great thing about dictionaries defined at the package level is their global
#(public-like) capability, avoiding constant passing down to 'lower' defs. 
#Static data only, no file objects or similar (or else!).
params = {'cfg'       : 'config.json',
          'bot_token' : ''}
IGSD_version = '0.0.1'







if __name__ == '__main__':
    asyncio.run(main())