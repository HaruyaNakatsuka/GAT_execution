from parser import parse_lilim200
from gat import initialize_individual_vrps, perform_gat_exchange
from visualizer import plot_routes

data = parse_lilim200("data/LC2_2_1.txt")
vehicle_capacity = data['vehicle_capacity']
num_vehicles = data['num_vehicles']

num_lsps=5 ##←運送業者の数を定義
routes, assignments = initialize_individual_vrps(
    data['customers'], data['pickup_to_delivery'], num_lsps, num_vehicles, vehicle_capacity=vehicle_capacity
)

plot_routes(data['customers'], routes, "初期ルート")

changed = perform_gat_exchange(
    routes, assignments, data['customers'], data['pickup_to_delivery'], vehicle_capacity=vehicle_capacity
)

if changed:
    plot_routes(data['customers'], routes, "GAT交換後ルート")
