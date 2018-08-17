import discord
from Common import DataManager, Utils
from Common.Mod import Mod


# TODO: Redo help so it only prints what the user's permissions allows
# TODO: Add command prefix when printing useage help?
# TODO: Improve help printing
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
        server, channel, author = message.server, message.channel, message.author
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
        # TODO: Add an optional mod/command parameter
        elif command is self.commands["Server Command"]:
            config = DataManager.get_manager("bot_config")
            disabled_servers = config.get_data("Disabled Servers")
            server_id = int(server.id)
            if len(split_message) > 1:
                if split_message[1] == "enable":
                    if server_id in disabled_servers:
                        disabled_servers.remove(server_id)
                        config.write_data(disabled_servers, key="Disabled Servers")
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been enabled in %s." %
                                                   (Utils.bot_nick, str(server)))
                elif split_message[1] == "disable":
                    if server_id not in disabled_servers:
                        config.write_data(disabled_servers + [server_id], key="Disabled Servers")
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                   (Utils.bot_nick, str(server)))
            else:
                if server_id in disabled_servers:
                    disabled_servers.remove(server_id)
                    config.write_data(disabled_servers, key="Disabled Servers")
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been enabled in %s." %
                                                   (Utils.bot_nick, str(server)))
                else:
                    config.write_data(disabled_servers + [server_id], key="Disabled Servers")
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                   (Utils.bot_nick, str(server)))
        # TODO: Add an optional mod/command parameter
        elif command is self.commands["Channel Command"]:
            config = DataManager.get_manager("bot_config")
            disabled_channels = config.get_data("Disabled Channels")
            channel_id = int(channel.id)
            if len(split_message) > 1:
                if split_message[1] == "enable":
                    if channel_id in disabled_channels:
                        disabled_channels.remove(channel_id)
                        config.write_data(disabled_channels, key="Disabled Channels")
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been enabled in %s." %
                                                   (Utils.bot_nick, str(channel)))
                elif split_message[1] == "disable":
                    if channel_id not in disabled_channels:
                        config.write_data(disabled_channels + [channel_id], key="Disabled Channels")
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                   (Utils.bot_nick, str(channel)))
            else:
                if channel_id in disabled_channels:
                    disabled_channels.remove(channel_id)
                    config.write_data(disabled_channels, key="Disabled Channels")
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been enabled in %s." %
                                                   (Utils.bot_nick, str(channel)))
                else:
                    config.write_data(disabled_channels + [channel_id], key="Disabled Channels")
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                   (Utils.bot_nick, str(channel)))
        elif command is self.commands["Permissions Command"]:
            raise Exception("Not implemented yet!")
