from parser import parse_lilim200
from flexible_vrp_solver import route_cost
from gat import initialize_individual_vrps, perform_gat_exchange
from visualizer import plot_routes
from web_exporter import export_vrp_state, generate_index_json
from checker import check_solution_feasibility

import time
import os
import logging
import sys
import unicodedata
from typing import Sequence, Any


def setup_logging(show_progress: bool = True):
    logging.basicConfig(
        level=logging.INFO if show_progress else logging.WARNING,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,  # ← これがポイント
    )
    
    
if __name__ == "__main__":
    setup_logging(show_progress=False)  # Falseにするとprint類がすべて非表示に


def print_testcase_title(
    case_index: int,
    file_paths: Sequence[str],
    offsets: Sequence[Any],
    exact_pd_pair_limit: int,
) -> None:
    """
    テストケース開始時のヘッダを整形して出力する。
    - 必須条件を満たさない場合はエラー終了する。
    """

    # ----------------------------
    # 0) バリデーション
    # ----------------------------
    if file_paths is None or len(file_paths) == 0:
        print("エラー：テストケース（入力ファイル）が1つも指定されていません。", file=sys.stderr)
        sys.exit(1)

    if offsets is None or len(offsets) == 0:
        print("エラー：オフセットが1つも指定されていません。", file=sys.stderr)
        sys.exit(1)

    if len(file_paths) != len(offsets):
        print(
            f"エラー：入力ファイル数とオフセット数が一致していません。"
            f"（ファイル数={len(file_paths)}, オフセット数={len(offsets)}）",
            file=sys.stderr,
        )
        sys.exit(1)

    if exact_pd_pair_limit is None:
        print("エラー：exact_pd_pair_limit が指定されていません。", file=sys.stderr)
        sys.exit(1)

    if not isinstance(exact_pd_pair_limit, int):
        print("エラー：exact_pd_pair_limit は整数で指定してください。", file=sys.stderr)
        sys.exit(1)

    # ----------------------------
    # 1) 表示用の整形
    # ----------------------------
    stems = []
    for p in file_paths:
        base = os.path.basename(str(p))
        stem, _ = os.path.splitext(base)
        stems.append(stem)

    files_str = " + ".join(stems)
    offsets_str = " , ".join(str(x) for x in offsets)

    title_line = f"テストケース {case_index}: {files_str}"

    # ----------------------------
    # 2) GATオプション文字列（limit強調 & sys.maxsize特別扱い）
    # ----------------------------
    if exact_pd_pair_limit == sys.maxsize:
        gat_option_str = "すべての2車両VRPを自作ソルバーで求解する"
    else:
        # ANSI太字（効かない端末もあるので【】も併用して視認性を担保）
        bold_on = "\033[1m"
        bold_off = "\033[0m"
        emphasized = f"{bold_on}【{exact_pd_pair_limit}】{bold_off}"
        gat_option_str = f"PDペア数{emphasized}ペア以下は自作VRPソルバーで厳密解を求解"

    labels = ["オフセット", "GATオプション"]
    values = [offsets_str, gat_option_str]

    # ----------------------------
    # 3) 見た目幅（全角=2, 半角=1）で揃える
    # ----------------------------
    def calc_width(s: str) -> int:
        w = 0
        for ch in s:
            eaw = unicodedata.east_asian_width(ch)
            w += 2 if eaw in ("W", "F") else 1
        return w

    # ラベル幅（見た目）を揃える
    label_w = max(calc_width(l) for l in labels)

    # 右パディング（見た目）で揃える
    kv_lines = []
    for lab, val in zip(labels, values):
        left = " -" + lab
        pad = label_w - calc_width(lab)
        if pad > 0:
            left += " " * pad
        kv_lines.append(f"{left} : {val}")

    # 罫線長を最大行幅に合わせる
    all_lines = [title_line] + kv_lines
    max_w = max(calc_width(line) for line in all_lines)
    border = "=" * max_w

    print("\n" + border)
    print(title_line)
    for line in kv_lines:
        print(line)
    print(border)



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


# ==============================
# === テストケースの定義部 ===
# ==============================

test_cases = [
    (["data/LC1_2_2.txt", "data/LC1_2_6.txt"], [(0, 0), (42, -42)], sys.maxsize),
    (["data/LC1_2_2.txt", "data/LC1_2_7.txt"], [(0, 0), (-32, -32)], sys.maxsize),
    (["data/LC1_2_4.txt", "data/LC1_2_7.txt"], [(0, 0), (-30, 0)], 9),
    (["data/LC1_2_4.txt", "data/LC1_2_8.txt"], [(0, 0), (-30, 0)], 9),
    (["data/LC1_2_10.txt", "data/LC1_2_4.txt"], [(0, 0), (30, 0)], 8),
    (["data/LR1_2_3.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)], 7),
    (["data/LR1_2_5.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)], 7),
    (["data/LR1_2_8.txt", "data/LR1_2_9.txt"], [(0, 0), (0, -30)], 7),
    (["data/LR1_2_10.txt", "data/LR1_2_3.txt"], [(0, 0), (0, -30)], 7),
    (["data/LR1_2_10.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)], 5)
]

"""
# --- 規模の小さいVRPに対し厳密解ソルバーを使用して実験する場合の入力 ---
test_cases = [
    (["data/LC1_2_2.txt", "data/LC1_2_6.txt"], [(0, 0), (42, -42)], sys.maxsize),
    (["data/LC1_2_2.txt", "data/LC1_2_7.txt"], [(0, 0), (-32, -32)], sys.maxsize),
    (["data/LC1_2_4.txt", "data/LC1_2_7.txt"], [(0, 0), (-30, 0)], 9),
    (["data/LC1_2_4.txt", "data/LC1_2_8.txt"], [(0, 0), (-30, 0)], 9),
    (["data/LC1_2_10.txt", "data/LC1_2_4.txt"], [(0, 0), (30, 0)], 8),
    (["data/LR1_2_3.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)], 7),
    (["data/LR1_2_5.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)], 7),
    (["data/LR1_2_8.txt", "data/LR1_2_9.txt"], [(0, 0), (0, -30)], 7),
    (["data/LR1_2_10.txt", "data/LR1_2_3.txt"], [(0, 0), (0, -30)], 7),
    (["data/LR1_2_10.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)], 5)
]

# --- ORToolsをのみを使用して実験する場合の入力 ---
test_cases = [
    (["data/LC1_2_2.txt", "data/LC1_2_6.txt"], [(0, 0), (42, -42)], 0),
    (["data/LC1_2_2.txt", "data/LC1_2_7.txt"], [(0, 0), (-32, -32)], 0),
    (["data/LC1_2_4.txt", "data/LC1_2_7.txt"], [(0, 0), (-30, 0)], 0),
    (["data/LC1_2_4.txt", "data/LC1_2_8.txt"], [(0, 0), (-30, 0)], 0),
    (["data/LC1_2_10.txt", "data/LC1_2_4.txt"], [(0, 0), (30, 0)], 0),
    (["data/LR1_2_3.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)], 0),
    (["data/LR1_2_5.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)], 0),
    (["data/LR1_2_8.txt", "data/LR1_2_9.txt"], [(0, 0), (0, -30)], 0),
    (["data/LR1_2_10.txt", "data/LR1_2_3.txt"], [(0, 0), (0, -30)], 0),
    (["data/LR1_2_10.txt", "data/LR1_2_8.txt"], [(0, 0), (0, 30)], 0)
]
"""


# ==============================
# === テストケースの実行部 ===
# ==============================
for case_index, (file_paths, offsets, exact_pd_pair_limit) in enumerate(test_cases, 1):
    print_testcase_title(
        case_index=case_index,
        file_paths=file_paths,
        offsets=offsets,
        exact_pd_pair_limit=exact_pd_pair_limit,
    )

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
        print(f"LSP {idx}: {c}")
    print(f"TOTAL: {initial_total_cost}")
    # [データ保存] -> jsonファイル、pngファイル
    export_vrp_state(all_customers, routes, all_PD_pairs, 0, case_index=case_index,depot_id_list=depot_id_list,
                    vehicle_num_list=vehicle_num_list,instance_name=instance_name, output_root="web_data")
    plot_routes(all_customers, routes, depot_id_list, vehicle_num_list, iteration=0, instance_name=instance_name)


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
            routes, all_customers, all_PD_pairs, vehicle_capacity, vehicle_num_list, exact_pd_pair_limit
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
            round_improve = ((cur_c - prev_c) / prev_c * 100.0) if prev_c > 0 else 0.0
            init_improve = ((cur_c - init_c) / init_c * 100.0) if init_c > 0 else 0.0
            print(
                f"LSP {idx:<2} " +
                "{:>{w}} {:>{w}} {:>{w}.2f} {:>{w}.2f}".format(
                    init_c, cur_c, round_improve, init_improve, w=colw
                )
            )
        # TOTAL行
        round_improve_total = ((curr_total_cost - prev_total_cost) / prev_total_cost * 100.0) if prev_total_cost > 0 else 0.0
        init_improve_total = ((curr_total_cost - initial_total_cost) / initial_total_cost * 100.0) if initial_total_cost > 0 else 0.0
        print(
            f"{'TOTAL':<6} " +
            "{:>{w}} {:>{w}} {:>{w}.2f} {:>{w}.2f}".format(
                initial_total_cost, curr_total_cost, round_improve_total, init_improve_total, w=colw
            )
        )
        
        # [データ保存] -> jsonファイル、pngファイル
        zantei_zikan = time.time()-start_time
        export_vrp_state(all_customers, routes, all_PD_pairs, i, case_index=case_index,depot_id_list=depot_id_list,
                        vehicle_num_list=vehicle_num_list,instance_name=instance_name, output_root="web_data")
        plot_routes(all_customers, routes, depot_id_list, vehicle_num_list, iteration=i, instance_name=instance_name, elapsed_time=zantei_zikan)


        if round(round_improve_total, 1) == 0.0:
            print("\n>>> 収束（改善率=0%）したため、GAT改善を終了")
            break
        else:
            i=i+1
    
    ok = check_solution_feasibility(
        routes,
        all_customers,
        all_PD_pairs,
        vehicle_capacity=vehicle_capacity,
        depot_id_list=depot_id_list,
        vehicle_num_list=vehicle_num_list,
        verbose=True,
    )
    if not ok:
        raise RuntimeError("Final routes are infeasible. See [CHECK] messages above.")

    generate_index_json(instance_name=instance_name, output_root="web_data", target_root="vrp-viewer/public/vrp_data")

    # 経路改善終了, 実行時間表示
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"=== テストケース {case_index} の実行時間: {elapsed:.2f} 秒 ===")
    