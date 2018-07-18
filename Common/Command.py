from Common import Permissions, Utils, DataManager

# TODO: Add examples for each command
class Command:
    def __init__(self, parent_mod, name, aliases, enabled=False, minimum_permissions="Owner", command_help="No help",
                 useage="No useage"):
        # Check if parameters are valid
        assert name is not None or "", "Command not given a valid name"
        assert aliases is not None and len(aliases) > 0, "Command not given aliases"
        # Var Init
        self.parent_mod = parent_mod
        self.name = name
        self.aliases = aliases
        self.enabled = enabled
        self.minimum_permissions = minimum_permissions
        self.help = command_help
        self.useage = useage

    def __eq__(self, other):
        return self.name == other.name

    def __iter__(self):
        self.alias_index = 0
        return self

    def __next__(self):
        if self.alias_index > len(self.aliases) - 1:
            raise StopIteration
        else:
            alias = self.aliases[self.alias_index]
            self.alias_index += 1
            return alias

    # Returns if the given string is a known command alias
    def is_alias(self, string):
        return string in self.aliases

    # Returns true if the passed user ID has the permissions to call this command
    def has_permissions(self, user_id):
        return Permissions.has_permission(user_id, self.minimum_permissions)

    # Calls the command if it's enabled and if the user has perms
    async def call_command(self, message):
        if self.enabled:
            server = message.server
            channel = message.channel
            author = message.author
            mod_config = DataManager.get_data("mod_config")
            # Check if the command is enabled in the server
            if server.id not in mod_config[self.parent_mod.name]["Command Perms"][self.name]["Disabled Servers"]:
                # Check if the command is enabled in the channel
                if channel.id not in mod_config[self.parent_mod.name]["Command Perms"][self.name]["Disabled Channels"]:
                    if self.has_permissions(author.id):
                        # Send "is typing", for  a e s t h e t i c s
                        await Utils.client.send_typing(channel)
                        await self.parent_mod.command_called(message, self)
                    # else:
                    #     print("User", author, "does not have permissions to call", self.name)
                # else:
                #     print("Command", self.name, "cannot be used in the channel", channel)
            # else:
            #     print("Command", self.name, "cannot be used in the server", server)
