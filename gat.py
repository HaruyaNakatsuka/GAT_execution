#from vrp_solver import solve_vrp, route
from flexible_vrp_solver import solve_vrp_flexible, route_cost


def initialize_individual_vrps(customers, pickup_to_delivery, num_all_lsps, num_all_vehicles, vehicle_capacity, seed=42):
    import random
    random.seed(seed)
    requests = list(pickup_to_delivery.items())
    random.shuffle(requests)

    last_id = customers[-1]['id']

    lsp_assignments = [[] for _ in range(num_all_lsps)]
    for i, req in enumerate(requests):
        lsp_assignments[i % num_all_lsps].append(req)

    lsp_routes = []
    for reqs in lsp_assignments:
        involved_ids = set()
        for p, d in reqs:
            involved_ids.update([p, d])
        sub_customers = [c for c in customers if c['id'] in involved_ids or c['id'] == 0]
        sub_pickup_to_delivery = {p: d for p, d in reqs}
        ### ↓エラー発生
        route = solve_vrp_flexible(sub_customers, sub_pickup_to_delivery, num_vehicles=int(num_all_vehicles/num_all_lsps), vehicle_capacity=vehicle_capacity,
                       use_capacity=False, use_time=False, use_pickup_delivery=True)
        #route = solve_vrp(sub_customers, sub_pickups, last_id, num_vehicles=int(num_all_vehicles/num_all_lsps), vehicle_capacity=vehicle_capacity)
        for r in route:
            lsp_routes.append(r)

    return lsp_routes, lsp_assignments

def perform_gat_exchange(all_vehicles_routes, customers, pickup_to_delivery, vehicle_capacity):
    feasible_actions = []#実行可能アクション集合
    num_vehicles = len(all_vehicles_routes)
    
    #各車両ごとの集荷->配達のペアをまとめたリストを作成
    pickup_to_delivery_for_vehicle = []
    for vehicle_route in all_vehicles_routes:
        related_pairs = []
        visited_set = set(vehicle_route)
        for pickup, delivery in pickup_to_delivery.items():
            if pickup in visited_set or delivery in visited_set:
                related_pairs.append((pickup, delivery))
        pickup_to_delivery_for_vehicle.append(related_pairs)

    #全2車両ペアに対して2車両VRPを実行
    for i in range(num_vehicles):
        for j in range(i + 1, num_vehicles):
            # 2車両分の訪問地点（空リストも考慮）を結合して集合に
            combined_node_ids = set(all_vehicles_routes[i] + all_vehicles_routes[j])
            
            # デポ（customers[0]）は必ず含める
            combined_node_ids.add(customers[0]['id'])

            # 該当する顧客情報を抽出
            sub_customers = [c for c in customers if c['id'] in combined_node_ids]

            # 該当するpickup→deliveryタプルを結合
            pickup_to_delivery_for_2vehicles = pickup_to_delivery_for_vehicle[i] + pickup_to_delivery_for_vehicle[j]
            
            new_routes = solve_vrp_flexible(sub_customers, pickup_to_delivery_for_2vehicles, 2, vehicle_capacity,
                                            use_capacity=False, use_time=False, use_pickup_delivery=True)
            old_cost = route_cost(all_vehicles_routes[i], customers) + route_cost(all_vehicles_routes[j], customers)
            new_cost = sum(route_cost(r, customers) for r in new_routes)
            if new_cost < old_cost:
                feasible_actions.append({
                    'vehicle_pair': (i, j),
                    'old_routes': [route[i], route[j]],
                    'new_routes': new_routes,
                    'old_cost': old_cost,
                    'new_cost': new_cost,
                    'cost_improvement': old_cost - new_cost
                })
                #探索空間を広げるために、互いの経路を交換する非効率な経路をアクション集合に追加する↓

    #アクション集合の中からコストが最も改善する経路交換を決定する↓
    
    return new_all_vehicles_routes
