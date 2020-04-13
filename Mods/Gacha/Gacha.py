from Common import DataManager, Utils
from Common.Mod import Mod


class Gacha(Mod):
    def __init__(self, mod_name, embed_color):
        super().__init__(mod_name, "Just an example mod.", {}, embed_color)
        # Config var init
        self.config = DataManager.JSON("Mods/Gacha/GachaConfig.json")
        # Init DBs
        self.gacha_database = DataManager.add_manager("gacha_database", "Mods/Gacha/GachaDatabase.db",
                                                      file_type=DataManager.FileType.SQL)
        self.generate_db()
        # Build command objects
        self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    def generate_db(self):
        return
        # for server in Utils.client.guilds:
        #     self.gacha_database.execute(
        #         "CREATE TABLE IF NOT EXISTS '%s'(gacha_name TEXT, print REAL)" % server.id
        #     )

# Gacha
# -> channel ID, gacha name, price, is purge, (other stuff..?)

# Gacha name
# -> name,
# -> role ID,
# -> duration,
# -> associated server,
