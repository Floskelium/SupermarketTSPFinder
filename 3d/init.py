import random

width = 10
height = 10

# Define the various types for the store layout
types = ["freezer", "bottle-return", "cash-register", "shelf-boxes",
         "shelf-bags", "freezer-standing", "display-bread", "display-fruit"]

# Create a category-to-display mapping (assuming these categories are in the database)
# Each key is a display type that corresponds to common grocery categories
category_to_display = {
    "Start": {"type": None, "id": 99},
    "Mehl": {"type": "shelf-boxes", "id": 1},
    "Apfel": {"type": "display-fruit", "id": 2},
    "Gemüse": {"type": "display-fruit", "id": 2},
    "Müsli": {"type": "shelf-bags", "id": 3},
    "Fleisch": {"type": "freezer", "id": 7},
    "Brot": {"type": "display-bread", "id": 6},
    "Milch": {"type": "freezer-standing", "id": 4},
    "Getränke": {"type": "bottle-return", "id": 10},
    "Kasse": {"type": "cash-register", "id": 0},
}

# Create the tiles for the map
map_data_dict = {
    "tiles": [
        {
            "id": None,
            "x": x,
            "y": y,
            "type": (
                "wall-corner" if (x == 0 and y == 0) or (x == 0 and y == height - 1) or
                                 (x == width - 1 and y == 0) or (x == width - 1 and y == height - 1)
                else "wall" if x == 0 or y == 0 or x == width - 1 or y == height - 1
                else None
            ),
            "rotation": (
                90 if x == 0 and y not in [0, height - 1] else
                180 if y == height - 1 and x not in [0, width - 1] else
                270 if x == width - 1 and y not in [0, height - 1] else
                0 if y == 0 and x not in [0, width - 1] else None
            )
        }
        for y in range(height)
        for x in range(width)
    ]
}

# Assign shelves according to `category_to_display` mapping, avoiding wall tiles
for category, display_type in category_to_display.items():
    tile_index = random.randint(0, width*height-1)
    while map_data_dict["tiles"][tile_index]["type"] != None:
        tile_index = random.randint(0, width*height-1)

    map_data_dict["tiles"][tile_index]["type"] = display_type['type']
    map_data_dict['tiles'][tile_index]['id'] = display_type['id']

if __name__ == '__main__':
    print(map_data_dict)
