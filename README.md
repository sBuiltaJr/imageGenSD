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

- [Python](https://www.python.org/) 3.11.2 or later
- [Stable Diffusion UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) 1.4 or later
- [Discord.py](https://discordpy.readthedocs.io/en/stable/index.html) 2.2.2 or later
- [Mariadb](https://mariadb.com/) 10.11 or later
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
5. Enter your Discord Bot's static login token into the `src/config/credentials.json` file.
    1. DO NOT commit this value to a public repo!

## To run

`<path to venv bin folder>python imageGenSD.py`

The bot will run in the terminal until killed with a `Ctrl+C` or similar.

## To run the Unit Tests

`<path to venv bin folder>python RunUnitTests.py`

Test results are stored in `covhtml` located at the top-level directory.

## To upgrade the database tables for a new version of IGSD

`mariadb -u root -p < table_update.sql`

You will need to use the password defined in the project's `config` file.

Upgrade scripts can be found under the `update_scripts` folder and must be run
in numeric order (e.g. `3.8` before `3.9`).

## Supported commands

Note: All command require a user to have at least slash command privileges.

`assignkeygen {tier}`

- Assign at least one Character Profile to Key Generation work.

Allows a user to fill key generation work slots with as many character
profiles as is allowed by their economy settings.  Multiple characters can be
assigned in a single action.  Selections will not be preserved across
drop-down pages if a user tries to both select a profile and navigate to a new
page in the same action.

`tier` indicates which tier should be managed, with 1 as the lowest and 6 as
the highest.  The command defaults to tier 1 if no selection is provided.

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

`/listprofiles {user}`

- Show all profiles associated with a specific Discord account.

Provides a paginated menu of profile names and IDs associated with a Discord
account (and stored in the database).  If none, it encourages the user to
create a profile with an appropriate command.

Pages can be navigated with the provided buttons and will be eventually
disabled after a timeout.

Not specifying `user` will cause the menu to show the author's profiles.

Only the command author is allowed to use the navigation buttons.

`removekeygen( {tier}`

- Remove at least one Character Profile from Key Generation work.

Allows a user to free key generation work slots from as many character
profiles as is allowed by their economy settings.  Multiple characters can be
removed in a single action.

`tier` indicates which tier should be managed, with 1 as the lowest and 6 as
the highest.  The command defaults to tier 1 if no selection is provided.

`/roll`

- Roll a daily profile

Generates a brand-new character and profile once daily.  Daily reset occurs at
midnight UTC.  The character and profile are saved to the user profile that
initiated the command and will appear in the `/listprofiles` command.

`/showprofile {user} {profile_id}`

- Display either a given profile linked by ID or a selectable list of profiles

If `profile_id` is specified, the command displays the request profile, if
it exists.  The can include profiles linked to other users if the author knows
the profile ID.

Profile Names cannot be used, only the unique identifier for a profile (ID)
like provided by `/listprofiles`.

If `user` is specified, the command displays a dropdown list of profiles that
user owns, if any.  Selecting a specific profile will cause it to be posted to
the channel underneath the dropdown menu.

The dropdown contains `next` and `back` options to allow viewing lists greater
than 25 characters.  The `cancel` command deletes the dropdown.

the dropdown will deactivate after 100 seconds of inactivity.

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