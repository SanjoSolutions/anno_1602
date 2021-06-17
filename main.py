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
    cities = []
    city_address = 0x005DC440
    while process.read_bool(city_address):
        city = read_city(process, city_address)
        cities.append(city)
        city_address += CITY_STRUCTURE_SIZE
    return cities


def read_city(process, city_address):
    city_bytes = process.read_bytes(city_address, CITY_STRUCTURE_SIZE)
    city = City()
    city.read_bytes(city_bytes)
    return city


SHIP_STRUCTURE_SIZE = 0x218


class Ship(StructureWithReadBytes):
    _fields_ = [
        ('name', c_char * 128)
    ]


def read_ships(process):
    ships = []
    ship_address = 0x004CF4E2
    while process.read_bool(ship_address):
        ship = read_ship(process, ship_address)
        ships.append(ship)
        ship_address += SHIP_STRUCTURE_SIZE
    return ships


def read_ship(process, ship_address):
    ship_bytes = process.read_bytes(ship_address, SHIP_STRUCTURE_SIZE)
    ship = Ship()
    ship.read_bytes(ship_bytes)
    return ship



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