import discord


# TODO: Command enable / disable
# TODO: Call command on other user if "admin" for add role / remove role / etc
# TODO: Logging levels
# TODO: Require role for command use
# TODO: Delete ALL colors in current server

class Main:
    def __init__(self, client, logging_level):
        self.client = client
        self.embed_color = "0xab12ba"
        return

    # Returns info about this mod
    def register_mod(self):
        return

    # Returns all commands that are used by this mod
    def mod_commands(self):
        return

    # Gets help - All of it, or specifics
    async def get_help(self, message):
        return

    # Used to generate help, all or it or specifics
    def generate_help(self, command=None):
        return

    async def command_called(self, message, command):
        return

    # Used for quickly replying to a channel with a message
    async def reply(self, channel, message):
        await self.client.send_message(channel, message)

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

    # Used for getting a discord color from a hex value
    def get_color(self, color):
        return discord.Color(int(color, 16))