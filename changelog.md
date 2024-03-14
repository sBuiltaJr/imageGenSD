# Version 0.3.8

## Highlights

- Added the `assignkeygen` and `removekeygen` to manage the key generation job.
- Fixed a bug where the `/generate` command was ignoring seed inputs.
- Created a DB script to migrate to the version 0.3.8 schemas.
- Added new types of dropdown menus to manage the new slash commands.
- Updated the profile displays to show profile ID and stats average.

### Specific Changes

- Added the `assignkeygen` command.
	- The command allows a user's profiles to be assigned to creating keys for dungeons.
	- Only profiles with stats >= to the average for their tier range can be assigned to work.
		- Higher-tier profiles can be assigned to work in lower-profile slots.
	- Users must specify which tier they wish to assign for.
		- The command defaults to tier 1, the lowest tier.
- Added the `removekeygen` command.
	- The command allows a user's profiles to be removed from the work of creating dungeon keys.
	- Users must specify which tier they wish to assign for.
		- The command defaults to tier 1, the lowest tier.
- Updated the `IGSDProfiles` with the `occupied` flag to show when a profile is assigned to work.
- Created the `IGSDEconomy` table to track a users' economy settings.
	- Defined several kinds of work (building, key generation, research, etc). to track in the table.
	- Defined limits for how many profiles can be assigned to each kind of work.
	- Associated all parameters with a Discord user profiles.
	- Created `economy_queries.json` to store table queries in an easily accessible format.
- Created the `IGSDInventory` to track work output for a given user.
	- Gave all users a default of 1 dungeon key to ensure they can run at least one dungeon mission.
	- Defined other categories (dust, tiered armor, tiered weapons, etc) for future commands and jobs.
	- Created `inventory_queries.json` to store table queries in an easily accessible format
- Created the `IGSDKeyGenWorkers` table to easily track which profiles a user owns are assigned to the keygen job.
	- Added columns to track work across levels.
	- The table relies on the tier limits set in the `IGSDEconomy` table.
	- Created `keygen_queries.json` to store table queries in an easily accessible format.
- Updated the Daily Event Manager to produce ekys based on the number of workers assigned to the key gen roll at daily reset.
	- Renamed the `testDailyRollReseWorks` to `testDailyResetWork` for clarity of the work.
- Created a new dropdown menu in the `DropDownFactory` for displaying profiles assignable under the `assignkeygen` command.
	- Navigation works the same as the `showprofiles` dropdown menu.
	- Dropdown choices are managed by the dropdown object.
- Created a new dropdown menu in the `DropDownFactory` for displaying profiles removable from work under the `removekeygen` command.
	- The dropdown does not have navigation (beyond `cancel`) since it will only ever handle 5 objects at most.
- Added commands to `MariadbIfc.py` to manage the new tables and commands needed for them.
	- Re-factored the command query file handling to enable the ability to loop.
	- Added new initial table creation statements to account for all new tables added with the 3.8 changes.
		- The init scripts do not calculate missing values, like stats averages.
- Corrected the `/generate` command to accept the seed value provided by a user arg.
- Added new unit tests to the `UiTests.py` file to test the new dropdown menus.
- Added new unit tests to the `UtilitiesTests.py` file to handle the average stats functions.
- Removed two additional tags from the `Tag_Randomizer_Dictionary.txt` file that were generating NSFW images.
- Fixed several typos noticed in doc strings.
- Fixed a bug that accidentally assigned all `/roll` results to the default profile.
- Reversed the order of the rarities returned by `getStandardNameList` and `getProbabilityList` for better iteration.
- Added a function to the `StatsClass` to return the average stat value for a stat profile.
- Created a DB update script under `upgrade_scripts/3.8/` for migrating from an older DB.

### Notes

- You must run the DB update script in `upgrade_scripts/3.8/` to upgrade an existing 3.7 or earlier DB.

# Version 0.3.7

## Highlights

- Added Unit Tests for most code.
- Converted the `/showprofile` command to a dynamic dropdown for easier use and future expansion.
- Modified how `MariadbIfc.py` returns profiles.
- Enabled players to list/show other players owned characters.

### Specific Changes

- Added a dependency for `coverage.py` for code coverage.
- Created `RunUnitTests.py` to execute all unit tests.
	- Added unit test cases in the `scr/` folder, as required based on relative imports in relevant files.
	- Unit tests can be invoked via `/path/to/venv/python RunUnitTests.py`
	- Test results are stored in `covhtml` located at the top-level directory.
- Added a `ui/` folder for containing files realted to Discord UI elements.
	- Moved `MenuPagination.py` to the `/ui` folder for better logical grouping.
		- Moved the `getPage` function into the `MenuPagination` class.
		- Modified the `get_owned_profs` query to return all components of all owned profiles for a given user.
- Updated `getProfiles` to return a list of complete profiles rather than one customized to `/listprofiles`.
	- Created a common formatting function for mapping Query results to profile and stats objects. 
	- Updated `getProfile` to use the common formatting function.
- Refactored the `Stats` and `Profile` classes to accept a dictionary of options instead of individual parameters.
	- Added `get` functions to provide default options for each class.
-Created `DropDownFactory.py` for generating DropDown menu options for various commands.
	- Added a `ShowDropdown` Class for use with the `/shwoprifle` command.
		- The dropdown object posts any requests to the job queue (like any other command).
	- Added Unit Tests for the `DropDownFactory.py` file.
	- Created a base class for future dropdown menu types.
	- Added the ability to navigate between pagianted lists of profiles within the dropdown menu.
		- A user selects `next` from the dropdown to see the next list of profiles.
		- A user selects `back` from the dropdown to see the previous list of profiles.
		- A user selects `cancel` to disable the dropdown.
		- the dropdown automatically disables after 100 seconds of inactivity.
		- The dropdown does not dynamically add new profiles generated after the dropdown was created.
- Modified the `/showprofile` command for better functionality and to use the dropdown factory.
	- Added a user argument to view profiles from a specific user.
		- If not given a user argument nor a specific profile ID, the command selects from the author's profiles.
- Modified the `/listprofiles` command to accept a user argument.
	- If supplied a user, the command will show a paginated list of all profiles that user owns.
	- If not supplied a user, the command will show a paginated list of all profiles the command author owns.
-Fixed minor formatting errors/typos across files.

### Notes

- The current unit tests do not provide 100% code coverage yet.

# Version 0.3.6

## Highlights

- Refactored slash command data into a factory.
- Split the Tag Randomizer into its own log file.
- Minor code cleanup as a result of the job factory.


- Created TagFactory.py to create specific jobs based on slash command.
	- Replaced all slash commands using the queue with a factory equivalent.
		- only `/listprofiles` and `/hello` do not use the job queue.
		- `/testshowprofile` was converted into a queue job for consistency.
	- Each command is now allowed to have a variable amount of data/metadata for its specific job.
- Gave the Tag Randomizer its own log file (instead of relying on the Queue class's log file)
	- The Tag Randomizer is now initialized by the main IGSD thread.
	- The Queue Manager has no knowledge of Tag Randomization and only calls a `randomize` function provided by the job object.
	- No error messages or logging levels where changed.
	- All Tag randomizer init code was removed from the Queue Manager.
- Minor code cleanup as a result of the job factory.
	- The specifics of `Post` where migrated to job internals instead of a unified function in `imageGenSD.py`
	- All dependencies necessary for posting have been moved into the job functionality.
	- The total job data and metadata required to use jobs has been reduced.
		- separate command identifiers/IDs are now just stored as job data.
		- `QueueManager.py`'s `add` function now relies on job properties instead of job data in a dictionary.
	- the `post` function in `imageGenSD.py` has been moved into correct alphabetical order.
	-Several older comments/notes have been removed.

### Notes

- Admins restarting the bot may need to reset the `daily` flag in the DB, depending on how IGSD was shut down.

# Version 0.3.5

## Highlights

- The bot can now create profiles for images and save them in a database.
- Added commands to view stored profiles.
- Added a rarity system driving profile stats and other items.
- Added new test commands to verify new functionality.
- Limited all commands to appropriate privileges.
- Various files have been updated to current code standards. 

### Specific Changes

- Created a Profile Generator to associate with generated image.
	- Profiles are only created for specific commands.
		- Currently profiles are only added by the `/roll` command.
	- Default test profiles have been defined by the class.
	- Default job data (such as for `/testpost` has been moved to the Profile Generator class.
		- Default job data was removed from the main IGSD thread, which was an ill-fitting location for it.
	- Profile information is partly based on the randomized Rarity attribute assigned to it during creation.
	- Profiles are assigned 'stats' based on Rarity.
	- All profiles are given a unique ID and saved in a Database as a single table.
	- Profiles are linked to their image in a separate table by a unique ID.
- Created a Rarity generator.
	- Provides a Rarity enum based on a fixed probability distribution.
- Created a Stats generator.
	- Stats are randomized within tiers, tiering based on a profile's Rarity.
- Created a Randomized Name generator.
	- Randomized names follow the western convention of <first name> <last name>.
	- The Randomizer simply extracts a pair of names from a firstname and last name dictionary.
		- Name dictionaries must be a list of newline-separated names without apostrophes or quotations.
	- The path to the dictionaries used by this class can be changed in the `src/config/config.json` file under the `profile_opts` section.
- Added default dictionaries for first and last names.
	- The default dictionaries can generate millions of unique name combinations.
	- The default names are intended to be plausible real names, but are not named after specific individuals.
- Removed some problematic tags found in the Tag Dictionary during testing.
- Added a Pagination class for displaying paginated data in Discord embed messages.
	- The class provides navigation buttons based on the list size.
	- Page sizes are customizable but are limited by Discord embed sizes.
	- This class is currently used to provide users a profile's ID so they can display it with the `/showprofile` command.
- Added a MariaDB interface singleton.
	- The class manages any interaction with the DB, such as getting or storing profiles, pictures, and users.
	- The class adds 3 tables to the database: Profiles, Images, and Users.
	- Class initialization deletes and writes test profiles and pictures to the database to ensure connectivity and permissions.
	- The interface currently uses a single connection thread for transactions, instead of a thread pool.
	- The interface class is responsible for creating picture/character/user entries in the database if they don't exist.
	- Interface options (like Table names and logging level) are customizable in the `src/config/config.json` file under the `db_opts` section.
	- All DB table commands are stored (by table) in `src/db/queries/`.
- Added a Daily Reset class.
	- The Daily Reset class is responsible for resetting the daily `/roll` command flag for a user at midnight UTC.
	- The class sends a reset command to the database interface.  The DB interface performs the actual reset on the User table.
	- The actual daily reset monitor is added as a separate, daemonic thread to prevent task deadlock.
	- The daemonic reset thread sleeps using `time.sleep()` for performance consistency, `sched` does not provide the desired behavior.
	- Class options are customizable in the `src/config/config.json` file under the `daily_opts` section.
- Defined a Test profile based on the image used for `/testpost`.
	- The Test Profile was given the name `IGSD Mascot`, which cannot be generated by the default name dictionaries.
	- The Test Profile was given unique stats and a custom Rarity.
	- The Test Profile's specific image is stored in the DB as a static text string.
		- This static definition is useful for verifying Stable Diffusion models/VAEs/extensions are installed correctly.
- Added the `/listprofiles` command.
	- This command shows the profile name and profile UUID of all characters owned by the caller.
	- Only the caller can use the navigation buttons provided by the command.
	- The buttons eventually time out, leaving the current page as the message contents.
- Added the `/roll` command.
	- This command generates a new character, profile, image, and DB entry for a user.
	- This command is limited to executing once daily (UTC).
	- Generated characters are automatically added to the user's profile and 'owned' list.
	- Character profiles can be displayed with the `/showprofile` command.
	- A user's command count statistics are updated after this command is successfully executed.
- Added the `/showprofile` command.
	- This command is used to show the profile of a character matching the specific ID.
	- A user can retrieve the character IDs of profiles they own with the `/listprofiles` command.
	- The command accepts a UUID string to search.
		- Names cannot be used to look-up a profile as they are not guaranteed to be unique, even for a particular user.
- Added the `/testroll` command.
	- This command executes a `/roll`-like sequence with the test profile.
	- The command re-generates the Test Image through the Stable Diffusion webui, but retrieves static Profile information.
		- The Test Profile parameters are the default information returned by the various Profile classes/subclasses.
	- The command is constructed to not modify the RNG state.
- Added the `/testshowprofile` command.
	- This command retrieves the Test profile data stored in the database and posts it to the invoking channel.
	- This command does not generate or store any new data.
	- The command is constructed to not modify the RNG state.
- Updated all slash commands to require at least the `use_application_commands` privilege to execute.
- Updated all `test` command to require at least the `manage_guild` privilege to execute.
- Split Queue options (like logging) into their own options in the `src/config/config.json` file under the `queue_opts` section.

### Notes

- The current version doesn't allow interaction between users (e.g. make characters fight).
- The `/roll` command does not include a pity mechanic.
- The database used by the program is assumed to not be externally accessible, allowing for relaxed password security.
	- The password for this user is not stored in the `src/config/credentials.json` file, which should never be committed to the repo.
- The bot does not currently handle having the back-end reset (i.e. Stable Diffusion webui or the database) in the middle of a command.
	- Users who had active commands in this window will be prevented from submitting new commands until the bot is reset.

# Version 0.3.0

## Highlights

- Reorganized directory structure to better group source and config files (and de-clutter the main directory).
- Added a tag randomizer as an option for image generation.
- Paths specified in the config file are now handled in a platform-independent manner.
- Provided a default, sanitized tag dictionary based on [danbooru tags](https://gwern.net/danbooru2021#publications).
- Minor typo fixes.

### Specific Changes

- The Generate command has two new options: 'Randomize' and 'tag_cnt'
	- Randomize determines whether the tag randomizer should add random tags to the user's prompt
	- tag_cnt defines how many tags to add, up to a limit in the config file.
	- These options can be used in addition to a user-supplied prompt.
- Log files have been moved to a log/ folder in the root directory.
- QueueManager has been moved to src/managers.
	- The config and credentials files have been moved to src/config.
- A default Tag Dictionary has been added to src/config.
	- A custom dictionary can be added by changing the config option 'rand_dict_path'
  	- This dictionary must be line-separated entries that conform to your model's expected prompt format (like danbooru tags).
	- All dictionaries must have more than max_rand_tag_cnt entries to be considered valid.
	- Additional sanity checks for expected Tag Dictionary bounds have been added to imageGenSD'py's loading of the config file.
- A new class, TagRandomizer, has been added under src/utilities.
	- The class enables appending random tags to a given prompt.
	- Tag limits are specified by 'max_rand_tag_cnt' and 'min_rand_tag_cnt' in the config file.
	- Tags are selected at random from the Tag Dictionary.
  	- The randomizer will attempt to only select unique tags from the Tag Dictionary.
		- The randomizer will give up after tag_retry_limit attempts, as defined in the config file.
	- Tags are clamped (or truncated) to the maximum allowed embed size.
	- TagRandomizer log info is currently fed to the QueueManager file.
	- The randomizer will add a random number of tags (between 'max_rand_tag_cnt' and 'min_rand_tag_cnt') to a prompt if tag_cnt is not specified.
	- The TagRandomizer class attempts to initialize the processes' seed upon start for better Tag selection behavior.
- The Response Message had two new fields: 'Randomized" and 'Tags Added to Prompt'.
	- These reflect the values set in the Generate command.
	- 'Tags Added to Prompt' will reflect the random number of tags added by the TagRandomizer if a number wasn't specified in tag_cnt.
- Fixed a bug that would cause an exception in QueueManager since the include for queue.Full's definition was commented out.
- All paths loaded from config files are now converted into pathlib objects.
	- Each path is sanitized by an .absolute() call beforehand to guarantee it works.
	- There are also early exit conditions for required files.
	- The pathlib object is not supported by all modules (like linecache) and is converted into a sanitized string when necessary.
- All exit calls have been converted to using unique, negative numbers for better (eventual) procedural handling
- Tweaked identification of test commands in the back-end to allow for bursts and more flexibility.
	- Commands can either be a known name (e.g. 'testgetid') or a number less than 10.

### Notes

- Too large of a tag/prompt combination will prevent responses from being posted to Discord.
	- This is the reason for the relatively small tag limit in the default configuration.

# Version 0.1.0

## Highlights

- Created and included a test image for bot identity and reference.
- Created basic testing commands for basic functionality verification and future regression testing.
- Created a 'Generate' command to make images based on user inputs.
- Added an (optional and enabled by default) banned word filter for both positive and negative Prompts.
- Added rate-limiting as '1 job per user per Guild'
- Minor typo fixes.

### Specific Changes

- Added the test command 'hello'
	- The command simply echos back the user's name, confirming the bot has posting access to the channel.
- Added the test command 'testget'
	- The command performs a simply 'get' request from the SD server by asking for its memory stats (/sdapi/v1/memory)
	- A successful return verifies the bot is able to talk to the SD server.
- Added the test command 'testpost'
	- The command generates a pre-defined image to verify that the SD server is able to send and receive data.
	- The test image matches the 'IGSD_image.png' file included in the repository.
  	- A server generating a different image is either using a different Model or is missing plugins/configurations.
- Added the user command 'generate'
	- All of Generate's parameters are optional and come with pre-defined defaults.
	- Each option corresponds to a parameter exposed by the SD server.
  	- Not all SD Server options have been made available due to volume.
	- Every option on the generate command has been bounded and sanitized.
  	- The bounds for each component are specified in various settings in the config file.
	- Limits imposed by discord (such as seed value) or the SD server (such as CFG value) are not specified in the config file.
- A Log has been created for the main Bot thread.
	- This log contains all log entries for the front-end component of the bot (directly handling Discord interactions).
	- The log is written to the file specified by the config file setting 'log_name'.
- A log has been created for the QueueManager thread.
	- This log contains all log entries for the back-end component of the bot (SD Server interactions and Queue Management).
	- The log is written to the file specified by the config file setting 'log_name_queue'.
- A banned word filter has been added to the 'Generate' command.
	- The banned words, specified in a comma-separated list, are specified in the 'banned_words' option of the config file.
	- A separate list for the negative prompt is specified in the 'banned_neg_words' option of the config file.
	- The word filter is currently simple, and thus aggressive (e.g. cumulus is banned in the default set).

### Notes

- There is currently no timeout limit on POST requests to get images from the SD server.

# Version 0.0.1

## Highlights

### Specific Changes

- Project generated.