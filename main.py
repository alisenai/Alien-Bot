import DBManager
import modHandler
import discord
import json

config = json.loads("".join(open("config.json", encoding="utf-8").readlines()))
# print(config["Token"])

client = discord.Client()

mod_handler = modHandler.ModHandler(client, config['LoggingLevel'], config['HelpCommands'], config['EmbedColor'])


@client.event
async def on_ready():
    print('[Starting]')
    self = None
    for server in client.servers:
        self = server.me
        await client.change_nickname(self, config['Nickname'])

    pfp_hash = self.avatar
    if DBManager.get_data('AvatarHash') == pfp_hash:
        print("[Skipping Profile Picture Update]")
    else:
        with open(config['ProfilePicture'], 'rb') as f:
            print("[Attempting Profile Picture]")
            try:
                await client.edit_profile(avatar=f.read())
                print("[Updated Profile Picture]")
            except discord.errors.HTTPException:
                print("[Skipping Profile Picture Update - Throttled]")
            DBManager.save_data('AvatarHash', self.avatar)

    await client.change_presence(game=discord.Game(name=config['GameStatus']))
    await mod_handler.load_mods()


@client.event
async def on_message(message):
    if message.content[0:len(config['CommandPrefix'])] == config['CommandPrefix']:
        command = message.content[len(config['CommandPrefix']):].split(" ")[0]
        await mod_handler.message_received(client, message, command)

client.run(config['Token'])
