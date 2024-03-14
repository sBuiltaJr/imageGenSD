# imageGenSD

## A Stable-Diffusion driven Image Generator Bot for Discord

imageGenSD is a multi-purpose Discord bot.  It creates character images and
profiles in a gacha-like manner for users to interact with and enjoy.

imageGenSD also contains a Stable-Diffusion wrapper written in Python.  It uses
[Discord.py](https://discordpy.readthedocs.io/en/stable/index.html) to listen
for user requests and pass the commands to a Stable-Diffusion backend for
processing, posting the results to the channel as requested.

This project does not contain Stable-Diffusion.  Be sure you've downloaded the
[webui project](https://github.com/AUTOMATIC1111/stable-diffusion-webui) and the
[desired weights](https://huggingface.co/models).  [Rentry.org](https://rentry.org/voldy)
has an excellent walkthrough for the newcomer.

Note that various Stable Diffusion training sets can generate a variety of
images, heavily influenced by the weight source.  Be prepared for the AI engine
to return NSFW content if you're not careful.  There effectively nothing the
bot can do to prevent this as it's a byproduct of the ML training set.  

# Dependencies

- [Python](https://www.python.org/) 3.10 or later
- [Stable Diffusion UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) 1.4 or later
- [Discord.py](https://discordpy.readthedocs.io/en/stable/index.html) 2.2.2 or later
- [Mariadb](https://mariadb.com/) 11 or later
- [Mariadb python connector](https://mariadb.com/resources/blog/how-to-connect-python-programs-to-mariadb/) 1.1.9 or later
- [coverage.py](https://coverage.readthedocs.io/en/latest/index.html) 7.4.3 or later

Many of these dependencies are inherited from the Stable-Diffusion project or
are required to interface with a database.

## License

All files in this repo fall under the [GPLv3](LICENSE).  See the individual
projects for their respective licenses.

## Testing

This project has been tested on:

- Windows 10
- Ubuntu 22
- Debian 12
- MacOS 14

# Usage

## Initial Setup

Note: setup varies by OS.

1. Install Stable Diffusion.
    1. Download any models, VAEs, and other extensions you want to use.
    2. Modify `webui-user.sh` or `webui-user.bat` to include the command line argument `--api`.
2. Install MariaDB (This must be done first on some OS's).
    1. Perform any initial MariaDB setup, if required (e.g. `mysql_secure_installation`).
    2. Ensure your MariaDB is initialized to acecpt large packets, i.e.:
        1. Set `max_allowed_packet=4G` in `my.ini` or `my.cnf`.
3. Install all pip modules (in a venv if using modern versions of Python).
    1. Note that some OS's require manual install of additional elements, such as:
        1. `libmariadb3 libmariadb-dev` on Linux.
        2. `Applications/Python <version> Profile.command` on MacOS.
4. Initialize the MariaDB database with the commands:
    1. `CREATE DATABASE IGSD;`
    2. `CREATE USER IF NOT EXISTS 'IGSD_Bot'@'%' IDENTIFIED BY 'password';`
    3. `GRANT ALL PRIVILEGES ON IGSD.* TO 'IGSD_Bot'@'%';`
4. Enter your Discord Bot's static login token into the `src/config/credentials.json` file.
    1. DO NOT commit this value to a public repo!

## To run

`<path to venv bin folder>python imageGenSD.py`

The bot will run in the terminal until killed with a `Ctrl+C` or similar.

## Supported commands

Note: All command require a user to have at least slash command privileges.

`/generate {randomize} {tag_cnt} {prompt} {negative_prompt} {height} {width} {steps} {seed} {cfg_scale} {sampler}`

- Generate an image

Provides a user-supplied job to the webui back-end.  All parameters
are optional and defaults are provided.  All inputs are limited to reasonable
values (or the constraints of Discord/Stable Diffusion).

Setting Randomize to 'true' causes the system to select a random number of tags
to append to the prompt (or a specific number if 'tag_cnt' is specified).  This
can be combined with a user-supplied prompt.

`/hello`

- Hello

Confirms the bot has the bare minimum capability for interacting in the Guild.

`/listprofiles`

- Show all profiles associated your Discord account

Provides a paginated menu of profile names and IDs associated with the user's
Discord account (and stored in the database).  If none, it encourages the user
to create a profile with an appropriate command.

Pages can be navigated with the provided buttons and will be eventually
disabled after a timeout.

Only the user requesting the list is allowed to use the navigation buttons.

`/roll`

- Roll a daily profile

Generates a brand-new character and profile once daily.  Daily reset occurs at
midnight UTC.  The character and profile are saved to the user profile that
initiated the command and will appear in the `/listprofiles` command.

`/showprofile {profile ID}`

- Display a given profile linked to an ID

Displays the request profile, if it exists.  The can include profiles linked to
other users if the author knows the profile ID.  Profile Names cannot be used,
only the unique identifier for a profile (ID) like provided by `/listprofiles`.

`/testget`

- Test GET

Makes a basic HTTP get to the webui back-end to verify it's there and works.
Also verifies the internal data path works (i.e. posting a job to the queue).

This command is limited to Guild (server) managers only.

`/testpost`

- Test POST

Runs a pre-defined job through the webui interface, verifying that the SD
server is able to provide data to a known request.  Meant for verifying the
server's ability to actually supply data.

This command is limited to Guild (server) managers only.

`/testroll`

- Test Roll

Performs a test version of the `/roll` command using known data.  Useful as a
test/diagnostic tool to confirm the bot has access to all necessary resources
(such as the database and Stable Diffusion Webui).

This command is limited to Guild (server) managers only.

`/testshowprofile`

- Test Show Profile

This command displays a test profile in the same manner as the `/showprofile`
command.  It is useful as a debugging/diagnostic feature to ensure that data
can be properly retrieved from the database and displayed by Discord.

This command is limited to Guild (server) managers only.

## Limitations/Known Issues

Also see the [changelog](changelog.md) and [roadmap](ROADMAP.md).

- No automated way to switch dataset types.
- Sharding not yet implemented.
