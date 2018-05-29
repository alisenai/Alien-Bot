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
class ModHandler:
    mod_command_aliases = {}
    mods = {}
    done_loading = False

    # Builds a mod handler with passed parameters
    def __init__(self, client, enabled_mods, bot_command_aliases, logging_level, embed_color):
        # Var init
        self.client = client
        self.enabled_mods = enabled_mods
        self.logging_level = logging_level
        self.bot_command_aliases = bot_command_aliases
        self.embed_color = embed_color

    async def load_mods(self):
        mod_dir = "Mods/"
        print("[Loading Mods]")
        # Cycle through all the files within the mod dir
        mod_names = []
        for mod_name in os.listdir(mod_dir):
            # Store the mod names to return them
            mod_names.append(mod_name)
            # Check if it's a newly installed mod or if the mod is enabled
            if mod_name not in self.enabled_mods or self.enabled_mods[mod_name] is not False:
                # Make the python files importable
                sys.path.insert(0, mod_dir + mod_name)
                # If it's a python file
                print("[Loading: " + mod_name + "]")
                # Import that python file
                mod = getattr(__import__(mod_name), mod_name)(self.client, self.logging_level, self.embed_color)
                # Register the import as a mod and get the mod's info
                mod_command, mod_commands = mod.register_mod()
                # Cycle through all the mod's commands and make sure there are no conflicting mod commands
                for command_name in mod_commands:
                    for command in mod_commands[command_name]['Aliases']:
                        if command in self.mod_command_aliases.keys():
                            # If there is a duplicate mod command, error
                            raise Exception("Duplicate mod commands - " + command)
                        elif command in self.bot_command_aliases:
                            # If there is a conflicting mod command (with the bot's commands), error
                            raise Exception("Mod copies a default command")
                        else:
                            # Link the mod object to that command
                            self.mod_command_aliases[command] = mod

                # Gets the mod's info
                mod_info = mod.get_info()
                # Store the mod reference withing the mod info
                mod_info['Mod'] = mod
                # Store mod's info
                self.mods[mod_command] = mod_info
            else:
                print("[Not Loading: " + mod_name + "]")
        # When finished loading all mods, state so and unblock
        self.done_loading = True
        print("[Done loading Mods]")
        return mod_names

    # Called when a user message looks like a command, and it attempts to work with that command
    async def command_called(self, client, message, command):
        # Get info from that message
        channel = message.channel
        # If mod loading is done, proceed (make sure everything initialized)
        if self.done_loading:
            # Send the "is typing", for  a e s t h e t i c s
            await client.send_typing(channel)
            # Get a list of the mod commands
            commands = list(self.mod_command_aliases.keys())
            # If it's not a bot command
            if command in commands:
                # Get the mod from the command dict and call the command handler on that mod
                await self.mod_command_aliases[command].command_called(message, command)
            # If it's not a known command
            else:
                # Find the most similar commands
                most_similar = most_similar_string(command, commands)
                # If there are no similar strings (...)
                if most_similar is None:
                    # Create a list from the known help commands
                    help_command_text = self.get_help_command_text()
                    # Reply with help
                    await self.simple_embed(channel, "[Unknown command]", "Try " + help_command_text + ".")
                # If there is a similar command
                else:
                    # Reply with the most similar command
                    await self.simple_embed(channel, "[Unknown command]", "Did you mean `" + most_similar + "`?")
        # If mods are still loading
        else:
            # Let the author know that the mods are still loading - Try again later
            await self.simple_embed(channel, "[Error]", "Loading , please wait")

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

    def get_mod_descriptions(self):
        mod_descriptions = {}
        for mod in self.mods:
            mod_descriptions[mod] = self.mods[mod]['Description']
        return mod_descriptions

    # Check if a command is a known command alias
    def is_mod_command_alias(self, command):
        if command in self.mod_command_aliases:
            return True
        return False

    def is_mod_name(self, name):
        if name in self.mods:
            return True
        return False

    # Calls the help command on a specific mod, given one of its commands
    async def get_mod_help(self, mod_command, message):
        await self.mod_command_aliases[mod_command].get_help(message)


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
