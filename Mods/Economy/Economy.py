import Common.DataManager as DataManager
from Common.Mod import Mod
from Common import Utils
import discord
import logging
import json


class Economy(Mod):
    def __init__(self, mod_name, embed_color):
        # General var init
        self.users = {}
        self.roles = {}
        self.name = mod_name
        self.embed_color = embed_color
        # Config var init
        self.config = json.loads("".join(open("Mods/Economy/EconomyConfig.json", encoding="utf-8").readlines()))
        # Database var init
        self.database = DataManager.add_manager("bank_database", "Mods/Economy/Bank.db",
                                                file_type=DataManager.FileType.SQL)
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config['Commands'])
        # Generate and Update DB
        self.generate_db()
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config['Mod Description'], self.commands, embed_color)

    async def command_called(self, message, command):
        server, channel, author = message.server, message.channel, message.author
        if command in self.commands["Balance command"]:
            await Utils.simple_embed_reply(channel, "Balance", self.database.execute("SELECT balance FROM " +
                                                                                     server + " WHERE user='" +
                                                                                     author.id + "'"))
            print("BAL COMMAND DEBUG")

    # Generates the bank DB and removes old data
    def generate_db(self):
        for server in Utils.client.servers:
            self.database.execute("CREATE TABLE IF NOT EXISTS '" + server.id + "'(user TEXT, balance TEXT, bank TEXT)")
            server_data = self.database.execute("SELECT user FROM '" + server.id + "'")
            user_ids = []
            for user in server.members:
                user_ids.append(user.id)
                if len(self.database.execute("SELECT balance FROM '" + server.id + "' WHERE user=" + str(
                        user.id) + " LIMIT 1")) == 0:
                    self.database.execute("INSERT INTO '" + server.id + "' VALUES(" + user.id + ", " + str(
                        self.config["Starting Balance"]) + ", 0)")
                    # Delete old data
                    # for user in server_data:
                    #     if user not in user_ids

    # Called when a member joins a server the bot is in
    async def on_member_join(self, member):
        pass
