from vrp_solver import solve_vrp, route_cost

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
        sub_pickups = {p: d for p, d in reqs}
        ### ↓エラー発生
        route = solve_vrp(sub_customers, sub_pickups, last_id, num_vehicles=int(num_all_vehicles/num_all_lsps), vehicle_capacity=vehicle_capacity)
        lsp_routes.append(route)

    return lsp_routes, lsp_assignments

def perform_gat_exchange(lsp_routes, lsp_assignments, customers, pickup_to_delivery, vehicle_capacity):
    num_lsps = len(lsp_routes)

    for i in range(num_lsps):
        for j in range(i + 1, num_lsps):
            pair_reqs = lsp_assignments[i] + lsp_assignments[j]
            involved_ids = set()
            for p, d in pair_reqs:
                involved_ids.update([p, d])
            sub_customers = [c for c in customers if c['id'] in involved_ids or c['id'] == 0]
            sub_pickups = {p: d for p, d in pair_reqs}

            new_routes = solve_vrp(sub_customers, sub_pickups, num_vehicles=2, vehicle_capacity=vehicle_capacity)
            if not new_routes or len(new_routes) < 2:
                continue

            old_cost = route_cost(lsp_routes[i], customers) + route_cost(lsp_routes[j], customers)
            new_cost = sum(route_cost(r, customers) for r in new_routes)

            if new_cost < old_cost:
                print(f"GAT交換成功: LSP {i} ⇄ LSP {j}")
                lsp_routes[i], lsp_routes[j] = new_routes
                return True

    return False
