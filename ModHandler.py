import os
import sys
import Utils
import discord
import difflib
from DataManager import DataManager


# TODO: Improve mod handling
# TODO: Add bot-wide channel restrictions
# TODO: Add per-mod channel restrictions
# TODO: Add per-mod perm handling
# TODO: Add per-command channel restrictions
# TODO: Add per-command perm handling
# TODO: Add "message received" function for non-command parsing and mod passing
class ModHandler:
    mod_command_aliases = {}
    mods = {}
    done_loading = False

    # Builds a mod handler with passed parameters
    def __init__(self, client, mod_configs, bot_command_aliases, logging_level, embed_color):
        # Var Init
        self.client = client
        self.modConfigManager = DataManager(mod_configs)
        self.logging_level = logging_level
        self.bot_command_aliases = bot_command_aliases
        self.embed_color = embed_color

    async def load_mods(self):
        print("[Loading Mods]")
        mod_configs = self.modConfigManager.get_data()
        new_mod_config = {}
        mod_names = []
        # Cycle through all the files within the mod dir
        for mod_name in os.listdir("Mods/"):
            # Store the mod names to return them
            mod_names.append(mod_name)
            # Check if it's a newly installed mod or if the mod is enabled
            # Mod doesn't exist -> Newly installed -> Load it
            # Mod exists        -> Not disabled    -> Load it
            if mod_name not in mod_configs.keys() or mod_configs[mod_name]['Enabled'] is not False:
                if mod_name not in mod_configs.keys():
                    new_mod_config[mod_name] = {"Enabled": True, "DisabledServers": [], "DisabledChannels": []}
                else:
                    # Append for config cleaning
                    new_mod_config[mod_name] = mod_configs[mod_name]
                # Make the python files importable and import them
                sys.path.insert(0, 'Mods/' + mod_name)
                print("[Loading: " + mod_name + "]")
                # Import and call mod init to get object
                mod = getattr(__import__(mod_name), mod_name)(self.client, self.logging_level, self.embed_color)
                mod.set_name(mod_name)
                # Register the import as a mod and get the mod's info
                mod_command, mod_commands = mod.register_mod()
                # Cycle through all the mod's commands and make sure there are no conflicting mod commands
                for command_name in mod_commands:
                    for command in mod_commands[command_name]['Aliases']:
                        # Check for conflicting commands
                        if command in self.mod_command_aliases.keys():
                            raise Exception("Duplicate mod commands - " + command)
                        elif command in self.bot_command_aliases:
                            raise Exception("Mod copies a default command")
                        # If all checks pass, link the mod object to that command
                        else:
                            self.mod_command_aliases[command] = mod
                # Get mod's info
                mod_info = mod.get_info()
                mod_info['Mod'] = mod
                # Store mod's info
                self.mods[mod_command] = mod_info
            # Mod exists -> Disabled -> Don't load it, as per config
            else:
                if mod_configs[mod_name]['Enabled'] is False:
                    # Append for config cleaning
                    new_mod_config[mod_name] = mod_configs[mod_name]
                print("[Not Loading: " + mod_name + "]")
        self.modConfigManager.write_data(new_mod_config)
        self.done_loading = True
        print("[Done loading Mods]")
        return mod_names

    # Called when a user message looks like a command, and it attempts to work with that command
    async def command_called(self, client, message, command, is_help=False):
        channel = message.channel
        server = message.server
        split_message = message.content.split(" ")
        # If it's a help command
        if is_help:
            # If it's help for a specific mod or one of its commands
            if self.is_mod_name(split_message[1]):
                await self.get_mod_help(split_message[1], message)
            # Not a known mod or mod command
            else:
                # Start building an embed reply
                embed = discord.Embed(title="[Help]", color=0x751DDF)
                # Get a printable version of the known help commands
                help_command_text = get_help_command_text()
                # Add a field to the reply embed
                embed.add_field(name="Unknown mod - " + split_message[1] + "",
                                value="Try: " + help_command_text + ".")
                # Reply with the created embed
                await client.send_message(channel, embed=embed)
        # Not a help command
        else:
            # Make sure everything initialized
            if self.done_loading:
                # Send "is typing", for  a e s t h e t i c s
                await client.send_typing(channel)
                # Get a list of the mods' commands' aliases
                commands = list(self.mod_command_aliases.keys())
                # If it's a known command, forward it to the appropriate mod
                if command in commands:
                    # TODO: Add check for enabled / disabled
                    await self.mod_command_aliases[command].command_called(message, command)
                # Not a known command
                else:
                    # Find the most similar commands
                    most_similar = most_similar_string(command, commands)
                    # No similar commands -> Reply with help commands
                    if most_similar is None:
                        help_command_text = get_help_command_text()
                        await Utils.simple_embed_reply(self.client, channel, "[Unknown command]",
                                                       "Try " + help_command_text + ".")
                    # Similar-looking command exists -> Reply with it
                    else:
                        await Utils.simple_embed_reply(self.client, channel, "[Unknown command]",
                                                       "Did you mean `" + most_similar + "`?")
            # Mods are still loading -> Let the author know
            else:
                await Utils.simple_embed_reply(self.client, channel, "[Error]",
                                               "The bot is still loading, please wait.")

    # Returns a dictionary - {mod name : mod description}
    def get_mod_descriptions(self):
        mod_descriptions = {}
        for mod in self.mods:
            mod_descriptions[self.mods[mod]['Name']] = self.mods[mod]['Description']
        return mod_descriptions

    # Checks if the passed var is a known mod name
    def is_mod_name(self, name):
        if name in self.mods:
            return True
        return False

    # Calls the help command on a specific mod, given one of its commands
    async def get_mod_help(self, mod, message):
        await self.mods[mod]['Mod'].get_help(message)

    # Returns if ModHandler is done loading mods
    def is_done_loading(self):
        return self.done_loading


# Todo: Workaround?
# Returns help text
def get_help_command_text():
    return ""


# Get the most similar string from an array, given a string
def most_similar_string(string, string_list):
    # Check if there are strings to compare to
    if len(string_list) > 0:
        # Loop through and find the most similar string
        most_similar = string_list[0]
        for i in string_list:
            if string_similarity(i, string) > string_similarity(most_similar, string):
                most_similar = i
        return most_similar
    # Return None if there are no strings to compare to
    return None


# Returns the similarity between two strings
def string_similarity(string_one, string_two):
    return difflib.SequenceMatcher(None, string_one, string_two).ratio()
