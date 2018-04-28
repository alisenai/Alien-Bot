import re
import discord

class Mod:
    def __init__(self, name, description, mod_command, commands, client, logging_level):
        self.name = name
        self.client = client
        self.commands = commands
        self.mod_command = mod_command
        self.description = description
        self.logging_level = logging_level

    def event(self, func):
        setattr(self, func.__name__, func)

    async def command_called(self, message):
        return

    # Returns info about this mod
    def register_mod(self):
        return {'Name': self.name, 'Description': self.description, 'Commands': self.mod_commands(),
                'Mod Command': self.mod_command}

    def mod_commands(self):
        return self.commands

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
                                                                    color=self.get_color(color)))

    # Used for quickly replying to a channel with a message
    async def reply(self, channel, message):
        await self.client.send_message(channel, message)

    # Used for getting user by user id in given server
    def get_user_by_id(self, server, user_id):
        # Gets a user by their ID
        return server.get_member(user_id)

    # Used for getting a role by id in given server
    def get_role_by_id(self, server, role_id):
        for role in server.roles:
            if role.id == role_id:
                return role

    # Used for getting a discord color from a hex value
    def get_color(self, color):
        return discord.Color(int(color, 16))

