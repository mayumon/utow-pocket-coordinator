import json


def load_teams(filepath='teams.json'):
    with open(filepath, 'r') as file:
        return sorted(json.load(file))


def load_maps(filepath='maps.json'):
    with open(filepath, 'r') as file:
        maps = json.load(file)

    # sort maps alphabetically
    sorted_maps = sorted(maps, key=lambda x: x.split("__")[1])
    return sorted_maps
