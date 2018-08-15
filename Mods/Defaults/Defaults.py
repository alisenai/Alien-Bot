import discord
from Common import DataManager, Utils
from Common.Mod import Mod


# TODO: Redo help so it only prints what the user's permissions allows
# TODO: Add command prefix when printing useage help?
class Defaults(Mod):
    def __init__(self, mod_name, embed_color):
        # Config var init
        self.config = DataManager.JSON("Mods/Defaults/DefaultsConfig.json")
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        if command is self.commands["Help Command"]:
            # If it's help for something specific, parse as so
            if len(split_message) > 1:
                await Utils.mod_handler.get_help(message)
                # await Utils.mod_handler.command_called(message, split_message[0], is_help=True)
            # Otherwise, it's a full general list and parse as so
            else:
                # Start building an embed
                embed = discord.Embed(title="[Help]", color=0x751DDF)
                mod_descriptions = Utils.mod_handler.get_mod_descriptions()
                # Loop through all mods' descriptions and create their fields
                for mod in mod_descriptions:
                    description = mod_descriptions[mod]
                    embed.add_field(name=mod, value=description, inline=False)
                # Reply with the created embed
                await Utils.client.send_message(message.channel, embed=embed)
        elif command is self.commands["Channel Command"]:
            raise Exception("Not implemented yet!")
        elif command is self.commands["Permissions Command"]:
            raise Exception("Not implemented yet!")
