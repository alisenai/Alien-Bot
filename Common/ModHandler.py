from Common import DataManager, Utils
import difflib
import sys
import os


class ModHandler:
    mods = {}
    commands = []
    done_loading = False
    mod_command_aliases = []

    # Builds a mod handler with passed parameters
    def __init__(self, embed_color):
        # Var Init
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
                        # TODO Check for same mod and command names (getting help doesn't work otherwise)
                        # Check for conflicting commands
                        assert alias not in self.mod_command_aliases, "Duplicate mod commands - " + command_alias
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
    async def command_called(self, message, command_alias):
        server = message.server
        channel = message.channel
        # split_message = message.content.split(" ")
        # Make sure everything initialized
        if self.done_loading:
            bot_config = DataManager.get_manager("bot_config")
            if int(server.id) not in bot_config.get_data("Disabled Servers"):
                if int(channel.id) not in bot_config.get_data("Disabled Channels"):
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
                    # # No command called -> Not a known command
                    # most_similar_command = most_similar_string(command_alias, self.mod_command_aliases)
                    # # No similar commands -> Reply with an error
                    # if most_similar_command is None:
                    #     # Reply that neither that mod nor command exists
                    #     await Utils.simple_embed_reply(channel, "[Help]",
                    #                                    "Unknown mod or command - %s" % split_message[1])
                    # # Similar-looking command exists -> Reply with it
                    # else:
                    #     # Reply with a similar command
                    #     await Utils.simple_embed_reply(channel, "[Unknown command]",
                    #                                    "Did you mean `" + most_similar_command + "`?")
        # Mods are still loading -> Let the author know
        else:
            await Utils.simple_embed_reply(channel, "[Error]",
                                           "The bot is still loading, please wait.")

    # Called when ANY message is received by the bot
    async def message_received(self, message):
        for mod_name in self.mods:
            await self.mods[mod_name].message_received(message)

    # Called once a second
    async def second_tick(self):
        for mod_name in self.mods:
            await self.mods[mod_name].second_tick()

    # Called once a minute
    async def minute_tick(self):
        for mod_name in self.mods:
            await self.mods[mod_name].minute_tick()

    # Returns a dictionary - {mod name : mod description}
    def get_mod_descriptions(self):
        mod_descriptions = {}
        for mod_name in self.mods:
            mod_descriptions[mod_name] = self.mods[mod_name].description
        return mod_descriptions

    async def get_help(self, message):
        split_message = message.content.split(" ")
        help_input = split_message[1].lower()
        # If it's help for a mod or a mod command
        # Mod -> Given mod name -> Get help
        # Command -> Get mod name -> Get help
        if self.is_mod_name(help_input) or help_input in [alias.lower() for alias in self.mod_command_aliases]:
            for mod_name in self.mods:
                lower_command_aliases = [_.lower() for _ in self.mods[mod_name].command_aliases]
                if help_input in lower_command_aliases or help_input == mod_name.lower():
                    return await self.mods[mod_name].get_help(message)
        # Not a known mod or mod command
        else:
            # Reply that neither that mod nor command exists
            await Utils.simple_embed_reply(message.channel, "[Help]", "Unknown mod or command - %s" % split_message[1])

    # Checks if the passed var is a known mod name
    def is_mod_name(self, name):
        for mod_name in self.mods:
            if name.lower() == mod_name.lower():
                return True
        return False

    # Returns if ModHandler is done loading mods
    def is_done_loading(self):
        return self.done_loading

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
