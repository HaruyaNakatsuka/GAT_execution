import os
import json
import shutil
import glob


def export_vrp_state(customers, routes, PD_pairs, step_index, case_index,
                     depot_id_list=None, vehicle_num_list=None):
    """
    VRP状態をReactアプリ用にJSON形式で保存（拡張版）
    """
    # 保存ディレクトリ作成
    output_dir = f"web_data/case_{case_index}"
    os.makedirs(output_dir, exist_ok=True)

    # 各デフォルト値の設定
    if depot_id_list is None:
        # customers内で demand==0 のノードをデポとみなす
        depot_id_list = [c["id"] for c in customers if c.get("demand", 0) == 0]
    if vehicle_num_list is None:
        # 1社分しかない場合などに備えて routes の数をそのまま登録
        vehicle_num_list = [len(routes)]

    # 出力データ構造
    data = {
        "customers": customers,
        "routes": routes,
        "PD_pairs": PD_pairs,
        "depot_id_list": depot_id_list,
        "vehicle_num_list": vehicle_num_list,
        "step_index": step_index
    }

    # ファイル書き出し
    json_path = os.path.join(output_dir, f"step_{step_index}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ VRP状態を出力しました: {json_path}")



def generate_index_json(output_root="web_data", target_root="vrp-viewer/public/vrp_data"):
    """すべてのケースフォルダを走査してindex.jsonを自動生成"""

    os.makedirs(target_root, exist_ok=True)
    cases = []
    for case_dir in sorted(glob.glob(os.path.join(output_root, "case_*"))):
        case_name = os.path.basename(case_dir)
        steps = sorted([f for f in os.listdir(case_dir) if f.endswith(".json")])
        cases.append({"name": case_name, "steps": steps})

        # publicフォルダにもコピー
        dest_case_dir = os.path.join(target_root, case_name)
        shutil.copytree(case_dir, dest_case_dir, dirs_exist_ok=True)

    # Reactで読むindex.jsonを出力
    index_path = os.path.join(target_root, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"cases": cases}, f, indent=2, ensure_ascii=False)

    print(f"✅ index.json を生成しました → {index_path}")
