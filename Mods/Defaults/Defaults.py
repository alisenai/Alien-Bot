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
                embed = discord.Embed(title="[Help]", color=Utils.default_hex_color)
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
            # No parameters passed, user is asking for all the info
            if len(split_message) == 1:
                all_info = True
            # At least one parameter passed
            else:
                main_param = split_message[1].lower()
                # Get which info the user is asking for
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
            # Printing for all info
            if all_info:
                embed = discord.Embed(title="[Info]", color=Utils.default_hex_color, description="Bot info.")
                # Append basic info
                embed.add_field(name="Bot Nick", value=str(Utils.bot_nick), inline=True)
                embed.add_field(name="Bot Prefix", value=str(Utils.prefix), inline=True)
                embed.add_field(name="Bot Emoji", value=str(Utils.bot_emoji), inline=True)
                embed.add_field(name="Uptime", value=Utils.seconds_format(time.time() - self.start_time), inline=True)
                # Go through every type of info available
                for info_type in [InfoType.SERVERS, InfoType.CHANNELS,
                                  InfoType.PERMISSIONS, InfoType.MODS, InfoType.COMMANDS]:
                    # Get the info for that text
                    given_info = self.get_specific_info(server, channel, info_type)
                    mod_text = ""
                    for item_name in given_info:
                        # Generate and append text to the info
                        mod_text += "%s: %d\n" % (item_name[0], len(item_name[1]))
                    # Add ONE field for each info type
                    embed.add_field(name=info_type, value=mod_text, inline=True)
            # Only print something specific, as requested
            elif given_type is not None:
                embed = discord.Embed(title="[%s]" % given_type, color=Utils.default_hex_color, description="Bot info.")
                # Get info about what was requested
                given_info = self.get_specific_info(server, channel, given_type)
                # Add a new field for each group of info
                for item_name in given_info:
                    embed.add_field(name=item_name[0], value=self.format(item_name[1], 400), inline=True)
            # Unknown parameter(s) passed
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

    # Get a vertical list text built from an array of Strings, given a max number of characters
    def format(self, item_list, max_char):
        mod_text = ""
        # Keep appending until it breaks the character limit (or doesn't and finishes)
        for mod_name in sorted(item_list):
            # "- 3" so it can append "..."
            if len(mod_text) + len(mod_name) < max_char - 3:
                mod_text += mod_name + "\n"
                max_char -= 1  # Newline char
            else:
                return mod_text + "..."
        if mod_text == "":
            return "None"
        return mod_text

    def get_specific_info(self, server, channel, info_type):
        # Info for servers and channels
        if info_type == InfoType.SERVERS or info_type == InfoType.CHANNELS:
            bot_config = DataManager.get_manager("bot_config")
            servers = [svr for svr in Utils.client.servers]
            # Info for servers
            if info_type == InfoType.SERVERS:
                # TODO: For current server only?
                return [("Servers", [svr.name for svr in servers]),
                        ("Disabled Servers", bot_config.get_data("Disabled Servers"))]
            # Info for channels
            elif info_type == InfoType.CHANNELS:
                channels = [cnl for cnl in server.channels if cnl.type == discord.ChannelType.text]
                return [("Channels", [cnl.name for cnl in channels]),
                        ("Disabled Channels", bot_config.get_data("Disabled Channels"))]
        # Info for permissions
        elif info_type == InfoType.PERMISSIONS:
            permissions = Permissions.permissions
            names, restricted = [], []
            owners, default = [Permissions.owner_perm.title], [Permissions.default_perm.title]
            # Get permission names and restricted permissions into their respective lists
            for permission in permissions:
                names.append(permission)
                if not permissions[permission].has_permissions:
                    restricted.append(permission)
            return [("Permissions", names),
                    ("Owner", owners),
                    ("Default", default),
                    ("Restricted", restricted)]
        # Info for mods and commands
        elif info_type == InfoType.MODS or InfoType.COMMANDS:
            mod_config = DataManager.get_manager("mod_config").get_data()
            # Info for mods
            if info_type == InfoType.MODS:
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
            # Info for commands
            elif info_type == InfoType.COMMANDS:
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
        # Build message info
        split_message = message.content.split(" ")
        server = message.server
        channel = message.channel
        # Grab the bot's config
        config = DataManager.get_manager("bot_config")
        # Init vars based on passed mode type
        key_word, mode_obj = ("Channels", channel) if channel_mode else ("Servers", server)
        disabled_ids = config.get_data("Disabled " + key_word)
        if len(split_message) > 1:
            first_parameter = split_message[1].lower()
            # Determine if the user is trying to enable/disable something other than the server or channel
            enable_mode = None
            if len(split_message) > 2:
                # The second parameter is some form of "enable" or "disable", if called correctly
                passed_change_mode = split_message[2].lower()
                if passed_change_mode == "enable" or passed_change_mode == "disable":
                    enable_mode = True if passed_change_mode == "enable" else False
            # Enable / Disable a Server / Channel
            if first_parameter == "enable" or first_parameter == "disable":
                if first_parameter == "enable":
                    # Make sure to not remove the ID if it's not there already
                    if int(mode_obj.id) in disabled_ids:
                        disabled_ids.remove(int(mode_obj.id))
                        config.write_data(disabled_ids, key="Disabled " + key_word)
                    await Utils.simple_embed_reply(channel, "[Enabled]", "%s has been enabled in %s." %
                                                   (Utils.bot_nick, str(mode_obj)))
                elif first_parameter == "disable":
                    # Make sure to not add the ID if it's not there already
                    if int(mode_obj.id) not in disabled_ids:
                        disabled_ids.append(int(mode_obj.id))
                    await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                   (Utils.bot_nick, str(mode_obj)))
                config.write_data(disabled_ids, key="Disabled " + key_word)
            # Enable / Disable a Mod / Command
            else:
                given_mod = Utils.mod_handler.get_mod_by_name(first_parameter)
                mod_config = DataManager.get_manager("mod_config")
                # Check if it found a mod given a name
                if given_mod is not None:
                    mod_data = mod_config.get_data(given_mod.name)
                    # Check if the mod should be enabled, or if it's currently disabled (to toggle)
                    if enable_mode or (int(mode_obj.id) in mod_data["Disabled " + key_word] and enable_mode is None):
                        # Make sure to not remove the ID if it's not there already
                        if int(mode_obj.id) in mod_data["Disabled " + key_word]:
                            mod_data["Disabled " + key_word].remove(int(mode_obj.id))
                        await Utils.simple_embed_reply(channel, "[Enabled]", "%s has been enabled in %s." %
                                                       (given_mod.name, str(mode_obj)))
                    # Mod should be disabled
                    else:
                        # Make sure to not add the ID if it's not there already
                        if int(mode_obj.id) not in mod_data["Disabled " + key_word]:
                            mod_data["Disabled " + key_word].append(int(mode_obj.id))
                        await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                       (given_mod.name, str(mode_obj)))
                    mod_config.write_data(mod_data, key=given_mod.name)
                # Passed parameter might refer to a command
                else:
                    given_command = Utils.mod_handler.get_command_by_alias(first_parameter)
                    # Check if it found a command given an alias
                    if given_command is not None:
                        mod_data = mod_config.get_data(given_command.parent_mod.name)
                        command_data = mod_data["Commands"][given_command.name]
                        # Check if the command should be enabled, or if it's currently disabled (to toggle)
                        if enable_mode or (
                                int(mode_obj.id) in command_data["Disabled " + key_word] and enable_mode is None
                        ):
                            # Make sure to not remove the ID if it's not there already
                            if int(mode_obj.id) in command_data["Disabled " + key_word]:
                                command_data["Disabled " + key_word].remove(int(mode_obj.id))
                            await Utils.simple_embed_reply(channel, "[Enabled]", "%s has been enabled in %s." %
                                                           (given_command.name, str(mode_obj)))
                        # Command should be disabled
                        else:
                            # Make sure to not add the ID if it's not there already
                            if int(mode_obj.id) not in command_data["Disabled " + key_word]:
                                command_data["Disabled " + key_word].append(int(mode_obj.id))
                            await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                                           (given_command.name, str(mode_obj)))
                        mod_data["Commands"][given_command.name] = command_data
                        mod_config.write_data(mod_data, key=given_command.parent_mod.name)
                    # That command wasn't found nor was a mod - error
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Neither that command nor mod exists.")
        # Not given whether to enable or disable - so toggle based on current status
        else:
            # Make sure to not remove the ID if it's not there already
            if int(mode_obj.id) in disabled_ids:
                disabled_ids.remove(int(mode_obj.id))
                await Utils.simple_embed_reply(channel, "[Enabled]", "%s has been enabled in %s." %
                                               (Utils.bot_nick, str(mode_obj)))
            # Otherwise the ID doesn't exist, so it can be added
            else:
                disabled_ids.append(int(mode_obj.id))
                await Utils.simple_embed_reply(channel, "[Disabled]", "%s has been disabled in %s." %
                                               (Utils.bot_nick, str(mode_obj)))
            config.write_data(disabled_ids, key="Disabled " + key_word)


class InfoType:
    MODS = "Mod Info"
    SERVERS = "Server Info"
    CHANNELS = "Channel Info"
    COMMANDS = "Command Info"
    PERMISSIONS = "Permission Info"
