from Common import DataManager, Utils
from Common.Mod import Mod
import discord
import random

try:
    from Mods.Economy import EconomyUtils
except ImportError:
    raise Exception("Economy mod not installed")


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
        elif command is self.commands["Bet Flip Command"]:
            if len(split_message) > 2:
                # Grab the author's cash
                author_cash = EconomyUtils.get_cash(server.id, author.id)
                amount = split_message[1].lower()
                if amount == "all":
                    amount = str(author_cash)
                if amount.isdigit():
                    amount = int(amount)
                    # Make sure their betting something
                    if amount > 0:
                        # Check if the user's bet is within their cash balance
                        if amount <= author_cash:
                            # Remove their bet amount immediately
                            EconomyUtils.set_cash(server.id, author.id, author_cash - amount)
                            guess = split_message[2].lower()
                            # Check if the user has picked either heads or tails
                            if guess == "heads" or guess == "h" or guess == "tails" or guess == "t":
                                # Flip and save their choice
                                if guess == "heads" or guess == "h":
                                    is_correct = test_flip(True)
                                    guess_type = "Heads"
                                else:
                                    is_correct = test_flip(False)
                                    guess_type = "Tails"

                                # Grab configs
                                config_data = self.config.get_data()
                                command_config = config_data["Commands"]["Bet Flip Command"]

                                # Set cash and set response type based on win / lose
                                if is_correct:
                                    response_type = "Win"
                                    EconomyUtils.set_cash(server.id, author.id, author_cash + amount)
                                else:
                                    response_type = "Lose"
                                    EconomyUtils.set_cash(server.id, author.id, author_cash - amount)

                                message_description = command_config["%s Message" % response_type]
                                # Insert author name where the bot owner requested it
                                message_description = message_description.replace(
                                    "{user}", author.name
                                )
                                # Insert the amount they won/lost where the bot owner requested it
                                message_description = message_description.replace(
                                    "{amount}", str(amount * 2 if is_correct else amount) + EconomyUtils.currency
                                )

                                # Discord with the generated message description
                                embed = discord.Embed(title="[Bet Flip]",
                                                      description=message_description,
                                                      color=discord.Color(int("0x751DDF", 16)))
                                # Set the thumbnail to the url of the won/lost coin type
                                embed.set_thumbnail(url=config_data["%s %s URL" % (guess_type, response_type)])
                                # Random chance to set footer from config
                                if random.random() < command_config["Footer Percent Chance"] / 100:
                                    embed.set_footer(text=command_config["%s Footer Message" % response_type])
                                # Reply with built embed
                                await Utils.client.send_message(channel, embed=embed)
                            else:
                                await Utils.simple_embed_reply(channel, "[Error]",
                                                               "You have to pick heads or tails (h/t).")
                        else:
                            await Utils.simple_embed_reply(channel, "[Error]", "You don't have enough cash to do that.")
                    else:
                        await Utils.simple_embed_reply(channel, "[Error]", "You can't bet nothing.")
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
