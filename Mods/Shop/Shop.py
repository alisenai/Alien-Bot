from Common import Utils
from Common.Mod import Mod
from Common import DataManager
from Mods.Economy import EconomyUtils


class Shop(Mod):
    def __init__(self, mod_name, embed_color):
        # Config var init
        self.config = DataManager.JSON("Mods/Shop/ShopConfig.json")
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    async def command_called(self, message, command):
        server, channel, author = message.server, message.channel, message.author
        # if command is self.commands["Add Success Reply Command"]:
