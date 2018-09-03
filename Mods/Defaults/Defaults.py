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
        # Mods, commands, bot, server, channel, permissions
        elif command is self.commands["Info Command"]:
            all_info, given_type = False, None
            if len(split_message) == 1:
                all_info = True
            else:
                main_param = split_message[1].lower()
                if len(split_message) < 2 and main_param == "all":
                    all_info = True
                elif main_param == 'server':
                    given_type = InfoType.SERVERS
                elif main_param == 'channel':
                    given_type = InfoType.CHANNELS
                elif main_param == 'mod':
                    given_type = InfoType.MODS
                elif main_param == 'command':
                    given_type = InfoType.COMMANDS
                elif main_param == 'permissions':
                    given_type = InfoType.PERMISSIONS
            if all_info:
                embed = discord.Embed(title="[Info]", color=0x751DDF, description="Bot info.")
                # Basic Info
                embed.add_field(name="Bot Nick", value=str(Utils.bot_nick), inline=True)
                embed.add_field(name="Bot Prefix", value=str(Utils.prefix), inline=True)
                embed.add_field(name="Bot Emoji", value=str(Utils.bot_emoji), inline=True)
                embed.add_field(name="Uptime", value=Utils.seconds_format(time.time() - self.start_time), inline=True)
                for info_type in [InfoType.SERVERS, InfoType.CHANNELS,
                                  InfoType.PERMISSIONS, InfoType.MODS, InfoType.COMMANDS]:
                    given_info = self.get_specific_info(server, channel, info_type)
                    mod_text = ""
                    for item_name in given_info:
                        mod_text += "%s: %d\n" % (item_name[0], len(item_name[1]))
                    embed.add_field(name=info_type, value=mod_text, inline=True)
            elif given_type is not None:
                embed = discord.Embed(title="[%s]" % given_type, color=0x751DDF, description="Bot info.")
                given_info = self.get_specific_info(server, channel, given_type)
                for item_name in given_info:
                    embed.add_field(name=item_name[0], value=self.format(item_name[1], 400), inline=True)
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Unknown parameter passed.")
                return
            await Utils.client.send_message(channel, embed=embed)
        elif command is self.commands["Server Command"]:
            await self.change_presence(message, False)
        elif command is self.commands["Channel Command"]:
            await self.change_presence(message, True)
        elif command is self.commands["Permissions Command"]:
            raise Exception("Not implemented yet!")

    def format(self, item_list, max_char):
        mod_text = ""
        for mod_name in sorted(item_list):
            if len(mod_text) + len(mod_name) < max_char:
                mod_text += mod_name + "\n"
            else:
                return mod_text + "..."
        if mod_text == "":
            return "None"
        return mod_text

    def get_specific_info(self, server, channel, info_type):
        if info_type == InfoType.SERVERS or info_type == InfoType.CHANNELS:
            bot_config = DataManager.get_manager("bot_config")
            servers = [svr for svr in Utils.client.servers]
            if info_type == InfoType.SERVERS:
                # TODO: For current server only?
                # Server Info
                return [("Servers", [svr.name for svr in servers]),
                        ("Disabled Servers", bot_config.get_data("Disabled Servers"))]
            elif info_type == InfoType.CHANNELS:
                # TODO: For current server only?
                # Channel info
                channels = [cnl for svr in servers for cnl in svr.channels if cnl.type == discord.ChannelType.text]
                return [("Channels", [cnl.name for cnl in channels]),
                        ("Disabled Channels", bot_config.get_data("Disabled Channels"))]
        elif info_type == InfoType.PERMISSIONS:
            permissions = Permissions.permissions
            names, restricted = [], []
            owners, default = [Permissions.owner_perm.title], [Permissions.default_perm.title]
            for permission in permissions:
                names.append(permission)
                if not permissions[permission].has_permissions:
                    restricted.append(permission)
            return [("Permissions", names),
                    ("Owner", owners),
                    ("Default", default),
                    ("Restricted", restricted)]
        elif info_type == InfoType.MODS or InfoType.COMMANDS:
            mod_config = DataManager.get_manager("mod_config").get_data()
            if info_type == InfoType.MODS:
                # Mod info
                mod_names = [mod_name for mod_name in mod_config]
                disabled_mods = [mod_name for mod_name in mod_names if not mod_config[mod_name]["Enabled"]]
                server_disabled_mods = [mod_name for mod_name in mod_names if
                                        len(mod_config[mod_name]["Disabled Servers"]) > 0]
                channel_disabled_mods = [mod_name for mod_name in mod_names if
                                         len(mod_config[mod_name]["Disabled Channels"]) > 0]
                return [("Mods", mod_names),
                        ("Disabled Mods", disabled_mods),
                        ("Server Disabled Mods", server_disabled_mods),
                        ("Channel Disabled Mods", channel_disabled_mods)]
            elif info_type == InfoType.COMMANDS:
                # Commands
                commands = [cmd for cmd in Utils.mod_handler.commands]
                command_names = [cmd.name for cmd in commands]
                command_aliases = [command_alias for cmd in commands for command_alias in cmd]
                server_disabled_commands = [cmd.name for cmd in commands if int(server.id) in
                                            mod_config[cmd.parent_mod.name]["Commands"][cmd.name][
                                                "Disabled Servers"]]
                channel_disabled_commands = [cmd.name for cmd in commands if int(channel.id) in
                                             mod_config[cmd.parent_mod.name]["Commands"][cmd.name][
                                                 "Disabled Channels"]]
                return [("Commands", command_names),
                        ("Command Aliases", command_aliases),
                        ("Server Disabled Mods", server_disabled_commands),
                        ("Channel Disabled Mods", channel_disabled_commands)]

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


class InfoType:
    MODS = "Mod Info"
    SERVERS = "Server Info"
    CHANNELS = "Channel Info"
    COMMANDS = "Command Info"
    PERMISSIONS = "Permission Info"
