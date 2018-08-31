from Common import DataManager, Utils, Permissions, Mod
import discord
import time


# TODO: Redo help so it only prints what the user's permissions allows
# TODO: Add command prefix when printing useage help??
# TODO: Improve help printing?
class Defaults(Mod.Mod):
    def __init__(self, mod_name, embed_color):
        # Vars
        self.start_time = time.time()
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
                await Utils.client.send_message(channel, embed=embed)
        elif command is self.commands["Stop Command"]:
            await Utils.simple_embed_reply(channel, "[Stopping...]", "Goodbye cruel world.")
            print("[Stopping the bot]")
            raise Exception("Stop Bot")
        # TODO add more specific params (EX: info mods)
        # Mods, commands, bot, server, channel, permissions
        elif command is self.commands["Info Command"]:
            if not len(split_message) > 1:
                embed = discord.Embed(title="[Info]", color=0x751DDF, description="Bot info.")
                embed.add_field(name="Bot Nick", value=str(Utils.bot_nick), inline=True)
                embed.add_field(name="Bot Prefix", value=str(Utils.prefix), inline=True)
                embed.add_field(name="Bot Emoji", value=str(Utils.bot_emoji), inline=True)
                bot_config = DataManager.get_manager("bot_config")
                # Server Info
                servers = [svr for svr in Utils.client.servers]
                server_text = "Servers: %d\n" % len(servers)
                server_text += "Disabled Servers: %d\n" % len(bot_config.get_data("Disabled Servers"))
                embed.add_field(name="Server Count", value=server_text, inline=True)
                # Channel info
                channels = [channel for channel in server.channels for server in servers]
                channel_text = "Channels: %d\n" % len(channels)
                channel_text += "Disabled Channels: %d\n" % len(bot_config.get_data("Disabled Channels"))
                embed.add_field(name="Channel Info", value=channel_text, inline=True)
                embed.add_field(name="Permissions", value=str(len(Permissions.permissions)))
                embed.add_field(name="Uptime", value=Utils.seconds_format(time.time() - self.start_time), inline=True)
                mod_config = DataManager.get_manager("mod_config").get_data()
                # Mod info
                mod_names = [mod_name for mod_name in mod_config]
                mod_text = "Mods: %d\n" % len(mod_names)
                disabled_mods = [mod_name for mod_name in mod_names if not mod_config[mod_name]["Enabled"]]
                mod_text += "Disabled Mods: %d\n" % len(disabled_mods)
                server_disabled_mods = [mod_name for mod_name in mod_names if
                                        len(mod_config[mod_name]["Disabled Servers"]) > 0]
                mod_text += "Server Disabled: %d\n" % len(server_disabled_mods)
                channel_disabled_mods = [mod_name for mod_name in mod_names if
                                         len(mod_config[mod_name]["Disabled Channels"]) > 0]
                mod_text += "Channel Disabled: %d\n" % len(channel_disabled_mods)
                embed.add_field(name="Mod Info", value=mod_text, inline=True)
                # Commands
                commands = [cmd for cmd in Utils.mod_handler.commands]
                command_names = [cmd.name for cmd in commands]
                command_text = "Commands: %d\n" % len(command_names)
                command_aliases = [command_alias for cmd in commands for command_alias in cmd]
                command_text += "Command Aliases: %d\n" % len(command_aliases)
                server_disabled_commands = [cmd.name for cmd in commands if int(server.id) in
                                            mod_config[cmd.parent_mod.name]["Commands"][cmd.name][
                                                "Disabled Servers"]]
                command_text += "Server Disabled: %d\n" % len(server_disabled_commands)
                channel_disabled_commands = [cmd.name for cmd in commands if int(channel.id) in
                                             mod_config[cmd.parent_mod.name]["Commands"][cmd.name][
                                                 "Disabled Channels"]]
                command_text += "Channel Disabled: %d\n" % len(channel_disabled_commands)
                embed.add_field(name="Command Info", value=command_text, inline=True)
                await Utils.client.send_message(channel, embed=embed)
            else:
                await Utils.simple_embed_reply(channel, "[Info]", "Not implemented.")
        elif command is self.commands["Server Command"]:
            await self.change_presence(message, False)
        elif command is self.commands["Channel Command"]:
            await self.change_presence(message, True)
        elif command is self.commands["Permissions Command"]:
            raise Exception("Not implemented yet!")

    async def change_presence(self, message, channel_mode=False):
        split_message = message.content.split(" ")
        server = message.server
        channel = message.channel
        key_word = "Channels" if channel_mode else "Servers"
        mode_obj = channel if channel_mode else server
        mode_id = int(channel.id) if channel_mode else int(server.id)
        enable_mode = None
        config = DataManager.get_manager("bot_config")
        disabled_ids = config.get_data("Disabled " + key_word)
        if len(split_message) > 2:
            passed_change_mode = split_message[2].lower()
            if passed_change_mode == "enable" or passed_change_mode == "disable":
                enable_mode = True if passed_change_mode == "enable" else False
        if len(split_message) > 1:
            lowered_parameter = split_message[1].lower()
            # Enable / Disable a Server / Channel
            if lowered_parameter == "enable" or lowered_parameter == "disable":
                if lowered_parameter == "enable":
                    if mode_id in disabled_ids:
                        disabled_ids.remove(mode_id)
                        config.write_data(disabled_ids, key="Disabled " + key_word)
                    await Utils.simple_embed_reply(channel, "[Enabled]", "%s has been enabled in %s." %
                                                   (Utils.bot_nick, str(mode_obj)))
                elif lowered_parameter == "disable":
                    if mode_id not in disabled_ids:
                        disabled_ids.append(mode_id)
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                   (Utils.bot_nick, str(mode_obj)))
                config.write_data(disabled_ids, key="Disabled " + key_word)
            # Enable / Disable a Mod / Command
            else:
                given_mod = Utils.mod_handler.get_mod_by_name(lowered_parameter)
                if given_mod is not None:
                    mod_config = DataManager.get_manager("mod_config")
                    mod_data = mod_config.get_data(given_mod.name)
                    if enable_mode or (mode_id in mod_data["Disabled " + key_word] and enable_mode is None):
                        if mode_id in mod_data["Disabled " + key_word]:
                            mod_data["Disabled " + key_word].remove(mode_id)
                        await Utils.simple_embed_reply(channel, "[Enabled]", "%s has been enabled in %s." %
                                                       (given_mod.name, str(mode_obj)))
                    else:
                        if mode_id not in mod_data["Disabled " + key_word]:
                            mod_data["Disabled " + key_word].append(mode_id)
                        await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                       (given_mod.name, str(mode_obj)))
                    mod_config.write_data(mod_data, key=given_mod.name)
                else:
                    given_command = Utils.mod_handler.get_command_by_alias(lowered_parameter)
                    if given_command is not None:
                        mod_config = DataManager.get_manager("mod_config")
                        mod_data = mod_config.get_data(given_command.parent_mod.name)
                        command_data = mod_data["Commands"][given_command.name]
                        if enable_mode or (mode_id in command_data["Disabled " + key_word] and enable_mode is None):
                            if mode_id in command_data["Disabled " + key_word]:
                                command_data["Disabled " + key_word].remove(mode_id)
                            await Utils.simple_embed_reply(channel, "[Enabled]", "%s has been enabled in %s." %
                                                           (given_command.name, str(mode_obj)))
                        else:
                            if mode_id not in command_data["Disabled " + key_word]:
                                command_data["Disabled " + key_word].append(mode_id)
                            await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                           (given_command.name, str(mode_obj)))
                        mod_data["Commands"][given_command.name] = command_data
                        mod_config.write_data(mod_data, key=given_command.parent_mod.name)
                    else:
                        await Utils.simple_embed_reply(channel, "[Presence]", "Neither that command nor mod exists.")
        else:
            if mode_id in disabled_ids:
                disabled_ids.remove(mode_id)
                await Utils.simple_embed_reply(channel, "[Enabled]", "%s has been enabled in %s." %
                                               (Utils.bot_nick, str(mode_obj)))
            else:
                disabled_ids.append(mode_id)
                await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                               (Utils.bot_nick, str(mode_obj)))
            config.write_data(disabled_ids, key="Disabled " + key_word)
