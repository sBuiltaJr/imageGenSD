# imageGenSD
## A Stable-Diffusion driven Image Generator Bot for Discord

iamgeGenSD is a Stable-Diffusion wrapper written in Python.  It uses [Discord.py](https://discordpy.readthedocs.io/en/stable/index.html)
to listen for user requests and pass the commands to a Stable-Diffusion backend
for processing, posting the results to the channel as requested.

This project does not contain Stable-Diffusion.  Be sure you've downloaded the
[webui project](https://github.com/AUTOMATIC1111/stable-diffusion-webui) and the [desired weights](https://huggingface.co/models).  [Rentry.org](https://rentry.org/voldy) has an excellent
walkthrough for the newcomer.

Note that various Stable Diffusion training sets can generate a variety of
images, heavily influenced by the weight source.  Be prepared for the AI engine
to return NSFW content if you're not careful.  There effectively nothing the
bot can do to prevent this as it's a byproduct of the ML training set.  

# Dependencies
- [Python](https://www.python.org/) 3.10 or later
- [Stable Diffusion UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) 1.4 or later
- [Discord.py](https://discordpy.readthedocs.io/en/stable/index.html) 2.2.2 or later

Many of these dependencies are inherited from the Stable-Diffusion project.

## License
All files in this repo fall under the [GPLv3](LICENSE).  See the individual
projects for their respective licenses.

# Usage

## To run
`python iamgeGenSD.py`

The bot will run in the terminal until killed with a `Ctrl+C` or similar.

## Supported commands
- Hello

`/hello`

Confirms the bot has the bare minimum capability for interacting in the Guild.

- Test GET

`/testget`

Makes a basic HTTP get to the webui back-end to verify it's there and works.
Also verifies the internal data path works (i.e. posting a job to the queue).

- Test POST

`/testpost`

Runs a pre-defined job through the webui interface, verifying that the SD
server is able to provide data to a known request.  Meant for verifying the
server's ability to actually supply data.

- Generate an image

`/generate {prompt} {negative_prompt} {height} {width} {steps} {seed} {cfg_scale} {sampler}`

Provides a user-supplied job to the webui back-end.  All parameters
are optional and defaults are provided.  All inputs are limited to reasonable
values (or the constraints of Discord/Stable Diffusion).

## Limitations/Known Issues
Also see the [changelog](ROADMAP.md).

- No automated way to switch dataset types.
- Sharding not yet implemented.
