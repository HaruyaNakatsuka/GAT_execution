from flexible_vrp_solver import solve_vrp_flexible, route_cost
from ortools.sat.python import cp_model
from exact_2vehicle_vrp_solver import solve_exact_2vehicle_vrp
from checker import check_single_route_feasibility
import sys


def initialize_individual_vrps(customers, pickup_to_delivery, num_lsps, vehicle_num_list, depot_id_list, vehicle_capacity, seed=42):
    all_vehicle_routes = []
    
    for i in range(num_lsps):
        depot_id = depot_id_list[i]
        num_vehicles = vehicle_num_list[i]

        # sub_customersの抽出（デポを含む）
        if i < num_lsps - 1:
            id_min = depot_id_list[i]
            id_max = depot_id_list[i + 1]
            sub_customers = [c for c in customers if id_min <= c['id'] < id_max]
        else:
            id_min = depot_id_list[i]
            sub_customers = [c for c in customers if c['id'] >= id_min]
        
        # sub_PD_pairsの抽出
        sub_customer_ids = {c['id'] for c in sub_customers}
        sub_PD_pairs = [
            (pickup, delivery)
            for pickup, delivery in pickup_to_delivery.items()
            if pickup in sub_customer_ids or delivery in sub_customer_ids
        ]

        # 各車両の出発／終了デポ設定
        start_depot = [depot_id] * num_vehicles
        end_depot = [depot_id] * num_vehicles
        
        initial_routes = None
        # VRPを解く
        print(f">>>LSP {i+1}の初期経路を生成中・・・")
        lsp_routes = solve_vrp_flexible(
            sub_customers,
            initial_routes,
            sub_PD_pairs,
            num_vehicles=num_vehicles,
            vehicle_capacity=vehicle_capacity,
            start_depots=start_depot,
            end_depots=end_depot,
            use_capacity=True,
            use_time=True,
            use_pickup_delivery=True,
            Warm_Start=False
        )

        all_vehicle_routes.extend(lsp_routes)

    return all_vehicle_routes

def perform_gat_exchange(
    original_routes,
    customers,
    PD_pairs,
    vehicle_capacity,
    vehicle_num_list,
    exact_pd_pair_limit,
    *,
    debug: bool = False,
):
    feasible_actions = []  # 実行可能アクション集合
    num_vehicles = len(original_routes)

    # 各車両 -> 会社 の単純マッピングを作る（vehicle_num_list に基づく）
    vehicle_to_company = []
    for comp_idx, n in enumerate(vehicle_num_list):
        for _ in range(n):
            vehicle_to_company.append(comp_idx)

    num_companies = max(vehicle_to_company) + 1 if vehicle_to_company else 1

    # 各車両ごとの関連PDペアを前計算
    PD_pairs_of_each_vehicle = []
    for vehicle_route in original_routes:
        related_pairs = []
        visited_set = set(vehicle_route)
        for pickup, delivery in PD_pairs.items():
            if pickup in visited_set or delivery in visited_set:
                related_pairs.append((pickup, delivery))
        PD_pairs_of_each_vehicle.append(related_pairs)

    # 全2車両ペアに対して2車両VRPを実行（候補収集）
    for i in range(num_vehicles):
        for j in range(i + 1, num_vehicles):
            combined_node_ids = set(original_routes[i] + original_routes[j])
            
            if debug:
                print(f"[DEBUG]車両{i},{j}の2車両VRP")
                print(f"       route{i}={original_routes[i]}")
                print(f"       route{i}={original_routes[j]}")

            # 両車両のデポは必ず含める
            if original_routes[i]:
                combined_node_ids.add(original_routes[i][0])
            if original_routes[j]:
                combined_node_ids.add(original_routes[j][0])

            sub_customers = [c for c in customers if c["id"] in combined_node_ids]
            PD_pairs_of_2vehicle = PD_pairs_of_each_vehicle[i] + PD_pairs_of_each_vehicle[j]

            # デポ情報
            start_depots = [
                original_routes[i][0] if original_routes[i] else customers[0]["id"],
                original_routes[j][0] if original_routes[j] else customers[0]["id"],
            ]
            end_depots = [start_depots[0], start_depots[1]]

            # ReadAssignmentFromRoutes 向け（デポ除去）
            initial_routes = [
                (r[1:-1] if len(r) >= 2 and r[0] == r[-1] else r)
                for r in [original_routes[i], original_routes[j]]
            ]

            # --- 厳密 or OR-Tools の分岐 ---
            if len(PD_pairs_of_2vehicle) <= exact_pd_pair_limit:
                
                # --- 厳密解（自作ソルバー）---
                if debug:
                    print("       -> 自作ソルバー実行")
                    
                exact_node_ids = set(combined_node_ids)
                exact_node_ids.update(start_depots)
                exact_node_ids.update(end_depots)
                for p_id, d_id in PD_pairs_of_2vehicle:
                    exact_node_ids.add(p_id)
                    exact_node_ids.add(d_id)

                sub_customers_exact = [c for c in customers if c["id"] in exact_node_ids]
                id_set_exact = {c["id"] for c in sub_customers_exact}
                sub_PD_pairs_exact = [
                    (p, d) for (p, d) in PD_pairs_of_2vehicle if (p in id_set_exact and d in id_set_exact)
                ]

                new_routes = solve_exact_2vehicle_vrp(
                    sub_customers_exact,
                    sub_PD_pairs_exact,
                    start_depots,
                    end_depots,
                    vehicle_capacity,
                )
            else:
                # --- ORTools ---
                if debug:
                    print("       -> ORTools VRPソルバー実行")
                    
                new_routes = solve_vrp_flexible(
                    sub_customers,
                    initial_routes,
                    PD_pairs_of_2vehicle,
                    2,
                    vehicle_capacity,
                    start_depots,
                    end_depots,
                    use_capacity=True,
                    use_time=True,
                    use_pickup_delivery=True,
                    Warm_Start=True,
                )

            # 返り値の対応付け（(i,j)順とは限らない）
            if new_routes is not None and len(new_routes) == 2:
                si, sj = start_depots[0], start_depots[1]
                ei, ej = end_depots[0], end_depots[1]
                r0, r1 = new_routes[0], new_routes[1]

                def _match_start_end(r, s, e):
                    return bool(r) and r[0] == s and r[-1] == e

                if _match_start_end(r0, si, ei) and _match_start_end(r1, sj, ej):
                    new_routes = [r0, r1]
                elif _match_start_end(r0, sj, ej) and _match_start_end(r1, si, ei):
                    new_routes = [r1, r0]
                else:
                    print("返ってきた2車両経路が想定外の形をしています")
                    raise RuntimeError("返ってきた2車両経路が想定外の形をしています")

            # 解なしの場合 --> ソルバー実行前の暫定経路を保存
            if new_routes is None:
                new_routes = [original_routes[i], original_routes[j]]
                old_cost = route_cost(original_routes[i], customers) + route_cost(original_routes[j], customers)
                new_cost = old_cost
                delta_per_company = [0.0] * num_companies
                feasible_actions.append({
                    "vehicle_pair": (i, j),
                    "old_routes": [original_routes[i], original_routes[j]],
                    "new_routes": new_routes,
                    "old_cost": old_cost,
                    "new_cost": new_cost,
                    "cost_improvement": 0,
                    "delta_per_company": delta_per_company,
                })
                continue

            # ------------------------------------------------------------
            # 【デバッグ】 2車両解のfeasibilityをチェック
            # 　（debug_feasibility=True のときだけ実行）
            # ------------------------------------------------------------
            if debug:
                ok0, errs0 = check_single_route_feasibility(
                    new_routes[0], customers, PD_pairs, vehicle_capacity, vehicle_id=i
                )
                ok1, errs1 = check_single_route_feasibility(
                    new_routes[1], customers, PD_pairs, vehicle_capacity, vehicle_id=j
                )
                if (not ok0) or (not ok1):
                    if not ok0:
                        print(f"[DEBUG-2vehicle check]  - vehicle{i} route={new_routes[0]}は実行不能解です")
                        for e in errs0[:10]:
                            print(f"    {e}")
                    if not ok1:
                        print(f"[DEBUG-2vehicle check]  - vehicle{j} route={new_routes[1]}は実行不能解です")
                        for e in errs1[:10]:
                            print(f"    {e}")
                    print("")
                    raise RuntimeError(
                        f"[DEBUG]ソルバーが実行不可能な2車両解を出力しています（pair={i},{j}）"
                    )
                else:
                    print(f"       -> new route={new_routes}は実行可能な解です")
                    print("")


            old_cost = route_cost(original_routes[i], customers) + route_cost(original_routes[j], customers)
            new_cost = sum(route_cost(r, customers) for r in new_routes)

            # 経路が改善されている場合はアクション集合に追加
            if new_cost < old_cost:
                delta_per_company = [0.0] * num_companies
                old_i = route_cost(original_routes[i], customers)
                new_i = route_cost(new_routes[0], customers)
                delta_per_company[vehicle_to_company[i]] += (new_i - old_i)

                old_j = route_cost(original_routes[j], customers)
                new_j = route_cost(new_routes[1], customers)
                delta_per_company[vehicle_to_company[j]] += (new_j - old_j)

                feasible_actions.append({
                    "vehicle_pair": (i, j),
                    "old_routes": [original_routes[i], original_routes[j]],
                    "new_routes": new_routes,
                    "old_cost": old_cost,
                    "new_cost": new_cost,
                    "cost_improvement": old_cost - new_cost,
                    "delta_per_company": delta_per_company,
                })

                # exchanged routeをアクション集合に追加する
                depot_i = new_routes[0][0]
                depot_j = new_routes[1][0]

                # depot を除いた中身（start/end/depot混入をまとめて排除）
                mid_i = [n for n in new_routes[0] if n != depot_i]
                mid_j = [n for n in new_routes[1] if n != depot_j]

                exchanged_routes = [
                    [depot_i] + mid_j + [depot_i],
                    [depot_j] + mid_i + [depot_j],
                ]

                ok0x, errs0x = check_single_route_feasibility(
                    exchanged_routes[0], customers, PD_pairs, vehicle_capacity, vehicle_id=i
                )
                ok1x, errs1x = check_single_route_feasibility(
                    exchanged_routes[1], customers, PD_pairs, vehicle_capacity, vehicle_id=j
                )

                # どちらも実行可能な場合のみ、アクション集合に追加する
                if  ok0x and ok1x:
                    exchanged_cost = sum(route_cost(r, customers) for r in exchanged_routes)
                    exchanged_delta = [0.0] * num_companies

                    ex_new_i = route_cost(exchanged_routes[0], customers)
                    ex_new_j = route_cost(exchanged_routes[1], customers)
                    old_i = route_cost(original_routes[i], customers)
                    old_j = route_cost(original_routes[j], customers)

                    exchanged_delta[vehicle_to_company[i]] += (ex_new_i - old_i)
                    exchanged_delta[vehicle_to_company[j]] += (ex_new_j - old_j)

                    feasible_actions.append({
                        "vehicle_pair": (i, j),
                        "old_routes": [original_routes[i], original_routes[j]],
                        "new_routes": exchanged_routes,
                        "old_cost": old_cost,
                        "new_cost": exchanged_cost,
                        "cost_improvement": old_cost - exchanged_cost,
                        "delta_per_company": exchanged_delta,
                    })

    # --- CP-SAT ---
    model = cp_model.CpModel()
    num_actions = len(feasible_actions)
    x = [model.NewBoolVar(f"action_{k}") for k in range(num_actions)]
    model.Maximize(sum(int(round(feasible_actions[k]["cost_improvement"])) * x[k] for k in range(num_actions)))

    # 制約1：各車両は高々1回だけ
    vehicle_to_actions = {}
    for k, action in enumerate(feasible_actions):
        v1, v2 = action["vehicle_pair"]
        for v in [v1, v2]:
            vehicle_to_actions.setdefault(v, []).append(k)
    for v, idxs in vehicle_to_actions.items():
        model.Add(sum(x[i] for i in idxs) <= 1)

    # 制約2：個別合理性（会社ごとに delta <= 0）
    for c in range(num_companies):
        terms = []
        for k, action in enumerate(feasible_actions):
            d = action["delta_per_company"][c]
            if abs(d) < 1e-9:
                continue
            terms.append(int(round(d)) * x[k])
        if terms:
            model.Add(sum(terms) <= 0)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    new_all_vehicles_routes = original_routes.copy()
    touched = set()
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for k in range(num_actions):
            if solver.Value(x[k]) == 1:
                v1, v2 = feasible_actions[k]["vehicle_pair"]
                new_routes = feasible_actions[k]["new_routes"]
                new_all_vehicles_routes[v1] = new_routes[0]
                new_all_vehicles_routes[v2] = new_routes[1]
                touched.add(v1)
                touched.add(v2)
    else:
        print("最適なアクションの組み合わせが見つかりませんでした。")

    # ------------------------------------------------------------
    # 【デバッグ】GAT実行後のFeasibilityチェック
    # ------------------------------------------------------------
    if debug and touched:
        for v in sorted(touched):
            ok, errs = check_single_route_feasibility(
                new_all_vehicles_routes[v], customers, PD_pairs, vehicle_capacity, vehicle_id=v
            )
            if not ok:
                print(f"[DEBUG-final check] vehicle={v}の経路は実行不能解です")
                print(f"                    route = {new_all_vehicles_routes[v]}")
                raise RuntimeError(f"[DEBUG-final check] vehicle={v}の経路は実行不能解です")
        print("[DEBUG]このGATループで更新された経路はすべて実行可能です")
        print("")

    return new_all_vehicles_routes


