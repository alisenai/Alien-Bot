from Common import DataManager, Utils
from Common.Mod import Mod
import discord
import random

try:
    from Mods.Economy import EconomyUtils
except ImportError:
    raise Exception("Economy mod not installed")


# TODO: Win text(s) and lose text(s)
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
                            if guess == "heads" or guess == "h" or guess == "tails" or guess == "t":
                                is_heads = guess == "heads" or guess == "h"
                                is_correct = test_flip(is_heads)
                                url_data = self.config.get_data()
                                if is_correct:
                                    # It's NOT amount * 2 since the 'amount' var is never updated
                                    EconomyUtils.set_cash(server.id, author.id, author_cash + amount)
                                    embed = discord.Embed(title="[Bet Flip]",
                                                          description="Well done, you won %d%s!" % (
                                                              amount * 2, EconomyUtils.currency
                                                          ),
                                                          color=discord.Color(int("0x751DDF", 16)))
                                    embed.set_thumbnail(
                                        url=url_data["Heads Win URL"] if is_heads else url_data["Tails Win URL"]
                                    )
                                    if random.randint(0, 250) == 1:
                                        embed.set_footer(text="You're cheating, aren't you?")
                                    await Utils.client.send_message(channel, embed=embed)
                                else:
                                    embed = discord.Embed(title="[Bet Flip]",
                                                          description="You lost %d%s! Better luck next time" % (
                                                              amount, EconomyUtils.currency
                                                          ),
                                                          color=discord.Color(int("0x751DDF", 16)))
                                    embed.set_thumbnail(
                                        url=url_data["Heads Lose URL"] if is_heads else url_data["Tails Lose URL"]
                                    )
                                    if random.randint(0, 250) == 1:
                                        embed.set_footer(text="It's rigged!")
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
