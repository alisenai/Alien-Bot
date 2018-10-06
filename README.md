# Alien-Bot ALPHA (Paused)
A fully-customizable bot for dynamic module loading
## Getting Started
### Prerequisites
* [Python 3.4.2](https://www.python.org/downloads/release/python-342/)+
* [Discord.py](https://github.com/Rapptz/discord.py)
* Asyncio
### Execution
1. Install prerequisites
2. Rename `Config.json.example` under `Alien-Bot\Config` to `Config.json`
3. Put your Discord bot token in `Config.json` under `Token`
4. Run: `python Bot.py` in a terminal within the `\Alien-Bot` directory
## Default Commands
The following commands come with the vanilla bot:
* Secret command
## Config
Since the bot is fully-customizable, this is the main config for the bot

Changes become active on the bot's restart

Config Parsing:
* Channel IDs and Server IDs are assumed to not have quotations around them (ex: `123456789123456789`)

* To enable or disable a config parameter, use either `true` or `false` without quotations

* As a general note, you usually shouldn't change parameter names but their values - see below for edge-cases
### Main Config
The primary config is found under `Alien-Bot\Config\Config.json`
* `Token` Sets the bot's login token
* `Nickname` Sets the bot's display name
* `Command Prefix` Sets the bot's command prefix
* `Save File` Sets the database file save location
* `Embed Color` Sets the bot's default hex embed color (ex: `"0xffffff"`)
* `Bot Emoji` Is replied when the secret command is called. (ex: `"🥝"`)
* `Profile Picture` Sets the bot's profile picture location (must be jpg)
* `Game Status` A list of statuses that will be randomly chosen on start
* `Disabled Servers` A list of server IDs that the bot is disabled in
* `Disabled Channels` A list of channel IDs that the bot is disabled in
* `Permissions` Contains all the bot permissions' configs, by name
   * You **MAY** change the name / title of each permission by changing the parameter name - see example config for reference
   * `Is Default` Default permission users are assumed to have if they don't have any other roles
   * `Has Permissions` Sets whether users with these permissions are allowed to call commands
   * `Inherits` The permission's name / title from which to inherit from 
   * `Is Owner` Users with this permission are given full use of the bot
   * `Associated Roles` Role IDs which are associated with the permission
* `Minimum Suggestion Permission` Minimum permissions a user must have to recieve command suggestions
### Mod Config
Not to be confused with individual mod configs, it is found under `Alien-Bot\Config\ModConfig.json`

Almost all of this config is auto-generated, auto-formatted and auto-cleaned 

Do **NOT** change mod names or command names - these are for reference

The config will contain each mod, by name, which will each have the following parameters:
* `Enabled` Sets whether mod is enabled or disabled bot-wide
* `Disabled Servers` A list of server IDs that this mod is disabled in
* `Disabled Channels` A list of channel IDs that this mod is disabled in
* `Commands` Contains all of the bot's commands' config, by name
   * `Disabled Servers` A list of server IDs that this mod is disabled in
   * `Disabled Channels` A list of channel IDs that this mod is disabled in
   * `Minimum Permissions` The name / title of the minimum permissions a user must have to call the command 
## Database Config
This config should generally be left untouched, but contains a persistent database for the bot and mods

This DB is auto-generated, auto-formatted and auto-cleaned
## Mods
Mods are modules that can be added on top of the vanilla Alien-Bot.
### Add A Mod
To add a mod, place the mod's folder under `Alien-Bot\Mods`

Generall config for the added mod will be auto-generated within the Mod Config on the first successful run

Check the mod's source, config, or readme for more information pertaining to the mod or its config
**WARNING:** Only install mods from trusted sources - the bot does not manage mod access in any way
