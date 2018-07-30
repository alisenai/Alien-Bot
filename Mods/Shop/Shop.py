import asyncio
import re

import discord

from Common import Utils
from Common.Mod import Mod
from Common import DataManager
from Mods.Economy import EconomyUtils


class Shop(Mod):
    def __init__(self, mod_name, embed_color):
        # Config var init
        self.config = DataManager.JSON("Mods/Shop/ShopConfig.json")
        # Init shop DB
        self.database = DataManager.add_manager("shop_database", "Mods/Shop/Shop.db",
                                                file_type=DataManager.FileType.SQL)
        # Verify DB - Check for deleted channels that shops exist in
        self.verify_db()
        # Create a shop table withing the DB if there isn't one
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS shops(channel_id TEXT UNIQUE, shop_name TEXT)")
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        server, channel, author = message.server, message.channel, message.author
        if command is self.commands["Set Shop Command"]:
            if len(split_message) > 1:
                shop_name = split_message[1]
                if re.fullmatch(r"[A-Za-z0-9]*", shop_name):
                    # Drop old shop table if needed
                    self.delete_shop_by_channel_id(channel.id)
                    # Create new tables and rows
                    self.database.execute(
                        "CREATE TABLE IF NOT EXISTS %s(item_name TEXT UNIQUE, cash REAL, bank REAL)" % shop_name)
                    self.database.execute("REPLACE INTO shops VALUES('%s', '%s')" % (channel.id, shop_name))
                    await Utils.simple_embed_reply(channel, "[Shop Created]",
                                                   "`%s` has been assigned `%s.`" % (str(channel), shop_name))
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid shop name.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["List Shops Command"]:
            shop_names = self.database.execute("SELECT shop_name FROM shops")
            if len(shop_names) > 0:
                # Get the length of the largest number (EX: "100" = 3, "10" = 2)
                max_number_length = len(str(len(shop_names)))
                current_index = 0
                embed_text = ""
                for shop_name in shop_names:
                    current_index += 1
                    if len(shop_name) > 50 - max_number_length:
                        embed_text += shop_name[0: 50 - max_number_length - 3] + "...\n"
                    else:
                        embed_text += shop_name + "\n"
                embed = discord.Embed(title="[Shops]", color=discord.Color(int("0x751DDF", 16)))
                embed.add_field(name="ID", value=''.join([str(i) + "\n" for i in range(current_index)]), inline=True)
                embed.add_field(name="Shop Name", value=embed_text, inline=True)
                await Utils.client.send_message(channel, embed=embed)
            else:
                await Utils.simple_embed_reply(channel, "[Shops]", "There are no shops.")
        elif command is self.commands["Delete Shop Command"]:
            if len(split_message) > 1:
                shop_name = split_message[1]
                self.database.execute("DROP TABLE IF EXISTS '%s'" % shop_name)
                self.database.execute("DELETE FROM shops WHERE shop_name='%s'" % shop_name)
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")

    def delete_shop_by_channel_id(self, channel_id):
        # old_channel_drop = self.database.execute(
        #     """SELECT "DROP TABLE IF EXISTS '" || shop_name || "'" FROM shops WHERE channel_id='%s'""" % channel_id)
        old_channel = self.database.execute("SELECT shop_name FROM shops WHERE channel_id='%s' LIMIT 1" % channel_id)
        if len(old_channel) > 0:
            self.database.execute("DROP TABLE IF EXISTS '%s'" % old_channel[0])

    async def message_received(self, message):
        deletion_channels = self.database.execute("SELECT channel_id FROM shops")
        if message.channel.id in deletion_channels:
            # Since async, blocking doesn't matter
            await asyncio.sleep(3)
            await Utils.delete_message(message)

    # Cleans up shops from deleted channels
    def verify_db(self):
        shop_channels = self.database.execute("SELECT channel_ID from shops")
        for server in Utils.client.servers:
            for channel in server.channels:
                if channel.id in shop_channels:
                    shop_channels.remove(channel.id)
        for channel in shop_channels:
            self.delete_shop_by_channel_id(channel)
            self.database.execute("DELETE FROM shops where channel_id='%s'" % channel)
