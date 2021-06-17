from pymem import Pymem

NUMBER_OF_SUPPLY_TYPES = 23


def read_city_supplies(process: Pymem, base_address):
    supply = [0] * NUMBER_OF_SUPPLY_TYPES
    for index in range(NUMBER_OF_SUPPLY_TYPES):
        offset = 0x6 + index * 0x3
        supply[index] = process.read_short(base_address + offset * 4 + 0x2A)
    return supply


process = Pymem('1602.exe')
supplies = read_city_supplies(process, 0x005DC440)
print(supplies)
