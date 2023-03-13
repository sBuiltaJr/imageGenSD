# imageGenSD
## A Stable-Diffusion driven Image Generator Bot for Discord

iamgeGenSD is a Stable-Diffusion wrapper written in Python.  It uses [Discord.py](https://discordpy.readthedocs.io/en/stable/index.html)
to listen for user requests and pass the commands to a Stable-Diffusion backend
for processing, posting the results to the channel as requested.

This project does not contain Stable-Diffusion.  Be sure you've downloaded the
[webui project](https://github.com/AUTOMATIC1111/stable-diffusion-webui) and the [desired weights](https://huggingface.co/models).  [Rentry.org](https://rentry.org/voldy) has an excellent
walkthrough for the newcomer.

Note that various Stable Diffusion training sets can generate a variety of
images, heavily influsenced by the weigth source.  Be prepared for the AI
engine to return NSFW content if you're not careful.  There effectively nothing
the bot can do to prevent this as it's a byproduct of the AI training set. 

# Dependencies
- [Python](https://www.python.org/) 3.10 or later
- [Stable Diffusion UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) 1.4 or later
- [Discord.py](https://discordpy.readthedocs.io/en/stable/index.html) 2.2.2 or later

Many of these dependencies are inherited from the Stable-Diffusion project.

## License
All files in this repo fall under the [GPLv3](LICENSE.md).  See the individual
projects for their respective licenses.

# Usage


## Limitations/Known Issues
Also see the [changelog](CHANGELOG.md).

- No automated way to switch dataset types.
- Sharding not yet implemented.
