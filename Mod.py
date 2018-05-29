import discord
import Utils
import os


# TODO: Admin and per-command role handling here? Maybe DB integration as well
# TODO: Add examples for each command
# Extendable class for mods
class Mod:
    def __init__(self, client, description="None", mod_command="", commands=None,
                 logging_level=Utils.LoggingLevels.VERBOSE, embed_color="0xab12ba"):
        # Check if the mod's info is valid
        if commands is None:
            commands = [""]
        if ' ' in mod_command:
            raise Exception("Mod command \",  mod_command, \" contains a space")
        if not Utils.is_hex(embed_color):
            raise Exception("Embed Color \"", embed_color, "\" is not a valid hex color")
        # Var init
        self.name = os.getcwd().split(os.sep)[-1]
        self.client = client
        self.commands = commands
        self.embed_color = embed_color
        self.mod_command = mod_command
        self.description = description
        self.logging_level = logging_level

    # Called when the bot receives a message
    async def command_called(self, message, command):
        await self.simple_embed_reply(message.channel, "[Error]", "No command parsing implemented for this mod")

    # Returns the registration info about this mod
    def register_mod(self):
        return self.mod_command, self.commands

    # Returns the important info about this mod
    def get_info(self):
        return {'Name': self.name, 'Description': self.description, 'Commands': self.mod_commands(),
                'Mod Command': self.mod_command}

    # Returns a list of commands that this mod "owns"
    def mod_commands(self):
        return self.commands

    # Prints the help message for the mod
    # Gets help - All of it, or specifics
    async def get_help(self, message):
        # Sets up an embed to return
        embed = discord.Embed(title="[" + self.name + " Help]", color=0x751DDF)
        # Parses the help message
        split_message = message.content.split(" ")
        # If it can be parsed as a specific command
        if len(split_message) >= 3:
            # Extract info and append to the embed
            help_title, help_description = self.generate_help(split_message[2])
            embed.add_field(name=help_title, value=help_description)
        else:
            # Get all the help for this mod
            help_texts = self.generate_help()
            for help_title, help_description in help_texts:
                embed.add_field(name=help_title, value=help_description, inline=False)
        # Return the embed
        await self.client.send_message(message.channel, embed=embed)

    # Used to generate help, all of it or a specific command
    def generate_help(self, specific_command=None):
        # If it's not asking for a specific command, recursively return everything
        if specific_command is None:
            generated_help = []
            for command_name in self.commands:
                generated_help.append(self.generate_help(self.commands[command_name]['Aliases'][0]))
            if len(generated_help) == 0:
                return [["Help Does Not Exist", "There is no help for this mod"]]
            return generated_help
        # Otherwise, return help for a specific command
        else:
            # Figures out which command was called and beings building a help message
            command_name, command_list, command_help = None, None, None
            for command_name in self.commands:
                command_info = self.commands[command_name]
                if specific_command in command_info['Aliases']:
                    command_list = command_info['Aliases']
                    command_help = command_info['Help']
                    break
            if command_name is None or command_list is None or command_help is None:
                # If passed something that doesn't exist, let them know
                return "Unknown Command", "\"" + specific_command + "\" is not a known command."
            # Build the rest of the help by appending the command list
            message = command_name + " - "
            for command in command_list:
                message += command + ", "
            # Return the help message built
            return message[0:-2], command_help

    # Used for replying with a simple, formatted, embed
    async def simple_embed_reply(self, channel, title, message, hex_color=None):
        # Get a color to use
        color = self.embed_color if hex_color is None else hex_color
        # Craft and reply with a simple embed
        await self.client.send_message(channel, embed=discord.Embed(title=title, description=message,
                                                                    color=Utils.get_color(color)))

    # Used for quickly replying to a channel with a message
    async def reply(self, channel, message):
        await self.client.send_message(channel, message)
