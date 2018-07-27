import re
import discord

from Common import DataManager
from Common.Command import Command

client = None
prefix = None


# Used to check if a string is a hex value
def is_hex(string):
    if re.match(r'^0[xX][0-9a-fA-F]{3,6}$', string):
        return True
    return False


# Used for getting user by user id in given server
def get_user_by_id(server, user_id):
    return server.get_member(user_id)


# Attempts to return a user given their ID or Tag
def get_user(server, user_text):
    # By ID
    if re.fullmatch(r"[0-9]{18}", user_text) is not None:
        return get_user_by_id(server, user_text)
    # By Tag
    elif re.fullmatch(r"<@[0-9]{18}>", user_text) is not None:
        return get_user_by_id(server, user_text[2:-1])
    else:
        return None


# Attempts to return a role given its ID or Tag
def get_role(server, role_text):
    # By ID
    if re.fullmatch(r"[0-9]{18}", role_text) is not None:
        return get_role_by_id(server, role_text)
    # By Tag
    elif re.fullmatch(r"<@&[0-9]{18}>", role_text) is not None:
        return get_role_by_id(server, role_text[3:-1])
    else:
        return None


# Used for getting a role by id in given server
def get_role_by_id(server, role_id):
    for role in server.roles:
        if role.id == role_id:
            return role


# Used for getting a discord color from a hex value
def get_color(color):
    return discord.Color(int(color, 16))


# Replies to a channel with a simple embed
async def simple_embed_reply(channel, title, description, hex_color=None):
    # Pick which color to use (if the function was passed a color)
    color = "0x751DDF" if hex_color is None else hex_color
    # Reply with a built embed
    await client.send_message(channel, embed=discord.Embed(title=title,
                                                           description=description,
                                                           color=discord.Color(int(color, 16))))


# Gets help - All of it, or specifics
async def get_help(message, name, commands, is_full_help):
    # Sets up an embed to return
    embed = discord.Embed(title="[" + name + " Help]", color=0x751DDF)
    # Parses the help message
    split_message = message.content.split(" ")
    # If it can be parsed as a specific command
    if is_full_help:
        # Get all the help
        help_texts = generate_help(commands)
        for help_title, help_description in help_texts:
            embed.add_field(name=help_title, value=help_description, inline=False)
    else:
        # Extract info and append to the embed
        help_title, help_description = generate_help(commands, split_message[1], get_command_useage=True)
        embed.add_field(name=help_title, value=help_description)
    # Return the embed
    await client.send_message(message.channel, embed=embed)


# Used to generate help, all of it or a specific command
def generate_help(commands, specific_command_alias=None, get_command_useage=False):
    # If it's not asking for a specific command, recursively return everything
    if specific_command_alias is None:
        generated_help = []
        for command_name in commands:
            generated_help.append(generate_help(commands, specific_command_alias=commands[command_name].aliases[0]))
        if len(generated_help) == 0:
            return [["Help Does Not Exist", "There is no help for this mod, as it has no commands"]]
        return generated_help
    # Otherwise, return help for a specific command
    else:
        # Figures out which command was called and begins building a help message
        command_name, command_list, command_help, command_useage = None, None, None, None
        for command_name in commands:
            command = commands[command_name]
            if command.is_alias(specific_command_alias):
                # Stores the command's info
                command_name, command_list, command_help = command.name, command.aliases, command.help
                if get_command_useage:
                    command_useage = command.useage
                break
        if command_name is None or command_list is None or command_help is None:
            # If passed something that doesn't exist, let them know
            return "Unknown Command", "\"" + specific_command_alias + "\" is not a known command."
        # Build the rest of the help by appending the command list
        message = command_name + " - "
        for command in command_list:
            message += command + ", "
        # Return the help message built
        return message[0:-2], command_help + (("\n" + command_useage) if get_command_useage else "")


# Parses commands from standard config
def parse_command_config(parent, parent_name, config):
    mod_config = DataManager.get_manager("mod_config").get_data()
    # TODO: Implement command cleaning
    # Generate config if it doesn't exist
    for command_name in config:
        if command_name not in mod_config[parent_name]["Command Perms"]:
            mod_config[parent_name]["Command Perms"][command_name] = {
                "Disabled Channels": [],
                "Disabled Servers": [],
                "Minimum Permissions": ""
            }
    DataManager.get_manager("mod_config").write_data(mod_config)
    # Delete old mods and commands?
    # Spawn commands based on config and return a dict with them
    return {command_name: (Command(parent, command_name, config[command_name]['Aliases'],
                                   config[command_name]["Enabled"],
                                   mod_config[parent_name]["Command Perms"][command_name]["Minimum Permissions"],
                                   config[command_name]['Help'],
                                   ''.join(use + "\n" for use in config[command_name]['Useage'])[0:-1],
                                   int(config[command_name]["Cool Down"]) if "Cool Down" in config[
                                       command_name] else 0))
            for command_name in config}
