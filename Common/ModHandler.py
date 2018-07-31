import os
import sys
import discord
import difflib
from Common import Utils
from Common import DataManager


# TODO: Redo help so it only prints what the user's permissions allows
# TODO: Add prefix when printing useage help?
class ModHandler:
    mods = {}
    commands = []
    done_loading = False
    mod_command_aliases = []

    # Builds a mod handler with passed parameters
    def __init__(self, bot_commands, bot_command_aliases, embed_color):
        # Var Init
        self.bot_commands = bot_commands
        self.bot_command_aliases = bot_command_aliases
        self.embed_color = embed_color

    async def load_mods(self):
        print("[Loading Mods]")
        mod_config_manager = DataManager.get_manager("mod_config")
        mod_configs = mod_config_manager.get_data()
        new_mod_config = {}
        # Cycle through all the mods in the mod directory
        # If the mod config doesn't contain the mod -> Generate config
        # If the mod config contains the mod        -> Keep Same config
        for mod_name in os.listdir("Mods/"):
            if mod_name not in mod_configs.keys():
                new_mod_config[mod_name] = {
                    "Command Perms": {},
                    "Enabled": True,
                    "Disabled Servers": [],
                    "Disabled Channels": []
                }
            else:
                # Append for config cleaning
                new_mod_config[mod_name] = mod_configs[mod_name]
            mod_config_manager.write_data(new_mod_config)
        # Cycle through all the files within the mod dir
        for mod_name in os.listdir("Mods/"):
            # Store the mod names to return them
            # Check if it's a newly installed mod or if the mod is enabled
            # Mod doesn't exist -> Newly installed -> Load it
            # Mod exists        -> Not disabled    -> Load it
            if mod_name not in mod_configs.keys() or mod_configs[mod_name]['Enabled'] is not False:
                # Make the python files importable and import them
                sys.path.insert(0, 'Mods/' + mod_name)
                print("[Loading: " + mod_name + "]")
                # Import and call mod init to get object
                mod = getattr(__import__(mod_name), mod_name)(mod_name, self.embed_color)
                # Check for command conflicts and store commands
                for command_name in mod.commands:
                    command_alias = mod.commands[command_name]
                    for alias in command_alias:
                        # Check for conflicting commands
                        assert alias not in self.mod_command_aliases, "Duplicate mod commands - " + command_alias
                        assert alias not in self.bot_command_aliases, "Mod copies a bot command - " + command_alias
                        # Add as known alias for further conflict checks
                        self.mod_command_aliases.append(alias)
                    # Register command
                    self.commands.append(command_alias)
                # Get mod's info
                # Store mod's info
                self.mods[mod.name] = mod
                print("[Done loading " + mod_name + "]")
            # Mod exists -> Disabled -> Don't load it, as per config
            else:
                print("[Not Loading: " + mod_name + "]")
        self.done_loading = True
        print("[Done loading Mods]")

    # Called when a user message looks like a command, and it attempts to work with that command
    async def command_called(self, client, message, command_alias, is_help=False):
        server = message.server
        channel = message.channel
        split_message = message.content.split(" ")
        # If it's a help command
        if is_help:
            help_input = split_message[1].lower()
            # If it's help for a mod or a mod command
            # Mod -> Given mod name -> Get help
            # Command -> Get mod name -> Get help
            if self.is_mod_name(help_input) or help_input in [alias.lower() for alias in self.mod_command_aliases]:
                mod = help_input
                for mod_name in self.mods:
                    if help_input in [_.lower() for _ in self.mods[mod_name].command_aliases]:
                        mod = mod_name
                await self.get_mod_help(mod, message)
            # Not a known mod or mod command
            else:
                # Start building an embed reply
                embed = discord.Embed(title="[Help]", color=0x751DDF)
                # Get a printable version of the known help commands
                help_command_text = self.get_help_command_text()
                # Add a field to the reply embed
                embed.add_field(name="Unknown mod or command - " + split_message[1] + "",
                                value="Try: " + help_command_text + ".")
                # Reply with the created embed
                await client.send_message(channel, embed=embed)
        # Not a help command
        else:
            # Make sure everything initialized
            if self.done_loading:
                # Send "is typing", for  a e s t h e t i c s
                # await client.send_typing(channel)

                # If it's a known command -> call it if it's enabled / allowed
                for command in self.commands:
                    if command_alias in command:
                        mod_config = DataManager.get_manager("mod_config").get_data()[command.parent_mod.name]
                        # Check if command's parent mod is disabled in the current server
                        if server.id not in mod_config["Disabled Servers"]:
                            # Check if command's parent mod is disabled in the current channel
                            if channel.id not in mod_config["Disabled Channels"]:
                                await command.call_command(message)
                        return

                # No command called -> Not a known command
                most_similar_commands = most_similar_string(command_alias, self.mod_command_aliases)
                # No similar commands -> Reply with help commands
                if most_similar_commands is None:
                    help_command_text = self.get_help_command_text()
                    await Utils.simple_embed_reply(channel, "[Unknown command]",
                                                   "Try " + help_command_text + ".")
                # Similar-looking command exists -> Reply with it
                else:
                    await Utils.simple_embed_reply(channel, "[Unknown command]",
                                                   "Did you mean `" + most_similar_commands + "`?")
            # Mods are still loading -> Let the author know
            else:
                await Utils.simple_embed_reply(channel, "[Error]",
                                               "The bot is still loading, please wait.")

    # Called when ANY message is received by the bot
    async def message_received(self, message):
        for mod_name in self.mods:
            await self.mods[mod_name].message_received(message)

    # Returns a dictionary - {mod name : mod description}
    def get_mod_descriptions(self):
        mod_descriptions = {}
        for mod_name in self.mods:
            mod_descriptions[mod_name] = self.mods[mod_name].description
        return mod_descriptions

    # Checks if the passed var is a known mod name
    def is_mod_name(self, name):
        for mod_name in self.mods:
            if name.lower() == mod_name.lower():
                return True
        return False

    # Calls the help command on a specific mod, given mod command
    async def get_mod_help(self, mod, message):
        for mod_name in self.mods:
            if mod_name.lower() == mod.lower():
                await self.mods[mod_name].get_help(message)

    # Returns if ModHandler is done loading mods
    def is_done_loading(self):
        return self.done_loading

    # Used to get a printable version of the help commands
    def get_help_command_text(self):
        # Build all the help commands
        help_command_text = ""
        for command_alias in self.bot_commands["Help Command"]:
            help_command_text += command_alias + ", "
        # Return built text
        return help_command_text[0:-2]

    async def on_member_join(self, member):
        for mod_name in self.mods:
            await self.mods[mod_name].on_member_join(member)


# Get the most similar string from an array, given a string
def most_similar_string(string, string_list):
    # Check if there are strings to compare to
    if len(string_list) > 0:
        # Loop through and find the most similar string
        most_similar = string_list[0]
        for i in string_list:
            if string_similarity(i, string) > string_similarity(most_similar, string):
                most_similar = i
        return most_similar
    # Return None if there are no strings to compare to
    return None


# Returns the similarity between two strings
def string_similarity(string_one, string_two):
    return difflib.SequenceMatcher(None, string_one, string_two).ratio()
