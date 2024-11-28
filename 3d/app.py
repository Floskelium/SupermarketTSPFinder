from flask import Flask, jsonify, request, render_template, send_from_directory
from pathfinder import calculate_distances, tsp_nearest_neighbor, tsp_brute_force
from db import GroceryDBInterface

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/map-data')
def map_data():
    return jsonify(map_data_dict)


@app.route('/model/<path:filename>')
def model(filename):
    # This serves the .fbx model file
    return send_from_directory('static/fbx', filename)


@app.route('/model/colormap.png')
def serve_image():
    return send_from_directory('static', 'colormap.png', mimetype='image/png')


@app.route('/pathfind', methods=['POST'])
def pathfind():
    data = request.json
    items = data['items']  # list of items

    #for item in items:
    #    print(item)
    #    result = db_interface.search_groceries(item)
    #    print(result)

    path_dict = [{'x': tile_dict[p]['x'], 'y': tile_dict[p]['y']} for p in path]
    optimal_path_dict = [{'x': tile_dict[p]['x'], 'y': tile_dict[p]['y']} for p in optimal_path]

    # TODO return list of subpaths, items per subpickup, pickupspot for subpickups
    return jsonify(path=path_dict, pickup=optimal_path_dict)


db_interface = GroceryDBInterface()


@app.route('/groceries', methods=['GET'])
def all_groceries():
    groceries = db_interface.get_all_groceries()
    return jsonify(groceries)


@app.route('/groceries/category/<category_name>', methods=['GET'])
def groceries_by_category(category_name):
    groceries = db_interface.get_groceries_by_category(category_name)
    return jsonify(groceries)


@app.route('/grocery/<int:grocery_id>', methods=['GET'])
def grocery_by_id(grocery_id):
    grocery = db_interface.get_grocery_by_id(grocery_id)
    return jsonify(grocery) if grocery else jsonify({"error": "Grocery not found"}), 404


@app.route('/groceries/shelf/<int:shelf_id>', methods=['GET'])
def groceries_by_shelf(shelf_id):
    groceries = db_interface.get_groceries_by_shelf(shelf_id)
    return jsonify(groceries)


@app.route('/search/<search_term>', methods=['GET'])
def search_groceries(search_term):
    results = db_interface.search_groceries(search_term)
    return jsonify(results)


if __name__ == '__main__':
    width = 10
    height = 10
    map_data_dict = {
        "tiles": [
            {"id": x+y*width, "x": x, "y": y, "shelf_id": None, "type": None if y > 0 and x > 0 else "wall-corner" if x == 0 and y == 0 else "wall", "rotation": 90 if x == 0 else None} for x in range(0, width) for y in range(0, height)
        ]
    }
    import random

    category_to_display = {
        "Start": {"type": "floor", "id": 99},
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

    ids_to_visit = []
    tile_dict = {tile['id']: tile for tile in map_data_dict['tiles']}

    for i in category_to_display.values():
        x = random.randint(1, width-2)
        y = random.randint(1, height-2)
        shelf = tile_dict[x+y*width]
        while shelf['type'] is not None:
            x = random.randint(1, 8)
            y = random.randint(1, 8)
            shelf = tile_dict[x+y*width]

        shelf["shelf_id"] = i['id']
        shelf["type"] = i['type']
        ids_to_visit.append(x+y*width)

    distances = calculate_distances(ids_to_visit, tile_dict)
    # tsp_path = tsp_nearest_neighbor(ids_to_visit[0], ids_to_visit[-1], ids_to_visit, distances)
    optimal_path, _ = tsp_brute_force(ids_to_visit[0], ids_to_visit[-1], ids_to_visit, distances)

    path = []
    for i in range(len(optimal_path)-1):
        path.extend(distances[(optimal_path[i], optimal_path[i+1])][1][1 if i > 0 else 0:])

    app.run(debug=True)
