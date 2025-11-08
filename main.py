from parser import parse_lilim200
from flexible_vrp_solver import route_cost
from gat import initialize_individual_vrps, perform_gat_exchange
from visualizer import plot_routes
from web_exporter import export_vrp_state, generate_index_json
import time
import os
import logging


def setup_logging(show_progress: bool = True):
    logging.basicConfig(
        level=logging.INFO if show_progress else logging.WARNING,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,  # ← これがポイント
    )
    
if __name__ == "__main__":
    setup_logging(show_progress=False)  # Falseにするとprint類がすべて非表示に


def compute_company_costs(routes, all_customers, vehicle_num_list):
    """各LSPごとの総コストを計算する"""
    company_costs = []
    vehicle_index = 0
    for num_vehicles in vehicle_num_list:
        lsp_cost = 0
        for _ in range(num_vehicles):
            lsp_cost += route_cost(routes[vehicle_index], all_customers)
            vehicle_index += 1
        company_costs.append(lsp_cost)
    return company_costs


def print_routes_with_lsp_separator(routes, vehicle_num_list):
    """各車両の経路確認用(コンソールに出力)"""
    print(">>> 初期経路一覧")  
    vehicle_index = 0
    for lsp_index, num_vehicles in enumerate(vehicle_num_list):
        print(f"--- LSP {lsp_index + 1} ---")
        for _ in range(num_vehicles):
            route = routes[vehicle_index]
            print(f"  Vehicle {vehicle_index + 1}: {' -> '.join(map(str, route))}")
            vehicle_index += 1



# ==============================
# === テストケースの定義部 ===
# ==============================

test_cases = [
    (["data/LC1_2_2.txt", "data/LC1_2_6.txt"], [(0, 0), (42, -42)]),
    (["data/LC1_2_2.txt", "data/LC1_2_7.txt"], [(0, 0), (-32, -32)]),
    (["data/LC1_2_4.txt", "data/LC1_2_7.txt"], [(0, 0), (-30, 0)]),
    (["data/LC1_2_4.txt", "data/LC1_2_8.txt"], [(0, 0), (-30, 0)]),
    (["data/LC1_2_10.txt", "data/LC1_2_4.txt"], [(0, 0), (30, 0)]),
    (["data/LR1_2_3.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)]),
    (["data/LR1_2_5.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)]),
    (["data/LR1_2_8.txt", "data/LR1_2_9.txt"], [(0, 0), (0, -30)]),
    (["data/LR1_2_10.txt", "data/LR1_2_3.txt"], [(0, 0), (0, -30)]),
    (["data/LR1_2_10.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)])
]


# ==============================
# === テストケースの実行部 ===
# ==============================
for case_index, (file_paths, offsets) in enumerate(test_cases, 1):
    print("\n" + "="*50)
    print(f"テストケース {case_index}: {file_paths[0]} + {file_paths[1]}")
    print(f"オフセット: {offsets[0]} , {offsets[1]}")
    print("="*50)
    
    instance_name = f"{os.path.basename(file_paths[0]).split('.')[0]}_{os.path.basename(file_paths[1]).split('.')[0]}"
    
    start_time = time.time()

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


    # =============================
    # === 初期：LSP個別の経路生成 ===
    # =============================
    routes = initialize_individual_vrps(
        all_customers, all_PD_pairs, num_lsps, vehicle_num_list, depot_id_list, vehicle_capacity=vehicle_capacity
    )

    #　[コンソール出力] -> 会社別コスト
    initial_company_costs = compute_company_costs(routes, all_customers, vehicle_num_list)
    initial_total_cost = sum(initial_company_costs)
    print("\n==== 初期経路：会社別コスト ====")
    for idx, c in enumerate(initial_company_costs, 1):
        print(f"LSP {idx}: {c:.2f}")
    print(f"TOTAL: {initial_total_cost:.2f}")
    # [データ保存] -> jsonファイル、pngファイル
    export_vrp_state(all_customers, routes, all_PD_pairs, 0, case_index=case_index,depot_id_list=depot_id_list,
                    vehicle_num_list=vehicle_num_list,instance_name=instance_name, output_root="web_data")
    plot_routes(all_customers, routes, depot_id_list, vehicle_num_list, iteration=0, instance_name=instance_name)

    #print_routes_with_lsp_separator(routes, vehicle_num_list)


    #       ==========================
    #       ===== GAT改善フェーズ =====
    #       ==========================
    print("\n=== GATによる経路最適化 ===")
    i=1
    while True:
        print(f"[GAT改善：{i}回目]")
        
        prev_company_costs = compute_company_costs(routes, all_customers, vehicle_num_list)
        prev_total_cost = sum(prev_company_costs)
        
        # === 経路生成 ===
        routes = perform_gat_exchange(
            routes, all_customers, all_PD_pairs, vehicle_capacity, vehicle_num_list
        )
        
        #　[コンソール出力] -> 改善率、他
        curr_company_costs = compute_company_costs(routes, all_customers, vehicle_num_list)
        curr_total_cost = sum(curr_company_costs)
        colw = 10
        # ヘッダー行
        print(
            " " * 7 +
            "{:>{w}} {:>{w}} {:>{w}} {:>{w}}".format(
                "初期コスト", "暫定コスト", "ラウンド改善(%)", "初期比改善(%)", w=colw
            )
        )
        # 各社の行
        colw = 15
        for idx, (init_c, prev_c, cur_c) in enumerate(zip(initial_company_costs, prev_company_costs, curr_company_costs), 1):
            round_improve = ((prev_c - cur_c) / prev_c * 100.0) if prev_c > 0 else 0.0
            init_improve = ((init_c - cur_c) / init_c * 100.0) if init_c > 0 else 0.0
            print(
                f"LSP {idx:<2} " +
                "{:>{w}.2f} {:>{w}.2f} {:>{w}.2f} {:>{w}.2f}".format(
                    init_c, cur_c, round_improve, init_improve, w=colw
                )
            )
        # TOTAL行
        round_improve_total = ((prev_total_cost - curr_total_cost) / prev_total_cost * 100.0) if prev_total_cost > 0 else 0.0
        init_improve_total = ((initial_total_cost - curr_total_cost) / initial_total_cost * 100.0) if initial_total_cost > 0 else 0.0
        print(
            f"{'TOTAL':<6} " +
            "{:>{w}.2f} {:>{w}.2f} {:>{w}.2f} {:>{w}.2f}".format(
                initial_total_cost, curr_total_cost, round_improve_total, init_improve_total, w=colw
            )
        )
        
        # [データ保存] -> jsonファイル、pngファイル
        export_vrp_state(all_customers, routes, all_PD_pairs, i, case_index=case_index,depot_id_list=depot_id_list,
                        vehicle_num_list=vehicle_num_list,instance_name=instance_name, output_root="web_data")
        plot_routes(all_customers, routes, depot_id_list, vehicle_num_list, iteration=i, instance_name=instance_name)
        
        #print_routes_with_lsp_separator(routes, vehicle_num_list)

        if round(round_improve_total, 1) == 0.0:
            print("\n>>> 収束（改善率=0%）したため、GAT改善を終了")
            break
        else:
            i=i+1

    generate_index_json(instance_name=instance_name, output_root="web_data", target_root="vrp-viewer/public/vrp_data")

    # 経路改善終了, 実行時間表示
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"=== テストケース {case_index} の実行時間: {elapsed:.2f} 秒 ===")
    