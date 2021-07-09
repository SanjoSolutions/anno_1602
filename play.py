import math
from time import sleep

import numpy as np
from pymem import Pymem
import pyautogui
from win32gui import FindWindow, GetClientRect, ClientToScreen, GetForegroundWindow

from other.build_template import the_ultimate_city, PlacementType, Placement
from other.main import read_ships, ShipMovingStatus


# Goal:
# n aristocrates
# with a production that is sufficient to make the aristocrats happy.

# TODO: taxes as yield of money.
# TODO: production building operating cost / production building sleep operating cost as consumption of money.
from other.rates import create_rates, good_names

cycle = 60.0  # in seconds

# progression
# pioneer -> settler -> citizen -> merchant -> aristocrat
population_groups = (
    'pioneers',
    'settlers',
    'citizens',
    'merchants',
    'aristocrats'
)


maximum_number_of_people_per_house = np.array((
    2,
    6,
    15,
    25,
    40
))


def calculate_number_of_houses_for_population(population_group, population_size):
    return math.ceil(population_size / maximum_number_of_people_per_house[population_groups.index(population_group)])


# originally: V (Verbrauchsraten)
# rates are per person
consumption_rates = np.array((
    # pioneers
    create_rates(
        {
            'food': 0.13,
        }
    ),
    # settlers
    create_rates(
        {
            'food': 0.13,
            'cloth': 0.06,
            'liquor': 0.05
        }
    ),
    # citizens
    create_rates(
        {
            'food': 0.13,
            'cloth': 0.07,
            'liquor': 0.06,
            'tobacco products': 0.05,
            'spices': 0.05
        }
    ),
    # merchants
    create_rates(
        {
            'food': 0.13,
            'cloth': 0.08,
            'liquor': 0.07,
            'cocoa': 0.07,
            'tobacco products': 0.06,
            'spices': 0.06
        }
    ),
    # aristocrats
    create_rates(
        {
            'food': 0.13,
            'liquor': 0.08,
            'cocoa': 0.06,
            'tobacco products': 0.06,
            'spices': 0.06,
            'clothes': 0.05,
            'jewelry': 0.02
        }
    ),
))

taxes = (
    # pioneers
    0,
    # settlers
    0,
    # citizens
    0,
    # merchants
    0,
    # aristocrats
    0
)


def create_building(building):
    keys_to_add = ('operating cost', 'yield rate')
    for key_to_add in keys_to_add:
        if key_to_add not in building:
            building[key_to_add] = {}
    if 'workload' not in building:
        building['workload'] = 1.0
    return building


def calculate_yield_rate(yield_amount, interval):
    return cycle / (yield_amount * interval)


buildings = (
    create_building({
        'name': 'dirt road',
        'operating cost': {},
        'building cost': {
            'money': 5
        }
    }),
    # ...
    create_building({
        'name': 'quarry',
        'yield rate': {
            'money': 0
        }
    }),
    create_building({
        'name': 'iron mine',
        'yield rate': {
            'money': -60,
            'iron ore': calculate_yield_rate(1, 40)
        }
    }),
    create_building({
        'name': 'deep iron mine',
        'yield rate': {
            'money': -60,
            'iron ore': calculate_yield_rate(1, 40)
        }
    }),
    create_building({
        'name': 'gold-mine',
        'yield rate': {
            'money': -60,
            'gold': calculate_yield_rate(1, 80)
        }
    }),
    create_building({
        'name': 'goldsmith',
        'yield rate': {
            'money': -45,
            'jewelry': calculate_yield_rate(1, 80)
        }
    }),
    create_building({
        'name': 'stonemason',
        'yield rate': {
            'money': -5,
            'jewelry': calculate_yield_rate(1, 80)
        }
    }),
    create_building({
        'name': "fisher's hut",
        'building cost': {
            'money': 100,
            'tools': 3,
            'wood': 5
        },
        'yield rate': {
            'money': -5,
            'food': calculate_yield_rate(3, 28)
        }
    })
)

building_names = (

)

production_building_names = (

)

production_building_build_costs = (

)

production_building_operating_costs = (

)

production_building_sleep_costs = (

)


def calculate_yield_rates_for_building(building):
    return create_rates(building['yield rate'])


yield_rates = np.array(
    tuple(calculate_yield_rates_for_building(building) for building in buildings)
)

process = Pymem('1602.exe')
base_address = process.process_base.lpBaseOfDll
population_offset = 0x622FE0
camera_x_offset = 0x1B1AEC
camera_y_offset = 0x1B1AF0

# TODO: Increase numbers as buildings are built
number_of_buildings = np.zeros((len(buildings),))

number_of_buildings_to_build = np.zeros((len(buildings),))

# TODO: Navigate to area of map by clicking on location on minimap. This also sets the visible area of the map.
#       Therefore the camera position does not need to be read out of the memory of the Anno 1602 process.

viewport_width = 1024
viewport_height = 768
minimap_left = 802
minimap_top = 14
minimap_width = 185
minimap_height = 159
min_minimap_click_map_x = 0
min_minimap_click_map_y = 0
max_minimap_click_map_x = 497
max_minimap_click_map_y = 347
map_width = 498
map_height = 350
map_viewport_left = 0
map_viewport_top = 0
map_viewport_width = 768
map_viewport_height = 734


def get_window_client_area_position():
    window_handle = FindWindow('ANNO 1602 GAMEWINDOW', 'Anno 1602')
    left, top, right, bottom = GetClientRect(window_handle)
    left2, top2 = ClientToScreen(window_handle, (left, top))
    return left2, top2


def click_at_client_area_position(position):
    left, top = get_window_client_area_position()
    click_position = (
        left + position[0],
        top + position[1]
    )
    pyautogui.click(click_position[0], click_position[1])


def select_build_menu():
    click_at_client_area_position((817, 308))


def select_streets_and_bridges():
    click_at_client_area_position((869, 667))


def select_public_buildings():
    click_at_client_area_position((983, 724))


def select_road():
    click_at_client_area_position((806, 593))


def select_house():
    click_at_client_area_position((805, 663))


def select_fire_brigade():
    click_at_client_area_position((978, 549))


def move_ship(index, position):
    select_ship(index)
    go_to_map_position(position)
    click_at_map_position(position)


def select_ship(index):
    open_ship_menu()
    click_at_client_area_position((897, 421 + index * 27))


def open_ship_menu():
    pyautogui.press('s')


def open_status_menu():
    pyautogui.press('i')


def build_warehouse_from_ship(ship, position):
    select_ship(ship)
    go_to_map_position(position)
    open_status_menu()
    select_warehouse_from_ship()
    click_at_map_position(position)


def select_warehouse_from_ship():
    click_at_client_area_position((840, 609))


def select_building(placement):
    select_build_menu()
    type = placement.type
    if type == PlacementType.Road:
        select_streets_and_bridges()
        select_road()
    elif type == PlacementType.House:
        select_public_buildings()
        select_house()
    elif type == PlacementType.FireBrigade:
        select_public_buildings()
        select_fire_brigade()
    else:
        raise ValueError('placement "' + str(type) + '" not supported.')


def place_building(placement):
    go_to_map_position(placement.position)
    select_building(placement)
    click_at_map_position(placement.position)


def click_at_map_position(position):
    camera_x = process.read_int(base_address + camera_x_offset)
    camera_y = process.read_int(base_address + camera_y_offset)
    delta_x = position[0] - camera_x
    delta_y = position[1] - camera_y
    angle = 26.6
    delta_x_angle = math.radians(360 - angle)
    delta_y_angle = math.radians(180 + angle)
    tile_length = 16
    map_viewport_center_left = map_viewport_left + round(0.5 * map_viewport_width) + 31
    map_viewport_center_top = map_viewport_top + round(0.5 * map_viewport_height) + 32
    click_at_client_area_position((
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
    ))
    mouse_click_position = determine_mouse_click_position()
    print(position, mouse_click_position, (mouse_click_position[0] - position[0], mouse_click_position[1] - position[1]))


def click_at_map_position_0():
    camera_x = process.read_int(base_address + camera_x_offset)
    camera_y = process.read_int(base_address + camera_y_offset)
    position = (camera_x, camera_y)
    click_at_map_position(position)



def determine_mouse_click_position():
    return (
        process.read_short(base_address + 0x2C3050),
        process.read_short(base_address + 0x2C3048)
    )


def go_to_map_position(position):
    click_at_client_area_position((
        minimap_left + (min(max(0.0, float(position[0]) / map_width), 1.0) * minimap_width) - 1,
        minimap_top + (min(max(0.0, float(position[1]) / map_height), 1.0) * minimap_height) - 1
    ))


def when_ship_has_arrived(ship, fn):
    while not has_ship_arrived(ship):
        sleep(1)
    fn()


def has_ship_arrived(ship_index):
    ships = read_ships(process)
    ship = ships[ship_index]
    return ship.moving_status == ShipMovingStatus.Standing


def build(build_template, position):
    for placement in build_template.placements:
        x = position[0] + placement.position[0]
        y = position[1] + placement.position[1]
        placement_position = (x, y)
        placement2 = Placement(placement.type, placement_position, placement.rotation)
        place_building(placement2)


def main():
    hwnd = FindWindow(None, 'Anno 1602')
    while GetForegroundWindow() != hwnd:
        sleep(1)

    # ship = 0
    # ship_destination = (216, 165)
    # move_ship(ship, ship_destination)
    # warehouse_position = (213, 160)
    # when_ship_has_arrived(ship, lambda: build_warehouse_from_ship(ship, warehouse_position))
    build(the_ultimate_city, (217, 151))
    exit()

    # -12, -6
    # 4
    place_building(Placement(PlacementType.House, (5 + 9, 5 + 6)))

    while True:
        # TODO: Input from game
        current_population = np.array((
            process.read_int(base_address + population_offset),
            process.read_int(base_address + population_offset + 4),
            process.read_int(base_address + population_offset + 8),
            process.read_int(base_address + population_offset + 16),
            process.read_int(base_address + population_offset + 20),
        ))
        # TODO: Incorporate available resources (read them from memory, see Cheat Engine file)

        population_group = 'aristocrats'
        print('population group', population_group)
        number_of_population = 1000
        print('number of population', number_of_population)
        population = np.zeros((len(population_groups),))
        population[population_groups.index(population_group)] = number_of_population
        print('population', population)
        number_of_houses = calculate_number_of_houses_for_population(population_group, number_of_population)
        print('number of houses', number_of_houses)
        consumption_rate = number_of_houses * consumption_rates[population_groups.index(population_group)]
        print('consumption rate', consumption_rate)


        def determine_available_building(population):
            # TODO: Implement
            return buildings


        def select_buildings(consumption_rate):
            available_buildings = determine_available_building(current_population)
            number_of_buildings = np.zeros((len(buildings),))
            for index, rate in enumerate(consumption_rate):
                if rate > 0:
                    good_name = good_names[index]
                    production_building = select_building_with_highest_production_efficiency(available_buildings, good_name)
                    if production_building:
                        number_of_production_building = int(math.ceil(rate / production_building['yield rate'][good_name]))
                        building_index = buildings.index(production_building)
                        number_of_buildings[building_index] = number_of_production_building
            return number_of_buildings


        def select_building_that_produce_good(buildings, good_name):
            return tuple(building for building in buildings if
                         good_name in building['yield rate'] and building['yield rate'][good_name] > 0)


        def calculate_production_efficiency(building):
            building_yield_rate = building['yield rate']
            yield_rate = building_yield_rate.copy()
            del yield_rate['money']
            production_per_cycle = sum(yield_rate.values())
            cost_per_cycle = -building_yield_rate['money']
            return float(production_per_cycle) / float(cost_per_cycle)


        def select_building_with_highest_production_efficiency(available_buildings, good):
            buildings_that_produce_good = select_building_that_produce_good(available_buildings, good)
            return max(buildings_that_produce_good, key=calculate_production_efficiency) \
                if len(buildings_that_produce_good) >= 1 \
                else None


        number_of_buildings_to_build = number_of_buildings - select_buildings(consumption_rate)
        print('number of buildings', number_of_buildings)

        production_rate = np.dot(np.transpose(yield_rates), number_of_buildings)
        print('production rate', production_rate)

        print('production rate - consumption_rate', production_rate - consumption_rate)

        # Optimize
        # p = v

        # TODO: Output into game


if __name__ == '__main__':
    main()
