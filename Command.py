# TODO: Add logging levels?
class Command:
    def __init__(self, parent_mod, name, aliases, enabled=False, command_help="No help", useage="No useage"):
        # Check if parameters are valid
        assert name is not None or "", "Command not given a valid name"
        assert aliases is not None and len(aliases) > 0, "Command not given aliases"
        # Var Init
        self.parent_mod = parent_mod
        self.name = name
        self.aliases = aliases
        self.enabled = enabled
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

    # Calls the command if it's enabled and if the user has perms
    async def call_command(self, message, user):
        if self.enabled:
            await self.parent_mod.command_called(message, self)
        # else:
            # return self.command_not_enabled_message
