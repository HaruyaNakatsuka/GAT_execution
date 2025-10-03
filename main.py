from parser import parse_lilim200
from flexible_vrp_solver import route_cost
from gat import initialize_individual_vrps, perform_gat_exchange
from visualizer import plot_routes
import time
import sys

start_time = time.time()

# 入力データセット
file_paths = [
    "data/LC1_2_2.txt",
    "data/LC1_2_6.txt"
]

# 元論文の手法に則り片方のデータセットをオフセット
offsets = [
    (0, 0),
    (42, -42)
]

# LSP（Logistics Service Provider:物流会社）の数 = データファイル数
num_lsps = len(file_paths)

num_vehicles = 0
all_customers = []
all_PD_pairs = {}
depot_id_list = []
depot_coords = []
vehicle_num_list = []
vehicle_capacity = None

# === データファイルをパース ===
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


#      =============================
#      === LSP個別経路生成フェーズ ===
#      =============================
routes = initialize_individual_vrps(
    all_customers, all_PD_pairs, num_lsps, vehicle_num_list, depot_id_list, vehicle_capacity=vehicle_capacity
)
initial_cost = sum(route_cost(route, all_customers) for route in routes)
previous_cost = initial_cost

def print_routes_with_lsp_separator(routes, vehicle_num_list):
    vehicle_index = 0
    for lsp_index, num_vehicles in enumerate(vehicle_num_list):
        print(f"--- LSP {lsp_index + 1} ---")
        for _ in range(num_vehicles):
            route = routes[vehicle_index]
            print(f"  Vehicle {vehicle_index + 1}: {' -> '.join(map(str, route))}")
            vehicle_index += 1

print("=== 初期経路 ===")  
print_routes_with_lsp_separator(routes, vehicle_num_list)


#       ==========================
#       ===== GAT改善フェーズ =====
#       ==========================
for i in range(5):
    print(f"\n=== gat改善：{i+1}回目 ===")
    
    routes = perform_gat_exchange(
        routes, all_customers, all_PD_pairs, vehicle_capacity=vehicle_capacity
    )

    print_routes_with_lsp_separator(routes, vehicle_num_list)
    
    # コスト改善率計算
    current_cost = sum(route_cost(route, all_customers) for route in routes)
    from_initial = (initial_cost - current_cost) / initial_cost * 100
    from_previous = (previous_cost - current_cost) / previous_cost * 100
    print(f"[初期ルートからのコスト改善率] {from_initial:.2f}%")
    print(f"[前回経路からのコスト改善率] {from_previous:.2f}%")
    if int(from_previous) == 0:
        break
    else:
        previous_cost = current_cost

# 経路改善終了, 実行時間表示
end_time = time.time()
elapsed = end_time - start_time
print(f"\n=== プログラム全体の実行時間: {elapsed:.2f} 秒 ===")
