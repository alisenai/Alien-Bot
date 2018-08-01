from Common import DataManager
from Common.Mod import Mod
from Common import Utils
import discord
import asyncio
import re

try:
    from Mods.Economy import EconomyUtils
except ImportError:
    raise Exception("Economy mod not installed")


class Shop(Mod):
    def __init__(self, mod_name, embed_color):
        # Config var init
        self.config = DataManager.JSON("Mods/Shop/ShopConfig.json")
        self.delete_delay = self.config.get_data("Message Delete Delay")
        # Init shop DB
        self.database = DataManager.add_manager("shop_database", "Mods/Shop/Shop.db",
                                                file_type=DataManager.FileType.SQL)
        # Create a shop table withing the DB if there isn't one
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS shops(channel_id TEXT UNIQUE, shop_name TEXT, is_purge BIT)"
        )
        # Verify DB - Check for deleted channels that shops exist in
        self.verify_db()
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
                if is_valid_shop_name(shop_name):
                    # Drop old shop table if needed
                    self.delete_shop_by_channel_id(channel.id)
                    # Create new tables and rows
                    self.database.execute(
                        "CREATE TABLE IF NOT EXISTS '%s'(role_id TEXT UNIQUE, price REAL, duration REAL)" % shop_name
                    )
                    self.database.execute("REPLACE INTO shops VALUES('%s', '%s', 0)" % (channel.id, shop_name))
                    await Utils.simple_embed_reply(
                        channel, "[Shop Created]", "`%s` has been assigned `%s.`" % (str(channel), shop_name)
                    )
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Shop parameter incorrect.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["List Shops Command"]:
            shop_names = self.database.execute("SELECT shop_name FROM shops")
            if len(shop_names) > 0:
                shop_text = ''.join([shop_name + "\n" for shop_name in shop_names])[:-1]
                await Utils.simple_embed_reply(channel, "[Shops]", shop_text)
            else:
                await Utils.simple_embed_reply(channel, "[Shops]", "No shops exist.")
        elif command is self.commands["Delete Shop Command"]:
            if len(split_message) > 1:
                shop_name = split_message[1]
                if is_valid_shop_name(shop_name):
                    shop_names = self.database.execute("SELECT shop_name FROM shops")
                    if len(shop_names) > 0:
                        if shop_name in shop_names:
                            self.database.execute("DROP TABLE IF EXISTS '%s'" % shop_name)
                            self.database.execute("DELETE FROM shops WHERE shop_name='%s'" % shop_name)
                            await Utils.simple_embed_reply(channel, "[Shops]", "Shop `%s` was deleted." % shop_name)
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "That shop doesn't exist.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "No shops exist.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Shop parameter incorrect.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Set Shop Role Command"]:
            if len(split_message) > 4:
                shop_name = split_message[1]
                price = split_message[2].lower()
                duration = split_message[3]
                role_text = split_message[4]
                if is_valid_shop_name(shop_name):
                    if self.shop_exists(shop_name):
                        if duration.isdigit() or duration == "permanent":
                            duration = -1 if duration == "permanent" or 0 else int(duration)
                            if price.isdigit():
                                price = int(price)
                                role = Utils.get_role(server, role_text)
                                if role is not None:
                                    self.database.execute(
                                        "REPLACE INTO '%s' VALUES(%s, %s, %s)" % (shop_name, role.id, price, duration))
                                    await Utils.simple_embed_reply(
                                        channel, "[Shops]",
                                        "`%s` has been assigned to `%s` at the price of `%s` for `%s` hours." % (
                                            str(role), shop_name, str(price), str(
                                                "infinite" if duration == -1 else duration
                                            )
                                        )
                                    )
                                else:
                                    await Utils.simple_embed_reply(channel, "[Error]", "That role doesn't exist.")
                            else:
                                await Utils.simple_embed_reply(channel, "[Error]", "Price parameter incorrect.")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "Duration parameter incorrect.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "That shop doesn't exist.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Shop parameter incorrect.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Toggle Shop Autodelete Command"]:
            if len(split_message) > 1:
                shop_name = split_message[1]
                if is_valid_shop_name(shop_name):
                    if self.shop_exists(shop_name):
                        new_value = int(
                            self.database.execute("SELECT is_purge FROM shops WHERE shop_name='%s'" % shop_name)[0]
                        ) ^ 1
                        self.database.execute(
                            "UPDATE shops SET is_purge='%d' WHERE shop_name='%s'" % (new_value, shop_name)
                        )
                        await Utils.simple_embed_reply(
                            channel, "[Shops]", "`%s`'s delete mode set to `%r`" % (shop_name, bool(new_value))
                        )
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "That shop doesn't exist.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Shop parameter incorrect.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Shop Command"]:
            if len(split_message) > 1:
                shop_name = split_message[1]
                roles = self.database.execute("SELECT role_id, price FROM '%s' ORDER BY price DESC" % shop_name)
                # Convert [id1, cost1, id2, cost2, id3, cost3, ...] to [[id1, cost1], [id2, cost2], [id3, cost3], ...]
                roles = [[roles[i * 2], str(roles[i * 2 + 1])] for i in range(len(roles) // 2)]
                embed = discord.Embed(title="[%s]" % shop_name,
                                      color=discord.Color(int("0x751DDF", 16)))
                for role_info in roles:
                    role = Utils.get_role_by_id(server, role_info[0])
                    embed.add_field(name=str(role), value=role_info[1] + EconomyUtils.currency, inline=True)
                await Utils.client.send_message(channel, embed=embed)
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")

    def delete_shop_by_channel_id(self, channel_id):
        # old_channel_drop = self.database.execute(
        #     """SELECT "DROP TABLE IF EXISTS '" || shop_name || "'" FROM shops WHERE channel_id='%s'""" % channel_id)
        old_channel = self.database.execute("SELECT shop_name FROM shops WHERE channel_id='%s' LIMIT 1" % channel_id)
        if len(old_channel) > 0:
            self.database.execute("DROP TABLE IF EXISTS '%s'" % old_channel[0])

    async def message_received(self, message):
        deletion_channels = self.database.execute("SELECT channel_id FROM shops where is_purge=1")
        if message.channel.id in deletion_channels:
            # Since async, blocking doesn't matter
            await asyncio.sleep(self.delete_delay)
            await Utils.delete_message(message)

    def shop_exists(self, shop_name):
        if is_valid_shop_name(shop_name):
            db_return = self.database.execute(
                "SELECT EXISTS(SELECT * FROM shops WHERE shop_name='%s' LIMIT 1)" % shop_name
            )
            if db_return == [1]:
                return True
        return False

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


def is_valid_shop_name(shop_name):
    return re.fullmatch(r"[A-Za-z0-9]*", shop_name)
