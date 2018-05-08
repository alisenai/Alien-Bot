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
# Initialize database data manager
dataBaseManager = DataManager(config['SaveFile'])
# Initialize the mod handler
mod_handler = ModHandler.ModHandler(config['EnabledMods'], client, config['LoggingLevel'], config['HelpCommands'], config['EmbedColor'])


# TODO: Enable / Disable mods in config
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
    # Check if the message is a possible command
    if message.content[0:len(config['CommandPrefix'])] == config['CommandPrefix']:
        # If it's a possible command, parse it
        command = message.content[len(config['CommandPrefix']):].split(" ")[0]
        # Use mod handler to parse the command
        await mod_handler.command_called(client, message, command)


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
