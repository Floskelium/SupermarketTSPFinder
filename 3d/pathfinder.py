
from itertools import permutations
import heapq


def heuristic(a, b):
    """Heuristic function for A* (Manhattan distance)"""
    return abs(a['x'] - b['x']) + abs(a['y'] - b['y'])


def get_neighbors(tile, tile_dict):
    """Generate neighboring tiles"""
    x, y = tile['x'], tile['y']
    neighbors = []
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # left, right, up, down
        neighbor_pos = (x + dx, y + dy)
        # Find tile at the neighboring position
        for neighbor in tile_dict.values():
            if (neighbor['x'], neighbor['y']) == neighbor_pos:
                neighbors.append(neighbor)
                break
    return neighbors


def a_star(start_id, goal_id, tile_dict):
    """A* algorithm to find the shortest path between two tiles"""
    start_tile = tile_dict[start_id]
    goal_tile = tile_dict[goal_id]

    open_set = []
    heapq.heappush(open_set, (0, start_id))
    came_from = {}
    g_score = {tile_id: float('inf') for tile_id in tile_dict}
    g_score[start_id] = 0
    f_score = {tile_id: float('inf') for tile_id in tile_dict}
    f_score[start_id] = heuristic(start_tile, goal_tile)

    while open_set:
        current_id = heapq.heappop(open_set)[1]

        if current_id == goal_id:
            # Reconstruct path
            path = []
            while current_id in came_from:
                path.append(current_id)
                current_id = came_from[current_id]
            path.append(start_id)
            return path[::-1]  # Return reversed path

        for neighbor in get_neighbors(tile_dict[current_id], tile_dict):
            neighbor_id = neighbor['id']
            tentative_g_score = g_score[current_id] + 1  # assume uniform cost

            if tentative_g_score < g_score[neighbor_id]:
                came_from[neighbor_id] = current_id
                g_score[neighbor_id] = tentative_g_score
                f_score[neighbor_id] = tentative_g_score + heuristic(neighbor, goal_tile)
                heapq.heappush(open_set, (f_score[neighbor_id], neighbor_id))

    return []  # Return empty if no path is found


def calculate_distances(ids, tile_dict):
    """Calculate pairwise distances between all tiles in the list using A*"""
    distances = {}
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            id1, id2 = ids[i], ids[j]
            path = a_star(id1, id2, tile_dict)
            distance = len(path) - 1  # distance is the number of edges
            distances[(id1, id2)] = (distance, path)
            distances[(id2, id1)] = (distance, path[::-1])
    return distances


def tsp_nearest_neighbor(start_id, end_id, ids, distances: dict):
    """Approximate TSP using a greedy nearest-neighbor approach"""
    path = [start_id]
    current_id = start_id
    unvisited = set(ids) - {start_id, end_id}

    while unvisited:
        # Find the nearest unvisited neighbor
        next_id = min(unvisited, key=lambda id: distances[(current_id, id)][0])
        path.append(next_id)
        unvisited.remove(next_id)
        current_id = next_id

    path.append(end_id)  # End at the specified endpoint
    return path


def total_distance(path, distances):
    """Calculate the total distance for a given path based on precomputed distances."""
    distance = 0
    for i in range(len(path) - 1):
        distance += distances[(path[i], path[i+1])][0]
    return distance


def tsp_brute_force(start_id, end_id, ids, distances):
    """Brute-force TSP to find the optimal path by checking all permutations."""
    # All IDs to visit except the start and end points
    intermediate_ids = set(ids) - {start_id, end_id}

    # Track the best path and minimum distance
    min_path = None
    min_distance = float('inf')

    # Generate all permutations of the intermediate IDs
    for perm in permutations(intermediate_ids):
        # Create a full path: start -> perm -> end
        path = [start_id] + list(perm) + [end_id]
        distance = total_distance(path, distances)

        # Check if this path is the shortest
        if distance < min_distance:
            min_distance = distance
            min_path = path

    return min_path, min_distance



# TODO implement greedy: lowest cost edge used as long as no degr > 2 created and no path from start to end until all nodes included
def tsp_greedy(start_id, end_id, ids, distances: dict):
    path = [start_id]  # Start the path with the starting node
    current_id = start_id
    unvisited = set(ids) - {start_id, end_id}
    edges = []  # Track the edges included in the path

    # Track the degree of each node to avoid nodes of degree > 2
    degrees = {node: 0 for node in ids}
    degrees[start_id] = 1  # start and end nodes will each have degree 1
    degrees[end_id] = 1

    # Helper function to check if adding an edge would form a cycle or violate node degree limits
    def can_add_edge(from_node, to_node):
        # Check if adding the edge would exceed the degree limit for either node
        if degrees[from_node] >= 2 or degrees[to_node] >= 2:
            return False
        # Check if the edge would create a cycle
        temp_edges = edges + [(from_node, to_node)]
        visited = set()

        def dfs(node):
            if node in visited:
                return
            visited.add(node)
            for a, b in temp_edges:
                if a == node and b not in visited:
                    dfs(b)
                elif b == node and a not in visited:
                    dfs(a)

        # Start DFS from the start node and see if all nodes in the path are connected
        dfs(start_id)
        # If all nodes in path are connected (visited set includes all but end node), no cycle is created
        return len(visited) < len(temp_edges) + 1

    # Main loop: Greedily add edges to build the path
    while unvisited:
        # Find the nearest unvisited neighbor
        next_id = min(unvisited, key=lambda id: distances[(current_id, id)][0])

        # Check if we can add the edge without violating the rules
        if can_add_edge(current_id, next_id):
            # Add the edge
            path.append(next_id)
            edges.append((current_id, next_id))
            degrees[current_id] += 1
            degrees[next_id] += 1

            # Update current node and remove from unvisited
            current_id = next_id
            unvisited.remove(next_id)
        else:
            # If the edge can't be added, remove the next_id from unvisited and try another node
            unvisited.remove(next_id)

    # Only connect to the endpoint if all nodes have been visited
    if can_add_edge(current_id, end_id) and not unvisited:
        path.append(end_id)
        edges.append((current_id, end_id))
        degrees[current_id] += 1
        degrees[end_id] += 1
    else:
        print("Warning: Could not connect to the end node without including all nodes or forming a cycle.")

    return path



if __name__ == '__main__':
    width = 10
    height = 10

    tiles = [
        {"id": x+y*width, "x": x, "y": y, "type": None if y > 0 and x > 0 else "wall-corner" if x == 0 and y == 0 else "wall", "rotation": 90 if x == 0 else None} for x in range(0, width) for y in range(0, height)
    ]

    # Convert tiles list to a dictionary for easy access by id
    tile_dict = {tile['id']: tile for tile in tiles}

    # list to collect
    ids_to_visit = [12, 17, 38, 52, 99, 80]  # List of IDs we want to visit
    start_id, end_id = ids_to_visit[0], ids_to_visit[-1]   # Define start and end IDs for TSP

    # Step 1: Calculate pairwise distances between IDs
    distances = calculate_distances(ids_to_visit, tile_dict)
    print(distances)

    # Step 2: Solve TSP to find the shortest path visiting all IDs
    tsp_path = tsp_nearest_neighbor(start_id, end_id, ids_to_visit, distances)
    print("NN path:", tsp_path)
    print("NN distance:", total_distance(tsp_path, distances))

    optimal_path, optimal_distance = tsp_brute_force(start_id, end_id, ids_to_visit, distances)

    # Display result
    print("Optimal paths:", optimal_path)
    print("Optimal distance:", optimal_distance)

    # greedy_path = tsp_greedy(start_id, end_id, ids_to_visit, distances)
    # print("Greedy path:", greedy_path)
    # print("Greedy distance:", total_distance(greedy_path, distances))
