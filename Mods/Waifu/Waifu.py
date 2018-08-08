from Common import DataManager
from Common.Mod import Mod
from Common import Utils


class Waifu(Mod):
    def __init__(self, mod_name, embed_color):
        # Config var init
        self.config = DataManager.JSON("Mods/Waifu/WaifuConfig.json")
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        super().__init__(mod_name, self.config.get_data("Mod Description"), {}, embed_color)
