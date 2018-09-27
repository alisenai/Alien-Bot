from Common import DataManager, Utils, Mod
import discord
import time


# TODO: Figure out how to actually kick people out of a vc
# > Create channel, move user, delete channel?
# > Change channel permissions, then change them back?
# > Change user permissions, then change them back?
# > Just move users to AFK channel
# TODO: Per-server
class VoiceTimeout(Mod.Mod):
    def __init__(self, mod_name, embed_color):
        # Vars
        self.user_times = {}  # User : Join Time
        # Config var init
        self.config = DataManager.JSON("Mods/VoiceTimeout/VoiceTimeoutConfig.json")
        # Build command objects
        # self.commands = Utils.parse_command_config(self, mod_name, self.config.get_data('Commands'))
        self.commands = {}
        # Init the super with all the info from this mod
        super().__init__(mod_name, self.config.get_data('Mod Description'), self.commands, embed_color)

    async def on_voice_state_update(self, before, after):
        # If the user joined a channel
        if before.voice_channel is None and after.voice_channel is not None:
            self.user_times[after.id] = time.time()
        elif after.voice_channel is None and before.voice_channel is not None:
            del self.user_times[after.id]

    async def second_tick(self):
        current_time = time.time()
        for user in self.user_times:
            if current_time - self.user_times[user] > self.config.get_data("Timeout Threshold"):
                return
