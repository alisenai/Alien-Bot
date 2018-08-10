from Common import DataManager, Utils
from Common.Mod import Mod
import discord

try:
    from Mods.Economy import EconomyUtils
except ImportError:
    raise Exception("Economy mod not installed")


class Waifu(Mod):
    def __init__(self, mod_name, embed_color):
        # Config var init
        self.config = DataManager.JSON("Mods/Waifu/WaifuConfig.json")
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Init shop DB
        self.database = DataManager.add_manager("shop_database", "Mods/Waifu/Waifus.db",
                                                file_type=DataManager.FileType.SQL)
        # Generate and Update DB
        self.generate_db()
        # Super...
        super().__init__(mod_name, self.config.get_data("Mod Description"), self.commands, embed_color)

    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        server, channel, author = message.server, message.channel, message.author
        if command is self.commands["Claim Waifu Command"]:
            if len(split_message) > 2:
                user = Utils.get_user(server, split_message[1])
                if user is not None:
                    if user.id != author.id:
                        amount = split_message[2]
                        if amount.isdigit():
                            amount = int(amount)
                            user_cash = EconomyUtils.get_cash(server.id, author.id)
                            waifu_price = int(self.database.execute(
                                "SELECT price FROM '%s' WHERE user_id='%s'" % (server.id, user.id)
                            )[0]) + int(self.config.get_data("Claim Addition Amount"))
                            if user_cash >= amount:
                                if amount >= waifu_price:
                                    self.database.execute(
                                        "UPDATE '%s' SET owner_id='%s', price='%d' WHERE user_id='%s'" %
                                        (server.id, author.id, amount, user.id)
                                    )
                                    EconomyUtils.set_cash(server.id, user.id, user_cash - amount)
                                    await Utils.simple_embed_reply(channel, "[Waifu]",
                                                                   "You claimed %s for %d%s." %
                                                                   (str(user), amount, EconomyUtils.currency))
                                else:
                                    await Utils.simple_embed_reply(channel, "[Error]",
                                                                   "You must pay at least %d to claim them!" %
                                                                   waifu_price)
                            else:
                                await Utils.simple_embed_reply(channel, "[Error]",
                                                               "You don't have enough cash to do that.")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "Invalid amount supplied.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "You cannot claim yourself.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Waifu Info Command"]:
            user = author
            if len(split_message) > 1:
                given_user = Utils.get_user(server, split_message[1])
                if given_user is not None:
                    user = given_user
                else:
                    return await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
            embed = discord.Embed(title="[Waifu Info]", description="Waifu info for %s" % str(user),
                                  color=discord.Color(int("0x751DDF", 16)))
            waifus = ''.join([str(Utils.get_user(server, i)) + "\n" for i in self.database.execute(
                "SELECT user_id FROM '%s' WHERE owner_id='%s'" % (server.id, user.id)
            )])[:-1]
            waifus = "None" if waifus == '' else waifus
            price, claimed_by = tuple(self.database.execute(
                "SELECT price, owner_id FROM '%s' WHERE user_id='%s'" % (server.id, user.id)
            ))
            claimed_by_user = Utils.get_user(server, str(claimed_by))
            embed.add_field(name="Price", value=price, inline=True)
            embed.add_field(name="Claimed By", value=str(claimed_by_user), inline=True)
            embed.add_field(name="Waifus", value=waifus, inline=True)
            await Utils.client.send_message(channel, embed=embed)
        elif command is self.commands["Divorce Waifu Command"]:
            if len(split_message) > 1:
                user = Utils.get_user(server, split_message[1])
                if user is not None:
                    waifus = self.database.execute(
                        "SELECT user_id FROM '%s' WHERE owner_id='%s'" % (server.id, author.id)
                    )
                    if user.id in waifus:
                        waifu_cost_split = round(self.database.execute(
                            "SELECT price FROM '%s' WHERE user_id='%s' LIMIT 1" % (server.id, user.id)
                        )[0] / 2)
                        author_cash = EconomyUtils.get_cash(server.id, author.id)
                        user_cash = EconomyUtils.get_cash(server.id, user.id)
                        EconomyUtils.set_cash(server.id, user.id, user_cash + waifu_cost_split)
                        EconomyUtils.set_cash(server.id, author.id, author_cash + waifu_cost_split)
                        self.database.execute(
                            "UPDATE '%s' SET owner_id=NULL WHERE user_id='%s'" % (server.id, user.id)
                        )
                        await Utils.simple_embed_reply(channel, "[Divorce]",
                                                       "You divorced %s and received %d back!" %
                                                       (str(user), waifu_cost_split))
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "That is not one of your waifus.")
                    return
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")

    # Called when a member joins a server the bot is in
    async def on_member_join(self, member):
        server_id = member.server.id
        user_id = member.id
        known_users = self.database.execute("SELECT user_id from '%s'" % server_id)
        if user_id not in known_users:
            self.database.execute("INSERT INTO '%s' VALUES('%s', '%s', NULL)" % (
                server_id, user_id, str(self.config.get_data("Default Claim Amount"))
            ))

    # Generates the waifu DB
    def generate_db(self):
        for server in Utils.client.servers:
            self.database.execute(
                "CREATE TABLE IF NOT EXISTS '%s'(user_id TEXT UNIQUE, price DIGIT, owner_id TEXT)" % server.id
            )
            known_users = self.database.execute("SELECT user_id from '%s'" % server.id)
            for user in server.members:
                if user.id not in known_users:
                    self.database.execute("INSERT INTO '%s' VALUES('%s', '%s', NULL)" % (
                        server.id, user.id, str(self.config.get_data("Default Claim Amount"))
                    ))
