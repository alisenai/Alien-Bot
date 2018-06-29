import os
import sys
import discord
import difflib


# TODO: Improve mod handling
# TODO: Add bot-wide channel restrictions
# TODO: Add per-mod channel restrictions
# TODO: Add per-mod perm handling
# TODO: Add per-command channel restrictions
# TODO: Add per-command perm handling
from DataManager import DataManager


class ModHandler:
    mod_command_aliases = {}
    mods = {}
    done_loading = False

    # Builds a mod handler with passed parameters
    def __init__(self, client, enabled_mods, bot_command_aliases, logging_level, embed_color):
        # Var Init
        self.client = client
        self.enabled_mods = enabled_mods
        self.logging_level = logging_level
        self.bot_command_aliases = bot_command_aliases
        self.embed_color = embed_color
        self.modConfigManager = DataManager("Config/ModConfig.json")

    async def load_mods(self):
        mod_dir = "Mods/"
        print("[Loading Mods]")
        mod_names = []
        # Cycle through all the files within the mod dir
        for mod_name in os.listdir(mod_dir):
            # Store the mod names to return them
            mod_names.append(mod_name)
            # Check if it's a newly installed mod or if the mod is enabled
            # Mod doesn't exist -> Newly installed -> Load it
            # Mod exists        -> Not disabled    -> Load it
            if mod_name not in self.enabled_mods or self.enabled_mods[mod_name] is not False:
                # Make the python files importable and import them
                sys.path.insert(0, mod_dir + mod_name)
                print("[Loading: " + mod_name + "]")
                mod = getattr(__import__(mod_name), mod_name)(self.client, self.logging_level, self.embed_color)
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
                print("[Not Loading: " + mod_name + "]")
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
                        await self.simple_embed(channel, "[Unknown command]", "Try " + help_command_text + ".")
                    # Similar-looking command exists -> Reply with it
                    else:
                        await self.simple_embed(channel, "[Unknown command]", "Did you mean `" + most_similar + "`?")
            # Mods are still loading -> Let the author know
            else:
                await self.simple_embed(channel, "[Error]", "The bot is still loading, please wait.")

    # Replies to a channel with a simple embed
    async def simple_embed(self, channel, title, description, color=None):
        # Pick which color to use (if the function was passed a color)
        if color is None:
            color_to_use = self.embed_color
        else:
            color_to_use = color
        # Reply with a built embed
        await self.client.send_message(channel, embed=discord.Embed(title=title,
                                                                    description=description,
                                                                    color=discord.Color(int(color_to_use, 16))))

    # Returns a dictionary - {mod name : mod description}
    def get_mod_descriptions(self):
        mod_descriptions = {}
        for mod in self.mods:
            mod_descriptions[mod] = self.mods[mod]['Description']
        return mod_descriptions

    # Checks if the passed var is a known mod name
    def is_mod_name(self, name):
        if name in self.mods:
            return True
        return False

    # Calls the help command on a specific mod, given one of its commands
    async def get_mod_help(self, mod, message):
        await self.mods[mod]['Mod'].get_help(message)


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