# Alien-Bot ALPHA
A fully-customizable bot for dynamic module loading
## Getting Started
### Prerequisites
* [Python 3.4.2](https://www.python.org/downloads/release/python-342/)+
* [Discord.py](https://github.com/Rapptz/discord.py)
### Execution
Put your Discord bot token in `Config\config.json` under `Token`

Then, run:
```
python Bot.py
```
## Default Commands
The following commands come with the vanilla bot:
*
## Config
Since the bot is fully-customizable, here's how to configure it
### Main Config
The primary config is found under `Config\config.json`

* `Token` Sets the bot's login token
* `Nickname` Sets the bot's display name
* `Command Prefix` Sets the bot's command prefix
* `Save File` Sets the database file save location
* `Embed Color` Sets the bot's default embed color
* `Bot Emoji` ***WIP***
* `Owner ID` ***WIP***
* `Enabled Mods` Sets whether every mod is enabled or disabled bot-wide
* `Profile Picture` Sets the bot's profile picture (must be jpg)
* `Logging Level` Sets how verbose the logs will be for the bot host
* `Game Status` Contains a list of statuses that will be randomly chosen on start
* Each command under `Commands` has the following parameters: 
    * `Aliases` Sets a list of aliases for the command
    * `Help` Sets the help text for the command
    * `Enabled` Sets whether the command can be used
    * `Useage` Sets how to use the command
### Mod Config
Not to be confused with individual mod configs, it is found under `Config/ModConfig.json`

* The config will contain each mod, by name, which will each have the following parameters:
    * `Enabled` Sets whether mod is enabled bot-wide
    * ***WIP***
## Database Config
This config is usually left untouched, but contains a persistent database for the bot and mods.
## Mods
Mods are modules that can be added on top of the vanilla Alien-Bot.
### Add A Mod
Being a modular bot, you get the ability to add mods.
#### Installation
To install a mod, place the mod's folder under `Mods/`
#### Config
Some mods come with a config, check the mod's source for a config explanation.

For further config, read [Mod Config](https://github.com/neptunesblade/Alien-Bot#mod-config)

