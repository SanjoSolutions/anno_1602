from enum import IntEnum

from other.Building import Building


class BuildTemplate:
    def __init__(self, width, height, placements):
        self.width = width
        self.height = height
        self.placements = placements


class Rotation(IntEnum):
    Default = 0
    Rotated90Degree = 1
    Rotated180Degree = 2
    Rotated270Degree = 3


class Placement:
    def __init__(self, type, position, rotation=Rotation.Default):
        self.type = type
        self.position = position
        self.rotation = rotation


the_ultimate_city = BuildTemplate(width=29, height=29, placements=(
    Placement(Building.DirtRoad, (5, 0)),
    Placement(Building.DirtRoad, (6, 0)),
    Placement(Building.DirtRoad, (7, 0)),
    Placement(Building.DirtRoad, (8, 0)),
    Placement(Building.DirtRoad, (9, 0)),
    Placement(Building.DirtRoad, (10, 0)),
    Placement(Building.DirtRoad, (11, 0)),
    Placement(Building.DirtRoad, (12, 0)),
    Placement(Building.DirtRoad, (13, 0)),
    Placement(Building.DirtRoad, (14, 0)),
    Placement(Building.DirtRoad, (15, 0)),
    Placement(Building.DirtRoad, (16, 0)),
    Placement(Building.DirtRoad, (17, 0)),
    Placement(Building.DirtRoad, (18, 0)),
    Placement(Building.DirtRoad, (19, 0)),
    Placement(Building.DirtRoad, (20, 0)),
    Placement(Building.DirtRoad, (21, 0)),
    Placement(Building.DirtRoad, (22, 0)),
    Placement(Building.DirtRoad, (23, 0)),
    Placement(Building.DirtRoad, (5, 1)),
    Placement(Building.House, (9, 1)),
    Placement(Building.House, (11, 1)),
    Placement(Building.House, (13, 1)),
    Placement(Building.DirtRoad, (15, 1)),
    Placement(Building.House, (16, 1)),
    Placement(Building.House, (18, 1)),
    Placement(Building.House, (20, 1)),
    Placement(Building.DirtRoad, (24, 1)),
    Placement(Building.DirtRoad, (5, 2)),
    Placement(Building.DirtRoad, (15, 2)),
    Placement(Building.DirtRoad, (24, 2)),
    Placement(Building.FireBrigade, (3, 3)),
))
