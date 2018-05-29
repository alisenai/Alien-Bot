from DataManager import DataManager
import ModHandler
import discord
import random

# Create a client object
client = discord.Client()
# Initialize the config data manager
configManager = DataManager("Config/config.json")
# Load the config
config = configManager.get_data()
# Grab the bot's nickname
bot_nick = config['Nickname']
# bot_nick = Grab the bot's commands from the config
bot_commands = config['Commands']
# Build a list of bot command aliases
bot_command_aliases = [alias for command in bot_commands for alias in bot_commands[command]['Aliases']]
# Initialize database data manager
dataBaseManager = DataManager(config['SaveFile'])
# Initialize the mod handler
mod_handler = ModHandler.ModHandler(client, config['EnabledMods'],
                                    bot_command_aliases, config['LoggingLevel'], config['EmbedColor'])


# When the bot is ready to be worked with
@client.event
async def on_ready():
    print('[Login successful]')
    print('[Starting]')
    self = None
    # Change the bot nickname and get a "self" user
    for server in client.servers:
        self = server.me
        await client.change_nickname(self, config['Nickname'])
    # Change the avatar if it's not already set
    pfp_hash = self.avatar
    if dataBaseManager.get_data('AvatarHash') == pfp_hash:
        print("[Skipping Profile Picture Update]")
    else:
        with open(config['ProfilePicture'], 'rb') as f:
            print("[Attempting Profile Picture]")
            try:
                await client.edit_profile(avatar=f.read())
                print("[Updated Profile Picture]")
            except discord.errors.HTTPException:
                print("[Skipping Profile Picture Update - Throttled]")
            dataBaseManager.write_data('AvatarHash', self.avatar)
    # Pick a random status
    status = config['GameStatus'][random.randint(0, len(config['GameStatus']) - 1)]
    print("[Chose status \"" + status + "\"]")
    # Set status
    await client.change_presence(game=discord.Game(name=status))
    # Use the mod handler to load mods
    mods = await mod_handler.load_mods()
    # Get the known enabled mods from the config
    enabled_mods = config['EnabledMods']
    # Create an objects to set new config values
    new_enabled_mods = {}
    # Loop through all the mods
    for mod in mods:
        # Check if it's already in the config
        if mod in enabled_mods:
            # If so, keep the vale
            new_enabled_mods[mod] = enabled_mods[mod]
        else:
            # Otherwise it's new and auto-enable it
            new_enabled_mods[mod] = True
    configManager.write_data('EnabledMods', new_enabled_mods)


# When a message is received by the bot
@client.event
async def on_message(message):
    # Grab the messages's channel
    channel = message.channel
    # Check if the message is a possible command
    if message.content[0:len(config['CommandPrefix'])] == config['CommandPrefix']:
        # Split the message up for parsing
        split_message = message.content.split(" ")
        # If it's a possible command, parse it
        command = split_message[0][len(config['CommandPrefix']):]
        # Check if the command called was a bot command
        if command in bot_command_aliases:
            if command in bot_commands['Help Command']['Aliases']:
                # Start building an embed reply
                embed = discord.Embed(title="[Help]", color=0x751DDF)
                # If it's help for something specific, parse as so
                if len(split_message) > 1:
                    # If it's help for known mod command
                    if mod_handler.is_mod_command_alias(split_message[1]):
                        # Get help from that mod
                        await mod_handler.get_mod_help(split_message[1], message)
                    # If it's help for the bot
                    elif split_message[1] == bot_nick:
                        raise Exception("Self-help not implemented yet!")
                    # If it's help for a specific mod
                    elif mod_handler.is_mod_name(split_message[1]):
                        return
                    # If it's help for an unknown mod command
                    else:
                        # Get a printable version of the known help commands
                        help_command_text = get_help_command_text()
                        # Add a field to the reply embed
                        embed.add_field(name="Unknown mod or command - " + split_message[1] + "",
                                        value="Try: " + help_command_text + ".")
                # Otherwise, it's a full general list and parse as so
                else:
                    # Add a field for the main bot commands
                    embed.add_field(name=bot_nick, value="Default bot commands", inline=False)
                    # Get all the mods' descriptions
                    mod_descriptions = mod_handler.get_mod_descriptions()
                    # Loop through all mods' descriptions and create their fields
                    for mod in mod_descriptions:
                        # Grab the description
                        description = mod_descriptions[mod]
                        # Add a field
                        embed.add_field(name=mod, value=description, inline=False)
                # Reply with the created embed
                await client.send_message(channel, embed=embed)
        else:
            # Use mod handler to parse the command
            await mod_handler.command_called(client, message, command)


# Used to get a printable version of the help commands
def get_help_command_text():
    help_command_text = ""
    # Build all the help commands
    for command in bot_commands['Help Command']['Aliases']:
        help_command_text += command + ", "
    # Return built text
    return help_command_text[0:-2]


# Make sure there is a token in the config
print("[Attempting to login]")
try:
    if config['Token'] == "TOKEN":
        print("Please add a token in the config file")
    else:
        # Run the bot with the token
        client.run(config['Token'])
except discord.errors.ClientException:
    print("[Could not login]")
