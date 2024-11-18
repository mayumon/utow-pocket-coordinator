import json

def load_teams(file_path='teams.json'):
    with open(file_path, 'r', encoding='utf-8') as file:
        return sorted(json.load(file))

def load_maps(file_path='maps.json'):
    with open(file_path, 'r', encoding='utf-8') as file:
        maps = json.load(file)
    sorted_maps = {}
    for game_mode, map_list in maps.items():
        sorted_maps[game_mode] = sorted(map_list, key=lambda x: x.split("__")[1].split("__")[0].strip())
    return sorted_maps
