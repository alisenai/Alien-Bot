from Common import DataManager, Utils
from Common.Mod import Mod
import discord
import random

try:
    from Mods.Economy import EconomyUtils
except ImportError:
    raise Exception("Economy mod not installed")


# TODO: Random footer config
# TODO: Multiple win/lose messages?
class Gamble(Mod):
    def __init__(self, mod_name, embed_color):
        super().__init__(mod_name, "Just an example mod.", {}, embed_color)
        # Config var init
        self.config = DataManager.JSON("Mods/Gamble/GambleConfig.json")
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    async def command_called(self, message, command):
        split_message = message.content.split(" ")
        server, channel, author = message.server, message.channel, message.author
        if command is self.commands["Flip Command"]:
            embed = discord.Embed(title="[Flip]", color=discord.Color(int("0x751DDF", 16)))
            if random.randint(0, 1) == 1:
                embed.set_image(url=self.config.get_data("Heads Win URL"))
            else:
                embed.set_image(url=self.config.get_data("Tails Win URL"))
            await Utils.client.send_message(channel, embed=embed)
        elif command is self.commands["Mega Flip Command"]:
            if len(split_message) > 1:
                if split_message[1].isdigit():
                    amount = int(split_message[1])
                    max_flip_amount = self.config.get_data("Commands")["Mega Flip Command"]["Max Flip Amount"]
                    if amount <= max_flip_amount:
                        flip_text = "`%s`" % ''.join(["H" if random.randint(0, 1) == 1 else "T" for _ in range(amount)])
                        await Utils.simple_embed_reply(channel, "[Mega Flip]", flip_text)
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]",
                                                       "Amount parameter is too large (Max: %s)." % max_flip_amount)
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Amount parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")
        # TODO: Create a method that will cut this code in 1/2
        elif command is self.commands["Bet Flip Command"]:
            if len(split_message) > 2:
                author_cash = EconomyUtils.get_cash(server.id, author.id)
                amount = split_message[1].lower()
                if amount == "all":
                    amount = author_cash
                if amount.isdigit():
                    amount = int(split_message[1])
                    if amount > 0:
                        if amount <= author_cash:
                            EconomyUtils.set_cash(server.id, author.id, author_cash - amount)
                            guess = split_message[2].lower()
                            command_config = self.config.get_data("Commands")["Bet Flip Command"]
                            if guess == "heads" or guess == "h" or guess == "tails" or guess == "t":
                                is_heads = guess == "heads" or guess == "h"
                                is_correct = test_flip(is_heads)
                                config_data = self.config.get_data()
                                if is_correct:
                                    # It's NOT amount * 2 since the 'amount' var is never updated
                                    EconomyUtils.set_cash(server.id, author.id, author_cash + amount)
                                    message_description = command_config["Win Message"]
                                    # Insert author name where they bot owner requested it
                                    message_description = message_description.replace(
                                        "{user}", author.name
                                    )
                                    # Insert the amount they won where they bot owner requested it
                                    message_description = message_description.replace(
                                        "{amount}", str(amount * 2) + EconomyUtils.currency
                                    )
                                    embed = discord.Embed(title="[Bet Flip]",
                                                          description=message_description,
                                                          color=discord.Color(int("0x751DDF", 16)))
                                    embed.set_thumbnail(
                                        url=config_data["Heads Win URL"] if is_heads else config_data["Tails Win URL"]
                                    )
                                    if random.random() < command_config["Footer Percent Chance"]/100:
                                        embed.set_footer(text=command_config["Win Footer Message"])
                                    await Utils.client.send_message(channel, embed=embed)
                                else:
                                    message_description = command_config["Lose Message"]
                                    # Insert author name where they bot owner requested it
                                    message_description = message_description.replace(
                                        "{user}", author.name
                                    )
                                    # Insert the amount they won where they bot owner requested it
                                    message_description = message_description.replace(
                                        "{amount}", str(amount) + EconomyUtils.currency
                                    )
                                    embed = discord.Embed(title="[Bet Flip]",
                                                          description=message_description,
                                                          color=discord.Color(int("0x751DDF", 16)))
                                    embed.set_thumbnail(
                                        url=config_data["Heads Lose URL"] if is_heads else config_data["Tails Lose URL"]
                                    )
                                    if random.random() < command_config["Footer Percent Chance"]/100:
                                        embed.set_footer(text=command_config["Lose Footer Message"])
                                    await Utils.client.send_message(channel, embed=embed)
                            else:
                                await Utils.simple_embed_reply(channel, "[Error]",
                                                               "You have to pick heads or tails (h/t).")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "You don't have enough cash to do that.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "Amount parameter is incorrect.")
                else:
                    await Utils.simple_embed_reply(channel, "[Error]", "Amount parameter is incorrect.")
            else:
                await Utils.simple_embed_reply(channel, "[Error]", "Insufficient parameters supplied.")


def test_flip(is_heads=True):
    rnd = random.randint(0, 1)
    if rnd == 1:
        if is_heads:
            return True
        return False
    if is_heads:
        return False
    return True
