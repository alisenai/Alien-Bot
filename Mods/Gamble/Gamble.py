from Common import DataManager, Utils
from Common.Mod import Mod
import discord
import random

try:
    from Mods.Economy import EconomyUtils
except ImportError:
    raise Exception("Economy mod not installed")


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
        server, channel = message.server, message.channel
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


def test_flip(is_heads=True):
    rnd = random.randint(0, 1)
    if rnd == 1:
        if is_heads:
            return True
        return False
    if is_heads:
        return False
    return True
