import math
from ctypes import *
from io import SEEK_CUR


def main():
    with open(r'C:\Anno_1602\SAVEGAME\game01.gam', 'rb') as file:
        while file.read(1) != b'':
            file.seek(-1, SEEK_CUR)
            read_block(file)



index = 0


def read_block(file):
    global index
    id = decode_zero_terminated_string(file.read(16))
    index += 16
    print(id)
    length = int.from_bytes(file.read(4), byteorder='little', signed=False)
    index += 4
    data_block_start = index
    print(length)
    data = file.read(length)
    index += length
    if id == 'INSELHAUS':
        island_fields_count = math.floor(length / sizeof(IslandField))
        island_fields_array = IslandField * island_fields_count
        island_fields = island_fields_array()
        memmove(addressof(island_fields), data, island_fields_count * sizeof(IslandField))
        island_fields = list(island_fields)
        buildings_set = set(island_field.type for island_field in island_fields)
        buildings = list(buildings_set)
        house_island_fields = [island_field for island_field in island_fields if island_field.type == 605]
        for house_island_field in house_island_fields:
            print('data_block_start', hex(data_block_start))
            print('house', house_island_field.x, house_island_field.y)
    else:
        print(data)



# class IslandHouse(Structure):
#     _fields_ = [
#         ('id', c_char * 16),
#         ('length', c_uint32),
#         ()
#     ]


class IslandField(Structure):
    _fields_ = [
        ('building', c_uint16),
        ('x', c_uint8),
        ('y', c_uint8),
        ('rotation', c_uint32),
        ('unknown_1', c_uint32),
        ('unknown_2', c_uint32),
        ('status', c_uint32),
        ('random', c_uint32),
        ('player', c_uint32),
        ('empty', c_uint32)
    ]


def decode_zero_terminated_string(string):
    index = string.find(0x00)
    string = string[:index]
    string = string.decode('utf-8')
    return string


if __name__ == '__main__':
    main()
