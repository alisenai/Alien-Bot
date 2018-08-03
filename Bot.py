import random
import threading

import discord
import time

from Common import Utils
from Common import Permissions
from Common import DataManager
from Common.Command import Command
from Common.ModHandler import ModHandler

MOD_CONFIG = "Config\ModConfigs.json"
# Create a client object
client = discord.Client()
# Set global client object
Utils.client = client
# Initialize the config data manager and load the config
config = DataManager.add_manager("bot_config", "Config\Config.json").get_data()
# Initialize database data manager
database_manager = DataManager.add_manager("database", config['Database'], file_type=DataManager.FileType.SQL)
# Initialize cool down data manager
cool_down_manager = DataManager.add_manager("commands", "Common\Command.db", file_type=DataManager.FileType.SQL)
# Initialize mod config manager
mod_config_manager = DataManager.add_manager("mod_config", MOD_CONFIG)
# Load permissions
Permissions.load_permissions()
# Grab the bot's nickname
bot_nick = config['Nickname']
# Grab command prefix
command_prefix = config['Command Prefix']
# Grab the bot's commands from the config
command_config = config['Commands']
# Build a list of bot commands
bot_commands = {command_name: (Command(None, command_name, command_config[command_name]['Aliases'], True,
                                       command_config[command_name]["Minimum Permissions"],
                                       command_config[command_name]['Help'],
                                       ''.join(use + "\n" for use in command_config[command_name]['Useage'])[0:-1]))
                for command_name in command_config}
# Build a list of bot command aliases
bot_command_aliases = [alias for command in bot_commands for alias in bot_commands[command]]
# Initialize the mod handler
mod_handler = ModHandler(bot_commands, bot_command_aliases, config['Embed Color'])
# Boolean to keep track of when it's safe to start parsing commands
mods_loaded = False


# When the bot is ready to be worked with
@client.event
async def on_ready():
    print('[Login successful]')
    print('[Starting]')
    self = None
    # Change the bot nickname and get a "self" user
    for server in client.servers:
        self = server.me
        await client.change_nickname(self, config['Nickname'])
    # Change the avatar if it's not already set
    avatar_hash = self.avatar
    database_manager.execute("CREATE TABLE IF NOT EXISTS bot_data(name TEXT, value TEXT)")
    hash_from_database = database_manager.execute("SELECT value FROM bot_data WHERE name='avatar_hash'")
    if len(hash_from_database) != 0 and hash_from_database[0] == avatar_hash:
        print("[Skipping Profile Picture Update]")
    else:
        with open(config['Profile Picture'], 'rb') as f:
            print("[Attempting Profile Picture Update]")
            try:
                await client.edit_profile(avatar=f.read())
                database_manager.execute("INSERT INTO bot_data VALUES('avatar_hash', '" + str(avatar_hash + "") + "')")
                print("[Updated Profile Picture]")
            except discord.errors.HTTPException:
                print("[Skipping Profile Picture Update (Throttled)]")
    # Pick a random status
    status = config['Game Status'][random.randint(0, len(config['Game Status']) - 1)]
    print("[Chose status \"" + status + "\"]")
    # Set status
    await client.change_presence(game=discord.Game(name=status))
    # Load mods
    await mod_handler.load_mods()
    # Start main loop
    t = threading.Thread(target=tick)
    t.start()


# When a message is received by the bot
@client.event
async def on_message(message):
    channel = message.channel
    # Check if the message is a possible command
    if message.content[0:len(command_prefix)] == command_prefix:
        split_message = message.content.split(" ")
        # Check if the mod handler is ready to be worked with
        if mod_handler.is_done_loading():
            # Get the command without the pesky prefixes or parameters
            command_alias = split_message[0][len(command_prefix):]
            if command_alias == "<3" or command_alias == "💜":
                await client.send_message(message.channel, config["Bot Emoji"])
                await mod_handler.message_received(message)
                return
            # Check if the command called was a bot command
            if command_alias in bot_command_aliases:
                # Help command called
                if command_alias in bot_commands['Help Command'] and bot_commands["Help Command"].enabled:
                    # If it's help for something specific, parse as so
                    if len(split_message) > 1:
                        # If it's help for the bot, call help util
                        if split_message[1] == bot_nick or split_message[1] in bot_command_aliases:
                            await Utils.get_help(message, bot_nick, bot_commands, split_message[1] == bot_nick)
                        else:
                            # Let the mod handler deal with possible mod help
                            await mod_handler.command_called(client, message, command_alias, is_help=True)
                    # Otherwise, it's a full general list and parse as so
                    else:
                        # Start building an embed
                        embed = discord.Embed(title="[Help]", color=0x751DDF)
                        embed.add_field(name=bot_nick, value="Default bot commands", inline=False)
                        mod_descriptions = mod_handler.get_mod_descriptions()
                        # Loop through all mods' descriptions and create their fields
                        for mod in mod_descriptions:
                            description = mod_descriptions[mod]
                            embed.add_field(name=mod, value=description, inline=False)
                        # Reply with the created embed
                        await client.send_message(channel, embed=embed)
                elif command_alias in bot_commands['Channel Command'] and bot_commands['Channel Command'].enabled:
                    raise Exception("Not implemented yet!")
                elif command_alias in bot_commands['Permissions Command'] and bot_commands['Permissions Command'].enabled:
                    raise Exception("Not implemented yet!")
            else:
                # Not a bot command; use mod handler to parse the command
                await mod_handler.command_called(client, message, command_alias)
        # Mod handler is not ready -> Let the author know
        else:
            await Utils.simple_embed_reply(channel, "[Error]", "The bot is still loading, please wait.")
    await mod_handler.message_received(message)


@client.event
async def on_member_join(member):
    await mod_handler.on_member_join(member)


def tick():
    while True:
        time.sleep(1)


# Make sure there is a token in the config
print("[Attempting to login]")
try:
    if config['Token'] == "TOKEN":
        print("Please add a token in the config file")
    else:
        # Run the bot with the token
        client.run(config['Token'])
except discord.errors.ClientException:
    print("[Could not login]")