from Common import DataManager, Utils
from Common.Mod import Mod
import discord
import asyncio
import time
import re

try:
    from Mods.Economy import EconomyUtils
except ImportError:
    raise Exception("Economy mod not installed")


# TODO: Support multiple servers
class Shops(Mod):
    def __init__(self, mod_name, embed_color):
        # Config var init
        self.config = DataManager.JSON("Mods/Shops/ShopsConfig.json")
        self.delete_delay = self.config.get_data("Message Delete Delay")
        # Init shop DB
        self.database = DataManager.add_manager("shop_database", "Mods/Shops/Shops.db",
                                                file_type=DataManager.FileType.SQL)
        # Create a shop table withing the DB if there isn't one
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS shops(channel_id TEXT UNIQUE, shop_name TEXT, is_purge BIT)"
        )
        self.database.execute(
            "CREATE TABLE IF NOT EXISTS messages(shop_name TEXT UNIQUE, message_id TEXT, channel_id TEXT)"
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
                        """CREATE TABLE IF NOT EXISTS '%s'(role_id TEXT UNIQUE, 
                        price NUMERIC, time_added REAL, duration REAL)""" % shop_name
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
            shop_names = []
            info = self.database.execute("SELECT channel_id, shop_name FROM shops")
            known_channels = [channel.id for channel in server.channels]
            for i in range(0, len(info), 2):
                if info[i] in known_channels:
                    shop_names.append(info[i + 1])
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
                            self.database.execute("DELETE FROM messages WHERE shop_name='%s'" % shop_name)
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
                shop_name, price, duration, role_text = split_message[1], split_message[2].lower(), split_message[3], \
                                                        split_message[4]
                if is_valid_shop_name(shop_name):
                    if self.shop_exists(shop_name):
                        if Utils.isfloat(duration) or duration == "permanent":
                            duration = -1 if duration == "permanent" or 0 else float(duration)
                            if price.isdigit():
                                price = int(price)
                                role = Utils.get_role(server, role_text)
                                if role is not None:
                                    role_ids = [name.lower() for name in
                                                self.database.execute("SELECT role_id FROM '%s'" % shop_name)]
                                    role_names = [str(Utils.get_role_by_id(server, role_id)) for role_id in role_ids]
                                    if str(role).lower() not in role_names:
                                        self.database.execute(
                                            "INSERT INTO '%s' VALUES('%s', '%d', '%s', '%s')" % (
                                                shop_name, role.id, int(price), time.time(), duration)
                                        )
                                        await Utils.simple_embed_reply(
                                            channel, "[Shops]",
                                            "`%s` has been assigned to `%s` at the price of `%s` for `%s` hours." % (
                                                str(role), shop_name, str(price), str(
                                                    "infinite" if duration == -1 else duration
                                                )
                                            )
                                        )
                                        await self.update_messages()
                                    else:
                                        if role.id in role_ids:
                                            self.database.execute(
                                                "REPLACE INTO '%s' VALUES('%s', '%d', '%s', '%s')" % (
                                                    shop_name, role.id, int(price), time.time(), duration)
                                            )
                                            await Utils.simple_embed_reply(
                                                channel, "[Shops]",
                                                "The role `%s` within `%s` now has a price of `%s` for `%s` hours." % (
                                                    str(role), shop_name, str(price), str(
                                                        "infinite" if duration == -1 else duration
                                                    )
                                                )
                                            )
                                            await self.update_messages()
                                        else:
                                            await Utils.simple_embed_reply(
                                                channel, "[Error]",
                                                "Duplicate role names not allowed. (lowercase-checked)")
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
                if self.shop_exists(shop_name):
                    embed = await self.get_shop_embed(shop_name, server)
                    shop_message = await Utils.client.send_message(channel, embed=embed)
                    self.database.execute(
                        "REPLACE INTO messages VALUES('%s', '%s', '%s')" % (shop_name, shop_message.id, channel.id)
                    )
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "That shop doesn't exist.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Buy Command"]:
            if len(split_message) > 1:
                given_name = ' '.join(split_message[1:]).lower()
                shop = self.database.execute("SELECT shop_name FROM shops where channel_id='%s'" % message.channel.id)
                if len(shop) > 0:
                    shop = shop[0]
                    role_ids = self.database.execute("SELECT role_id FROM '%s'" % shop)
                    role_costs = self.database.execute("SELECT price FROM '%s'" % shop)
                    if len(role_ids) > 0:
                        role_names = [str(Utils.get_role_by_id(server, role_id)) for role_id in role_ids]
                        if given_name in [str(name).lower() for name in role_names]:
                            for i in range(len(role_ids)):
                                role_id, role_name, role_cost = role_ids[i], role_names[i], role_costs[i]
                                if role_name.lower() == given_name:
                                    user_cash = EconomyUtils.get_cash(server.id, author.id)
                                    if user_cash >= role_cost:
                                        EconomyUtils.set_cash(server.id, author.id, user_cash - role_cost)
                                        role = Utils.get_role_by_id(server, role_id)
                                        if role not in author.roles:
                                            await Utils.client.add_roles(author, role)
                                            await Utils.simple_embed_reply(channel, "[%s]" % shop,
                                                                           "You have purchased `%s`." % role_name)
                                        else:
                                            await Utils.simple_embed_reply(channel, "[Error]",
                                                                           "You already have that role.")
                                    else:
                                        await Utils.simple_embed_reply(channel, "[Error]",
                                                                       "You don't have enough cash to do that.")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "Role not found.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "No roles found.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Shop not found for this channel.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Delete Shop Role Command"]:
            if len(split_message) > 1:
                given_name = ' '.join(split_message[1:]).lower()
                shop = self.database.execute("SELECT shop_name FROM shops where channel_id='%s'" % channel.id)
                if len(shop) > 0:
                    shop = shop[0]
                    role_ids = self.database.execute("SELECT role_id FROM '%s'" % shop)
                    if len(role_ids) > 0:
                        role_names = [str(Utils.get_role_by_id(server, role_id)) for role_id in role_ids]
                        if given_name in [str(name).lower() for name in role_names]:
                            for i in range(len(role_ids)):
                                self.database.execute(
                                    "DELETE FROM '%s' WHERE role_name='%s'" % (shop, role_names[i])
                                )
                                await Utils.simple_embed_reply(channel, "[%s]" % shop,
                                                               "Role `%s` has been deleted from `%s`." % (role_names[i],
                                                                                                          shop))
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "Role not found.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "No roles found.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Shop not found for this channel.")
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

    async def update_messages(self):
        data = self.database.execute("SELECT * from messages")
        # Convert [a1, b1, c1, a2, b2, c2, ...] to [[a1, b1, c1], [a2, b2, c2], ...]
        messages = [[str(data[i * 3]), str(data[i * 3 + 1]), str(data[i * 3 + 2])] for i in range(len(data) // 3)]
        for message_info in messages:
            shop_name, message_id, channel_id = message_info[0], message_info[1], message_info[2]
            channel = Utils.client.get_channel(channel_id)
            message = await Utils.client.get_message(channel, message_id)
            server = message.server
            embed = await self.get_shop_embed(shop_name, server)
            await Utils.client.edit_message(message, embed=embed)

    async def get_shop_embed(self, shop_name, server):
        roles = self.database.execute("SELECT role_id, price FROM '%s' ORDER BY price DESC" % shop_name)
        # Convert [id1, cost1, id2, cost2, ...] to [[id1, cost1], [id2, cost2], ...]
        roles = [[roles[i * 2], str(roles[i * 2 + 1])] for i in range(len(roles) // 2)]
        embed = discord.Embed(title="[%s]" % shop_name,
                              color=discord.Color(int("0x751DDF", 16)))
        if len(roles) > 0:
            for role_info in roles:
                role = Utils.get_role_by_id(server, role_info[0])
                embed.add_field(name=str(role), value=role_info[1] + EconomyUtils.currency,
                                inline=True)
        else:
            embed.description = "No roles currently available."
        return embed

    # Deletes messages if their duration is up
    async def second_tick(self):
        shops = self.database.execute("SELECT shop_name FROM shops")
        current_time = time.time()
        for shop_name in shops:
            data = self.database.execute("SELECT time_added, duration, role_id FROM '%s'" % shop_name)
            # Convert [a1, b1, c1, a2, b2, c2, ...] to [[a1, b1, c1], [a2, b2, c2], ...]
            messages = [[float(data[i * 3]), float(data[i * 3 + 1]), str(data[i * 3 + 2])] for i in
                        range(len(data) // 3)]
            for message_info in messages:
                if message_info[1] != -1:
                    if current_time - message_info[0] >= message_info[1] * 60 * 60:
                        self.database.execute("DELETE FROM '%s' where role_id='%s'" % (shop_name, message_info[2]))
                        await self.update_messages()

    # Cleans up shops from deleted channels
    def verify_db(self):
        shop_channels = self.database.execute("SELECT channel_ID from shops")
        # Remove all existing channels from the shop_channels list
        for server in Utils.client.servers:
            for channel in server.channels:
                if channel.id in shop_channels:
                    shop_channels.remove(channel.id)
        # Delete any remaining channels as they don't exist (weren't removed previously)
        for channel in shop_channels:
            self.delete_shop_by_channel_id(channel)
            self.database.execute("DELETE FROM shops where channel_id='%s'" % channel)


# Prevents SQL Injection
def is_valid_shop_name(shop_name):
    return re.fullmatch(r"[A-Za-z0-9]*", shop_name)
