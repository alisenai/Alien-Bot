from Common import Permissions, Utils, DataManager
import time


class Command:
    def __init__(self, parent_mod, name, aliases, enabled=False, minimum_permissions="Owner", command_help="No help",
                 useage="No useage", cool_down_seconds=0, bypass_server_restrictions=False,
                 bypass_channel_restrictions=False, dm_enabled=False):
        # Check if parameters are valid
        assert name is not None or "", "Command not given a valid name"
        assert aliases is not None and len(aliases) > 0, "Command not given aliases"
        assert cool_down_seconds >= 0, "Cool down time must be greater than 0"
        # Var Init
        self.parent_mod = parent_mod
        self.name = name
        self.aliases = [alias.lower() for alias in aliases]
        self.enabled = enabled
        self.minimum_permissions = minimum_permissions
        self.help = command_help
        self.useage = useage
        self.cool_down_seconds = cool_down_seconds
        self.bypass_server_restrictions = bypass_server_restrictions
        self.bypass_channel_restrictions = bypass_channel_restrictions
        self.dm_enabled = dm_enabled
        # Get cool down manager
        self.command_database = DataManager.get_manager("commands")
        self.command_database.execute("CREATE TABLE IF NOT EXISTS '" + name + "'(user_id TEXT, last_called REAL)")

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

    # Reset user's cool down (If a command wasn't called correctly / cool down doesn't apply to it / etc)
    def reset_cool_down(self, user_id):
        self.command_database.execute("DELETE FROM '%s' WHERE user_id='%s'" % (self.name, user_id))

    # Returns if the given string is a known command alias
    def is_alias(self, string):
        return string in self.aliases

    # Returns true if the passed user has the permissions to call this command
    def has_permissions(self, user):
        return Permissions.has_permission(user, self.minimum_permissions)

    async def call_command_skip_checks(self, message):
        # Send "is typing", for  a e s t h e t i c s
        async with message.channel.typing():
            # Keep a record of the last call time
            author = message.author
            if self.last_called(author.id) == -1:
                self.command_database.execute(
                    "INSERT OR IGNORE INTO '%s' VALUES('%s', '%s')" % (self.name, author.id, str(time.time()))
                )
            else:
                self.command_database.execute(
                    "UPDATE '%s' SET last_called='%s' WHERE user_id='%s'" % (self.name, str(time.time()), author.id)
                )
            # Call the command on the parent mod
            await self.parent_mod.command_called(message, self)

    # Returns when the user last called the command
    def last_called(self, user_id):
        last_called = self.command_database.execute("SELECT last_called FROM '" + self.name + "' WHERE user_id=" +
                                                    str(user_id) + " LIMIT 1")
        if len(last_called) != 0:
            return int(last_called[0])
        return -1

    def get_cool_down_left(self):
        return self.command_database.execute

    # Calls the command if it's enabled and if the user has perms
    async def call_command(self, message):
        if self.enabled:
            server = message.guild
            channel = message.channel
            author = message.author
            mod_config = DataManager.get_manager("mod_config").get_data()
            # Check if the command is enabled in the server, or if it's a DM
            if int(server.id) not in mod_config[self.parent_mod.name]["Commands"][self.name]["Disabled Servers"] \
                    or self.dm_enabled:
                # Check if the command is enabled in the channel
                if int(channel.id) not in mod_config[self.parent_mod.name]["Commands"][self.name]["Disabled Channels"]:
                    # Check if the user has the permissions to call the command, or if it's a DM
                    if self.has_permissions(author) \
                            or self.dm_enabled:
                        # If there is no cool down for this command, all checks were passed so call the command
                        if self.cool_down_seconds == 0:
                            await self.call_command_skip_checks(message)
                        # There's a cool down for this command, use it
                        else:
                            # Get the last time the user called the command
                            last_called = self.last_called(author.id)
                            # If the user has never called the command before (or there is no record of it)
                            if last_called == -1:
                                await self.call_command_skip_checks(message)
                            else:
                                current_tick = time.time()
                                # If the cool down has expired, update DB and call command
                                if current_tick - last_called > self.cool_down_seconds:
                                    await self.call_command_skip_checks(message)
                                # Command is on cool down for this user
                                else:
                                    await self.parent_mod.error_cool_down(message, self)
                    else:
                        await self.parent_mod.error_no_permissions(message, self)
                else:
                    await self.parent_mod.error_disabled_channel(message, self)
            else:
                await self.parent_mod.error_disabled_server(message, self)
