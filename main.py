import math
from enum import IntEnum

import pyautogui
from pymem import Pymem
from ctypes import *
import re

from win32gui import FindWindow, GetClientRect, ClientToScreen

from other.memory import CAMERA_X, CAMERA_Y, MOUSE_X, MOUSE_Y, MOUSE_CLICK_X, MOUSE_CLICK_Y

NUMBER_OF_SUPPLY_TYPES = 23


class Anno1602:
    VIEWPORT_WIDTH = 1024
    VIEWPORT_HEIGHT = 768
    MINIMAP_LEFT = 802
    MINIMAP_TOP = 14
    MINIMAP_WIDTH = 185
    MINIMAP_HEIGHT = 159
    MIN_MINIMAP_CLICK_MAP_X = 0
    MIN_MINIMAP_CLICK_MAP_Y = 0
    MAX_MINIMAP_CLICK_MAP_X = 497
    MAX_MINIMAP_CLICK_MAP_Y = 347
    MAP_WIDTH = 498
    MAP_HEIGHT = 350
    MAP_VIEWPORT_LEFT = 0
    MAP_VIEWPORT_TOP = 0
    MAP_VIEWPORT_WIDTH = 768
    MAP_VIEWPORT_HEIGHT = 734

    def __init__(self):
        self.process = Pymem('1602.exe')
        self.window = FindWindow('ANNO 1602 GAMEWINDOW', 'Anno 1602')

    def click_at_client_area_position(self, position):
        click_position = self.convert_client_area_position_to_screen_position(position)
        pyautogui.click(click_position[0], click_position[1])

    def move_to_client_area_position(self, position):
        move_position = self.convert_client_area_position_to_screen_position(position)
        pyautogui.moveTo(move_position[0], move_position[1])

    def drag_to_client_area_position(self, position):
        drag_to_position = self.convert_client_area_position_to_screen_position(position)
        pyautogui.mouseDown()
        pyautogui.moveTo(drag_to_position[0], drag_to_position[1])
        pyautogui.mouseUp()
        pyautogui.mouseUp()

    def get_window_client_area_position(self):
        left, top, right, bottom = GetClientRect(self.window)
        left2, top2 = ClientToScreen(self.window, (left, top))
        return left2, top2

    def convert_client_area_position_to_screen_position(self, mouse_client_area_position):
        left, top = self.get_window_client_area_position()
        mouse_position = (
            left + mouse_client_area_position[0],
            top + mouse_client_area_position[1]
        )
        return mouse_position

    def click_at_map_position(self, position):
        mouse_position = self.determine_mouse_client_area_position(position)
        self.click_at_client_area_position(mouse_position)
        mouse_click_position = self.determine_mouse_position()
        print(position, mouse_click_position,
              (mouse_click_position[0] - position[0], mouse_click_position[1] - position[1]))

    def move_mouse_to_map_position(self, position):
        mouse_position = self.determine_mouse_client_area_position(position)
        self.move_to_client_area_position(mouse_position)

    def drag_mouse_to_map_position(self, position):
        mouse_position = self.determine_mouse_client_area_position(position)
        self.drag_to_client_area_position(mouse_position)

        actual_mouse_position = self.determine_mouse_position()
        print(
            position,
            actual_mouse_position,
            (actual_mouse_position[0] - position[0], actual_mouse_position[1] - position[1])
        )

    def determine_mouse_client_area_position(self, position):
        camera_x = self.process.read_int(self.process.base_address + CAMERA_X)
        camera_y = self.process.read_int(self.process.base_address + CAMERA_Y)
        delta_x = position[0] - camera_x + 0.5 + 2
        delta_y = position[1] - camera_y + 0.5
        tile_width = 32
        tile_height = 16
        angle = math.atan(float(0.5 * tile_height) / (0.5 * tile_width))
        delta_x_angle = math.radians(360) - angle
        delta_y_angle = math.radians(180) + angle
        tile_length = math.sqrt((0.5 * tile_width) ** 2 + (0.5 * tile_height) ** 2)
        map_viewport_center_left = Anno1602.MAP_VIEWPORT_LEFT + round(0.5 * Anno1602.MAP_VIEWPORT_WIDTH)
        map_viewport_center_top = Anno1602.MAP_VIEWPORT_TOP + round(0.5 * Anno1602.MAP_VIEWPORT_HEIGHT)
        return (
            round(
                map_viewport_center_left +
                delta_x * tile_length * math.cos(delta_x_angle) +
                delta_y * tile_length * math.cos(delta_y_angle)
            ),
            round(
                map_viewport_center_top -
                (
                        delta_x * tile_length * math.sin(delta_x_angle) +
                        delta_y * tile_length * math.sin(delta_y_angle)
                )
            )
        )

    def determine_mouse_position(self):
        return (
            self.process.read_short(self.process.base_address + MOUSE_X),
            self.process.read_short(self.process.base_address + MOUSE_Y)
        )

    def determine_mouse_click_position(self):
        return (
            self.process.read_short(self.process.base_address + MOUSE_CLICK_X),
            self.process.read_short(self.process.base_address + MOUSE_CLICK_Y)
        )

    def read_players(self):
        player_address = 0x005B7684
        return self.read_entities(Player, player_address)

    def read_player(self, player_address):
        return self.read_entity(Player, player_address)

    def read_island_fields(self, island):
        block_ids = [None] * island.height
        for y in range(island.height):
            block_ids[y] = [0] * island.width
        fields_base_address = island.pFields
        for y in range(island.height):
            for x in range(island.width):
                index = island.width * y + x
                address = fields_base_address + index * 4
                offset = (self.process.read_uint(address) & 0x1FFF) * 4
                block_pointer = self.process.read_uint(0x00619b60 + offset)
                block_id = self.process.read_ushort(block_pointer)
                block_ids[y][x] = block_id
        return block_ids

    # FIXME: When previously more islands existed then it seems those islands are still kinda in memory.
    def read_islands(self):
        island_address = 0x005E6B20
        return self.read_entities(Island, island_address)

    def read_island(self, island_address):
        return self.read_entity(Island, island_address)

    def read_cities(self):
        city_address = 0x005DBAE0
        return self.read_entities(City, city_address)

    def read_city(self, city_address):
        return self.read_entity(City, city_address)

    def read_ships(self):
        ship_address = 0x004CF35C
        return self.read_entities(Ship, ship_address)

    def read_ship(self, ship_address):
        return self.read_entity(Ship, ship_address)

    def read_entities(self, entity_class, address):
        entities = []
        while self.process.read_ulonglong(address) > 0:
            entity = self.read_entity(entity_class, address)
            entities.append(entity)
            address += entity_class.SIZE
        return entities

    def read_entity(self, entity_class, address):
        bytes = self.process.read_bytes(address, entity_class.SIZE)
        entity = entity_class()
        entity.read_bytes(bytes)
        self.read_referred_entities(entity)

        return entity

    def read_referred_entities(self, entity):
        pointer_field_names = self.get_pointer_field_names(entity.__class__)
        for field_name in pointer_field_names:
            self.read_referred_entity(entity, field_name)

    def get_pointer_field_names(self, entity_class):
        field_names = []
        for field in entity_class._fields_:
            field_name, field_type = field
            match = re.match('(.+)_pointer', field_name)
            if match:
                field_name = match.group(1)
                field_names.append(field_name)
        return field_names

    def read_referred_entity(self, entity, field_name):
        referred_entity_type_field = field_name.upper() + '_TYPE'
        referred_entity_type = getattr(entity.__class__, referred_entity_type_field)
        if not referred_entity_type:
            raise NameError(
                'Field "' + referred_entity_type_field + '" not found on class "' + entity.__class__.__name__ + '".'
            )
        referred_entity_address = getattr(entity, field_name + '_pointer')
        referred_entity = self.read_entity(referred_entity_type, referred_entity_address)
        setattr(entity, field_name, referred_entity)


class StructureWithReadBytes(Structure):
    def read_bytes(self, bytes):
        memmove(addressof(self), bytes, min(sizeof(self), len(bytes)))


class Player(StructureWithReadBytes):
    _fields_ = [
        ('gold', c_uint32),
        ('name', c_char * 0x60)
    ]

    SIZE = 0x280


class Island(StructureWithReadBytes):
    _fields_ = [
        ('_spacer_', c_byte * 4),  # 0x0
        ('x', c_uint32),  # 0x4
        ('y', c_uint32),  # 0x8
        ('width', c_uint32),  # 0xC
        ('height', c_uint32),  # 0x10
        ('_spacer_2_', c_byte * 0xAE4),
        ('pFields', c_uint32),  # 0xAF4
        # 0xAFC
    ]

    SIZE = 0xB00


class Supply(Structure):
    _fields_ = [
        ('amount', c_short),
        ('_spacer_', c_byte * 10)
    ]


class City(StructureWithReadBytes):
    _fields_ = [
        ('name', c_char * 0x18),  # 0x0
        ('island_index', c_byte),  # 0x18
        ('_spacer_', c_byte * 0x29),  # 0x19
        ('supplies', Supply * NUMBER_OF_SUPPLY_TYPES),
        ('_spacer_2_', c_byte * 0xCA),
        ('population', c_uint32 * 5),  # 0x220
        ('stop_supplying_materials_to_the_settlers', c_bool)  # 0x257
    ]

    SIZE = 0x258


class ShipCoordinates(StructureWithReadBytes):
    _fields_ = [
        ('_spacer_', c_byte * 0x28),
        ('x', c_float),
        ('y', c_float)
    ]

    SIZE = 0x30


class Ship(StructureWithReadBytes):
    _fields_ = [
        ('coordinates_pointer', c_uint32),  # 0x0
        ('_spacer_', c_byte * 0x14),  # 0x4
        ('moving_status', c_ushort),  # 0x18
        ('_spacer_2_', c_byte * 0x16C),  # 0x1A
        ('name', c_char * 0x18),  # 0x186
        ('cannon_count', c_byte)  # 0x19E
    ]

    SIZE = 0x218
    COORDINATES_TYPE = ShipCoordinates


class ShipMovingStatus(IntEnum):
    Standing = 0
    Moving = 55


def main():
    anno1602 = Anno1602()

    players = anno1602.read_players()
    print('Players:')
    for player in players:
        print(player.name.decode('utf-8') + ': ' + str(player.gold))

    print('')

    city_address = 0x005DC440
    city = anno1602.read_city(city_address)
    print('City:', city.name.decode('utf-8'))
    print('Population:', tuple(city.population))
    print('Supplies:')
    for supply in city.supplies:
        print(supply.amount)

    print('')

    islands = anno1602.read_islands()
    print('Number of islands:', len(islands))
    print('Islands:')
    for island in islands:
        print('x: ' + str(island.x) + ', y: ' + str(island.y) + ', width: ' + str(island.width) + ', height: ' + str(island.height) + ', pSomething: ' + hex(island.pFields))
        island_fields = anno1602.read_island_fields(island)
        print('island fields:')
        for row in island_fields:
            print(row)

    print('')

    cities = anno1602.read_cities()
    print('Number of cities:', len(cities))
    print('Cities:')
    for city in cities:
        print(city.name.decode('utf-8') + ' (population: ' + str(tuple(city.population)) + ')')

    print('')

    ships = anno1602.read_ships()
    print('Number of ships:', len(ships))
    print('Ships:')
    for ship in ships:
        print(ship.name.decode('utf-8'), ship.coordinates.x, ship.coordinates.y, ship.moving_status, ship.cannon_count)


if __name__ == '__main__':
    main()
