from Common import DataManager, Utils
from Mods.Economy import EconomyUtils
from datetime import date, timedelta
from Common.Mod import Mod
import calendar
import discord
import time


# TODO: Major commenting needed
# TODO: "" + x + "" -> %
class Economy(Mod):
    def __init__(self, mod_name, embed_color):
        # General var init
        self.name = mod_name
        self.embed_color = embed_color
        self.applied_interest = False
        # Config var init
        self.config = DataManager.JSON("Mods/Economy/EconomyConfig.json")
        # Init the bank DB for mods to use
        EconomyUtils.init_database()
        # Set the currency for mods to use
        EconomyUtils.currency = self.config.get_data("Currency")
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Generate and Update DB
        self.generate_db()
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        server, channel, author = message.server, message.channel, message.author
        if command is self.commands["Set Currency Command"]:
            if len(split_message) > 1:
                self.config.write_data(split_message[1], key="Currency")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Currency parameter not supplied.")
        elif command is self.commands["Set Starting Balance Command"]:
            if len(split_message) > 1:
                starting_balance = split_message[1]
                if starting_balance.isdigit():
                    self.config.write_data(int(starting_balance), key="Starting Balance")
                    await Utils.simple_embed_reply(channel, "[Success]",
                                                   "Starting balance set to `" + starting_balance + "`.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]",
                                                   "Starting balance command parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]",
                                               "Starting balance command parameter not supplied.")
        elif command is self.commands["Balance Command"]:
            user = author
            if len(split_message) > 1:
                given_user = Utils.get_user(server, split_message[1])
                if given_user is not None:
                    user = given_user
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
            user_cash = EconomyUtils.get_cash(server.id, user.id)
            user_bank = EconomyUtils.get_bank(server.id, user.id)
            user_rank = EconomyUtils.get_rank(server.id, user.id)
            rank_text = Utils.add_number_abbreviation(user_rank)
            user_worth = user_cash + user_bank
            embed = discord.Embed(title=" [" + str(user) + "]",
                                  description="Server Rank: " + str(rank_text),
                                  color=discord.Color(int("0x751DDF", 16)))
            embed.add_field(name="Cash", value=str(user_cash) + EconomyUtils.currency, inline=True)
            embed.add_field(name="Bank", value=str(user_bank) + EconomyUtils.currency, inline=True)
            embed.add_field(name="Net Worth", value=str(user_worth) + EconomyUtils.currency, inline=True)
            await Utils.client.send_message(channel, embed=embed)
        elif command is self.commands["Deposit Command"]:
            if len(split_message) > 1:
                deposit_amount = split_message[1]
                user_cash = EconomyUtils.get_cash(server.id, author.id)
                user_bank = EconomyUtils.get_bank(server.id, author.id)
                if user_cash != 0:
                    if deposit_amount.isdigit():
                        deposit_amount = int(deposit_amount)
                        if user_cash >= deposit_amount:
                            EconomyUtils.set_cash(server.id, author.id, user_cash - deposit_amount)
                            EconomyUtils.set_bank(server.id, author.id, user_bank + deposit_amount)
                            await Utils.simple_embed_reply(channel, "[" + str(author) + "]", "Deposited " +
                                                           str(deposit_amount) + EconomyUtils.currency +
                                                           " into your bank account.")
                        else:
                            await Utils.simple_embed_reply(channel, "[" + str(author) + "]",
                                                           "Sorry, but you don't have enough money to do that.")
                    elif deposit_amount == "all":
                        EconomyUtils.set_cash(server.id, author.id, 0)
                        EconomyUtils.set_bank(server.id, author.id, user_bank + user_cash)
                        await Utils.simple_embed_reply(channel, "[" + str(author) + "]", "Deposited " +
                                                       str(user_cash) + EconomyUtils.currency +
                                                       " into your bank account.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Amount parameter is incorrect.")
                else:
                    await Utils.simple_embed_reply(channel, "[" + str(author) + "]",
                                                   "Sorry, but you don't have any money to deposit.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Amount command parameter not supplied.")
        elif command is self.commands["Withdraw Command"]:
            if len(split_message) > 1:
                withdraw_amount = split_message[1]
                user_cash = EconomyUtils.get_cash(server.id, author.id)
                user_bank = EconomyUtils.get_bank(server.id, author.id)
                if user_bank != 0:
                    if withdraw_amount.isdigit():
                        withdraw_amount = int(withdraw_amount)
                        if user_bank >= withdraw_amount:
                            EconomyUtils.set_cash(server.id, author.id, user_cash + withdraw_amount)
                            EconomyUtils.set_bank(server.id, author.id, user_bank - withdraw_amount)
                            await Utils.simple_embed_reply(channel, "[" + str(author) + "]", "Withdrew " +
                                                           str(withdraw_amount) + EconomyUtils.currency +
                                                           " into cash.")
                        else:
                            await Utils.simple_embed_reply(channel, "[" + str(author) + "]",
                                                           "Sorry, but you don't have enough money to do that.")
                    elif withdraw_amount == "all":
                        EconomyUtils.set_bank(server.id, author.id, 0)
                        EconomyUtils.set_cash(server.id, author.id, user_cash + user_bank)
                        await Utils.simple_embed_reply(channel, "[" + str(author) + "]", "Withdrew " +
                                                       str(user_bank) + EconomyUtils.currency +
                                                       " into cash.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Amount parameter is incorrect.")
                else:
                    await Utils.simple_embed_reply(channel, "[" + str(author) + "]",
                                                   "Sorry, but you don't have any money to withdraw.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Amount command parameter not supplied.")
        elif command is self.commands["Give Command"]:
            if len(split_message) > 2:
                user = Utils.get_user(server, split_message[1])
                author_cash = EconomyUtils.get_cash(server.id, author.id)
                user_cash = EconomyUtils.get_cash(server.id, user.id)
                if user is not None:
                    if split_message[2].isdigit():
                        give_amount = int(split_message[2])
                        if author_cash < int(split_message[2]):
                            return await Utils.simple_embed_reply(channel, "[Error]",
                                                                  "You don't have enough cash to do that.")
                    elif split_message[2] == "all":
                        give_amount = EconomyUtils.get_cash(server.id, author.id)
                    else:
                        return await Utils.simple_embed_reply(channel, "[Error]", "Amount parameter is incorrect.")
                    EconomyUtils.set_cash(server.id, author.id, author_cash - give_amount)
                    EconomyUtils.set_cash(server.id, user.id, user_cash + give_amount)
                    await Utils.simple_embed_reply(channel, "[Error]", "You gave " + str(user) + " " + str(give_amount)
                                                   + EconomyUtils.currency + ".")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        # TODO: Optimize this?
        elif command is self.commands["Leaderboard Command"]:
            page = 1
            if len(split_message) > 1:
                page = split_message[1]
                if page.isdigit():
                    page = int(page)
                else:
                    return await Utils.simple_embed_reply(channel, "[Error]", "Page number parameter is incorrect.")
            user_rank_order = EconomyUtils.database_execute(
                "SELECT user FROM '" + server.id + "' ORDER BY bank + cash DESC")
            max_page = int((len(user_rank_order) + 9) // 10)
            if page <= max_page:
                if (len(user_rank_order) + 10) / 10 >= page:
                    embed = discord.Embed(title="[" + str(server) + " Leaderboard]",
                                          color=discord.Color(int("0x751DDF", 16)))
                    for i in range(min(10, len(user_rank_order))):
                        user_rank = (page - 1) * 10 + i
                        rank_text = Utils.add_number_abbreviation(user_rank + 1)
                        if len(user_rank_order) <= user_rank:
                            break
                        user_id = user_rank_order[user_rank]
                        user = Utils.get_user_by_id(server, user_id)
                        user_worth = EconomyUtils.get_bank(server.id, user_id) + EconomyUtils.get_cash(server.id,
                                                                                                       user_id)
                        embed.add_field(name=str(user) + " : " + rank_text,
                                        value=str(user_worth) + EconomyUtils.currency, inline=False)
                    embed.set_footer(text="Page " + str(page) + "/" + str(max_page))
                    await Utils.client.send_message(channel, embed=embed)
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Page number is too high.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]",
                                               "You can only view a page between 1 and " + str(max_page) + ".")
        elif command is self.commands["Bank Command"]:
            embed = discord.Embed(description="**The bank never goes Bankrupt!**",
                                  color=discord.Color(int("0x751DDF", 16)))
            # Remove this if?
            if server.icon is None:
                embed.set_author(name="%s Bank" % str(server),
                                 icon_url=author.default_avatar_url)
            else:
                embed.set_author(name="%s Bank" % str(server),
                                 icon_url="https://media.discordapp.net/icons/%s/%s.jpg" % (server.id, server.icon))
            embed.set_thumbnail(url=self.config.get_data("Bank Icon Url"))
            total_balance = int(EconomyUtils.database_execute("SELECT SUM(bank + cash) FROM `" + server.id + "`")[0])
            embed.add_field(name="Balance:",
                            value=str(total_balance) + EconomyUtils.currency, inline=True)
            embed.add_field(name="Interest:", value=str(self.config.get_data("Interest Rate")))
            embed.set_footer(text="%s" % str(time.strftime("%m-%d-%Y")))
            await Utils.client.send_message(channel, embed=embed)
        elif command is self.commands["Award Command"]:
            await self.award_take(message, True)
        elif command is self.commands["Take Command"]:
            await self.award_take(message, False)

    async def award_take(self, message, is_award):
        server, channel, author = message.server, message.channel, message.author
        split_message = message.content.split(" ")
        mode_text, mode_change = ("awarded", 1) if is_award else ("deducted", -1)
        if len(split_message) > 2:
            amount = split_message[1]
            if amount.isdigit():
                amount = int(amount)
                user = Utils.get_user(server, split_message[2])
                if user is not None:
                    EconomyUtils.set_cash(server.id, user.id,
                                          EconomyUtils.get_cash(server.id, user.id) + amount * mode_change)
                    await Utils.simple_embed_reply(channel, "[" + str(author) + "]",
                                                   "User `" + str(user) +
                                                   "` was " + mode_text + " " + str(amount) +
                                                   EconomyUtils.currency + ".")
                else:
                    given_role = Utils.get_role(server, ''.join(split_message[2]))
                    users = []
                    if given_role is not None:
                        for user in server.members:
                            if given_role in user.roles:
                                EconomyUtils.set_cash(server.id, user.id, EconomyUtils.get_cash(server.id, user.id) +
                                                      amount * mode_change)
                                users.append(user)
                        if len(users) > 0:
                            await Utils.simple_embed_reply(channel, "[" + str(author) + "]",
                                                           "Users with the role `" + str(given_role) +
                                                           "` were " + mode_text + " " + str(amount) +
                                                           EconomyUtils.currency + ".")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]",
                                                           "No users are equipped with that role.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Invalid user or role supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Amount parameter is incorrect.")
        else:
            await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")

    # Check if interest needs to be applied every minute
    async def minute_tick(self):
        yesterday = (date.today() - timedelta(1))
        # If yesterday was the end of the previous month, today is the first day of this month
        if calendar.monthrange(yesterday.year, yesterday.month)[1] == yesterday.day:
            # Check if interest has already been applied
            if not self.applied_interest:
                self.applied_interest = True
                # If not, apply interest
                for server in Utils.client.servers:
                    EconomyUtils.database_execute(
                        "UPDATE '%s' SET bank=bank*%f" % (server.id, 1 + self.config.get_data("Interest Rate"))
                    )
        else:
            # Allow interest to be applied since at least 1 day has passed since it should of been applied previously
            self.applied_interest = False

    # Called when the bot joins a server
    @Utils.client.event
    async def on_server_join(self, server):
        EconomyUtils.database_execute(
            "CREATE TABLE IF NOT EXISTS '%s'(user TEXT, cash REAL, bank REAL)" % server.id
        )
        for user in server.members:
            if not EconomyUtils.user_exists(server.id, user.id):
                EconomyUtils.database_execute("INSERT INTO '%s' VALUES('%s', 0, '%s')" % (
                    server.id, user.id, str(self.config.get_data("Starting Balance"))
                ))

    # Called when a member joins a server the bot is in
    @Utils.client.event
    async def on_member_join(self, member):
        server_id = member.server.id
        user_id = member.id
        if not EconomyUtils.user_exists(server_id, user_id):
            EconomyUtils.database_execute("INSERT INTO '%s' VALUES('%s', 0, '%s')" % (
                server_id, user_id, str(self.config.get_data("Starting Balance"))
            ))

    # Generates the bank DB
    def generate_db(self):
        for server in Utils.client.servers:
            EconomyUtils.database_execute(
                "CREATE TABLE IF NOT EXISTS '%s'(user TEXT, cash REAL, bank REAL)" % server.id
            )
            for user in server.members:
                if not EconomyUtils.user_exists(server.id, user.id):
                    EconomyUtils.database_execute("INSERT INTO '%s' VALUES('%s', 0, '%s')" % (
                        server.id, user.id, str(self.config.get_data("Starting Balance"))
                    ))
