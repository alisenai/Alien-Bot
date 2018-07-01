import Utils
import random
import discord
import ModHandler
from Command import Command
from DataManager import DataManager

# TODO: Self-help (scroll down)
# Create a client object
client = discord.Client()
# Initialize the config data manager
configManager = DataManager("Config/Config.json")
# Load the config
config = configManager.get_data()
# Grab the bot's nickname
bot_nick = config['Nickname']
# bot_nick = Grab the bot's commands from the config
bot_commands = config['Commands']
# TODO: Implement the below
# bot_commands = []
# for command in config['Commands']:
#     bot_commands.append(Command(None, command, config['Commands'][command]['Aliases'], True, config['Commands'][command]['Help']))
# Build a list of bot command aliases
bot_command_aliases = [alias for command in bot_commands for alias in bot_commands[command]['Aliases']]
# Initialize database data manager
dataBaseManager = DataManager(config['SaveFile'])
# Initialize the mod handler
mod_handler = ModHandler.ModHandler(client, config['ModConfig'],
                                    bot_command_aliases, config['LoggingLevel'], config['EmbedColor'])
# Boolean to keep track of when it's safe to start parsing commands
mods_loaded = False


# TODO: Command class
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
            dataBaseManager.write_data(self.avatar, key='AvatarHash')
    # Pick a random status
    status = config['GameStatus'][random.randint(0, len(config['GameStatus']) - 1)]
    print("[Chose status \"" + status + "\"]")
    # Set status
    await client.change_presence(game=discord.Game(name=status))
    # Load mods, getting their names
    mods = await mod_handler.load_mods()


# TODO: Wait for mod handler to finish
# When a message is received by the bot
@client.event
async def on_message(message):
    channel = message.channel
    # Check if the message is a possible command
    if message.content[0:len(config['CommandPrefix'])] == config['CommandPrefix']:
        split_message = message.content.split(" ")
        # Check if the mod handler is ready to be worked with
        if mod_handler.is_done_loading():
            # Get the command without the pesky prefixes or parameters
            command = split_message[0][len(config['CommandPrefix']):]
            # Check if the command called was a bot command
            if command in bot_command_aliases:
                # Help command called
                if command in bot_commands['Help Command']['Aliases']:
                    # If it's help for something specific, parse as so
                    if len(split_message) > 1:
                        # If it's help for the bot
                        if split_message[1] == bot_nick:
                            raise Exception("Self-help not implemented yet!")
                        else:
                            # Let the mod handler deal with possible mod help
                            await mod_handler.command_called(client, message, command, is_help=True)
                    # Otherwise, it's a full general list and parse as so
                    else:
                        # Start building an embed
                        embed = discord.Embed(title="[Help]", color=0x751DDF)
                        embed.add_field(name=bot_nick, value="Default bot commands", inline=False)
                        mod_descriptions = mod_handler.get_mod_descriptions()
                        # Loop through all mods' descriptions and create their fields
                        for mod in mod_descriptions:
                            description = mod_descriptions[mod]
                            embed.add_field(name=mod, value=description, inline=False)
                        # Reply with the created embed
                        await client.send_message(channel, embed=embed)
                elif command in bot_commands['Channel Command']['Aliases']:
                    raise Exception("Not implemented yet!")
            else:
                # Not a bot command; use mod handler to parse the command
                await mod_handler.command_called(client, message, command)
        # Mod handler is not ready -> Let the author know
        else:
            await Utils.simple_embed_reply(client, channel, "[Error]", "The bot is still loading, please wait.")


# Used to get a printable version of the help commands
def get_help_command_text():
    # Build all the help commands
    help_command_text = ""
    for command in bot_commands['Help Command']['Aliases']:
        help_command_text += command + ", "
    # Return built text
    return help_command_text[0:-2]


# Setup the help command text function
ModHandler.get_help_command_text = get_help_command_text

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
