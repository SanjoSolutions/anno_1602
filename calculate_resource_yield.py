from a_parser import parse


def is_house_of_kind(house, kind):
    return (
        'HAUS_PRODTYP' in house and
        'Kind' in house['HAUS_PRODTYP'] and
        house['HAUS_PRODTYP']['Kind'] == 'FISCHEREI'
    )


haeuser = parse('../haeuser.txt')
fishers_hut = next(house for house in haeuser['HAUS'] if is_house_of_kind(house, 'FISCHEREI'))
print(fishers_hut)


def calculate_resource_yield(building):
    pass
