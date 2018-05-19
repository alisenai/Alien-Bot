import Mod


# Literally just an example mod
class ExampleMod(Mod.Mod):
    def __init__(self, client, logging_level, embed_color):
        super().__init__(client, "Just an example mod", "e", "", logging_level, embed_color)
