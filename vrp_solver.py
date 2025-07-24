from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math


def euclidean_distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)


def create_distance_matrix(customers):
    size = len(customers)
    matrix = [[0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            matrix[i][j] = int(
                euclidean_distance(
                    customers[i]['x'], customers[i]['y'],
                    customers[j]['x'], customers[j]['y']
                )
            )
    return matrix


def solve_vrp(customers, pickup_to_delivery, num_allnodes, num_vehicles, vehicle_capacity):
    # ノード数とデポのインデックス（通常0）
    depot = 0

    # 時間窓の抽出
    time_windows = [(c['ready'], c['due']) for c in customers]
    service_times = [c['service'] for c in customers]
    demands = [c['demand'] for c in customers]

    # 距離行列
    distance_matrix = create_distance_matrix(customers)

    # Routing Index Manager
    manager = pywrapcp.RoutingIndexManager(num_allnodes, num_vehicles, depot)

    # Routing Model
    routing = pywrapcp.RoutingModel(manager)

    # 距離コスト
    def distance_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # 容量制約
    def demand_callback(from_idx):
        from_node = manager.IndexToNode(from_idx)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index, 0, [vehicle_capacity] * num_vehicles, True, 'Capacity')

    # 時間制約
    def time_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return distance_matrix[from_node][to_node] + service_times[from_node]

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        time_callback_index,
        30,  # allow waiting time
        10000,  # max horizon
        False,
        "Time"
    )
    time_dim = routing.GetDimensionOrDie("Time")
    for node_idx in range(len(customers)):
        index = manager.NodeToIndex(node_idx)
        time_dim.CumulVar(index).SetRange(*time_windows[node_idx])

    # Pickup and Delivery constraints
    for pickup_id, delivery_id in pickup_to_delivery.items():
        pickup_idx = manager.NodeToIndex(pickup_id - customers[0]['id'])
        delivery_idx = manager.NodeToIndex(delivery_id - customers[0]['id'])
        routing.AddPickupAndDelivery(pickup_idx, delivery_idx)
        routing.solver().Add(routing.VehicleVar(pickup_idx) == routing.VehicleVar(delivery_idx))
        routing.solver().Add(time_dim.CumulVar(pickup_idx) <= time_dim.CumulVar(delivery_idx))

    print("Here")
    # 解く
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    print("H1")
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    print("H2")
    solution = routing.SolveWithParameters(search_params)
    print("H3")

    if not solution:
        print("解が見つかりませんでした。")
        return None

    # 解の表示
    result = []
    for vehicle_id in range(num_vehicles):
        idx = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(idx):
            node_index = manager.IndexToNode(idx)
            route.append(customers[node_index]['id'])
            idx = solution.Value(routing.NextVar(idx))
        route.append(customers[manager.IndexToNode(idx)]['id'])  # End node
        result.append(route)

    return result

def route_cost(route, customers):
    """ルートの総距離を計算する簡易関数"""
    id_to_coord = {c['id']: (c['x'], c['y']) for c in customers}
    cost = 0
    for i in range(len(route) - 1):
        x1, y1 = id_to_coord[route[i]]
        x2, y2 = id_to_coord[route[i + 1]]
        cost += ((x2 - x1)**2 + (y2 - y1)**2)**0.5
    return cost

