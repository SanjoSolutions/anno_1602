import itertools
import math
from time import sleep

import numpy as np
import pyautogui
from win32gui import GetForegroundWindow

from other.Good import Good
from other.build_template import the_ultimate_city, Placement, Rotation
from other.calculate_resource_yield import determine_building_cost
from other.Building import Building
from other.main import ShipMovingStatus, Anno1602
from other.memory import CAMERA_X, CAMERA_Y, POPULATION
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

# TODO: Increase numbers as buildings are built
number_of_buildings = np.zeros((len(buildings),))

number_of_buildings_to_build = np.zeros((len(buildings),))


# TODO: Navigate to area of map by clicking on location on minimap. This also sets the visible area of the map.
#       Therefore the camera position does not need to be read out of the memory of the Anno 1602 process.


building_menu = (
    (
        (Building.Castle, Building.LargeCastle, Building.Fortress),
        (Building.Wall, Building.Gate, Building.Watchtower, Building.CityGate),
        (Building.Palisade, Building.WoodenGate, Building.WoodenWatchtower)
    ),
    (
        (Building.Square1, Building.Square2, Building.Square3, Building.OrnamentalTree),
        (Building.DirtRoad, Building.CobblestoneStreet, Building.WoodenBridge, Building.StoneBridge)
    ),
    (
        (Building.Quarry, Building.IronMine, Building.DeepIronMine, Building.GoldMine),
    ),
    tuple(),
    (
        (Building.Goldsmith, Building.Armourer, Building.MusketMaker, Building.CannonFoundry),
        (Building.Stonemason, Building.WaterMill, Building.OreSmelter, Building.ToolMaker),
        (Building.TobaccoProducts, Building.Distillery, Building.Bakery, Building.WeavingMill),
        (Building.WeaversHut, Building.ButchersShop, Building.FlourMill, Building.Bakery)
    ),
    (
        (Building.CottonPlantation, Building.CottonField, Building.CocoaPlantation, Building.CocoaField),
        (Building.Winery, Building.Vines, Building.SugarcanePlantation, Building.CaneField),
        (Building.TobaccoPlantation, Building.TobaccoField, Building.SpicePlantation, Building.SpiceField),
        (Building.GrainFarm, Building.GrainField, Building.SheepFarm, Building.CattleFarm),
        (Building.HuntingLodge, Building.ForestersHut, Building.Forest)
    ),
    (
        (Building.FishersHut, Building.Dock, Building.SmallShipyard, Building.LargeShipyard),
        (Building.Warehouse1, Building.Warehouse2, Building.Warehouse3, Building.Warehouse4)
    ),
    (
        (Building.Palace, Building.Gallows),
        (Building.College, Building.PublicBaths, Building.Theater, Building.FireBrigade),
        (Building.Cathedral, Building.Tavern, Building.Doctor, Building.School),
        (Building.HouseSettlers, Building.HouseCitizens, Building.HouseMerchants, Building.HouseAristocrats),
        (Building.HousePioneers, Building.MarketPlace, Building.Chapel, Building.Church)
    ),
)


building_unlocking = (
    # (condition, buildings)
    (lambda population: population[0] >= 0, {Building.Warehouse1, Building.ForestersHut, Building.FishersHut, Building.HuntingLodge, Building.SheepFarm, Building.WeaversHut, Building.MarketPlace, Building.DirtRoad, Building.WoodenBridge, Building.Chapel, Building.Forest, Building.Dock, Building.HousePioneers}),
    (lambda population: population[0] >= 30, {Building.CattleFarm, Building.ButchersShop}),
    (lambda population: population[1] >= 15, {Building.Quarry, Building.Stonemason, Building.CobblestoneStreet, Building.StoneBridge, Building.FireBrigade}),
    (lambda population: population[1] >= 30, {Building.Warehouse2, Building.Palisade, Building.WoodenGate}),
    (lambda population: population[1] >= 40, {Building.SpicePlantation, Building.SpiceField, Building.Winery, Building.Vines, Building.SugarcanePlantation, Building.CaneField, Building.Distillery, Building.TobaccoPlantation, Building.TobaccoField, Building.TobaccoProducts}),
    (lambda population: population[1] >= 50, {Building.Tavern}),
    (lambda population: population[1] >= 75, {Building.GrainFarm, Building.GrainField, Building.FlourMill, Building.WaterMill, Building.Bakery}),
    (lambda population: population[1] >= 100, {Building.School, Building.ToolMaker}),
    (lambda population: population[1] >= 120, {Building.IronMine, Building.OreSmelter, Building.SmallShipyard}),
    (lambda population: population[1] >= 200, {Building.Castle, Building.Armourer, Building.WoodenWatchtower, Building.Wall, Building.Watchtower, Building.Square1, Building.Gate, Building.CityGate}),
    (lambda population: population[2] >= 50, {Building.Doctor}),
    (lambda population: population[2] >= 100, {Building.Gallows, Building.Warehouse3}),
    (lambda population: population[2] >= 150, {Building.Church, Building.GoldMine}),
    (lambda population: population[2] >= 200, {Building.CottonPlantation, Building.CottonField, Building.CocoaField, Building.CocoaField, Building.TailorsShop, Building.WeavingMill}),
    (lambda population: population[2] >= 210, {Building.PublicBaths}),
    (lambda population: population[2] >= 400, {Building.CannonFoundry}),
    (lambda population: population[2] >= 450, {Building.DeepIronMine}),
    (lambda population: population[3] >= 250, {Building.College, Building.Warehouse4, Building.Goldsmith, Building.Square2, Building.Square3, Building.OrnamentalTree}),  # FIXME: Squares here?
    (lambda population: population[3] >= 300, {Building.Theater}),
    (lambda population: population[3] >= 400, {Building.LargeCastle, Building.MusketMaker}),
    (lambda population: population[3] >= 500, {Building.LargeShipyard}),
    (lambda population: population[4] >= 600, {Building.Fortress}),
    (lambda population: population[4] >= 1500, {Building.Palace}),
    (lambda population: population[4] >= 2500, {Building.Cathedral})
)


def generate_building_menu_for_current_population(population):
    available_buildings = set(itertools.chain.from_iterable(buildings for condition, buildings in building_unlocking if condition(population)))
    building_menu_for_current_population = []
    for category in building_menu:
        category_for_current_population = []
        for row in category:
            row_for_current_population = tuple(building if building in available_buildings else None for building in row)
            if any(item is not None for item in row_for_current_population):
                category_for_current_population.append(row_for_current_population)
        building_menu_for_current_population.append(category_for_current_population)
    return building_menu_for_current_population


def find_building_in_building_menu(building: Building, building_menu):
    for category_index in range(len(building_menu)):
        category = building_menu[category_index]
        for row_index in range(len(category)):
            row = category[row_index]
            for column_index in range(len(row)):
                item = row[column_index]
                if item == building:
                    return category_index, len(category) - row_index - 1, column_index


class Anno1602AI(Anno1602):
    NUMBER_OF_ROTATIONS = 4

    BUILDING_CATEGORY_POSITIONS = [
        (816, 662),
        (871, 662),
        (928, 662),
        (985, 662),
        (816, 725),
        (871, 725),
        (928, 725),
        (985, 725)
    ]

    def speed_up_8x(self):
        pyautogui.hotkey('shift', 'f8')

    def select_construction_mode(self):
        pyautogui.press('b')

    def move_ship(self, index, position):
        self.select_ship(index)
        self.go_to_map_position(position)
        self.click_at_map_position(position)

    def select_ship(self, index):
        self.open_ship_menu()
        self.click_at_client_area_position((897, 421 + index * 27))

    def open_ship_menu(self):
        pyautogui.press('s')

    def select_info_mode(self):
        pyautogui.press('i')

    def explore_the_island(self, ship):
        self.select_ship(ship)
        self.select_info_mode()
        self.click_at_client_area_position((822, 484))

    def build_warehouse_from_ship(self, ship, position):
        self.select_ship(ship)
        self.go_to_map_position(position)
        self.select_info_mode()
        self.select_warehouse_from_ship()
        self.click_at_map_position(position)

    def select_warehouse_from_ship(self):
        self.click_at_client_area_position((840, 609))

    def select_building(self, building: Building):
        population = self.determine_maximum_population()
        building_menu = generate_building_menu_for_current_population(population)
        category, row, column = find_building_in_building_menu(building, building_menu)
        self.select_construction_mode()
        self.select_building_category(category)
        self.select_building_category_submenu_item(category, row, column)

    def determine_maximum_population(self):
        cities = self.read_cities()
        NUMBER_OF_POPULATION_GROUPS = 5
        return tuple(
            max(city.population[index] for city in cities) for index in range(NUMBER_OF_POPULATION_GROUPS)
        )

    def select_building_category(self, category):
        building_category_position = Anno1602AI.BUILDING_CATEGORY_POSITIONS[category]
        self.click_at_client_area_position(building_category_position)

    def select_building_category_submenu_item(self, category, row, column):
        BUILD_MENU_ITEM_WIDTH = 50
        BUILD_MENU_ITEM_HEIGHT = 50
        BUILD_SUBMENU_BETWEEN_ROW_SPACE = 11
        BUILD_SUBMENU_BETWEEN_COLUMN_SPACE = 4
        BUILD_SUBMENU_ITEM_WIDTH = 53
        BUILD_SUBMENU_ITEM_HEIGHT = 50

        build_menu_item_position = Anno1602AI.BUILDING_CATEGORY_POSITIONS[category]
        build_menu_item_x, build_menu_item_y = build_menu_item_position

        ROW_DELTA = BUILD_SUBMENU_BETWEEN_ROW_SPACE + BUILD_SUBMENU_ITEM_HEIGHT
        COLUMN_DELTA = BUILD_SUBMENU_BETWEEN_COLUMN_SPACE + BUILD_SUBMENU_ITEM_WIDTH

        y = build_menu_item_y - 0.5 * BUILD_MENU_ITEM_HEIGHT - BUILD_SUBMENU_BETWEEN_ROW_SPACE - 0.5 * BUILD_SUBMENU_ITEM_HEIGHT - \
            row * ROW_DELTA
        x = 776 + BUILD_SUBMENU_BETWEEN_COLUMN_SPACE + 0.5 * BUILD_SUBMENU_ITEM_WIDTH + \
            column * COLUMN_DELTA

        self.click_at_client_area_position((x, y))

    def select_streets_and_bridges(self):
        self.click_at_client_area_position((869, 667))

    def select_road(self):
        self.click_at_client_area_position((806, 593))

    def select_workshops(self):
        self.click_at_client_area_position((815, 725))

    def select_weavers_hut(self):
        self.click_at_client_area_position((807, 665))

    def select_farms_and_plantations(self):
        self.click_at_client_area_position((870, 731))

    def select_sheep_farm(self):
        self.click_at_client_area_position((923, 608))

    def select_foresters_hut(self):
        self.click_at_client_area_position((865, 662))

    def select_forest(self):
        self.click_at_client_area_position((922, 662))

    def select_docks(self):
        self.click_at_client_area_position((928, 728))

    def select_fishers_hut(self):
        self.click_at_client_area_position((806, 604))

    def select_public_buildings(self):
        self.click_at_client_area_position((983, 724))

    def select_house(self):
        self.click_at_client_area_position((805, 663))

    def select_market_place(self):
        self.click_at_client_area_position((864, 662))

    def select_chapel(self):
        self.click_at_client_area_position((921, 665))

    def select_fire_brigade(self):
        self.click_at_client_area_position((978, 549))

    def place_building(self, placement):
        self.go_to_map_position(placement.position)
        self.select_building(placement.type)
        self.rotate_building(placement.rotation)
        self.click_at_map_position(placement.position)

    def rotate_building(self, rotation):
        current_rotation = self.read_rotation()
        if current_rotation != rotation:
            if (rotation - current_rotation) % Anno1602AI.NUMBER_OF_ROTATIONS <= 2:
                rotate = self.rotate_90_degree_clockwise
            else:
                rotate = self.rotate_90_degree_counter_clockwise
            while current_rotation != rotation:
                rotate()
                current_rotation = self.read_rotation()

    def read_rotation(self):
        return self.process.read_bytes(self.process.base_address + 0x9E6F4, 1)[0]

    def rotate_90_degree_clockwise(self):
        self.click_at_client_area_position((1003, 434))

    def rotate_90_degree_counter_clockwise(self):
        self.click_at_client_area_position((799, 431))

    def click_at_map_position_0(self):
        camera_x = self.process.read_int(self.process.base_address + CAMERA_X)
        camera_y = self.process.read_int(self.process.base_address + CAMERA_Y)
        position = (camera_x, camera_y)
        self.click_at_map_position(position)

    def go_to_map_position(self, position):
        self.click_at_client_area_position((
            Anno1602.MINIMAP_LEFT + (
                min(max(0.0, float(position[0]) / Anno1602.MAP_WIDTH), 1.0) * Anno1602.MINIMAP_WIDTH) - 1,
            Anno1602.MINIMAP_TOP + (
                min(max(0.0, float(position[1]) / Anno1602.MAP_HEIGHT), 1.0) * Anno1602.MINIMAP_HEIGHT) - 1
        ))

    def when_can_build_house(self, city, fn):
        self.when_can_build_building(city, Building.HousePioneers, fn)

    def when_can_build_market_place(self, city, fn):
        self.when_can_build_building(city, Building.MarketPlace, fn)

    def wait_for_ship_has_arrived(self, ship):
        self.wait_for_condition(lambda: self.has_ship_arrived(ship))

    def when_ship_has_arrived(self, ship, fn):
        self.do_when_condition_is_fulfilled(lambda: self.has_ship_arrived(ship), fn)

    def has_ship_arrived(self, ship_index):
        ships = self.read_ships()
        ship = ships[ship_index]
        return ship.moving_status == ShipMovingStatus.Standing

    def when_resources_available(self, city, resources, fn):
        self.do_when_condition_is_fulfilled(lambda: self.are_resources_available(city, resources), fn)

    def are_resources_available(self, city_index, resources):
        cities = self.read_cities()
        city = cities[city_index]
        supplies = np.array(tuple(int(supply.amount / 32) for supply in city.supplies))
        return all(supplies >= resources[:len(supplies)])

    def when_can_build_fishers_hut(self, city, fn):
        self.when_can_build_building(city, Building.FishersHut, fn)

    def when_can_build_chapel(self, city, fn):
        self.when_can_build_building(city, Building.Chapel, fn)

    def when_can_build_building(self, city, building, fn):
        self.when_resources_available(city, determine_building_cost(building), fn)

    def wait_for_conditions(self, conditions):
        while not all(condition() for condition in conditions):
            sleep(1.0 / 60)

    def wait_for_condition(self, condition):
        self.wait_for_conditions((condition,))

    def do_when_conditions_are_fulfilled(self, conditions, fn):
        self.wait_for_conditions(conditions)
        fn()

    def do_when_condition_is_fulfilled(self, condition, fn):
        self.do_when_conditions_are_fulfilled((condition,), fn)

    def exchange_goods_between_warehouse_and_ship(self, ship):
        self.select_ship(ship)
        self.select_info_mode()
        self.click_at_client_area_position((821, 611))

    def move_all_goods_from_ship_to_warehouse(self, ship):
        self.exchange_goods_between_warehouse_and_ship(ship)
        self.set_amount_to_be_traded_to_50t()
        self.load_goods_into_the_warehouse()
        self.select_slot_2_of_ship()
        self.load_goods_into_the_warehouse()
        self.select_slot_3_of_ship()
        self.load_goods_into_the_warehouse()
        self.select_slot_4_of_ship()
        self.load_goods_into_the_warehouse()

    def load_goods_into_the_warehouse(self):
        self.click_at_client_area_position((979, 554))

    def select_slot_2_of_ship(self):
        self.click_at_client_area_position((875, 674))

    def select_slot_3_of_ship(self):
        self.click_at_client_area_position((928, 676))

    def select_slot_4_of_ship(self):
        self.click_at_client_area_position((980, 672))

    def build_foresters_hut(self, position):
        self.place_building(Placement(Building.ForestersHut, position))

    def build_road(self, from_position, to_position):
        self.go_to_map_position(from_position)
        self.select_construction_mode()
        self.select_streets_and_bridges()
        self.select_road()
        self.move_mouse_to_map_position(from_position)
        self.drag_mouse_to_map_position(to_position)

    def build_forest_around_foresters_hut(self, position):
        self.go_to_map_position(position)
        self.select_construction_mode()
        self.select_farms_and_plantations()
        self.select_forest()
        self.move_mouse_to_map_position((position[0] + 2, position[1] + 4))
        self.drag_mouse_to_map_position((position[0] - 1, position[1] - 3))
        self.move_mouse_to_map_position((position[0] - 3, position[1] + 2))
        self.drag_mouse_to_map_position((position[0] + 4, position[1] - 1))
        self.click_at_map_position((position[0] - 2, position[1] + 3))
        self.click_at_map_position((position[0] - 2, position[1] - 2))
        self.click_at_map_position((position[0] + 3, position[1] - 1))
        self.click_at_map_position((position[0] + 3, position[1] + 3))

    def build_house(self, position):
        self.place_building(Placement(Building.HousePioneers, position))

    def increase_taxes_to_maximum(self, house_position):
        self.back_to_previous_menu()
        self.click_at_map_position(house_position)
        for i in range(16):
            self.increase_taxes_one_step()

    def increase_taxes_one_step(self):
        self.click_at_client_area_position((988, 537))

    def back_to_previous_menu(self):
        pyautogui.press('esc')

    def build_fishers_hut(self, position):
        self.place_building(Placement(Building.FishersHut, position))

    def build_market_place(self, position, rotation):
        self.place_building(Placement(Building.MarketPlace, position, rotation))

    def load_resources_into_ship(self, ship, resources):
        self.select_ship(ship)
        self.exchange_goods_between_warehouse_and_ship(ship)
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
                        self.select_exchange_goods_good_group(good_group_index)
                        has_good_group_been_selected = True
                    self.select_good_to_be_transferred(good_index)
                    self.transfer_selected_good_to_ship(resources[good])

    def select_exchange_goods_good_group(self, index):
        if index == 0:
            self.select_exchange_goods_good_group_building_material()
        elif index == 1:
            self.select_exchange_goods_good_group_weapons()
        elif index == 2:
            self.select_exchange_goods_good_group_consumer_goods()
        elif index == 3:
            self.select_exchange_goods_good_group_raw_materials()
        else:
            raise Exception('Unexpected index: ' + str(index))

    def select_exchange_goods_good_group_building_material(self):
        self.click_at_client_area_position((815, 495))

    def select_exchange_goods_good_group_weapons(self):
        self.click_at_client_area_position((873, 495))

    def select_exchange_goods_good_group_consumer_goods(self):
        self.click_at_client_area_position((929, 495))

    def select_exchange_goods_good_group_raw_materials(self):
        self.click_at_client_area_position((988, 499))

    def select_good_to_be_transferred(self, good_index):
        if good_index == 0:
            self.select_good_to_be_transferred_1()
        elif good_index == 1:
            self.select_good_to_be_transferred_2()
        elif good_index == 2:
            self.select_good_to_be_transferred_3()
        elif good_index == 3:
            self.select_good_to_be_transferred_4()
        else:
            raise Exception('Not implemented to select good to be transferred with index: ' + str(good_index))
        # TODO: Implement scrolling to goods

    def select_good_to_be_transferred_1(self):
        self.click_at_client_area_position((825, 445))

    def select_good_to_be_transferred_2(self):
        self.click_at_client_area_position((874, 445))

    def select_good_to_be_transferred_3(self):
        self.click_at_client_area_position((930, 445))

    def select_good_to_be_transferred_4(self):
        self.click_at_client_area_position((979, 445))

    def transfer_selected_good_to_ship(self, amount):
        remaining_amount = amount
        amounts_to_be_traded = [1, 5, 10, 50]
        for index in range(len(amounts_to_be_traded) - 1, -1, -1):
            amount_to_be_traded = amounts_to_be_traded[index]
            if remaining_amount >= amount_to_be_traded:
                self.set_amount_to_be_traded(amount_to_be_traded)
                while remaining_amount >= amount_to_be_traded:
                    self.load_goods_onboard_the_ship()
                    remaining_amount -= amount_to_be_traded

    def set_amount_to_be_traded(self, amount):
        if amount == 1:
            self.set_amount_to_be_traded_to_1t()
        elif amount == 5:
            self.set_amount_to_be_traded_to_5t()
        elif amount == 10:
            self.set_amount_to_be_traded_to_10t()
        elif amount == 50:
            self.set_amount_to_be_traded_to_50t()

    def set_amount_to_be_traded_to_1t(self):
        self.click_at_client_area_position((856, 555))

    def set_amount_to_be_traded_to_5t(self):
        self.click_at_client_area_position((879, 554))

    def set_amount_to_be_traded_to_10t(self):
        self.click_at_client_area_position((904, 553))

    def set_amount_to_be_traded_to_50t(self):
        self.click_at_client_area_position((934, 553))

    def load_goods_onboard_the_ship(self):
        self.click_at_client_area_position((821, 552))

    def set_tools_to_be_bought(self):
        self.select_warehouse()
        self.determine_products_to_be_bought()
        self.determine_first_product_to_be_bought_to_be_tools()

    def select_warehouse(self):
        warehouse_position = (214, 161)
        self.go_to_map_position(warehouse_position)
        self.click_at_map_position(warehouse_position)

    def determine_products_to_be_bought(self):
        self.click_at_client_area_position((864, 731))

    def determine_first_product_to_be_bought_to_be_tools(self):
        self.click_at_client_area_position((822, 619))
        self.click_at_client_area_position((815, 718))
        self.click_at_client_area_position((875, 533))  # set buy price to 75 gold

    def build_cloth_production_group(self, city, position):
        self.when_can_build_building(city, Building.SheepFarm,
                                     lambda: self.build_sheep_farm((position[0] + 3, position[1] - 4)))
        self.when_can_build_building(city, Building.SheepFarm,
                                     lambda: self.build_sheep_farm((position[0] + 3, position[1] - 12)))
        self.when_can_build_building(city, Building.WeaversHut,
                                     lambda: self.build_weavers_hut((position[0] + 6, position[1] - 8)))

    def build_sheep_farm(self, position):
        self.place_building(Placement(Building.SheepFarm, position))
        self.remove_trees_around_sheep_farm(position)

    def remove_trees_around_sheep_farm(self, position):
        self.go_to_map_position(position)
        self.activate_demolition_mode()
        self.move_mouse_to_map_position((position[0] + 2, position[1] + 4))
        self.drag_mouse_to_map_position((position[0] - 1, position[1] - 3))
        self.move_mouse_to_map_position((position[0] - 3, position[1] + 2))
        self.drag_mouse_to_map_position((position[0] + 4, position[1] - 1))
        self.click_at_map_position((position[0] - 2, position[1] + 3))
        self.click_at_map_position((position[0] - 2, position[1] - 2))
        self.click_at_map_position((position[0] + 3, position[1] - 1))
        self.click_at_map_position((position[0] + 3, position[1] + 3))

    def activate_demolition_mode(self):
        self.select_construction_mode()
        self.click_at_client_area_position((984, 661))

    def build_weavers_hut(self, position):
        self.place_building(Placement(Building.WeaversHut, position))

    def build_chapel(self, position):
        self.place_building(Placement(Building.Chapel, position))

    def when_a_house_has_upgraded_to_settlers(self, city, fn):
        self.do_when_condition_is_fulfilled(lambda: self.has_a_house_upgraded_to_settlers(city), fn)

    def has_a_house_upgraded_to_settlers(self, city):
        cities = self.read_cities()
        city = cities[city]
        return city.population[1] >= 1

    def increase_taxes_for_settlers(self, city_index):
        city = self.retrieve_city(city_index)
        island = self.retrieve_island(city.island_index)
        self.select_a_settler_house(island)
        self.increase_taxes_one_step()

    def retrieve_city(self, city_index):
        cities = self.read_cities()
        city = cities[city_index]
        return city

    def retrieve_island(self, island_index):
        islands = self.read_islands()
        island = islands[island_index]
        return island

    def select_a_settler_house(self, island):
        settler_house_island_position = self.find_settler_house(island)
        if settler_house_island_position:
            settler_house_position = (
                island.x + settler_house_island_position[0],
                island.y + settler_house_island_position[1]
            )
            self.click_at_map_position(settler_house_position)
        else:
            raise Exception('0 settler houses have been found.')

    def find_settler_house(self, island):
        fields = self.read_island_fields(island)
        for row in range(len(fields)):
            for column in range(len(fields[0])):
                if fields[row][column] in {20621, 20622, 20623, 20624, 20625}:
                    return (column, row)
        return None

    def build(self, build_template, position):
        for placement in build_template.placements:
            x = position[0] + placement.position[0]
            y = position[1] + placement.position[1]
            placement_position = (x, y)
            placement2 = Placement(placement.type, placement_position, placement.rotation)
            self.place_building(placement2)


def main():
    anno1602 = Anno1602AI()

    while GetForegroundWindow() != anno1602.window:
        sleep(1)
    sleep(1)

    anno1602.speed_up_8x()

    # ship = 0
    # ship_destination = (217, 162)
    # anno1602.move_ship(ship, ship_destination)
    # warehouse_position = (213, 160)
    # anno1602.wait_for_ship_has_arrived(ship)
    # anno1602.explore_the_island(ship)
    # anno1602.build_warehouse_from_ship(ship, warehouse_position)
    # anno1602.move_all_goods_from_ship_to_warehouse(ship)
    # anno1602.build_road((212, 162), (197, 162))
    # foresters_hut_position = (207, 166)
    # anno1602.build_foresters_hut(foresters_hut_position)
    # anno1602.build_road((208, 165), (208, 163))
    # anno1602.build_forest_around_foresters_hut(foresters_hut_position)
    # foresters_hut_position = (199, 166)
    # anno1602.build_foresters_hut(foresters_hut_position)
    # anno1602.build_road((200, 165), (200, 163))
    # anno1602.build_forest_around_foresters_hut(foresters_hut_position)
    # anno1602.build_road((212, 161), (212, 148))
    city = 0
    # house_positions = (
    #     (210, 160),
    #     (208, 160),
    #     (206, 160),
    #     (210, 158),
    #     (208, 158),
    #     (206, 158),
    #     (210, 155),
    #     (208, 155),
    #     (206, 155),
    #     (210, 153),
    #     (208, 153),
    #     (206, 153),
    #     (203, 160),
    #     (203, 158),
    #     (201, 160),
    #     (201, 158),
    #     (199, 158)
    # )
    # for index in range(len(house_positions)):
    #     house_position = house_positions[index]
    #     anno1602.when_can_build_house(city, lambda: anno1602.build_house(house_position))
    #     if index == 0:
    #         anno1602.increase_taxes_to_maximum(house_position)
    # anno1602.when_can_build_fishers_hut(city, lambda: anno1602.build_fishers_hut((215, 159)))
    # anno1602.build_road((214, 159), (213, 159))
    # warehouse_cost = create_rates({'tools': 3, 'wood': 6})
    #
    # def settle_second_island():
    #     anno1602.load_resources_into_ship(ship, warehouse_cost)
    #     anno1602.move_ship(ship, (248, 159))
    #     anno1602.when_ship_has_arrived(ship, build_second_warehouse_and_move_ship_back_and_set_tools_to_be_bought)
    #
    # def build_second_warehouse_and_move_ship_back_and_set_tools_to_be_bought():
    #     anno1602.build_warehouse_from_ship(ship, (251, 156))
    #     anno1602.move_ship(ship, (217, 162))
    #     anno1602.set_tools_to_be_bought()
    #
    # anno1602.when_resources_available(city, warehouse_cost, settle_second_island)
    # anno1602.when_can_build_market_place(city, lambda: anno1602.build_market_place((195, 158),
    #                                                                                Rotation.Rotated90Degree))  # FIXME: seems to sometimes build it with different rotation
    # anno1602.build_cloth_production_group(city, (186, 161))
    # anno1602.build_road((196, 162), (194, 153))
    # anno1602.when_can_build_chapel(city, lambda: anno1602.build_chapel((203, 155)))
    # anno1602.when_can_build_fishers_hut(city, lambda: anno1602.build_fishers_hut((217, 148)))
    # anno1602.build_road((216, 148), (213, 148))
    city = 1
    anno1602.when_a_house_has_upgraded_to_settlers(city, lambda: anno1602.increase_taxes_for_settlers(city))
    # build(the_ultimate_city, (217, 151))
    exit()

    # -12, -6
    # 4
    anno1602.place_building(Placement(Building.HousePioneers, (5 + 9, 5 + 6)))

    while True:
        # milestones
        # * population group 2
        #   * cloth production
        #   * market place
        #   * chapel

        # TODO: Input from game
        current_population = np.array((
            anno1602.process.read_int(anno1602.process.base_address + POPULATION),
            anno1602.process.read_int(anno1602.process.base_address + POPULATION + 4),
            anno1602.process.read_int(anno1602.process.base_address + POPULATION + 8),
            anno1602.process.read_int(anno1602.process.base_address + POPULATION + 16),
            anno1602.process.read_int(anno1602.process.base_address + POPULATION + 20),
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
                    production_building = select_building_with_highest_production_efficiency(available_buildings,
                                                                                             good_name)
                    if production_building:
                        number_of_production_building = int(
                            math.ceil(rate / production_building['yield rate'][good_name]))
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
