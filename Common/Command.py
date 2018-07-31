import time

from Common import Permissions, Utils, DataManager


class Command:
    def __init__(self, parent_mod, name, aliases, enabled=False, minimum_permissions="Owner", command_help="No help",
                 useage="No useage", cool_down_seconds=0):
        # Check if parameters are valid
        assert name is not None or "", "Command not given a valid name"
        assert aliases is not None and len(aliases) > 0, "Command not given aliases"
        assert cool_down_seconds >= 0, "Cool down time must be greater than 0"
        # Var Init
        self.parent_mod = parent_mod
        self.name = name
        self.aliases = aliases
        self.enabled = enabled
        self.minimum_permissions = minimum_permissions
        self.help = command_help
        self.useage = useage
        self.cool_down_seconds = cool_down_seconds
        # Get cool down manager
        self.command_database = DataManager.get_manager("commands")
        self.command_database.execute("CREATE TABLE IF NOT EXISTS '" + name + "'(user TEXT, last_called REAL)")

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

    async def call_command_skip_checks(self, message):
        # Send "is typing", for  a e s t h e t i c s
        await Utils.client.send_typing(message.channel)
        # Call the command on the parent mod
        await self.parent_mod.command_called(message, self)

    # Returns when the user last called the command
    def last_called(self, user_id):
        last_called = self.command_database.execute("SELECT last_called FROM '" + self.name + "' WHERE user=" +
                                                    str(user_id) + " LIMIT 1")
        if len(last_called) != 0:
            return int(last_called[0])
        return -1

    def get_cool_down_left(self):
        return self.command_database.execute

    # Calls the command if it's enabled and if the user has perms
    async def call_command(self, message):
        if self.enabled:
            server = message.server
            channel = message.channel
            author = message.author
            mod_config = DataManager.get_manager("mod_config").get_data()
            # Check if the command is enabled in the server
            if server.id not in mod_config[self.parent_mod.name]["Command Perms"][self.name]["Disabled Servers"]:
                # Check if the command is enabled in the channel
                if channel.id not in mod_config[self.parent_mod.name]["Command Perms"][self.name]["Disabled Channels"]:
                    # Check if the user has the permissions to call the command
                    if self.has_permissions(author.id):
                        # If there is no cool down for this command, all checks were passed so call the command
                        if self.cool_down_seconds == 0:
                            await self.call_command_skip_checks(message)
                        # There's a cool down for this command, use it
                        else:
                            # Get the last time the user called the command
                            last_called = self.last_called(author.id)
                            # If the user has never called the command before (or there is no record of it)
                            if last_called == -1:
                                self.command_database.execute(
                                    "INSERT INTO '" + self.name + "' VALUES('" + author.id + "', " + str(
                                        time.time()) + ")")
                                await self.call_command_skip_checks(message)
                            else:
                                current_tick = time.time()
                                # If the cool down has expired, update DB and call command
                                if current_tick - last_called > self.cool_down_seconds:
                                    self.command_database.execute("UPDATE '" + self.name + "' SET last_called=" + str(
                                        current_tick) + " WHERE user='" + author.id + "'")
                                    await self.call_command_skip_checks(message)
                                else:
                                    await self.parent_mod.error_cool_down(message, self)
                    else:
                        await self.parent_mod.error_no_permissions(message, self)
                else:
                    await self.parent_mod.error_disabled_channel(message, self)
            else:
                await self.parent_mod.error_disabled_server(message, self)
