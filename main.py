from parser import parse_lilim200
from gat import initialize_individual_vrps, perform_gat_exchange
from visualizer import plot_routes

data = parse_lilim200("data/LC2_2_1.txt")
routes, assignments = initialize_individual_vrps(data['customers'], data['pickup_to_delivery'], num_lsps=3)
plot_routes(data['customers'], routes, "初期ルート")

# GAT交換ステップ（1回）
changed = perform_gat_exchange(routes, assignments, data['customers'], data['pickup_to_delivery'])

if changed:
    plot_routes(data['customers'], routes, "GAT交換後ルート")
