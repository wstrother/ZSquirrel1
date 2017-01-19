from zs_src.physics import Wall


class Region:
    WALL_COLOR = 255, 0, 255

    def __init__(self, name, *points, **kwargs):
        self.name = name
        self.walls = []
        self.set_walls(points, **kwargs)

    def set_walls(self, points, **kwargs):
        self.walls = self.get_walls(points, **kwargs)

    @staticmethod
    def get_walls(points, ground_angle=0.0, orientation=True,
                  offset=(0, 0), friction=None, closed=True):
        if not orientation:
            points = list(points)
            points.reverse()
            points = tuple(points)

        def get_wall(p1, p2):
            x1, y1 = p1
            x2, y2 = p2
            x1 += offset[0]
            x2 += offset[0]
            y2 += offset[1]
            y2 += offset[1]

            return Wall((x1, y1), (x2, y2),
                        friction=friction)

        last = None
        walls = []
        for point in points:
            if last:
                walls.append(get_wall(last, point))

            last = point
        if closed:
            walls.append(get_wall(last, points[0]))

        for w in walls:
            angle = w.get_angle()
            w.ground = angle <= ground_angle or angle >= 1 - ground_angle

        return walls

    def get_collision_system(self, items, check_collision, handle_collision):

        def collision_system():
            for item in items:
                for w in self.walls:
                    if check_collision(item, w):
                        handle_collision(item, w)

        return collision_system

    def get_sprite_collision_system(self, group, handle_collision):
        return self.get_collision_system(
            group, Wall.sprite_collision, handle_collision)

    def get_vector_collision_system(self, vectors, handle_collision):
        return self.get_collision_system(
            vectors, Wall.vector_collision, handle_collision
        )

    def get_smooth_sprite_collision_system(self, group):
        return self.get_sprite_collision_system(
            group, Wall.handle_collision_smooth
        )

    def get_mirror_sprite_collision_system(self, group):
        return self.get_sprite_collision_system(
            group, Wall.handle_collision_mirror
        )

    def draw(self, screen, offset=(0, 0)):
        for wall in self.walls:
            wall.draw(screen, self.WALL_COLOR, offset=offset)


class RectRegion(Region):
    def __init__(self, name, rect, **kwargs):
        points = (rect.bottomleft, rect.topleft,
                  rect.topright, rect.bottomright)
        self._rect = rect
        super(RectRegion, self).__init__(name, *points, **kwargs)

    def get_rect(self):
        return self._rect
