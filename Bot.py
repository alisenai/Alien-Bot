from Common import DataManager, Permissions, Utils
from Common.ModHandler import ModHandler
import threading
import asyncio
import discord
import random
import time

# Create a client object
client = discord.Client()
# Set global client object
Utils.client = client
# Initialize the config data manager and load the config
config = DataManager.add_manager("bot_config", "Config/config.json").get_data()
# Initialize database data manager
database_manager = DataManager.add_manager("database", config['Database'], file_type=DataManager.FileType.SQL)
# Initialize cool down data manager
cool_down_manager = DataManager.add_manager("commands", "Common/Command.db", file_type=DataManager.FileType.SQL)
# Initialize mod config manager
mod_config_manager = DataManager.add_manager("mod_config", "Config/ModConfigs.json")
# Load permissions
Permissions.load_permissions()
# Grab the bot's nickname
Utils.bot_nick = config['Nickname']
# Grab command prefix
command_prefix = config['Command Prefix']
Utils.prefix = command_prefix
# Grab the bot's emoji
Utils.bot_emoji = config["Bot Emoji"]
# Grab default hex color
Utils.default_hex_color = int(config['Embed Color'], 16)
# Initialize the mod handler
mod_handler = ModHandler(config["Minimum Suggestion Permission"], Utils.default_hex_color)
# Add to Utils
Utils.mod_handler = mod_handler
# Boolean to keep track of when it's safe to start parsing commands
mods_loaded = False
# For ticks
loop = asyncio.get_event_loop()
tick_thread = None
# Shutdown variable
shutdown = False


# When the bot is ready to be worked with
@client.event
async def on_ready():
    global tick_thread
    print('[Login successful]')
    print('[Starting]')
    self = None
    # Change the bot nickname and get a "self" user
    for server in client.guilds:
        self = server.me
        # await client.change_nickname(self, config['Nickname'])
    # Change the avatar if it's not already set
    avatar_hash = self.avatar
    database_manager.execute("CREATE TABLE IF NOT EXISTS bot_data(name TEXT, value TEXT)")
    hash_from_database = database_manager.execute("SELECT value FROM bot_data WHERE name='avatar_hash'")
    if len(hash_from_database) != 0 and hash_from_database[0] == avatar_hash:
        print("[Skipping Profile Picture Update]")
    else:
        with open(config['Profile Picture'], 'rb') as f:
            print("[Attempting Profile Picture Update]")
            try:
                client.user.edit(avatar=f.read())
                database_manager.execute("INSERT OR IGNORE INTO bot_data VALUES('avatar_hash', '" + str(avatar_hash + "") + "')")
                print("[Updated Profile Picture]")
            except discord.errors.HTTPException:
                print("[Skipping Profile Picture Update (Throttled)]")
    # Pick a random status
    status = config['Game Status'][random.randint(0, len(config['Game Status']) - 1)]
    print("[Chose status \"" + status + "\"]")
    # Set status
    game = discord.Game(status)
    await client.change_presence(status=discord.Status.do_not_disturb, activity=game)
    # Load mods
    await mod_handler.load_mods()
    # Start main loop
    tick_thread = threading.Thread(target=tick)
    tick_thread.start()


# Calls ticks throughout the bot once a second
def tick():
    minute_timer = 0
    while not shutdown:
        time.sleep(1)
        loop.create_task(mod_handler.second_tick())
        minute_timer += 1
        if minute_timer == 60:
            minute_timer = 0
            loop.create_task(mod_handler.minute_tick())


# When a message is received by the bot
@client.event
async def on_message(message):
    global shutdown
    # Check if the message is a possible command
    if message.content[0:len(command_prefix)] == command_prefix:
        # Check if the mod handler is ready to be worked with
        if mod_handler.is_done_loading():
            if message.content == command_prefix + "<3":
                await message.channel.send(config["Bot Emoji"])
            else:
                try:
                    # Not a bot command; use mod handler to parse the command
                    await mod_handler.command_called(message, message.content.split(" ")[0][len(command_prefix):])
                # Handle exceptions, stopping and restarting
                except Exception as e:
                    shutdown = True
                    print("[Cleaning threads]")
                    tick_thread.join()
                    print("[Logging out]")
                    await client.logout()
                    if e.args[0] != "Stop Bot":
                        # For DEBUG
                        # print("Ungraceful error caught", e)
                        raise e
                        # TODO: Restarting on error or command / special exception
                        # shutdown = False
                        # print("[Restarting]")
                        # login()
        # Mod handler is not ready -> Let the author know
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "The bot is still loading, please wait.")
    await mod_handler.message_received(message)


# Called when the bot joins a server
@Utils.client.event
async def on_server_join(server):
    await mod_handler.on_server_join(server)


# Called when a member joins a server
@Utils.client.event
async def on_member_join(member):
    await mod_handler.on_member_join(member)


# Called when a message is deleted
@Utils.client.event
async def on_message_delete(message):
    await mod_handler.on_message_delete(message)


# Called when a user's VoiceState changes
@Utils.client.event
async def on_voice_state_update(before, after):
    await mod_handler.on_voice_state_update(before, after)


def login():
    # Make sure there is a token in the config
    print("[Attempting to login]")
    try:
        if config['Token'] == "TOKEN":
            print("Please set a token in the config file")
        else:
            # Run the bot with the token
            client.run(config['Token'])
    except discord.errors.ClientException:
        print("[Could not login]")


login()
