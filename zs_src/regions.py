from zs_src.physics import Wall


class Region:
    def __init__(self, name, *points):
        self.name = name
        self.points = points

    def get_walls(self, positive=True, ground_angle=0.0, friction=None):
        points = list(self.points)
        if not positive:
            points.reverse()

        last = None
        walls = []
        for point in points:
            if last:
                walls.append(
                    Wall(last, point, friction=friction)
                )

            last = point

        for w in walls:
            angle = w.get_angle()
            w.ground = angle <= ground_angle or angle >= 1 - ground_angle

        return walls


class RectRegion(Region):
    def __init__(self, name, rect):
        points = (
            rect.topleft, rect.topright,
            rect.bottomleft, rect.bottomright
        )
        self.rect = rect
        super(RectRegion, self).__init__(name, points)
