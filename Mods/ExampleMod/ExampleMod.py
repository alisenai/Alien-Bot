import Mod


class ExampleMod(Mod.Mod):
    def __init__(self, client, logging_level, embed_color):
        super().__init__("Just an example mod", "e", "", client, logging_level, embed_color)
