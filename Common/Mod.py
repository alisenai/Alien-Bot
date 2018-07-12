from Common import Utils
from Common.Command import Command


# TODO: Admin and per-command role handling here? Maybe DB integration as well
# TODO: Add examples for each command
# Extendable class for mods
class Mod:
    def __init__(self, description="No description", mod_command="", commands=None,
                 logging_level=Utils.LoggingLevels.VERBOSE, embed_color="0xab12ba"):
        # Check if parameters are valid
        assert ' ' not in mod_command, "Mod command \"" + mod_command + "\" contains a space"
        assert Utils.is_hex(embed_color), "Embed Color \"" + embed_color + "\" is not a valid hex color"
        assert type(commands) is dict, "Mod command list is not of type dict"
        for command_name in commands:
            assert type(commands[command_name]) is Command, "Mod commands are not of type \"Command\""
        # Var init
        self.commands = {} if commands is None else commands
        self.name = "No name set"  # Name will be set by ModHandler
        self.embed_color = embed_color
        self.mod_command = mod_command
        self.description = description
        self.logging_level = logging_level
        self.command_aliases = [alias for command_name in self.commands for alias in self.commands[command_name]]

    # Called when the bot receives a message
    async def command_called(self, message, command):
        await Utils.simple_embed_reply(Utils.client, message.channel, "[Error]",
                                       "No command parsing implemented for this mod")

    # Returns true if the passed command alias is known by the mod
    def is_command_alias(self, command_alias):
        return command_alias in self.command_aliases

    # Replies with help (specific or broad)
    async def get_help(self, message):
        split_message = message.content.split(" ")
        await Utils.get_help(message, self.name, self.commands, split_message[1] == self.name)

    # Returns the registration info about this mod
    def register_mod(self):
        return self.mod_command, self.commands

    # Returns the important info about this mod
    def get_info(self):
        return {'Name': self.name, 'Description': self.description, 'Commands': self.mod_commands(),
                'Mod Command': self.mod_command}

    # Returns a list of known commands from this mod
    def mod_commands(self):
        return self.commands

    # Used for quickly replying to a channel with a message
    async def reply(self, channel, message):
        await Utils.client.send_message(channel, message)

    # Sets the mod's name
    def set_name(self, name):
        if ' ' in name:
            raise Exception("Mod name \"", name, "\" contains a space")
        self.name = name
