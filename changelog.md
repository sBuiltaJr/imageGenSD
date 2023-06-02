
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
  - These optiosn can be used in addition to a user-supplied prompt.
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
- Too large of a tag/prompt combination will prevent responses from being posted to discord.
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