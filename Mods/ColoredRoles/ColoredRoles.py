import Mod
import discord
import logging
import json
import Utils
from Command import Command


# TODO: Call command on other user if "admin" for add role / remove role / etc
# TODO: Require role for command use
# TODO: Logging levels - the rest


class ColoredRoles(Mod.Mod):
    def __init__(self, client, logging_level, embed_color):
        # General var init
        self.users = {}
        self.roles = {}
        self.client = client
        self.logging_level = logging_level
        # Config var init
        self.config = json.loads("".join(open("Mods/ColoredRoles/ColorRolesConfig.json", encoding="utf-8").readlines()))
        self.max_colors = self.config['MaxColors']
        # Build command objects
        self.commands = []
        for command in self.config['Commands']:
            self.commands.append(Command(self, command, self.config['Commands'][command]['Aliases'], True,
                                         self.config['Commands'][command]['Help']))
        # Generate a fresh DB
        self.generate_db()
        # Init the super with all the info from this mod
        super().__init__(client, self.config['ModDescription'], self.config['ModCommand'],
                         self.commands, logging_level, embed_color)

    # Called when the bot receives a message
    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        channel, author, server = message.channel, message.author, message.server
        try:
            # Adding a role
            if command in self.commands['Add Color Command']['Aliases']:
                # Check command format
                if len(split_message) > 1:
                    # If the first parameter is hex
                    if Utils.is_hex(split_message[1]):
                        hex_color = split_message[1].upper()
                        # If role hasn't been created and max color count hasn't been reached -> Create Role
                        if len(self.roles[server.id]) < self.max_colors:
                            if self.get_role_by_hex(server, hex_color) is None:
                                new_color_role = await self.create_role(server, hex_color)
                            # Role already exists -> Get it
                            else:
                                new_color_role = self.get_role_by_hex(server, hex_color)
                            # Give the user their color
                            await self.give_role(server, author, new_color_role)
                            await Utils.simple_embed_reply(self.client, channel, "[Add Role]",
                                                           "Added " + hex_color + " to your roles.", hex_color)
                        else:
                            await Utils.simple_embed_reply(self.client, channel, "[Added Color]",
                                                           "Max role count reached.",
                                                           hex_color=hex_color)
                    # First parameter is not a valid hex value -> Error
                    else:
                        Utils.simple_embed_reply(self.client, channel, "[Error]", "Invalid hex value.",
                                                 split_message[1])
                # Hex parameter not supplied -> Error
                else:
                    Utils.simple_embed_reply(self.client, channel, "[Error]", "Missing color parameter.")
            # Removing a role
            elif command in self.commands["Remove Color Command"]["Aliases"]:
                # Get current role info
                current_color_role_id = self.users[server.id][author.id]
                current_color_role = Utils.get_role_by_id(server, current_color_role_id)
                hex_color = current_color_role.name
                # Remove the role
                await self.remove_role(server, author, current_color_role)
                # Reply
                await Utils.simple_embed_reply(self.client, channel, "[Removed Color]",
                                               "Removed " + hex_color + " from your roles.",
                                               hex_color=hex_color)
            # Deleting a role
            elif command in self.commands["Delete Color Command"]["Aliases"]:
                # If the hex color was supplied
                if len(split_message) > 1:
                    if Utils.is_hex(split_message[1]):
                        hex_color = split_message[1].upper()
                        color_role = self.get_role_by_hex(server, hex_color)
                        # If the role doesn't exist -> Error
                        if color_role is None:
                            await Utils.simple_embed_reply(self.client, channel, "[Error]", "Color not found.",
                                                           hex_color)
                        # Role found -> Delete it and let the user know
                        else:
                            await self.delete_role(server, color_role)
                            # Reply
                            await Utils.simple_embed_reply(self.client, channel, "[Deleted Color]",
                                                           "Deleted " + hex_color + ".",
                                                           hex_color=hex_color)
                    # First parameter is not a valid hex value -> Error
                    else:
                        await Utils.simple_embed_reply(self.client, channel, "[Error]", "Invalid hex value.",
                                                       split_message[1])
                # Hex parameter not supplied -> Error
                else:
                    await Utils.simple_embed_reply(self.client, channel, "[Error]", "Missing color parameter.")
            # Listing roles
            elif command in self.commands["List Colors Command"]["Aliases"]:
                roles_text = ""
                # If roles exist
                if len(self.roles[server.id]) > 0:
                    # Build text from every role name
                    for role in self.roles[server.id]:
                        roles_text += Utils.get_role_by_id(server, role).name + "\n"
                # No roles exist -> state so
                else:
                    roles_text = "No roles exist."
                # Reply with the list
                await Utils.simple_embed_reply(self.client, channel, "[Color List]", roles_text)
            # Listing users equipped with role
            elif command in self.commands["Equipped Users Command"]["Aliases"]:
                # If the hex color was supplied
                if len(split_message) > 1:
                    if Utils.is_hex(split_message[1]):
                        hex_color = split_message[1].upper()
                        role = self.get_role_by_hex(server, hex_color)
                        # If the role exists
                        if role is not None:
                            users_text = ""
                            # Check if users are equipped with this role
                            if len(self.roles[server.id][role.id]) > 0:
                                for user_id in self.roles[server.id][role.id]:
                                    user = Utils.get_user_by_id(server, user_id)
                                    users_text += user.name + "\n"
                            # No users are equipped -> State so
                            else:
                                users_text = "No users are equipped with this role."
                            # Reply with the equipped roles
                            await Utils.simple_embed_reply(self.client, channel, "[" + role.name + " Equipped List]",
                                                           users_text,
                                                           hex_color)
                        # Hex parameter doesn't have an associated role -> Error
                        else:
                            await Utils.simple_embed_reply(self.client, channel, "[Error]", "Color not found.",
                                                           hex_color)
                    # First parameter is not a valid hex value -> Error
                    else:
                        await Utils.simple_embed_reply(self.client, channel, "[Error]", "Invalid hex value.",
                                                       split_message[1])
                # Hex parameter not supplied -> Error
                else:
                    await Utils.simple_embed_reply(self.client, channel, "[Error]", "Missing color parameter.")
            # List all info known by this mod for current server
            elif command in self.commands["Color Info Command"]["Aliases"]:
                # If roles exist
                if len(self.roles[server.id]) > 0:
                    # Begin reply crafting
                    embed = discord.Embed(title="[Info]", color=0x751DDF)
                    # Cycle all the roles, creating user list per role
                    for role_id in self.roles[server.id]:
                        role = Utils.get_role_by_id(server, role_id)
                        users_text = ""
                        for user_id in self.roles[server.id][role_id]:
                            user = Utils.get_user_by_id(server, user_id)
                            users_text += user.name + "\n"
                        # Create embed field per role
                        embed.add_field(name=role.name, value=users_text)
                    # Reply
                    await self.client.send_message(channel, embed=embed)
                # No used roles -> state so
                else:
                    await Utils.simple_embed_reply(self.client, channel, "[Info]", "No color exist.")
            # Purge a given role
            elif command in self.commands["Purge Color Command"]["Aliases"]:
                # If the hex color was supplied
                if len(split_message) > 1:
                    if Utils.is_hex(split_message[1]):
                        hex_color = split_message[1].upper()
                        role = self.get_role_by_hex(server, hex_color)
                        # If the role exists
                        if role is not None:
                            # Delete the role and state so
                            await self.delete_role(server, role)
                            await Utils.simple_embed_reply(self.client, channel, "[Purged Color]",
                                                           "Purged " + hex_color + ".")
                        # Hex parameter doesn't have an associated role -> Error
                        else:
                            await Utils.simple_embed_reply(self.client, channel, "[Error]", "Color not found.",
                                                           hex_color)
                    # First parameter is not a valid hex value -> Error
                    else:
                        await Utils.simple_embed_reply(self.client, channel, "[Error]", "Invalid hex value.",
                                                       split_message[1])
                # Hex parameter not supplied -> Error
                else:
                    await Utils.simple_embed_reply(self.client, channel, "[Error]", "Missing color parameter.")
        # Bot isn't supplied with sufficient perms -> Error
        except discord.errors.Forbidden as e:
            await Utils.simple_embed_reply(self.client, channel, "[Error]", "Bot does not have enough perms.")
            logging.exception("An error occurred.")
        # Some error I don't know of occurred, PING ALIEN!
        except Exception as e:  # Leave as a general exception!
            await Utils.simple_embed_reply(self.client, channel, "[Error]", "Unknown error occurred (Ping Alien).")
            logging.exception("An error occurred.")

    # Used to give a role to a user and record it in the mod DB
    async def give_role(self, server, user, role):
        old_role_id = self.users[server.id][user.id]
        # If the user has an old role -> Delete old role
        if old_role_id is not None:
            old_role = Utils.get_role_by_id(server, old_role_id)
            # If the role isn't what's needed -> Delete old role
            if old_role.name is not role.name:
                await self.remove_role(server, user, old_role)
        # Give role to user
        await self.client.add_roles(user, role)
        # Save new user role to user's data
        self.users[server.id][user.id] = role.id
        # Save user to the color's data
        # Color data exists        -> Append user id
        # Color data doesn't exist -> Create and append it
        if role.id in self.roles[server.id].keys():
            self.roles[server.id][role.id].append(user.id)
        else:
            self.roles[server.id][role.id] = [user.id]

    # Used to delete a role from the user and mod DB
    async def remove_role(self, server, user, role):
        # Remove role from user
        await self.client.remove_roles(user, role)
        # Remove the old role from the role list
        self.roles[server.id][role.id].remove(user.id)
        # Remove color from user's data
        self.users[server.id][user.id] = None
        # Delete the old role if it is not used
        if len(self.roles[server.id][role.id]) == 0:
            await self.delete_role(server, role)

    # Used to delete a role from the server and mod DB
    async def delete_role(self, server, role):
        # Delete role from the server
        await self.client.delete_role(server, role)
        for user_id in self.roles[server.id][role.id]:
            self.users[server.id][user_id] = None
        # Delete the role database
        del self.roles[server.id][role.id]

    # Used for creating a role (Specific for this mod)
    async def create_role(self, server, color):
        role = await self.client.create_role(server, name=color, color=Utils.get_color(color),
                                             permissions=discord.Permissions(permissions=0))
        self.roles[server.id][role.id] = []
        # Move it to top priority (so other roles's colors get over-written)
        await self.role_max_shift(server, role)
        return role

    # Used for bringing a color forward in viewing priority
    async def role_max_shift(self, server, role):
        try:
            pos = 1
            while True:
                await self.client.move_role(server, role, pos)
                pos += 1
        except (discord.Forbidden, discord.HTTPException):
            return

    # Used for getting a role by hex value in given server
    def get_role_by_hex(self, server, role_hex):
        return discord.utils.get(server.roles, name=role_hex)

    # Generates a fresh database on users and their color roles for every server the bot is in
    def generate_db(self):
        # Created a local DB based on live info (fresh DB)
        for server in self.client.servers:
            # Create a user database for each server
            self.users[server.id], self.roles[server.id] = {}, {}
            for user in server.members:
                # Create a role database for each user
                self.users[server.id][user.id] = None
                for role in user.roles:
                    # If a user's role is a color -> Save it
                    if Utils.is_hex(role.name):
                        self.users[server.id][user.id] = role.id
                        if role.id in self.roles[server.id].keys():
                            self.roles[server.id][role.id].append(user.id)
                        else:
                            self.roles[server.id][role.id] = [user.id]
