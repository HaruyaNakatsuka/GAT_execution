from parser import parse_lilim200
from flexible_vrp_solver import solve_vrp_flexible
from gat import initialize_individual_vrps, perform_gat_exchange
from visualizer import plot_routes

# === パラメータ設定 ===
file_paths = [
    "data/LC1_2_2.txt",
    "data/LC1_2_6.txt"
]
offsets = [
    (0, 0),
    (42, -42)
]
num_lsps = len(file_paths)  # LSPの数 = データファイル数

# === 全LSP分のデータ読み込みとオフセット適用 ===
num_vehicles = 0
all_customers = []
all_PD_pairs = {}
depot_id_list = []
depot_coords = []
vehicle_num_list = []
vehicle_capacity = None

id_offset = 0  # 初期IDオフセット
for path, offset in zip(file_paths, offsets):
    data = parse_lilim200(path, x_offset=offset[0], y_offset=offset[1], id_offset=id_offset)

    # データ蓄積
    all_customers.extend(data['customers'])
    all_PD_pairs.update(data['PD_pairs'])
    depot_id_list.append(data['depot_id'])
    depot_coords.append(data['depot_coord'])
    vehicle_num_list.append(data['num_vehicles'])
    num_vehicles += data['num_vehicles']
    
    # IDオフセットを次に備えて更新
    max_id = max(c['id'] for c in data['customers'])
    id_offset = max_id + 1

    # 車両容量の情報を保存（全ファイルで同じ前提）
    if vehicle_capacity is None:
        vehicle_capacity = data['vehicle_capacity']

    
routes = initialize_individual_vrps(
    all_customers, all_PD_pairs, num_lsps, vehicle_num_list, depot_id_list, vehicle_capacity=vehicle_capacity
)

#plot_routes(data['customers'], routes, "初期ルート")

print(routes)

for i in range(5):
    routes = perform_gat_exchange(
        routes, all_customers, all_PD_pairs, vehicle_num_list, depot_id_list, vehicle_capacity=vehicle_capacity
    )
    