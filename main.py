from pymem import Pymem
from ctypes import *

NUMBER_OF_SUPPLY_TYPES = 23


class StructureWithReadBytes(Structure):
    def read_bytes(self, bytes):
        memmove(addressof(self), bytes, min(sizeof(self), len(bytes)))


class Supply(Structure):
    _fields_ = [
        ('amount', c_short),
        ('_spacer_', c_byte * 10)
    ]


# city structure size: 0x258
#   city name offset: 0x0

CITY_STRUCTURE_SIZE = 0x258


class City(StructureWithReadBytes):
    _fields_ = [
        ('name', c_char * 0x2A),
        ('_spacer_', c_byte * 0x18),
        ('supplies', Supply * NUMBER_OF_SUPPLY_TYPES)
    ]


def read_cities(process):
    city_address = 0x005DC440
    return read_entities(process, City, CITY_STRUCTURE_SIZE, city_address)


def read_city(process, city_address):
    return read_entity(process, City, CITY_STRUCTURE_SIZE, city_address)


SHIP_STRUCTURE_SIZE = 0x218


class Ship(StructureWithReadBytes):
    _fields_ = [
        ('name', c_char * 128)
    ]


def read_ships(process):
    ship_address = 0x004CF4E2
    return read_entities(process, Ship, SHIP_STRUCTURE_SIZE, ship_address)


def read_ship(process, ship_address):
    return read_entity(process, Ship, SHIP_STRUCTURE_SIZE, ship_address)


def read_entities(process, entity_class, structure_size, address):
    entities = []
    while process.read_bool(address):
        entity = read_entity(process, entity_class, structure_size, address)
        entities.append(entity)
        address += structure_size
    return entities


def read_entity(process, entity_class, structure_size, address):
    bytes = process.read_bytes(address, structure_size)
    entity = entity_class()
    entity.read_bytes(bytes)
    return entity


process = Pymem('1602.exe')

city_address = 0x005DC440
city = read_city(process, city_address)
print('City:', city.name.decode('utf-8'))
print('Supplies:')
for supply in city.supplies:
    print(supply.amount)


cities = read_cities(process)
print('Number of cities:', len(cities))
print('City names:')
for city in cities:
    print(city.name.decode('utf-8'))


ships = read_ships(process)
print('Number of ships:', len(ships))
print('Ship names:')
for ship in ships:
    print(ship.name.decode('utf-8'))