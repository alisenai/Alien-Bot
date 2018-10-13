from Common import DataManager, Utils
from Common.Mod import Mod
import re


class SelfRoles(Mod):
    def __init__(self, mod_name, embed_color):
        super().__init__(mod_name, "Just an example mod.", {}, embed_color)
        # Config var init
        self.config = DataManager.JSON("Mods/SelfRoles/SelfRolesConfig.json")
        # Init DBs
        self.roles_db = DataManager.add_manager("shop_database", "Mods/SelfRoles/Roles.db",
                                                file_type=DataManager.FileType.SQL)
        self.generate_db()
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    async def command_called(self, message, command):
        # Slip the message on space to help parse the command
        split_message = message.content.split(" ")
        # Extract the server, channel and author from the message
        server, channel, author = message.server, message.channel, message.author
        if command is self.commands["I Am Command"]:
            if len(split_message) > 1:
                given_name = split_message[1].lower()
                if is_valid_name(given_name):
                    role_id = self.roles_db.execute(
                        "SELECT role_id FROM '%s' where name='%s'" % (server.id, given_name)
                    )
                    if len(role_id) > 0:
                        role = Utils.get_role_by_id(server, role_id[0])
                        if role is not None:
                            await Utils.client.add_roles(author, role)
                            await Utils.simple_embed_reply(channel, "[SelfRoles]", "You now have the `%s` role!" %
                                                           given_name)
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "Role not found.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Role not found.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid role supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Invalid parameters supplied.")
        elif command is self.commands["I Am Not Command"]:
            if len(split_message) > 1:
                given_name = split_message[1].lower()
                if is_valid_name(given_name):
                    role_id = self.roles_db.execute(
                        "SELECT role_id FROM '%s' where name='%s'" % (server.id, given_name)
                    )
                    if len(role_id) > 0:
                        role = Utils.get_role_by_id(server, role_id[0])
                        if role is not None:
                            await Utils.client.remove_roles(author, role)
                            await Utils.simple_embed_reply(channel, "[SelfRoles]", "You no longer have the `%s` role!" %
                                                           given_name)
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "Role not found.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Role not found.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid role supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Invalid parameters supplied.")
        elif command is self.commands["Add Self Role Command"]:
            if len(split_message) > 2:
                role_name = split_message[1].lower()
                if is_valid_name(role_name):
                    role = Utils.get_role(server, split_message[2])
                    if role is not None:
                        self.roles_db.execute("INSERT INTO '%s' VALUES ('%s', '%s')" % (server.id, role.id, role_name))
                        await Utils.simple_embed_reply(channel, "[SelfRoles]", "Role `%s` was added as `%s`." %
                                                       (role.name, role_name))
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Role not found.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid name supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Invalid parameters supplied.")
        elif command is self.commands["Delete Self Role Command"]:
            if len(split_message) > 1:
                role_name = split_message[1].lower()
                if is_valid_name(role_name):
                    if len(self.roles_db.execute(
                            "SELECT name FROM `%s` WHERE name='%s'" % (server.id, role_name)
                    )) > 0:
                        self.roles_db.execute("DELETE FROM '%s' where name='%s'" % (server.id, role_name))
                        await Utils.simple_embed_reply(channel, "[SelfRoles]", "Role `%s` was deleted." % role_name)
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Role not found.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid name supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Invalid parameters supplied.")

    # Generates the roles DB
    def generate_db(self):
        for server in Utils.client.servers:
            self.roles_db.execute(
                "CREATE TABLE IF NOT EXISTS '%s'(role_id TEXT, name TEXT)" % server.id
            )


# Prevents SQL Injection
def is_valid_name(shop_name):
    return re.fullmatch(r"[A-Za-z0-9]*", shop_name)
