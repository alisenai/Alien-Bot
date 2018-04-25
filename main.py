import dataManager
import modHandler
import discord
import random
import json

# Create a client object
client = discord.Client()
# Load the config
config = json.loads("".join(open("Config/config.json", encoding="utf-8").readlines()))
# Initialize the data manager
dataManager.init(config['SaveFile'])
# Initialize the mod handler
mod_handler = modHandler.ModHandler(client, config['LoggingLevel'], config['HelpCommands'], config['EmbedColor'])


@client.event
# When the bot is ready to be worked with
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
    if dataManager.get_data('AvatarHash') == pfp_hash:
        print("[Skipping Profile Picture Update]")
    else:
        with open(config['ProfilePicture'], 'rb') as f:
            print("[Attempting Profile Picture]")
            try:
                await client.edit_profile(avatar=f.read())
                print("[Updated Profile Picture]")
            except discord.errors.HTTPException:
                print("[Skipping Profile Picture Update - Throttled]")
            dataManager.write_data('AvatarHash', self.avatar)
    # Pick a random status
    status = config['GameStatus'][random.randint(0, len(config['GameStatus']) - 1)]
    print("[Chose status \"" + status + "\"]")
    # Set status
    await client.change_presence(game=discord.Game(name=status))
    # Use the mod handler to load mods
    await mod_handler.load_mods()


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
