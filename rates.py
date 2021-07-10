import numpy as np


good_names = (
    'iron ore',
    'gold',
    'wool',
    'sugar',
    'tobacco',
    'cattle',
    'grain',
    'flour',
    'iron',
    'swords',
    'muskets',
    'cannon',
    'food',
    'tobacco products',
    'spices',
    'cocoa',
    'liquor',
    'cloth',
    'clothes',
    'jewelry',
    'tools',
    'wood',
    'bricks',
    'money'
)


good_names_COD = (
    'EISENERZ',
    'GOLD',
    'BAUMWOLLE',
    'ZUCKER',
    'TABAK',
    'FLEISCH',
    'GETREIDE',
    'MEHL',
    'EISEN',
    'SCHWERTER',
    'MUSKETEN',
    'KANONEN',
    'NAHRUNG',
    'TABAKWAREN',
    'GEWUERZE',
    'KAKAO',
    'ALKOHOL',
    'STOFFE',
    'KLEIDUNG',
    'SCHMUCK',
    'WERKZEUG',
    'HOLZ',
    'STEINE',
    'MONEY'
)


def cod_good_name_to_internal_good_name(cod_good_name):
    index = good_names_COD.index(cod_good_name)
    return good_names[index]


# consumption or yield rates
# positive number can be interpreted as yield
# negative number can be interpreted as consumption
def create_rates_vector():
    return np.zeros((len(good_names)))


def create_rates(rates):
    consumption_rates_values = create_rates_vector()
    for good_name, consumption_rate in rates.items():
        consumption_rates_values[good_names.index(good_name)] = float(consumption_rate)
    return np.array(consumption_rates_values)
