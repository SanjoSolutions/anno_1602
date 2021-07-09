from enum import IntEnum


class BuildTemplate:
    def __init__(self, width, height, placements):
        self.width = width
        self.height = height
        self.placements = placements


class PlacementType(IntEnum):
    Road = 1
    House = 2
    FireBrigade = 3


class Rotation(IntEnum):
    Default = 0
    Rotated90Degree = 90
    Rotated180Degree = 180
    Rotated270Degree = 270


class Placement:
    def __init__(self, type, position, rotation=Rotation.Default):
        self.type = type
        self.position = position
        self.rotation = rotation


the_ultimate_city = BuildTemplate(width=29, height=29, placements=(
    Placement(PlacementType.Road, (5, 0)),
    Placement(PlacementType.Road, (6, 0)),
    Placement(PlacementType.Road, (7, 0)),
    Placement(PlacementType.Road, (8, 0)),
    Placement(PlacementType.Road, (9, 0)),
    Placement(PlacementType.Road, (10, 0)),
    Placement(PlacementType.Road, (11, 0)),
    Placement(PlacementType.Road, (12, 0)),
    Placement(PlacementType.Road, (13, 0)),
    Placement(PlacementType.Road, (14, 0)),
    Placement(PlacementType.Road, (15, 0)),
    Placement(PlacementType.Road, (16, 0)),
    Placement(PlacementType.Road, (17, 0)),
    Placement(PlacementType.Road, (18, 0)),
    Placement(PlacementType.Road, (19, 0)),
    Placement(PlacementType.Road, (20, 0)),
    Placement(PlacementType.Road, (21, 0)),
    Placement(PlacementType.Road, (22, 0)),
    Placement(PlacementType.Road, (23, 0)),
    Placement(PlacementType.Road, (5, 1)),
    Placement(PlacementType.House, (9, 1)),
    Placement(PlacementType.House, (11, 1)),
    Placement(PlacementType.House, (13, 1)),
    Placement(PlacementType.Road, (15, 1)),
    Placement(PlacementType.House, (16, 1)),
    Placement(PlacementType.House, (18, 1)),
    Placement(PlacementType.House, (20, 1)),
    Placement(PlacementType.Road, (24, 1)),
    Placement(PlacementType.Road, (5, 2)),
    Placement(PlacementType.Road, (15, 2)),
    Placement(PlacementType.Road, (24, 2)),
    Placement(PlacementType.FireBrigade, (3, 3)),
))
