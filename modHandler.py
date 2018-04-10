import difflib
import os
import re
import sys
import discord


class ModHandler:
    client = None
    mod_commands = {}
    mods = {}
    done_loading = False

    def __init__(self, client, logging_level, help_commands, embed_color):
        self.client = client
        self.logging_level = logging_level
        self.help_commands = help_commands
        self.embed_color = embed_color

    async def load_mods(self):
        mod_dir = "Mods/"
        sys.path.insert(0, mod_dir)
        print("[Loading Mods]")
        for file in os.listdir(mod_dir):
            if re.match(".*\.py", file):
                print("[Loading: " + file[0:-3] + "]")
                mod = __import__(file[0:-3]).Main(self.client, self.logging_level)
                mod_command, mod_info = mod.register_mod()
                mod_info['Mod'] = mod
                for command in mod_info['Commands']:
                    if command not in self.mod_commands.keys() and command not in self.help_commands:
                        self.mod_commands[command] = mod
                    else:
                        if command in self.mod_commands.keys():
                            raise Exception("Duplicate mod commands - " + command)
                        else:
                            raise Exception("Mod copies bot help command")
                self.mods[mod_command] = mod_info
        self.done_loading = True
        print("[Done loading Mods]")

    async def message_received(self, client, message, command):
        channel = message.channel
        if self.done_loading:
            commands = list(self.mod_commands.keys())
            if command in self.help_commands:
                split_message = message.content.split(" ")
                embed = discord.Embed(title="[Help]", color=0x751DDF)
                if len(split_message) > 1:
                    if split_message[1] in self.mods.keys():
                        await self.mods[split_message[1]]['Mod'].get_help(message)
                        return
                    else:
                        help_command_text = ""
                        for command in self.help_commands:
                            help_command_text += command + ", "
                        embed.add_field(name="Unknown mod - " + split_message[1] + "",
                                        value="Try: " + help_command_text[0:-2])
                else:
                    for mod in self.mods.keys():
                        embed.add_field(name=self.mods[mod]['Name'] + " - " + mod, value=self.mods[mod]['Description'])
                await self.client.send_message(channel, embed=embed)
            elif command in commands:
                await client.send_typing(channel)
                await self.mod_commands[command].command_called(message, command)
            else:
                most_similar = most_similar_string(command, commands)
                if most_similar is None:
                    help_command_text = ""
                    for command in self.help_commands:
                        help_command_text += command + ", "
                    await self.simple_embed(channel, "[Unknown command]", "Try " + help_command_text)
                else:
                    await self.simple_embed(channel, "[Unknown command]", "Did you mean `" + most_similar + "`?")
        else:
            await self.simple_embed(channel, "[Error]", "Loading , please wait")

    async def simple_embed(self, channel, title, description, color=None):
        color_to_use = None
        if color is None:
            color_to_use = self.embed_color
        else:
            color_to_use = color
        await self.client.send_message(channel, embed=discord.Embed(title=title,
                                                                    description=description,
                                                                    color=discord.Color(int(color_to_use, 16))))


def most_similar_string(string, string_list):
    if len(string_list) > 0:
        most_similar = string_list[0]
        for i in string_list:
            if string_similarity(i, string) > string_similarity(most_similar, string):
                most_similar = i
        return most_similar


def string_similarity(string_one, string_two):
    return difflib.SequenceMatcher(None, string_one, string_two).ratio()
