import os
import re
import sys
import discord
import difflib
import EventHandler


# TODO: Add mod perm/admin handling
# TODO: Add channel restrictions
class ModHandler:
    client = None
    mod_commands = {}
    mods = {}
    done_loading = False

    # Builds a mod handler with passed parameters
    def __init__(self, client, logging_level, help_commands, embed_color):
        # Var init
        self.client = client
        self.logging_level = logging_level
        self.help_commands = help_commands
        self.embed_color = embed_color

    async def load_mods(self):
        mod_dir = "Mods/"
        # Make the python files importable
        sys.path.insert(0, mod_dir)
        print("[Loading Mods]")
        # Cycle through all the files within the mod dir
        for file in os.listdir(mod_dir):
            # If it's a python file
            # TODO: Check if there is a better way to get the file extension
            if re.match(".*\.py", file):
                print("[Loading: " + file[0:-3] + "]")
                # Import that python file
                mod = getattr(__import__(file[0:-3]), file.replace(".py", ""))(self.client, self.logging_level)
                # Register the import as a mod and get the mod's info
                mod_info = mod.register_mod()
                mod_command = mod_info['Mod Command']
                # Store the mod reference withing the mod info
                mod_info['Mod'] = mod
                # Cycle through all the mod's commands
                for command in mod_info['Commands']:
                    # Make sure there are no conflicting mod commands
                    if command not in self.mod_commands.keys() and command not in self.help_commands:
                        # Link the mod object to that command
                        self.mod_commands[command] = mod
                    else:
                        # If there is a duplicate mod command, error
                        if command in self.mod_commands.keys():
                            # If it's with another mod, state so
                            raise Exception("Duplicate mod commands - " + command)
                        else:
                            # If it's with the help commands, state so
                            raise Exception("Mod copies bot help command")
                # Check if the mod's info is valid
                if ' ' in mod_command:
                    raise Exception("Mod command \"" + mod_command + "\" contains a space")
                # Store mod's info
                self.mods[mod_command] = mod_info
        # When finished loading all mods, state so and unblock
        self.done_loading = True
        print("[Done loading Mods]")

    # Called when a user message looks like a command, and it attempts to work with that command
    async def command_called(self, client, message, command):
        # Get info from that message
        channel = message.channel
        # If mod loading is done, proceed (make sure everything initialized)
        if self.done_loading:
            # Send the "is typing", for  a e s t h e t i c s
            await client.send_typing(channel)
            # Get a list of the mod commands
            commands = list(self.mod_commands.keys())
            # Check if the command called was a help command
            if command in self.help_commands:
                split_message = message.content.split(" ")
                # Start building an embed reply
                embed = discord.Embed(title="[Help]", color=0x751DDF)
                # If it's help for a specific command, parse as so
                if len(split_message) > 1:
                    # If it's help for known mod command
                    if split_message[1] in self.mods.keys():
                        # Get help from that mod
                        await self.mods[split_message[1]]['Mod'].get_help(message)
                        # Return since the help command executed on the mod will reply instead
                        return
                    # If it's help for an unknown mod command
                    else:
                        # Get a printable version of the known help commands
                        help_command_text = self.get_help_command_text()
                        # Add a field to the reply embed
                        embed.add_field(name="Unknown mod - " + split_message[1] + "",
                                        value="Try: " + help_command_text[0:-2] + ".")
                # Otherwise, it's a full general list and parse as so
                else:
                    # Loop through all mods and create fields for their info
                    for mod in self.mods.keys():
                        embed.add_field(name=self.mods[mod]['Name'] + " - " + mod, value=self.mods[mod]['Description'])
                # Reply with the created embed
                await self.client.send_message(channel, embed=embed)
            # If it's not a help command
            elif command in commands:
                # Get the mod from the command dict and call the command handler on that mod
                await self.mod_commands[command].command_called(message, command)
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

    # Used to get a printable version of the help commands
    def get_help_command_text(self):
        help_command_text = ""
        # Build all the help commands
        for command in self.help_commands:
            help_command_text += command + ", "
        # Return built text
        return help_command_text


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


# Returns the similarity between two strings
def string_similarity(string_one, string_two):
    return difflib.SequenceMatcher(None, string_one, string_two).ratio()
