from zs_src.menus import HeadsUpDisplay


class DebugMenu(HeadsUpDisplay):
    def __init__(self, **kwargs):
        super(DebugMenu, self).__init__("debug menu", **kwargs)

    def populate(self):
        g = self.hud_group
        tools = self.tools

        ts = tools.TextSprite("hello")
        ts.add(g)


