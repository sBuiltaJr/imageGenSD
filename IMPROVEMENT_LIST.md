# Overview
This is a list of possible upgrades/updates that may be added to the project.
They're listed here so as to not be forgotten.  Neither list is in priority
order. [The discord.py github](https://github.com/Rapptz/discord.py/tree/master/examples) has many examples for reference.

## Bug-fixes
(These items have higher priority but aren't guaranteed to be first).
- Properly manage the 1024-character embed limit.
  - Requires all fields in the embed message, as currently written, to be less than 1024 characters.
  - Causes annoying interactions with the tag randomizer.
  - Is currently only partially mitigated by simply shrinking the allowed tag size.
  - Perhaps prompts should be returned in a separate embed?
  - See Discord's [embed limits](https://discord.com/developers/docs/resources/channel#embed-object-embed-limits) for more details.

## Investigations
(Items that may not be bugs but should still be investigated)
- Determine why the discord.py examples always require hard-coding a guild. (should be auto-detectable?)
- Determine how to properly background the task (discord.py has some examples, may not work as needed?)

## Planned
- Allow the default prompt to be added to a user prompt, especially if using randomized tags.
- Allow a bot to manage multiple guilds.
- Allow a bot to shard.
- Crash recovery.
- Add the image's actual seed value to the embed.
- Guild info command (for setting parameters).
- Argument sanitization/limiting (discord knows as transformers).
- Add user-supplied paths for config/credential files.
- Implement better logging configuration/customization by using the logging config files.
- Multitasking (including separate logging tasks).
- zipping logs to reduce increase logged information.
- Help menu via messaging the bot.
- Command-line inputs for a local user to generate images.

## Unplanned
- weeb shit