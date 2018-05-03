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
            raise Exception("Embed Color \"", embed_color, "\" is not a valid hex color")
        self.name = name
        self.client = client
        self.commands = commands
        self.embed_color = embed_color
        self.mod_command = mod_command
        self.description = description
        self.logging_level = logging_level

    # TODO: remove "command" param
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

    # TODO: Comment
    # Prints the help message for the mod
    # Gets help - All of it, or specifics
    async def get_help(self, message):
        embed = discord.Embed(title="[" + self.name + " Help]", color=0x751DDF)
        split_message = message.content.split(" ")
        if len(split_message) >= 3:
            help_title, help_description = self.generate_help(split_message[2])
            embed.add_field(name=help_title, value=help_description)
        else:
            help_texts = self.generate_help()
            for help_title, help_description in help_texts:
                embed.add_field(name=help_title, value=help_description, inline=False)
        await self.client.send_message(message.channel, embed=embed)

    # Used to generate help, all or it or specifics
    def generate_help(self, specific_command=None):
        # If it's not asking for specifics, recursively return everything
        if specific_command is None:
            generated_help = []
            for command_name in self.commands:
                generated_help.append(self.generate_help(self.commands[command_name]['Commands'][0]))
            return generated_help
        # Otherwise, return help for a specific command
        else:
            # TODO: Compress and add config for all of this
            # Figures out which command was called and beings building a help message
            command_name, command_list, command_help = None, None, None
            for command_name in self.commands:
                command_info = self.commands[command_name]
                if specific_command in command_info['Commands']:
                    command_list = command_info['Commands']
                    command_help = command_info['Help']
                    break
            if (command_name or command_list or command_help) is None:
                # If passed something that doesn't exist, let them know
                return "Unknown Command - " + specific_command, "Unknown command for " + self.name
            # Build the rest of the help by appending the command list
            message = command_name + " - "
            for command in command_list:
                message += command + ", "
            # Return the help message built
            return message[0:-2], command_help

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
