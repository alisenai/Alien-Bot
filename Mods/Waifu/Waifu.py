import re

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
        # Make sure all gifts follow a proper naming convention
        for gift_name in self.config.get_data("Gifts"):
            if not re.fullmatch(r"[A-Za-z0-9 ]*", gift_name):
                raise Exception("Waifu gift name \"%s\" can only contain spaces, A-Z, a-z, 0-9" % gift_name)
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Init DBs
        self.waifus_db = DataManager.add_manager("shop_database", "Mods/Waifu/Waifus.db",
                                                 file_type=DataManager.FileType.SQL)
        self.gifts_db = DataManager.add_manager("shop_database", "Mods/Waifu/Gifts.db",
                                                file_type=DataManager.FileType.SQL)
        # Generate and Update DB
        self.generate_db()
        # Super...
        super().__init__(mod_name, self.config.get_data("Mod Description"), self.commands, embed_color)

    # Called when a waifu command is called
    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        server, channel, author = message.server, message.channel, message.author
        if command is self.commands["Claim Command"]:
            if len(split_message) > 2:
                # Try and get a user from the passed arguments
                user = Utils.get_user(server, split_message[1])
                # Check if a user was found (arguments were valid)
                if user is not None:
                    # Check if the author is trying to claim themselves
                    if user.id != author.id:
                        amount = split_message[2]
                        # Check if the "Amount" parameter is a digit so it can be used correctly later
                        if amount.isdigit():
                            amount = int(amount)
                            user_cash = EconomyUtils.get_cash(server.id, author.id)
                            # Calculate the waifu price -> DB Waifu Price + Claim Addition Amount
                            waifu_price = int(self.waifus_db.execute(
                                "SELECT price FROM '%s' WHERE user_id='%s'" % (server.id, user.id)
                            )[0]) + int(self.config.get_data("Claim Addition Amount"))
                            # Check if the user has enough cash
                            if user_cash >= amount:
                                # Check if the given argument is at least the minimum waifu price
                                if amount >= waifu_price:
                                    # Set the user's (waifu) owner's ID in the DB
                                    self.waifus_db.execute(
                                        "UPDATE '%s' SET owner_id='%s', price='%d' WHERE user_id='%s'" %
                                        (server.id, author.id, amount, user.id)
                                    )
                                    # Deduct from the user's cash the amount they spent
                                    EconomyUtils.set_cash(server.id, user.id, user_cash - amount)
                                    # Tell them it was a successful waifu claim
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
            # Get the user this command is being called on - the author by default
            user = author
            if len(split_message) > 1:
                given_user = Utils.get_user(server, split_message[1])
                if given_user is not None:
                    user = given_user
                else:
                    return await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
            # Start a new embed for the info to be displayed on
            embed = discord.Embed(title="[Waifu Info]", description="Waifu info for %s" % str(user),
                                  color=discord.Color(int("0x751DDF", 16)))
            # Create text of the user's waifus from the DB
            waifus = ''.join([str(Utils.get_user(server, i)) + "\n" for i in self.waifus_db.execute(
                "SELECT user_id FROM '%s' WHERE owner_id='%s'" % (server.id, user.id)
            )])[:-1]
            waifus = "None" if waifus == '' else waifus
            # Grab the price and owner of the user from the Db
            gifts = self.config.get_data("Gifts")
            # Get gift names from gifts DB (Table names) for gift and pocket gifts text
            db_gift_names = [gift_name for gift_name in gifts]
            # db_gift_names = self.gifts_db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            # ---------- GIFT TEXT ----------
            gifts_text = ""
            pocket_text = ""
            for gift_name in db_gift_names:
                # Get the number of gifts of that type the user has
                gift_amount, pocket_amount = tuple(self.gifts_db.execute(
                    "SELECT amount, pocket_amount FROM '%s' WHERE server_id='%s' AND user_id='%s'" %
                    (gift_name, server.id, user.id)
                ))
                # If they have at least one of that gift, add it to the gift text
                if gift_amount > 0:
                    gifts_text += "%s x%d" % (gifts[gift_name]["Symbol"], gift_amount)
                if pocket_amount > 0:
                    pocket_text += "%s x%d" % (gifts[gift_name]["Symbol"], pocket_amount)
            # If the user doesn't have any gifts, set the text to "None"
            gifts_text = "None" if gifts_text == "" else gifts_text
            # If the user doesn't have any pocket gifts, set the text to "None"
            pocket_text = "None" if pocket_text == "" else pocket_text
            # Grab more info for the embed from the DB
            price, claimed_by, affinity, changes_of_heart, divorces = tuple(self.waifus_db.execute(
                "SELECT price, owner_id, affinity, changes_of_heart, divorces FROM '%s' WHERE user_id='%s'" %
                (server.id, user.id)
            ))
            # Grab user info - it will be "None" if it doesn't apply
            claimed_by_user = Utils.get_user(server, str(claimed_by))
            affinity_user = Utils.get_user(server, str(affinity))
            # Generate the rest of the embed
            embed.add_field(name="Claimed By", value=str(claimed_by_user), inline=True)
            embed.add_field(name="Price", value=price, inline=True)
            embed.add_field(name="Divorces", value=divorces, inline=True)
            embed.add_field(name="Gifts", value=gifts_text, inline=False)
            embed.add_field(name="Pocket", value=pocket_text, inline=False)
            embed.add_field(name="Affinity", value=str(affinity_user), inline=True)
            embed.add_field(name="Changes of Heart", value=changes_of_heart, inline=True)
            embed.add_field(name="Waifus", value=waifus, inline=True)
            # Send the embed as the reply
            await Utils.client.send_message(channel, embed=embed)
        # TODO: Delete marriage role
        elif command is self.commands["Divorce Command"]:
            if len(split_message) > 1:
                # Try and get a user from the passed arguments
                user = Utils.get_user(server, split_message[1])
                # Check if a user was found (arguments were valid)
                if user is not None:
                    # Get the message author's waifus from DB
                    waifus = self.waifus_db.execute(
                        "SELECT user_id FROM '%s' WHERE owner_id='%s'" % (server.id, author.id)
                    )
                    # Check if the passed user is actually one of the author's waifus
                    if user.id in waifus:
                        # Calculate how much each user will get back from the divorce
                        waifu_cost_split = round(self.waifus_db.execute(
                            "SELECT price FROM '%s' WHERE user_id='%s' LIMIT 1" % (server.id, user.id)
                        )[0] / 2)
                        # Grab cash values of each user and update the balance with the divorce money
                        author_cash = EconomyUtils.get_cash(server.id, author.id)
                        user_cash = EconomyUtils.get_cash(server.id, user.id)
                        EconomyUtils.set_cash(server.id, user.id, user_cash + waifu_cost_split)
                        EconomyUtils.set_cash(server.id, author.id, author_cash + waifu_cost_split)
                        # Remove the owner from the user
                        self.waifus_db.execute(
                            "UPDATE '%s' SET owner_id=NULL WHERE user_id='%s'" % (server.id, user.id)
                        )
                        # Increase author divorce count
                        self.waifus_db.execute(
                            "UPDATE '%s' SET divorces=divorces+1 WHERE user_id='%s'" % (server.id, author.id)
                        )
                        # Let the user know it was a successful divorce and how much they got back
                        await Utils.simple_embed_reply(channel, "[Divorce]",
                                                       "You divorced %s and received %d back!" %
                                                       (str(user), waifu_cost_split))
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "That is not one of your waifus.")
                        command.reset_cool_down(author.id)
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
                    command.reset_cool_down(author.id)
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
                command.reset_cool_down(author.id)
        elif command is self.commands["Gifts Command"]:
            # Config
            gifts_per_page = 6
            # Default 1st page, or set it as the passed argument if it exists and is valid
            page = 1
            if len(split_message) > 1:
                if split_message[1].isdigit():
                    page = int(split_message[1])
                    # There is no 0th page, but this is a valid digit - so error if it's 0
                    if page == 0:
                        return await Utils.simple_embed_reply(channel, "[Error]", "Page parameter is incorrect.")
                else:
                    return await Utils.simple_embed_reply(channel, "[Error]", "Page parameter is incorrect.")
            # Start the embed for returning
            embed = discord.Embed(title="[Waifu Gifts]", description="Gifts for your waifus!",
                                  color=discord.Color(int("0x751DDF", 16)))
            # Grab all the gifts from the config
            gifts = self.config.get_data("Gifts")
            # Calculate the page count based on gift count and gifts per page
            page_count = (len(gifts) + gifts_per_page - 1) // gifts_per_page
            # Check if the page for display exists
            if page <= page_count:
                # Put the gift names into a list from each gift
                gift_names = [gift for gift in gifts]
                # Loop through gifts_per_page or the remaining number of gifts times
                for gift_number in range(min(gifts_per_page, len(gifts) - (page - 1) * gifts_per_page)):
                    # Get the gift name and then the gift itself
                    gift_name = gift_names[gifts_per_page * (page - 1) + gift_number]
                    gift = gifts[gift_name]
                    # Add found info to the embed as a new field
                    embed.add_field(name="%s - %s" % (gift["Symbol"], gift_name), value=gift["Cost"], inline=True)
                # Set page number info footer
                embed.set_footer(text="%d/%d" % (page, page_count))
                # Send the created embed as a reply
                await Utils.client.send_message(channel, embed=embed)
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "That page doesn't exist.")
        elif command is self.commands["Gift Command"]:
            if len(split_message) > 2:
                user = Utils.get_user(server, split_message[1])
                if user is not None:
                    if user is not author:
                        # Build the given gift name (since it caN CONTAIN spaces)
                        # ["A", "goOD", "gIfT"] -> "a good gift"
                        given_gift_name = (' '.join(split_message[2:])).lower()
                        raw_gifts = self.config.get_data("Gifts")
                        if given_gift_name in [gift_name.lower() for gift_name in raw_gifts]:
                            for gift_name in raw_gifts:
                                # Check if the lowercase gift name is the same as the lowercase given gift name
                                if gift_name.lower() == given_gift_name:
                                    gift = raw_gifts[gift_name]
                                    author_cash = EconomyUtils.get_cash(server.id, author.id)
                                    if author_cash >= gift["Cost"]:
                                        # Add one to gift counter in DB
                                        self.gifts_db.execute(
                                            "UPDATE '%s' SET amount=amount+1 WHERE server_id='%s' AND user_id='%s'" %
                                            (gift_name, server.id, user.id)
                                        )
                                        # Update author cash
                                        EconomyUtils.set_cash(server.id, author.id, author_cash - gift["Cost"])
                                        # Let the author know the user got the gift
                                        await Utils.simple_embed_reply(channel, "[Gift]", "%s was gifted **%s**." %
                                                                       (str(user),
                                                                        "%s %s" % (gift_name, gift["Symbol"])))
                                        break
                                    else:
                                        await Utils.simple_embed_reply(channel, "[Error]",
                                                                       "You don't have enough cash to do that.")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "Gift not found.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "You cannot give yourself a gift.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        elif command is self.commands["Affinity Command"]:
            if len(split_message) > 1:
                # Try and get a user from what was passed
                user = Utils.get_user(server, split_message[1])
                # Check if a valid user was given
                if user is not None:
                    if user is not author:
                        current_affinity = self.waifus_db.execute(
                            "SELECT affinity FROM '%s' WHERE user_id='%s'" % (server.id, author.id)
                        )[0]
                        if current_affinity != user.id:
                            # If the current author affinity is not Null, then increase the changes of heart
                            if current_affinity is not None:
                                self.waifus_db.execute(
                                    "UPDATE '%s' SET changes_of_heart=changes_of_heart+1 WHERE user_id='%s'" %
                                    (server.id, author.id)
                                )
                            # Set the affinity in the DB
                            self.waifus_db.execute(
                                "UPDATE '%s' SET affinity='%s' WHERE user_id='%s'" % (server.id, user.id, author.id)
                            )
                            # Let the user know the affinity was set
                            await Utils.simple_embed_reply(channel, "[Affinity]",
                                                           "Your affinity is now set towards %s." % str(user))
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]",
                                                           "You already have your affinity set towards %s." % str(user))
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "You cannot set your affinity to yourself.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Invalid user supplied.")
        elif command is self.commands["Waifu Leaderboard Command"]:
            # Grab ALL user IDs
            user_ids = self.waifus_db.execute("SELECT user_id FROM '%s'" % server.id)
            # Get Owner IDs (basically 1 person from each couple)
            owner_ids = self.waifus_db.execute(
                "SELECT owner_id FROM '%s' WHERE owner_id IS NOT NULL" % server.id)
            # If there's at least one couple
            if len(owner_ids) > 0:
                gifts = self.config.get_data("Gifts")
                # User ID : Gift Value
                gift_values = {}
                # Populate the dict with user IDs
                for user_id in user_ids:
                    gift_values[user_id] = 0
                # Calculate gift values for each owner
                for gift_name in gifts:
                    db_data = self.gifts_db.execute(
                        "SELECT user_id, amount FROM '%s' WHERE server_id='%s' AND amount IS NOT 0" % (
                            gift_name, server.id)
                    )
                    # If there was data found
                    if db_data:
                        db_data = [[db_data[i], db_data[i + 1]] for i in range(0, len(db_data), 2)]
                        # Add up each gift price for each user
                        for user_info in db_data:
                            gift_values[user_info[0]] += gifts[gift_name]["Cost"] * user_info[1]
                # Owner ID : Total Value
                owner_total_values = {}
                # Add up all the parameters to calculate total value
                for owner_id in owner_ids:
                    owner_affinity = tuple(self.waifus_db.execute(
                        "SELECT affinity FROM '%s' WHERE user_id='%s'" % (server.id, owner_id)
                    ))
                    # Get the other ID of the person in the couple, their value and affinity
                    waifu_id, waifu_value, waifu_affinity = tuple(self.waifus_db.execute(
                        "SELECT user_id, price, affinity FROM '%s' WHERE owner_id='%s'" % (server.id, owner_id)
                    ))
                    total_value = waifu_value + gift_values[waifu_id]
                    # Add 10% to the value if both users have their affinities set to each other
                    if waifu_affinity == owner_id and owner_affinity == waifu_id:
                        owner_total_values[owner_id] = int(total_value * 1.1)
                    else:
                        owner_total_values[owner_id] = total_value
                # Get the top ten values by sorting the keys in the dictionary, reversing it and grabbing 10 or the max
                top_ten = sorted(owner_total_values.items(), key=lambda x: x[1])[::-1][
                          :min(len(owner_total_values), 11)]
                embed = discord.Embed(title=" [Waifu Leaderboard]",
                                      color=discord.Color(int("0x751DDF", 16)))
                for i in range(len(top_ten)):
                    # Get the info from the current spot in the top 10
                    owner_id, value = top_ten[i]
                    # Grab the owner's affinity
                    owner_affinity = self.waifus_db.execute(
                        "SELECT affinity FROM '%s' WHERE user_id='%s'" % (server.id, owner_id)
                    )[0]
                    # Get the other ID of the person in the couple and their affinity
                    waifu_id, waifu_affinity = tuple(self.waifus_db.execute(
                        "SELECT user_id, affinity FROM '%s' WHERE owner_id='%s'" % (server.id, owner_id)
                    ))
                    owner_user = Utils.get_user_by_id(server, owner_id)
                    waifu_user = Utils.get_user_by_id(server, waifu_id)
                    desc = "**%s** - Claimed by **%s**\n" % (str(waifu_user), str(owner_user))
                    if waifu_affinity == owner_id and owner_affinity == waifu_id:
                        desc += "... and %s likes %s too!" % (str(waifu_user), str(owner_user))
                    else:
                        other_user = Utils.get_user_by_id(server, waifu_affinity)
                        desc += "... but %s likes %s!" % (str(waifu_user), str(other_user))
                    embed.add_field(name="%s - %s%s" %
                                         (Utils.add_number_abbreviation(i + 1), value, EconomyUtils.currency),
                                    value=desc)
                await Utils.client.send_message(channel, embed=embed)
            else:
                await Utils.simple_embed_reply(channel, "[Waifu Leaderboard]", "No waifus are currently claimed!")
        elif command is self.commands["Delete Waifu Leaderboard Command"]:
            # Reset all waifu info
            self.waifus_db.execute(
                "UPDATE '%s' SET owner_id=NULL, affinity=NULL, divorces=0, changes_of_heart=0, price='%d'" %
                (server.id, self.config.get_data("Default Claim Amount"))
            )
            # Pocket all gifts
            for gift_name in self.config.get_data("Gifts"):
                self.gifts_db.execute("UPDATE '%s' SET pocket_amount=pocket_amount+amount, amount=0" % gift_name)
            # Reply
            await Utils.simple_embed_reply(channel, "[Waifu Leaderboard]", "The leaderboard has been deleted.")

    # Called when the bot joins a server
    @Utils.client.event
    async def on_server_join(self, server):
        # Create waifu server table if it doesn't exist
        self.waifus_db.execute(
            """CREATE TABLE IF NOT EXISTS '%s'(user_id TEXT UNIQUE, price DIGIT, changes_of_heart DIGIT, 
            divorces DIGIT, owner_id TEXT, affinity TEXT)""" % server.id
        )
        # Populate waifu server tables with any unknown users
        known_users = self.waifus_db.execute("SELECT user_id from '%s'" % server.id)
        for user in server.members:
            if user.id not in known_users:
                self.waifus_db.execute("INSERT INTO '%s' VALUES('%s', '%s', 0, 0, NULL, NULL)" % (
                    server.id, user.id, str(self.config.get_data("Default Claim Amount"))
                ))
        # Grab known gift names from the DB and Config
        db_gift_names = self.gifts_db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        # Add any new gifts to the DB
        for gift_name in db_gift_names:
            # Populate the new table
            for user in server.members:
                self.gifts_db.execute("INSERT INTO '%s' VALUES('%s', '%s', 0, 0)" % (gift_name, server.id, user.id))

    # Called when a member joins a server the bot is in
    @Utils.client.event
    async def on_member_join(self, member):
        server_id = member.server.id
        user_id = member.id
        # Get known users from the waifus DB
        known_users = self.waifus_db.execute("SELECT user_id from '%s'" % server_id)
        if user_id not in known_users:
            # Add user to waifus DB
            self.waifus_db.execute("INSERT INTO '%s' VALUES('%s', '%s', 0, 0, NULL, NULL)" % (
                server_id, user_id, str(self.config.get_data("Default Claim Amount"))
            ))
            # Get known gift names
            db_gift_names = [gift_name for gift_name in self.config.get_data("Gifts")]
            # Populate gifts DB tables with new user
            for gift_name in db_gift_names:
                self.gifts_db.execute("INSERT INTO '%s' VALUES('%s', 0, 0)" % (gift_name, user_id))

    # Generates the waifu DB
    def generate_db(self):
        # Create waifu server tables if they don't exist
        for server in Utils.client.servers:
            self.waifus_db.execute(
                """CREATE TABLE IF NOT EXISTS '%s'(user_id TEXT UNIQUE, price DIGIT, changes_of_heart DIGIT, 
                divorces DIGIT, owner_id TEXT, affinity TEXT)""" % server.id
            )
            # Populate waifu server tables with any unknown users
            known_users = self.waifus_db.execute("SELECT user_id from '%s'" % server.id)
            for user in server.members:
                if user.id not in known_users:
                    self.waifus_db.execute("INSERT INTO '%s' VALUES('%s', '%s', 0, 0, NULL, NULL)" % (
                        server.id, user.id, str(self.config.get_data("Default Claim Amount"))
                    ))
        # Grab known gift names from the DB and Config
        db_gift_names = self.gifts_db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        config_gift_names = [gift_name for gift_name in self.config.get_data("Gifts")]
        # Find which gifts need to be added or removed from the DB (if any)
        gifts_to_remove = [gift_name for gift_name in db_gift_names if gift_name not in config_gift_names]
        gifts_to_add = [gift_name for gift_name in config_gift_names if gift_name not in db_gift_names]
        # Remove any gifts that are no longer in the config
        for gift_name in gifts_to_remove:
            self.gifts_db.execute("DROP TABLE '%s'" % gift_name)
        # Add any new gifts to the DB
        for gift_name in gifts_to_add:
            # Create a table
            self.gifts_db.execute(
                "CREATE TABLE IF NOT EXISTS '%s'(server_id TEXT, user_id TEXT, amount DIGIT, pocket_amount DIGIT)" %
                gift_name
            )
            # Populate the new table
            for server in Utils.client.servers:
                for user in server.members:
                    self.gifts_db.execute(
                        "INSERT INTO '%s' VALUES('%s', '%s', 0, 0)" % (gift_name, server.id, user.id))
