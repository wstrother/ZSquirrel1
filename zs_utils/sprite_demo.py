from zs_src.layers.context import PauseMenuLayer


class SpriteDemo(PauseMenuLayer):
    def __init__(self, **kwargs):
        super(SpriteDemo, self).__init__(
            "Sprite Demo", "sprite_demo", **kwargs)

    def populate(self):
        spawn = self.context.load_item

        player = spawn("Player", position=(450, 100))
        self.set_value("Player", player)

        plats = [
            (5, .01, (0, 450), True),
            (2, .08125, (1200, 480), True),
            (1, .9, (1850, 120), True),
            (3, .105, (2180, 150), True),
            (8, .8175, (3000, -150), True),
        ]

        for args in plats:
            length, angle, origin, ground = args[0:4]
            if len(args) == 5:
                friction = args[4]
            else:
                friction = False
            spawn("Tree Plat", length, angle, origin,
                  ground=ground, friction=friction)
