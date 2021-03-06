from enum import IntEnum

from pymem import Pymem
from ctypes import *
import re

NUMBER_OF_SUPPLY_TYPES = 23


class StructureWithReadBytes(Structure):
    def read_bytes(self, bytes):
        memmove(addressof(self), bytes, min(sizeof(self), len(bytes)))


class Player(StructureWithReadBytes):
    _fields_ = [
        ('gold', c_uint32),
        ('name', c_char * 0x60)
    ]

    SIZE = 0x280


def read_players(process):
    player_address = 0x005B7684
    return read_entities(process, Player, player_address)


def read_player(process, player_address):
    return read_entity(process, Player, player_address)


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


# 005b3160
# 00619b60 <-

# offset = (*(island.0xAF4 + (island.width * y + x) * 4) & 0x1FFF) * 4

# pBlockId = (short *)(0x00619b60 + offset)


def read_island_fields(process, island):
    block_ids = [None] * island.height
    for y in range(island.height):
        block_ids[y] = [0] * island.width
    fields_base_address = island.pFields
    for y in range(island.height):
        for x in range(island.width):
            index = island.width * y + x
            address = fields_base_address + index * 4
            offset = (process.read_uint(address) & 0x1FFF) * 4
            block_pointer = process.read_uint(0x00619b60 + offset)
            block_id = process.read_ushort(block_pointer)
            block_ids[y][x] = block_id
    return block_ids


# FIXME: When previously more islands existed then it seems those islands are still kinda in memory.
def read_islands(process):
    island_address = 0x005E6B20
    return read_entities(process, Island, island_address)


def read_island(process, island_address):
    return read_entity(process, Island, island_address)


class Supply(Structure):
    _fields_ = [
        ('amount', c_short),
        ('_spacer_', c_byte * 10)
    ]


class City(StructureWithReadBytes):
    _fields_ = [
        ('name', c_char * 0x2A),  # 0x0
        ('_spacer_', c_byte * 0x18),
        ('supplies', Supply * NUMBER_OF_SUPPLY_TYPES),
        ('_spacer_2_', c_byte * 0xCA),
        ('number_of_pioneers', c_uint32),  # 0x220
        ('stop_supplying_materials_to_the_settlers', c_bool)  # 0x257
    ]

    SIZE = 0x258


def read_cities(process):
    city_address = 0x005DBAE0
    return read_entities(process, City, city_address)


def read_city(process, city_address):
    return read_entity(process, City, city_address)


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


def read_ships(process):
    ship_address = 0x004CF35C
    return read_entities(process, Ship, ship_address)


def read_ship(process, ship_address):
    return read_entity(process, Ship, ship_address)


def read_entities(process, entity_class, address):
    entities = []
    while process.read_ulonglong(address) > 0:
        entity = read_entity(process, entity_class, address)
        entities.append(entity)
        address += entity_class.SIZE
    return entities


def read_entity(process, entity_class, address):
    bytes = process.read_bytes(address, entity_class.SIZE)
    entity = entity_class()
    entity.read_bytes(bytes)
    read_referred_entities(process, entity)

    return entity


def read_referred_entities(process, entity):
    pointer_field_names = get_pointer_field_names(entity.__class__)
    for field_name in pointer_field_names:
        read_referred_entity(process, entity, field_name)


def get_pointer_field_names(entity_class):
    field_names = []
    for field in entity_class._fields_:
        field_name, field_type = field
        match = re.match('(.+)_pointer', field_name)
        if match:
            field_name = match.group(1)
            field_names.append(field_name)
    return field_names


def read_referred_entity(process, entity, field_name):
    referred_entity_type_field = field_name.upper() + '_TYPE'
    referred_entity_type = getattr(entity.__class__, referred_entity_type_field)
    if not referred_entity_type:
        raise NameError(
            'Field "' + referred_entity_type_field + '" not found on class "' + entity.__class__.__name__ + '".'
        )
    referred_entity_address = getattr(entity, field_name + '_pointer')
    referred_entity = read_entity(process, referred_entity_type, referred_entity_address)
    setattr(entity, field_name, referred_entity)


def main():
    process = Pymem('1602.exe')

    players = read_players(process)
    print('Players:')
    for player in players:
        print(player.name.decode('utf-8') + ': ' + str(player.gold))

    print('')

    city_address = 0x005DC440
    city = read_city(process, city_address)
    print('City:', city.name.decode('utf-8'))
    print('Number of pioneers:', city.number_of_pioneers)
    print('Supplies:')
    for supply in city.supplies:
        print(supply.amount)

    print('')

    islands = read_islands(process)
    print('Number of islands:', len(islands))
    print('Islands:')
    for island in islands:
        print('x: ' + str(island.x) + ', y: ' + str(island.y) + ', width: ' + str(island.width) + ', height: ' + str(island.height) + ', pSomething: ' + hex(island.pFields))
        island_fields = read_island_fields(process, island)
        print('island fields:')
        for row in island_fields:
            print(row)

    print('')

    cities = read_cities(process)
    print('Number of cities:', len(cities))
    print('Cities:')
    for city in cities:
        print(city.name.decode('utf-8') + ' (' + str(city.number_of_pioneers) + ' pioneers)')

    print('')

    ships = read_ships(process)
    print('Number of ships:', len(ships))
    print('Ships:')
    for ship in ships:
        print(ship.name.decode('utf-8'), ship.coordinates.x, ship.coordinates.y, ship.moving_status, ship.cannon_count)


if __name__ == '__main__':
    main()
