import re
import discord


# Used to check if a string is a hex value
def is_hex(string):
    if re.match(r'^0x(?:[0-9a-fA-F]{3}){1,2}$', string):
        return True
    return False


# Used for getting user by user id in given server
def get_user_by_id(server, user_id):
    # Gets a user by their ID
    return server.get_member(user_id)


# Used for getting a role by id in given server
def get_role_by_id(server, role_id):
    for role in server.roles:
        if role.id == role_id:
            return role


# Used for getting a discord color from a hex value
def get_color(color):
    return discord.Color(int(color, 16))