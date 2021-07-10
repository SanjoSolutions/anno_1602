from a_parser import parse
from other.Building import Building
from other.rates import create_rates, cod_good_name_to_internal_good_name


def is_house_of_kind(house, kind):
    return (
        'HAUS_PRODTYP' in house and
        'Kind' in house['HAUS_PRODTYP'] and
        house['HAUS_PRODTYP']['Kind'] == kind
    )


haeuser = parse('../haeuser.txt')
figuren = parse('../figuren.txt')


def is_figure_with_number(figure, id):
    return (
        'Nummer' in figure and
        figure['Nummer'] == id
    )


def retrieve_figure(id):
    return next(figure for figure in figuren['FIGUR'] if is_figure_with_number(figure, id))


buildings_where_the_worker_collects_resources_and_processes_them = {
    Building.HuntingLodge,
    Building.FishersHut,
    Building.GrainFarm,
    Building.FlourMill,
    Building.WaterMill,
    Building.ButchersShop,
    Building.Bakery,
    Building.ForestersHut,
    Building.Stonemason,
    Building.OreSmelter,
    Building.ToolMaker,
    Building.CottonPlantation,
    Building.WeaversHut,
    Building.WeavingMill,
    Building.TailorsShop,
    Building.SugarcanePlantation,
    Building.Winery,
    Building.Distillery,
    Building.CocoaPlantation,
    Building.TobaccoPlantation,
    Building.TobaccoProducts,
    Building.SpicePlantation,
    Building.Goldsmith
}

buildings_where_the_worker_only_processes_resources = {
    Building.CattleFarm,
    Building.SheepFarm
}


def calculate_resource_yield(building):
    worker = retrieve_figure(building['HAUS_PRODTYP']['Figurnr'])
    number = building['@Nummer']
    if number in buildings_where_the_worker_collects_resources_and_processes_them:
        production_of_resource = (60.0 / (building['HAUS_PRODTYP']['Rohmenge'] * worker['Worktime'] + building['HAUS_PRODTYP']['Interval'])) / 60.0  # units per second
    elif number in buildings_where_the_worker_only_processes_resources:
        production_of_resource = (60.0 / building['HAUS_PRODTYP']['Interval']) / 60.0  # units per second
    else:
        raise Exception('Formula for house with number "' + str(number) + '" seems to be unimplemented.')

    rates = create_rates({
        cod_good_name_to_internal_good_name(building['HAUS_PRODTYP']['Ware']): production_of_resource
    })
    return rates


def determine_building_cost(building):
    building_data = find_building(building)
    building_cost = building_data['HAUS_BAUKOST']
    return create_rates(
        dict(
            (
                cod_good_name_to_internal_good_name(resource_name.upper()),
                amount
            )
            for resource_name, amount
            in building_cost.items()
        )
    )


def find_building(building):
    return next((house for house in haeuser['HAUS'] if house['@Nummer'] == building), default=None)


def main():
    fishers_hut = next(house for house in haeuser['HAUS'] if is_house_of_kind(house, 'FISCHEREI'))
    print(fishers_hut)
    fisher = retrieve_figure('FISCHER')
    fishers_hut_yield = calculate_resource_yield(fishers_hut)
    print('fishers_hut_yield:', fishers_hut_yield)


if __name__ == '__main__':
    main()
