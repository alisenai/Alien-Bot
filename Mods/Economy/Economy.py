import Common.DataManager as DataManager
from Common import Utils
from Common.Mod import Mod
import datetime
import discord
import random
import time
import re


# TODO: Major commenting needed
class Economy(Mod):
    def __init__(self, mod_name, embed_color):
        # General var init
        self.users = {}
        self.roles = {}
        self.name = mod_name
        self.embed_color = embed_color
        # Config var init
        self.config = DataManager.JSON("Mods/Economy/EconomyConfig.json")
        # Database var init
        self.database = DataManager.add_manager("bank_database", "Mods/Economy/Bank.db",
                                                file_type=DataManager.FileType.SQL)
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
            user_cash = self.get_cash(server.id, user.id)
            user_bank = self.get_bank(server.id, user.id)
            user_rank = self.get_rank(server.id, user.id)
            rank_text = str(user_rank) + (
                "th" if 4 <= user_rank % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(user_rank % 10, "th"))
            user_worth = user_cash + user_bank
            embed = discord.Embed(title="[" + str(user) + "]", description="Server Rank: " + str(rank_text),
                                  color=discord.Color(int("0x751DDF", 16)))
            embed.add_field(name="Cash", value=str(user_cash) + self.config.get_data("Currency"), inline=True)
            embed.add_field(name="Bank", value=str(user_bank) + self.config.get_data("Currency"), inline=True)
            embed.add_field(name="Net Worth", value=str(user_worth) + self.config.get_data("Currency"), inline=True)
            await Utils.client.send_message(channel, embed=embed)
        elif command is self.commands["Set Success Rate Command"]:
            if len(split_message) > 2:
                income_command = split_message[1]
                new_rate = split_message[2]
                if income_command == "slut" or "work" or "crime":
                    income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                    if new_rate.isdigit():
                        new_rate = int(new_rate)
                        if 0 <= new_rate <= 100:
                            economy_config = self.config.get_data()
                            economy_config["Commands"][income_command]["Success Rate"] = new_rate
                            self.config.write_data(economy_config)
                            await Utils.simple_embed_reply(channel, "[Success]", "`" + income_command +
                                                           "` success rate set to " + str(new_rate) + "%.")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]",
                                                           "Success rate parameter not between 0 and 100.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]",
                                                       "Success rate parameter is incorrect.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Income command parameter not supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Deposit Command"]:
            if len(split_message) > 1:
                deposit_amount = split_message[1]
                user_cash = self.get_cash(server.id, author.id)
                user_bank = self.get_bank(server.id, author.id)
                if user_cash != 0:
                    if deposit_amount.isdigit():
                        deposit_amount = int(deposit_amount)
                        if user_cash >= deposit_amount:
                            self.set_cash(server.id, author.id, user_cash - deposit_amount)
                            self.set_bank(server.id, author.id, user_bank + deposit_amount)
                            await Utils.simple_embed_reply(channel, "[" + str(author) + "]", "Deposited " +
                                                           str(deposit_amount) + self.config.get_data("Currency") +
                                                           " into your bank account.")
                        else:
                            await Utils.simple_embed_reply(channel, "[" + str(author) + "]",
                                                           "Sorry, but you don't have enough money to do that.")
                    elif deposit_amount == "all":
                        self.set_cash(server.id, author.id, 0)
                        self.set_bank(server.id, author.id, user_bank + user_cash)
                        await Utils.simple_embed_reply(channel, "[" + str(author) + "]", "Deposited " +
                                                       str(user_cash) + self.config.get_data("Currency") +
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
                user_cash = self.get_cash(server.id, author.id)
                user_bank = self.get_bank(server.id, author.id)
                if user_bank != 0:
                    if withdraw_amount.isdigit():
                        withdraw_amount = int(withdraw_amount)
                        if user_bank >= withdraw_amount:
                            self.set_cash(server.id, author.id, user_cash + withdraw_amount)
                            self.set_bank(server.id, author.id, user_bank - withdraw_amount)
                            await Utils.simple_embed_reply(channel, "[" + str(author) + "]", "Withdrew " +
                                                           str(withdraw_amount) + self.config.get_data("Currency") +
                                                           " into cash.")
                        else:
                            await Utils.simple_embed_reply(channel, "[" + str(author) + "]",
                                                           "Sorry, but you don't have enough money to do that.")
                    elif withdraw_amount == "all":
                        self.set_bank(server.id, author.id, 0)
                        self.set_cash(server.id, author.id, user_cash + user_bank)
                        await Utils.simple_embed_reply(channel, "[" + str(author) + "]", "Withdrew " +
                                                       str(user_cash) + self.config.get_data("Currency") +
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
                author_cash = self.get_cash(server.id, author.id)
                user_cash = self.get_cash(server.id, user.id)
                if user is None:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
                else:
                    if split_message[2].isdigit():
                        give_amount = int(split_message[2])
                        if author_cash < int(split_message[2]):
                            return await Utils.simple_embed_reply(channel, "[Error]",
                                                                  "You don't have enough cash to do that.")
                    elif split_message[2] == "all":
                        give_amount = self.get_cash(server.id, author.id)
                    else:
                        return await Utils.simple_embed_reply(channel, "[Error]", "Amount parameter is incorrect.")
                    self.set_cash(server.id, author.id, author_cash - give_amount)
                    self.set_cash(server.id, user.id, user_cash + give_amount)
                    await Utils.simple_embed_reply(channel, "[Error]", "You gave " + str(user) + " " + str(give_amount)
                                                   + self.config.get_data("Currency") + ".")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Award Command"]:
            if len(split_message) > 2:
                amount = split_message[1]
                if amount.isdigit():
                    amount = int(amount)
                    user = Utils.get_user(server, split_message[2])
                    if user is not None:
                        self.set_cash(server.id, user.id, self.get_cash(server.id, user.id) + amount)
                        await Utils.simple_embed_reply(channel, "[Error]",
                                                       "User `" + str(user) +
                                                       "` was awarded " + str(amount) +
                                                       self.config.get_data("Currency") + ".")
                    else:
                        given_role = Utils.get_role(server, ' '.join(split_message[2:]))
                        users = []
                        if given_role is not None:
                            for user in server.members:
                                if given_role in user.roles:
                                    self.set_cash(server.id, user.id, self.get_cash(server.id, user.id) + amount)
                                    users.append(user)
                            if len(users) > 0:
                                await Utils.simple_embed_reply(channel, "[Error]",
                                                               "Users with the role `" + str(given_role) +
                                                               "` were awarded " + str(amount) +
                                                               self.config.get_data("Currency") + ".")
                            else:
                                await Utils.simple_embed_reply(channel, "[Error]",
                                                               "No users are equipped with that role.")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "Invalid user or role supplied.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Amount parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Add Success Reply Command"]:
            await self.set_income_reply(message, is_success=True)
        elif command is self.commands["Add Failure Reply Command"]:
            await self.set_income_reply(message, is_success=False)
        elif command is self.commands["List Success Reply Command"]:
            await self.list_reply_commands(message, is_success=True)
        elif command is self.commands["List Failure Reply Command"]:
            await self.list_reply_commands(message, is_success=False)
        elif command is self.commands["Delete Success Reply Command"]:
            await self.delete_command_reply(message, True)
        elif command is self.commands["Delete Failure Reply Command"]:
            await self.delete_command_reply(message, False)
        elif command is self.commands["Work Command"]:
            await self.roll_income(message, "Work Command")
        elif command is self.commands["Slut Command"]:
            await self.roll_income(message, "Slut Command")
        elif command is self.commands["Crime Command"]:
            await self.roll_income(message, "Crime Command")
        # TODO: Determine how to calculate success chance
        elif command is self.commands["Rob Command"]:
            await Utils.simple_embed_reply(channel, "[Error]", "Awaiting method of calculating success rate")
        elif command is self.commands["Set Payout Command"]:
            await self.set_income_min_max(message, is_payout=True)
        elif command is self.commands["Set Deduction Command"]:
            await self.set_income_min_max(message, is_payout=False)

    # Sets a given user's cash balance from a given server
    def set_cash(self, server_id, user_id, amount):
        self.database.execute("UPDATE '" + server_id + "' SET cash=" + str(amount) + " WHERE user='" + user_id + "'")

    # Sets a given user's bank balance from a given server
    def set_bank(self, server_id, user_id, amount):
        self.database.execute("UPDATE '" + server_id + "' SET bank=" + str(amount) + " WHERE user='" + user_id + "'")

    # Gets a given user's cash balance from a given server
    def get_cash(self, server_id, user_id):
        return int(self.database.execute("SELECT cash FROM '" + server_id + "' WHERE user='" + user_id +
                                         "' LIMIT 1")[0])

    # Gets a given user's bank balance from a given server
    def get_bank(self, server_id, user_id):
        return int(self.database.execute("SELECT bank FROM '" + server_id + "' WHERE user='" + user_id +
                                         "' LIMIT 1")[0])

    # Gets a given user's rank from a given server
    def get_rank(self, server_id, user_id):
        return int(self.database.execute("SELECT COUNT(user) FROM '" + server_id +
                                         "' WHERE bank + cash >= (SELECT bank + cash from '" + server_id +
                                         "' WHERE user='" + user_id + "')")[0])

    # TODO: Add max reply message count and length limits
    async def set_income_reply(self, message, is_success):
        server, channel, author = message.server, message.channel, message.author
        split_message = message.content.split(" ")
        if len(split_message) > 2:
            income_command = split_message[1]
            reply = message.content[len(split_message[0]) + len(split_message[1]) + 2:]
            if income_command == "slut" or "work" or "crime":
                income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                economy_config = self.config.get_data()
                reply_type = "Success" if is_success else "Failure"
                # Check to make sure that and {user_id}s supplied are valid
                for section in reply.split(" "):
                    if re.fullmatch(r"{[0-9]{18}}", section) is not None:
                        if Utils.get_user_by_id(server, section[1:-1]) is None:
                            return await Utils.simple_embed_reply(channel, "[Error]",
                                                                  "User ID `" + section[1:-1] + "` not found.")
                economy_config["Commands"][income_command][reply_type]["Messages"].append(reply)
                self.config.write_data(economy_config)
                await Utils.simple_embed_reply(message.channel, "[Success]", "Added `" + reply + "` to `" +
                                               income_command + "`'s replies.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter not supplied.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # TODO: Compress by putting the re-used code into a func
    # Called when a member joins a server the bot is in
    async def on_member_join(self, member):
        user_id = member.id
        server_id = member.server.id
        if len(self.database.execute("SELECT cash FROM '" + server_id + "' WHERE user=" + str(
                user_id) + " LIMIT 1")) == 0:
            self.database.execute("INSERT INTO '" + server_id + "' VALUES('" + user_id + "', " +
                                  str(self.config.get_data("Starting Balance")) + ", 0)")

    # Pics a random win/loss based on the command and prints a win/loss message respectively
    async def roll_income(self, message, command_name):
        server, channel, author = message.server, message.channel, message.author
        command_config = self.config.get_data(key="Commands")[command_name]
        user_cash = self.get_cash(server.id, author.id)
        # Pick success or failure
        win_mode, change_mode, balance_change = ("Success", "Payout", 1) if roll(
            int(self.config.get_data(key="Commands")[command_name]["Success Rate"])) else ("Failure", "Deduction", -1)
        balance_change_range = command_config[win_mode][change_mode]
        cash_change = random.randint(balance_change_range["Min"], balance_change_range["Max"]) * balance_change
        messages = command_config[win_mode]["Messages"]
        reply = messages[rng(len(messages) - 1)]
        self.set_cash(server.id, author.id, user_cash + cash_change)
        for section in reply.split(" "):
            if re.fullmatch(r"{[0-9]{18}}", section) is not None:
                reply = reply.replace(section, Utils.get_user_by_id(server, section[1:-1]).mention)
        await Utils.simple_embed_reply(channel, "[" + str(author) + "]", reply.replace("{amount}",
                                                                                       str(abs(cash_change)) +
                                                                                       self.config.get_data(
                                                                                           key="Currency")))

    async def error_cool_down(self, message, command):
        last_called = command.last_called(message.author.id)
        minutes, seconds = divmod(command.cool_down_seconds - (time.time() - last_called), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        days, hours, minutes, seconds = int(days), int(hours), int(minutes), int(seconds)
        # Turn x hours y minutes and z seconds into text format
        time_left_text = ((str(days) + "d ") if days != 0 else "") + \
                         ((str(hours) + "h ") if hours != 0 else "") + \
                         ((str(minutes) + "m ") if minutes != 0 else "") + \
                         ((str(seconds) + "s") if seconds != 0 else "1s")
        await Utils.simple_embed_reply(message.channel, str(message.author),
                                       "You can call " + command.name + " again in " + time_left_text + ".",
                                       self.embed_color)

    # Generates the bank DB
    def generate_db(self):
        for server in Utils.client.servers:
            self.database.execute("CREATE TABLE IF NOT EXISTS '" + server.id + "'(user TEXT, cash REAL, bank REAL)")
            for user in server.members:
                if len(self.database.execute("SELECT cash FROM '" + server.id + "' WHERE user=" + str(
                        user.id) + " LIMIT 1")) == 0:
                    self.database.execute("INSERT INTO '" + server.id + "' VALUES('" + user.id + "', 0, " +
                                          str(self.config.get_data("Starting Balance")) + ")")

    # Sets the range for a given income command
    async def set_income_min_max(self, message, is_payout):
        split_message = message.content.split(" ")
        success_type, change_type = ("Success", "Payout") if is_payout else ("Failure", "Deduction")
        if len(split_message) > 3:
            income_command, minimum, maximum = split_message[1], split_message[2], split_message[3]
            if income_command == "slut" or "work" or "crime":
                income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                if minimum.isdigit():
                    if maximum.isdigit():
                        # Make sure the minimum is lower than the maximum
                        minimum, maximum = (minimum, maximum) if minimum < maximum else (maximum, minimum)
                        economy_config = self.config.get_data()
                        min_max_config = economy_config["Commands"][income_command][success_type][change_type]
                        min_max_config["Min"], min_max_config["Max"] = int(minimum), int(maximum)
                        self.config.write_data(economy_config)
                        await Utils.simple_embed_reply(message.channel, "[Success]",
                                                       "The `" + income_command + "` now has a " + change_type +
                                                       " between " + minimum + " and " + maximum)
                    else:
                        await Utils.simple_embed_reply(message.channel, "[Error]",
                                                       "Maximum parameter is incorrect.")
                else:
                    await Utils.simple_embed_reply(message.channel, "[Error]",
                                                   "Minimum parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter not supplied.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # Deletes a success/failure reply message given an ID
    async def delete_command_reply(self, message, is_success):
        server, channel, author = message.server, message.channel, message.author
        split_message = message.content.split(" ")
        if len(split_message) > 2:
            reply_type = "Success" if is_success else "Failure"
            income_command, index = split_message[1], split_message[2]
            if income_command == "slut" or "work" or "crime":
                if index.isdigit():
                    income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                    economy_config = self.config.get_data()
                    messages = economy_config["Commands"][income_command][reply_type]["Messages"]
                    message_to_remove = messages[int(index)]
                    messages.remove(message_to_remove)
                    self.config.write_data(economy_config)
                    await Utils.simple_embed_reply(message.channel, "[Success]",
                                                   "Deleted `" + message_to_remove + "` from `" + income_command + "`.")
                else:
                    await Utils.simple_embed_reply(message.channel, "[Error]", "ID parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter not supplied.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")

    # Lists all the success or failure reply messages for an income command
    async def list_reply_commands(self, message, is_success):
        server, channel, author = message.server, message.channel, message.author
        split_message = message.content.split(" ")
        if len(split_message) > 1:
            reply_type = "Success" if is_success else "Failure"
            income_command = split_message[1]
            if income_command == "slut" or "work" or "crime":
                income_command = "Slut Command" if income_command == "slut" else "Work Command" if income_command == "work" else "Crime Command"
                current_index = 0
                embed = discord.Embed(title="[Reply Messages]", color=discord.Color(int("0x751DDF", 16)))
                messages = self.config.get_data(key="Commands")[income_command][reply_type]["Messages"]
                max_number_length = len(str(len(messages)))
                embed_text = ""
                for reply_message in messages:
                    current_index += 1
                    if len(reply_message) > 50 - max_number_length:
                        embed_text += reply_message[0: 50 - max_number_length - 3] + "...\n"
                    else:
                        embed_text += reply_message + "\n"
                embed.add_field(name="ID", value=''.join([str(i) + "\n" for i in range(current_index)]), inline=True)
                embed.add_field(name="Message", value=embed_text, inline=True)
                await Utils.client.send_message(channel, embed=embed)
            else:
                await Utils.simple_embed_reply(message.channel, "[Error]", "Income command parameter not supplied.")
        else:
            await Utils.simple_embed_reply(message.channel, "[Error]", "Insufficient parameters supplied.")


# Roll a True/Fall with a given success chance
def roll(success_percent_chance):
    if success_percent_chance > random.randint(0, 100):
        return True
    return False


# Returns a random number between 0 and max_value
def rng(max_value):
    # Some more RNG
    random.seed(random.randint(0, 1000))
    return random.randint(0, max_value)
