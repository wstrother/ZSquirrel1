from zs_src.classes import CollisionSystem
from zs_src.entities import Layer
from zs_src.geometry import Wall


class RegionLayer(Layer):
    def __init__(self, *args, **kwargs):
        super(RegionLayer, self).__init__(*args, **kwargs)

        self.walls_visible = True

    @staticmethod
    def get_walls(group):
        walls = []

        for region in group:
            walls += region.walls

        return walls

    @staticmethod
    def smooth_wall_collision_system(items, group):
        walls = RegionLayer.get_walls(group)
        check = Wall.sprite_collision
        handle = Wall.handle_collision_smooth

        return CollisionSystem.group_collision_system(check, handle, items, walls)

    def draw(self, screen, offset=(0, 0)):
        for g in self.groups:
            g.draw(screen, offset=offset)

            if self.walls_visible:
                for item in g:
                    item.draw_walls(screen, offset=offset)
