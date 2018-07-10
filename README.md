# Alien-Bot ALPHA
A fully-customizable bot for dynamic module loading
## Getting Started
### Prerequisites
* [Python 3.4.2](https://www.python.org/downloads/release/python-342/)+
* [Discord.py](https://github.com/Rapptz/discord.py)
### Execution
Put your Discord bot token in ```Config\config.json``` under ```Token```

Then, run:
```
python Bot.py
```
## Commands
## Config
Since the bot is fully-customizable, here's how to configure it
### Main Config
The primary config is found under ```Config\config.json```
* ```Token``` Sets the bot's login token
* ```Nickname``` Sets the bot's display name
* ```Command Prefix``` Sets the bot's command prefix
* ```Save File``` Sets the database file save location
* ```Embed Color``` Sets the bot's default embed color
* ```Bot Emoji``` ***WIP***
* ```Owner ID``` ***WIP***
* ```Enabled Mods``` Sets whether every mod is enabled or disabled bot-wide
* ```Profile Picture``` Sets the bot's profile picture (must be jpg)
* ```Logging Level``` Sets how verbose the logs will be for the bot host
* ```Game Status``` Contains a list of statuses that will be randomly chosen on start
* ```Commands``` Contains all of the bot's commands
  * Each command has the following parameters:
    * ```Aliases``` Sets a list of aliases for the command
    * ```Help``` Sets the help text for the command
    * ```Enabled``` Sets whether the command can be used
    * ```Useage``` Sets how to use the command
## Mods

