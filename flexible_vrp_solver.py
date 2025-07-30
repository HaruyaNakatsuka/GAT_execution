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


def solve_vrp_flexible(customers, pickup_to_delivery, num_vehicles, vehicle_capacity,
                       use_capacity:bool, use_time:bool, use_pickup_delivery:bool):

    depot = 0
    time_windows = [(c['ready'], c['due']) for c in customers]
    service_times = [c['service'] for c in customers]
    demands = [c['demand'] for c in customers]
    distance_matrix = create_distance_matrix(customers)

    manager = pywrapcp.RoutingIndexManager(len(customers), num_vehicles, depot)
    routing = pywrapcp.RoutingModel(manager)
    

    def distance_callback(from_idx, to_idx):
        try:
            from_node = manager.IndexToNode(from_idx)
            to_node = manager.IndexToNode(to_idx)
            return distance_matrix[from_node][to_node]
        except:
            return 999999
    transit_cb = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)
    
    

    # 容量制約
    if use_capacity:
        def demand_callback(from_idx):
            return demands[manager.IndexToNode(from_idx)]
        demand_cb = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_cb, 0, [vehicle_capacity] * num_vehicles, True, 'Capacity'
        )

    # 時間制約
    if use_time:
        def time_callback(from_idx, to_idx):
            from_node = manager.IndexToNode(from_idx)
            to_node = manager.IndexToNode(to_idx)
            return distance_matrix[from_node][to_node] + service_times[from_node]
        time_cb = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(time_cb, 30, 10000, False, "Time")
        time_dim = routing.GetDimensionOrDie("Time")
        for node_idx in range(len(customers)):
            idx = manager.NodeToIndex(node_idx)
            time_dim.CumulVar(idx).SetRange(*time_windows[node_idx])

    # Pickup and Delivery 制約（修正）
    if use_pickup_delivery:
        routing.AddDimension(
            transit_cb,
            0,  # no slack
            10000,  # vehicle maximum travel distance
            True,  # start cumul to zero
            "Distance",
        )
        distance_dimension = routing.GetDimensionOrDie("Distance")
        distance_dimension.SetGlobalSpanCostCoefficient(100)
        
        id_to_index = {c['id']: i for i, c in enumerate(customers)}# ID → インデックス辞書
        for pickup_id, delivery_id in pickup_to_delivery.items():
            if pickup_id not in id_to_index or delivery_id not in id_to_index:
                print(f"Invalid ID pair: {pickup_id}, {delivery_id}")
                continue

            pickup_idx = manager.NodeToIndex(id_to_index[pickup_id])
            delivery_idx = manager.NodeToIndex(id_to_index[delivery_id])

            routing.AddPickupAndDelivery(pickup_idx, delivery_idx)
            routing.solver().Add(routing.VehicleVar(pickup_idx)
                                 == routing.VehicleVar(delivery_idx))
            routing.solver().Add(distance_dimension.CumulVar(pickup_idx)
                                 <= distance_dimension.CumulVar(delivery_idx))


    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    #search_params.log_search = True

    solution = routing.SolveWithParameters(search_params)
    if not solution:
        print("No solution found.")
        return None

    # 解の取得
    result = []
    for vehicle_id in range(num_vehicles):
        idx = routing.Start(vehicle_id)
        plan_output = f"vehicle {vehicle_id+1} : "
        route = []
        while not routing.IsEnd(idx):
            route.append(customers[manager.IndexToNode(idx)]['id'])
            plan_output += f"{customers[manager.IndexToNode(idx)]['id']} -> "
            idx = solution.Value(routing.NextVar(idx))
        route.append(customers[manager.IndexToNode(idx)]['id'])
        plan_output += f"{customers[manager.IndexToNode(idx)]['id']}"
        print(plan_output)
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