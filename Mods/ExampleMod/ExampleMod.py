import Mod


class ExampleMod(Mod.Mod):
    def __init__(self, client, logging_level, embed_color):
        super().__init__("ExampleMod", "Just an example mod", "e", "", client, logging_level, embed_color)

    def command_called(self, message, command):
        print("Command Called")