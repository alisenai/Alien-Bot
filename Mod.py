import discord
import Utils


# TODO: Handel help here
# Extendable class for mods
class Mod:
    def __init__(self, name, description, mod_command, commands, client, logging_level, embed_color="0xab12ba"):
        # Check if the mod's info is valid
        if ' ' in mod_command:
            raise Exception("Mod command \",  mod_command, \" contains a space")
        if not Utils.is_hex(embed_color):
            raise Exception("Embed Color \"",  embed_color, "\" is not a valid hex color")
        self.name = name
        self.client = client
        self.commands = commands
        self.embed_color = embed_color
        self.mod_command = mod_command
        self.description = description
        self.logging_level = logging_level

    # Called when the bot receives a message
    async def command_called(self, message, command):
        return

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
    async def get_help(self, message):
        return "There is no help for this command"

    # Used for replying with a simple, formatted, embed
    async def simple_embed_reply(self, channel, title, message, hex_color=None):
        color = None
        if hex_color is None:
            color = self.embed_color
        else:
            color = hex_color
        # Craft and reply with a simple embed
        await self.client.send_message(channel, embed=discord.Embed(title=title, description=message,
                                                                    color=Utils.get_color(color)))

    # Used for quickly replying to a channel with a message
    async def reply(self, channel, message):
        await self.client.send_message(channel, message)