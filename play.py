import math
from time import sleep

import numpy as np
from pymem import Pymem
import pyautogui
from win32gui import FindWindow, GetClientRect, ClientToScreen, GetForegroundWindow

from other.Good import Good
from other.build_template import the_ultimate_city, Placement, Rotation
from other.calculate_resource_yield import determine_building_cost
from other.Building import Building
from other.main import read_ships, ShipMovingStatus, read_cities
from other.rates import create_rates, good_names


pyautogui.FAILSAFE = False

# Goal:
# n aristocrates
# with a production that is sufficient to make the aristocrats happy.

# TODO: taxes as yield of money.
# TODO: production building operating cost / production building sleep operating cost as consumption of money.

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
    click_position = convert_client_area_position_to_screen_position(position)
    pyautogui.click(click_position[0], click_position[1])


def move_to_client_area_position(position):
    move_position = convert_client_area_position_to_screen_position(position)
    pyautogui.moveTo(move_position[0], move_position[1])


def drag_to_client_area_position(position):
    drag_to_position = convert_client_area_position_to_screen_position(position)
    pyautogui.mouseDown()
    pyautogui.moveTo(drag_to_position[0], drag_to_position[1])
    pyautogui.mouseUp()
    pyautogui.mouseUp()


def convert_client_area_position_to_screen_position(mouse_client_area_position):
    left, top = get_window_client_area_position()
    mouse_position = (
        left + mouse_client_area_position[0],
        top + mouse_client_area_position[1]
    )
    return mouse_position


def speed_up_8x():
    pyautogui.hotkey('shift', 'f8')


def select_construction_mode():
    pyautogui.press('b')


def move_ship(index, position):
    select_ship(index)
    go_to_map_position(position)
    click_at_map_position(position)


def select_ship(index):
    open_ship_menu()
    click_at_client_area_position((897, 421 + index * 27))


def open_ship_menu():
    pyautogui.press('s')


def select_info_mode():
    pyautogui.press('i')


def build_warehouse_from_ship(ship, position):
    select_ship(ship)
    go_to_map_position(position)
    select_info_mode()
    select_warehouse_from_ship()
    click_at_map_position(position)


def select_warehouse_from_ship():
    click_at_client_area_position((840, 609))


def select_building(placement):
    select_construction_mode()
    type = placement.type
    if type == Building.Road:
        select_streets_and_bridges()
        select_road()
    elif type == Building.ForestersHut:
        select_farms_and_plantations()
        select_foresters_hut()
    elif type == Building.House:
        select_public_buildings()
        select_house()
    elif type == Building.FishersHut:
        select_docks()
        select_fishers_hut()
    elif type == Building.MarketPlace:
        select_public_buildings()
        select_market_place()
    elif type == Building.SheepFarm:
        select_farms_and_plantations()
        select_sheep_farm()
    elif type == Building.WeaversHut:
        select_workshops()
        select_weavers_hut()
    elif type == Building.Chapel:
        select_public_buildings()
        select_chapel()
    elif type == Building.FireBrigade:
        select_public_buildings()
        select_fire_brigade()
    else:
        raise ValueError('placement "' + str(type) + '" not supported.')


def select_streets_and_bridges():
    click_at_client_area_position((869, 667))


def select_road():
    click_at_client_area_position((806, 593))


def select_workshops():
    click_at_client_area_position((815, 725))


def select_weavers_hut():
    click_at_client_area_position((807, 665))


def select_farms_and_plantations():
    click_at_client_area_position((870, 731))


def select_sheep_farm():
    click_at_client_area_position((923, 608))


def select_foresters_hut():
    click_at_client_area_position((865, 662))


def select_forest():
    click_at_client_area_position((922, 662))


def select_docks():
    click_at_client_area_position((928, 728))


def select_fishers_hut():
    click_at_client_area_position((806, 604))


def select_public_buildings():
    click_at_client_area_position((983, 724))


def select_house():
    click_at_client_area_position((805, 663))


def select_market_place():
    click_at_client_area_position((864, 662))


def select_chapel():
    click_at_client_area_position((921, 665))


def select_fire_brigade():
    click_at_client_area_position((978, 549))


def place_building(placement):
    go_to_map_position(placement.position)
    select_building(placement)
    click_at_map_position(placement.position)


def click_at_map_position(position):
    mouse_position = determine_mouse_client_area_position(position)
    click_at_client_area_position(mouse_position)
    mouse_click_position = determine_mouse_position()
    print(position, mouse_click_position, (mouse_click_position[0] - position[0], mouse_click_position[1] - position[1]))


def move_mouse_to_map_position(position):
    mouse_position = determine_mouse_client_area_position(position)
    move_to_client_area_position(mouse_position)


def drag_mouse_to_map_position(position):
    mouse_position = determine_mouse_client_area_position(position)
    drag_to_client_area_position(mouse_position)

    actual_mouse_position = determine_mouse_position()
    print(
        position,
        actual_mouse_position,
        (actual_mouse_position[0] - position[0], actual_mouse_position[1] - position[1])
    )


def determine_mouse_client_area_position(position):
    camera_x = process.read_int(base_address + camera_x_offset)
    camera_y = process.read_int(base_address + camera_y_offset)
    delta_x = position[0] - camera_x + 0.5 + 2
    delta_y = position[1] - camera_y + 0.5
    tile_width = 32
    tile_height = 16
    angle = math.atan(float(0.5 * tile_height) / (0.5 * tile_width))
    delta_x_angle = math.radians(360) - angle
    delta_y_angle = math.radians(180) + angle
    tile_length = math.sqrt((0.5 * tile_width) ** 2 + (0.5 * tile_height) ** 2)
    map_viewport_center_left = map_viewport_left + round(0.5 * map_viewport_width)  # + 31
    map_viewport_center_top = map_viewport_top + round(0.5 * map_viewport_height)  # + 32
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


def click_at_map_position_0():
    camera_x = process.read_int(base_address + camera_x_offset)
    camera_y = process.read_int(base_address + camera_y_offset)
    position = (camera_x, camera_y)
    click_at_map_position(position)


def determine_mouse_position():
    return (
        process.read_short(base_address + 0x2C308C),
        process.read_short(base_address + 0x2C3088)
    )


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


def when_can_build_house(city, fn):
    when_can_build_building(city, Building.House, fn)


def when_can_build_market_place(city, fn):
    when_can_build_building(city, Building.MarketPlace, fn)


def when_ship_has_arrived(ship, fn):
    do_when_condition_is_fulfilled(lambda: has_ship_arrived(ship), fn)


def has_ship_arrived(ship_index):
    ships = read_ships(process)
    ship = ships[ship_index]
    return ship.moving_status == ShipMovingStatus.Standing


def when_resources_available(city, resources, fn):
    do_when_condition_is_fulfilled(lambda: are_resources_available(city, resources), fn)


def are_resources_available(city_index, resources):
    cities = read_cities(process)
    city = cities[city_index]
    supplies = np.array(tuple(int(supply.amount / 32) for supply in city.supplies))
    return all(supplies >= resources[:len(supplies)])


def when_can_build_fishers_hut(city, fn):
    when_can_build_building(city, Building.FishersHut, fn)


def when_can_build_chapel(city, fn):
    when_can_build_building(city, Building.Chapel, fn)


def when_can_build_building(city, building, fn):
    when_resources_available(city, determine_building_cost(building), fn)


def do_when_conditions_are_fulfilled(conditions, fn):
    while not all(condition() for condition in conditions):
        sleep(1.0 / 60)
    fn()


def do_when_condition_is_fulfilled(condition, fn):
    do_when_conditions_are_fulfilled((condition,), fn)


def exchange_goods_between_warehouse_and_ship(ship):
    select_ship(ship)
    select_info_mode()
    click_at_client_area_position((821, 611))


def move_all_goods_from_ship_to_warehouse(ship):
    exchange_goods_between_warehouse_and_ship(ship)
    set_amount_to_be_traded_to_50t()
    load_goods_into_the_warehouse()
    select_slot_2_of_ship()
    load_goods_into_the_warehouse()
    select_slot_3_of_ship()
    load_goods_into_the_warehouse()
    select_slot_4_of_ship()
    load_goods_into_the_warehouse()


def load_goods_into_the_warehouse():
    click_at_client_area_position((979, 554))


def select_slot_2_of_ship():
    click_at_client_area_position((875, 674))


def select_slot_3_of_ship():
    click_at_client_area_position((928, 676))


def select_slot_4_of_ship():
    click_at_client_area_position((980, 672))


def build_foresters_hut(position):
    place_building(Placement(Building.ForestersHut, position))


def build_road(from_position, to_position):
    go_to_map_position(from_position)
    select_construction_mode()
    select_streets_and_bridges()
    select_road()
    move_mouse_to_map_position(from_position)
    drag_mouse_to_map_position(to_position)


def build_forest_around_foresters_hut(position):
    go_to_map_position(position)
    select_construction_mode()
    select_farms_and_plantations()
    select_forest()
    move_mouse_to_map_position((position[0] + 2, position[1] + 4))
    drag_mouse_to_map_position((position[0] - 1, position[1] - 3))
    move_mouse_to_map_position((position[0] - 3, position[1] + 2))
    drag_mouse_to_map_position((position[0] + 4, position[1] - 1))
    click_at_map_position((position[0] - 2, position[1] + 3))
    click_at_map_position((position[0] - 2, position[1] - 2))
    click_at_map_position((position[0] + 3, position[1] - 1))
    click_at_map_position((position[0] + 3, position[1] + 3))


def build_house(position):
    place_building(Placement(Building.House, position))


def increase_taxes_to_maximum(house_position):
    back_to_previous_menu()
    click_at_map_position(house_position)
    for i in range(16):
        increase_taxes_one_step()


def increase_taxes_one_step():
    click_at_client_area_position((988, 537))


def back_to_previous_menu():
    pyautogui.press('esc')


def build_fishers_hut(position):
    place_building(Placement(Building.FishersHut, position))


def build_market_place(position):
    place_building(Placement(Building.MarketPlace, position))


def load_resources_into_ship(ship, resources):
    select_ship(ship)
    exchange_goods_between_warehouse_and_ship(ship)
    good_groups = (
        (
            Good.Tools,
            Good.Wood,
            Good.Bricks
        ),
        (
            Good.Swords,
            Good.Muskets,
            Good.Cannon
        ),
        (
            Good.Food,
            Good.TabaccoProducts,
            Good.Spices,
            Good.Cocoa,
            Good.Liquor,
            Good.Cloth,
            Good.Clothes,
            Good.Jewelry
        ),
        (
            Good.IronOre,
            Good.Gold,
            Good.Wool,
            Good.Sugar,
            Good.Tabacco,
            Good.Cattle,
            Good.Grain,
            Good.Flour,
            Good.Iron
        )
    )
    for good_group_index in range(len(good_groups)):
        good_group = good_groups[good_group_index]
        has_good_group_been_selected = False
        for good_index in range(len(good_group)):
            good = good_group[good_index]
            if resources[good] >= 1:
                if not has_good_group_been_selected:
                    select_exchange_goods_good_group(good_group_index)
                    has_good_group_been_selected = True
                select_good_to_be_transferred(good_index)
                transfer_selected_good_to_ship(resources[good])


def select_exchange_goods_good_group(index):
    if index == 0:
        select_exchange_goods_good_group_building_material()
    elif index == 1:
        select_exchange_goods_good_group_weapons()
    elif index == 2:
        select_exchange_goods_good_group_consumer_goods()
    elif index == 3:
        select_exchange_goods_good_group_raw_materials()
    else:
        raise Exception('Unexpected index: ' + str(index))


def select_exchange_goods_good_group_building_material():
    click_at_client_area_position((815, 495))


def select_exchange_goods_good_group_weapons():
    click_at_client_area_position((873, 495))


def select_exchange_goods_good_group_consumer_goods():
    click_at_client_area_position((929, 495))


def select_exchange_goods_good_group_raw_materials():
    click_at_client_area_position((988, 499))


def select_good_to_be_transferred(good_index):
    if good_index == 0:
        select_good_to_be_transferred_1()
    elif good_index == 1:
        select_good_to_be_transferred_2()
    elif good_index == 2:
        select_good_to_be_transferred_3()
    elif good_index == 3:
        select_good_to_be_transferred_4()
    else:
        raise Exception('Not implemented to select good to be transferred with index: ' + str(good_index))
    # TODO: Implement scrolling to goods


def select_good_to_be_transferred_1():
    click_at_client_area_position((825, 445))


def select_good_to_be_transferred_2():
    click_at_client_area_position((874, 445))


def select_good_to_be_transferred_3():
    click_at_client_area_position((930, 445))


def select_good_to_be_transferred_4():
    click_at_client_area_position((979, 445))


def transfer_selected_good_to_ship(amount):
    remaining_amount = amount
    amounts_to_be_traded = [1, 5, 10, 50]
    for index in range(len(amounts_to_be_traded) - 1, -1, -1):
        amount_to_be_traded = amounts_to_be_traded[index]
        if remaining_amount >= amount_to_be_traded:
            set_amount_to_be_traded(amount_to_be_traded)
            while remaining_amount >= amount_to_be_traded:
                load_goods_onboard_the_ship()
                remaining_amount -= amount_to_be_traded


def set_amount_to_be_traded(amount):
    if amount == 1:
        set_amount_to_be_traded_to_1t()
    elif amount == 5:
        set_amount_to_be_traded_to_5t()
    elif amount == 10:
        set_amount_to_be_traded_to_10t()
    elif amount == 50:
        set_amount_to_be_traded_to_50t()


def set_amount_to_be_traded_to_1t():
    click_at_client_area_position((856, 555))


def set_amount_to_be_traded_to_5t():
    click_at_client_area_position((879, 554))


def set_amount_to_be_traded_to_10t():
    click_at_client_area_position((904, 553))


def set_amount_to_be_traded_to_50t():
    click_at_client_area_position((934, 553))


def load_goods_onboard_the_ship():
    click_at_client_area_position((821, 552))


def set_tools_to_be_bought():
    select_warehouse()
    determine_products_to_be_bought()
    determine_first_product_to_be_bought_to_be_tools()


def select_warehouse():
    warehouse_position = (214, 161)
    go_to_map_position(warehouse_position)
    click_at_map_position(warehouse_position)


def determine_products_to_be_bought():
    click_at_client_area_position((864, 731))


def determine_first_product_to_be_bought_to_be_tools():
    click_at_client_area_position((822, 619))
    click_at_client_area_position((815, 718))
    click_at_client_area_position((875, 533))  # set buy price to 75 gold


def build_cloth_production_group(city, position):
    when_can_build_building(city, Building.SheepFarm, lambda: build_sheep_farm((position[0] + 3, position[1] - 4)))
    when_can_build_building(city, Building.SheepFarm, lambda: build_sheep_farm((position[0] + 3, position[1] - 12)))
    when_can_build_building(city, Building.WeaversHut, lambda: build_weavers_hut((position[0] + 6, position[1] - 8)))


def build_sheep_farm(position):
    place_building(Placement(Building.SheepFarm, position))
    remove_trees_around_sheep_farm(position)


def remove_trees_around_sheep_farm(position):
    go_to_map_position(position)
    activate_demolition_mode()
    move_mouse_to_map_position((position[0] + 2, position[1] + 4))
    drag_mouse_to_map_position((position[0] - 1, position[1] - 3))
    move_mouse_to_map_position((position[0] - 3, position[1] + 2))
    drag_mouse_to_map_position((position[0] + 4, position[1] - 1))
    click_at_map_position((position[0] - 2, position[1] + 3))
    click_at_map_position((position[0] - 2, position[1] - 2))
    click_at_map_position((position[0] + 3, position[1] - 1))
    click_at_map_position((position[0] + 3, position[1] + 3))


def activate_demolition_mode():
    select_construction_mode()
    click_at_client_area_position((984, 661))


def build_weavers_hut(position):
    place_building(Placement(Building.WeaversHut, position))


def build_chapel(position):
    place_building(Placement(Building.Chapel, position))


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
    sleep(1)

    speed_up_8x()

    ship = 0
    ship_destination = (217, 162)
    move_ship(ship, ship_destination)
    warehouse_position = (213, 160)
    when_ship_has_arrived(ship, lambda: build_warehouse_from_ship(ship, warehouse_position))
    move_all_goods_from_ship_to_warehouse(ship)
    build_road((212, 162), (197, 162))
    foresters_hut_position = (207, 166)
    build_foresters_hut(foresters_hut_position)
    build_road((208, 165), (208, 163))
    build_forest_around_foresters_hut(foresters_hut_position)
    foresters_hut_position = (199, 166)
    build_foresters_hut(foresters_hut_position)
    build_road((200, 165), (200, 163))
    build_forest_around_foresters_hut(foresters_hut_position)
    build_road((212, 161), (212, 148))
    city = 0
    house_positions = (
        (210, 160),
        (208, 160),
        (206, 160),
        (210, 158),
        (208, 158),
        (206, 158),
        (210, 155),
        (208, 155),
        (206, 155),
        (210, 153),
        (208, 153),
        (206, 153),
        (203, 160),
        (203, 158),
        (201, 160),
        (201, 158),
        (199, 158)
    )
    for index in range(len(house_positions)):
        house_position = house_positions[index]
        when_can_build_house(city, lambda: build_house(house_position))
        if index == 0:
            increase_taxes_to_maximum(house_position)
    when_can_build_fishers_hut(city, lambda: build_fishers_hut((215, 159)))
    build_road((214, 159), (213, 159))
    warehouse_cost = create_rates({'tools': 3, 'wood': 6})

    def settle_second_island():
        load_resources_into_ship(ship, warehouse_cost)
        move_ship(ship, (248, 159))
        when_ship_has_arrived(ship, build_second_warehouse_and_move_ship_back_and_set_tools_to_be_bought)

    def build_second_warehouse_and_move_ship_back_and_set_tools_to_be_bought():
        build_warehouse_from_ship(ship, (251, 156))
        move_ship(ship, (217, 162))
        set_tools_to_be_bought()

    when_resources_available(city, warehouse_cost, settle_second_island)
    when_can_build_market_place(city, lambda: build_market_place((195, 158)))
    build_cloth_production_group(city, (186, 161))
    build_road((196, 162), (194, 153))
    when_can_build_chapel(city, lambda: build_chapel((203, 155)))
    # build(the_ultimate_city, (217, 151))
    exit()

    # -12, -6
    # 4
    place_building(Placement(Building.House, (5 + 9, 5 + 6)))

    while True:
        # milestones
        # * population group 2
        #   * cloth production
        #   * market place
        #   * chapel

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
        number_of_population = 25000
        print('number of population', number_of_population)
        population = np.zeros((len(population_groups),))
        population[population_groups.index(population_group)] = number_of_population
        print('population', population)

        # def determine_required_number_of_houses_from_aimed_number_of_aristocrats(population):
        #     number_of_aristocrats = population[-1]
        #     maximimum_number_of_aristocrats_per_house = maximum_number_of_people_per_house[-1]
        #     number_of_houses = math.ceil(number_of_aristocrats / float(maximimum_number_of_aristocrats_per_house))
        #     return number_of_houses
        #
        # def determine_required_population_group_sizes_from_aimed_number_of_aristocrats(population):
        #

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
