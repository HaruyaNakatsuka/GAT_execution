# checker.py
from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence, Tuple


def check_solution_feasibility(
    routes: List[List[int]],
    all_customers: List[Dict[str, Any]],
    all_PD_pairs: Dict[int, int],
    *,
    vehicle_capacity: int,
    depot_id_list: Sequence[int],
    vehicle_num_list: Sequence[int],
    verbose: bool = True,
    max_print: int = 50,
) -> bool:
    """
    最終ルート集合が実行可能（feasible）かどうかを検査する。

    チェック内容（主なもの）:
      - 全pickup/deliveryノードがちょうど1回ずつ訪問されている（coverage）
      - 各車両ルートが [depot, ..., depot] 形式（空/未使用は [depot, depot] とみなす）
      - 同一ノードの重複訪問なし（depot除く）
      - PD制約: pickup と delivery が同一車両にあり pickupが先
      - 容量制約: 0 <= load <= vehicle_capacity
      - TW制約: 到着→待機→サービス開始が due を超えない
      - 余計なノード（PDに属さないノード）を訪問していない（depot除く）
      - ルート中間に（他社含む）depotを入れない（先頭末尾のみ許可）
    """

    # -------------------------
    # helpers
    # -------------------------
    def _get_num(cust: Dict[str, Any], keys: List[str], default: float = 0.0) -> float:
        for k in keys:
            if k in cust and cust[k] is not None:
                try:
                    return float(cust[k])
                except Exception:
                    pass
        return float(default)

    def _get_int(cust: Dict[str, Any], keys: List[str], default: int = 0) -> int:
        return int(round(_get_num(cust, keys, default=default)))

    READY_KEYS = ["ready_time", "ready", "tw_start", "start_time", "r"]
    DUE_KEYS = ["due_time", "due", "tw_end", "end_time", "d"]
    SERVICE_KEYS = ["service_time", "service", "s"]
    DEMAND_KEYS = ["demand", "q", "Q", "quantity", "load"]

    id_to_customer: Dict[int, Dict[str, Any]] = {int(c["id"]): c for c in all_customers}

    depot_ids = {int(d) for d in depot_id_list}

    pickup_to_delivery: Dict[int, int] = {int(p): int(d) for p, d in all_PD_pairs.items()}
    delivery_to_pickup: Dict[int, int] = {int(d): int(p) for p, d in pickup_to_delivery.items()}
    required_nodes = set(pickup_to_delivery.keys()) | set(pickup_to_delivery.values())

    # pickup側の需要を正として使う（deliveryが負でも吸収）
    pair_demand: Dict[int, int] = {}
    for p in pickup_to_delivery.keys():
        cust = id_to_customer.get(int(p))
        if cust is None:
            pair_demand[int(p)] = 0
            continue
        dem = _get_int(cust, DEMAND_KEYS, default=0)
        pair_demand[int(p)] = abs(dem)

    def dist(a: int, b: int) -> int:
        ca = id_to_customer.get(int(a))
        cb = id_to_customer.get(int(b))
        if ca is None or cb is None:
            # 未知ノードの距離は定義できないので巨大値
            return 10**9
        ax = _get_num(ca, ["x", "X"], 0.0)
        ay = _get_num(ca, ["y", "Y"], 0.0)
        bx = _get_num(cb, ["x", "X"], 0.0)
        by = _get_num(cb, ["y", "Y"], 0.0)
        return int(math.hypot(bx - ax, by - ay))  # floor by int-cast

    errors: List[str] = []

    # -------------------------
    # expected depot per vehicle
    # -------------------------
    expected_depot: List[int] = []
    for dep, n in zip(depot_id_list, vehicle_num_list):
        expected_depot.extend([int(dep)] * int(n))

    if len(expected_depot) != len(routes):
        errors.append(
            f"[Meta] len(routes)={len(routes)} と vehicle_num_list 合計={len(expected_depot)} が不一致"
        )

    # -------------------------
    # 1) coverage check
    # -------------------------
    node_count: Dict[int, int] = {nid: 0 for nid in required_nodes}
    extra_nodes: List[int] = []

    for r in routes:
        if not r:
            continue
        for nid in r:
            nid = int(nid)
            if nid in depot_ids:
                continue
            if nid in node_count:
                node_count[nid] += 1
            else:
                extra_nodes.append(nid)

    missing = [nid for nid, c in node_count.items() if c == 0]
    bad = [(nid, c) for nid, c in node_count.items() if c != 1]

    if missing:
        errors.append(f"[Coverage] 未訪問ノード: count={len(missing)}, 例={missing[:10]}")
    if bad:
        errors.append(f"[Coverage] ちょうど1回でないノード: count={len(bad)}, 例={bad[:10]}")
    if extra_nodes:
        errors.append(
            f"[Coverage] PDに属さないノード訪問（depot除く）: count={len(extra_nodes)}, 例={extra_nodes[:10]}"
        )

    # -------------------------
    # 2) per-route checks
    # -------------------------
    def _canon_route(route: List[int], dep: int) -> List[int]:
        if route is None or len(route) == 0:
            return [dep, dep]
        r = [int(x) for x in route]
        if len(r) == 1:
            return [r[0], r[0]]
        return r

    for v_idx, raw in enumerate(routes):
        exp_dep = expected_depot[v_idx] if v_idx < len(expected_depot) else None
        if exp_dep is None:
            # ここまで来る時点で meta mismatch
            exp_dep = int(raw[0]) if raw else int(depot_id_list[0])

        r = _canon_route(raw, exp_dep)

        # 形式: 先頭末尾デポ
        if r[0] != exp_dep or r[-1] != exp_dep:
            errors.append(
                f"[Form] vehicle={v_idx}: depot mismatch. expected={exp_dep}, route_head={r[0]}, route_tail={r[-1]}"
            )

        # 中間に depot を入れない（他社デポ含む）
        mid_depots = [nid for nid in r[1:-1] if int(nid) in depot_ids]
        if mid_depots:
            errors.append(f"[Form] vehicle={v_idx}: depot appears in middle: {mid_depots[:10]}")

        # 重複訪問（depot除く）
        non_depot = [nid for nid in r if int(nid) not in depot_ids]
        if len(non_depot) != len(set(non_depot)):
            # 例だけ出す
            seen = set()
            dups = []
            for nid in non_depot:
                if nid in seen:
                    dups.append(nid)
                else:
                    seen.add(nid)
            errors.append(f"[Duplicate] vehicle={v_idx}: duplicated nodes (non-depot): {dups[:10]}")

        # ---- PD/TW/Capacity simulation ----
        load = 0
        t = 0.0

        # depot start TW
        depot_c = id_to_customer.get(int(exp_dep), {})
        depot_ready = _get_num(depot_c, READY_KEYS, 0.0)
        depot_due = _get_num(depot_c, DUE_KEYS, float("inf"))
        depot_srv = _get_num(depot_c, SERVICE_KEYS, 0.0)

        if t < depot_ready:
            t = depot_ready
        if t > depot_due:
            errors.append(f"[TW] vehicle={v_idx}: start depot violates TW (t={t}, due={depot_due})")
        t += depot_srv

        visited_pickups = set()
        visited_deliveries = set()

        prev = int(exp_dep)
        for pos, nid in enumerate(r[1:], start=1):
            nid = int(nid)

            # 移動
            t += dist(prev, nid)

            cust = id_to_customer.get(nid)
            if cust is None:
                errors.append(f"[UnknownNode] vehicle={v_idx}: node {nid} not found in customers")
                prev = nid
                continue

            ready = _get_num(cust, READY_KEYS, 0.0)
            due = _get_num(cust, DUE_KEYS, float("inf"))
            service = _get_num(cust, SERVICE_KEYS, 0.0)

            if t < ready:
                t = ready
            if t > due:
                errors.append(f"[TW] vehicle={v_idx}: node={nid} pos={pos} violates TW (t={t}, due={due})")

            t += service

            # depot（末尾想定）はPD/容量に影響なし
            if nid in depot_ids:
                prev = nid
                continue

            # PD / capacity
            if nid in pickup_to_delivery:
                visited_pickups.add(nid)
                load += pair_demand.get(nid, 0)
            elif nid in delivery_to_pickup:
                p = delivery_to_pickup[nid]
                if p not in visited_pickups:
                    errors.append(
                        f"[PD] vehicle={v_idx}: delivery {nid} appears before pickup {p} (pos={pos})"
                    )
                visited_deliveries.add(nid)
                load -= pair_demand.get(p, 0)
            else:
                errors.append(f"[ExtraNode] vehicle={v_idx}: node {nid} is not in PD pairs (non-depot)")

            if load < 0 or load > int(vehicle_capacity):
                errors.append(
                    f"[Cap] vehicle={v_idx}: node={nid} pos={pos} load={load} out of [0,{vehicle_capacity}]"
                )

            prev = nid

        # pickup/delivery 両端が同一車両にあるか
        #（当該ルートで触れたものだけチェック）
        visited_set = set(non_depot)
        for p in visited_pickups:
            d = pickup_to_delivery.get(p)
            if d is not None and d not in visited_set:
                errors.append(f"[PD] vehicle={v_idx}: pickup {p} exists but delivery {d} missing in same route")
        for d in visited_deliveries:
            p = delivery_to_pickup.get(d)
            if p is not None and p not in visited_set:
                errors.append(f"[PD] vehicle={v_idx}: delivery {d} exists but pickup {p} missing in same route")

        # 最終的に荷物が0に戻っているか（PDPTWでは通常必要）
        if load != 0:
            errors.append(f"[Cap] vehicle={v_idx}: load does not return to 0 at end (load={load})")

    # -------------------------
    # print & return
    # -------------------------
    ok = (len(errors) == 0)
    if verbose:
        if ok:
            print("✅[CHECK] OK: final routes are feasible (Capacity/TW/PD/Coverage).")
        else:
            print(f"❌[CHECK] NG: found {len(errors)} feasibility errors.")
            for msg in errors[:max_print]:
                print("  - " + msg)
            if len(errors) > max_print:
                print(f"  ... ({len(errors) - max_print} more)")

    return ok


# ============================================================
# 局所診断用の単一路線チェッカー
#
# - GAT が生成する「候補ルート(new_routes / exchanged_routes)」の時点で
#   実行可能性(TW/容量/PD/形式)を確認する用途を想定。
# - 全ノード網羅(coverage)はチェックしない（候補生成の段階では部分問題だから）。
# ============================================================
def check_single_route_feasibility(
    route: list,
    customers: list,
    pickup_to_delivery: dict,
    vehicle_capacity: int,
    *,
    vehicle_id: int | None = None,
) -> tuple[bool, list[str]]:
    """
    Returns:
        (ok, errors)
        errors は人間が見て原因が分かる粒度の文字列リスト。
    """
    errors: list[str] = []
    if route is None or len(route) == 0:
        return True, errors

    # id -> customer
    id2c = {int(c["id"]): c for c in customers}

    # route 形式（先頭末尾が同じ depot）
    depot = int(route[0])
    if int(route[-1]) != depot:
        errors.append(f"[FORM] vehicle={vehicle_id}: route does not return to depot (start={route[0]}, end={route[-1]})")

    # depot の途中出現は許す設計もあるが、ここでは「途中depotは無視して評価」する（多くのVRP前提）
    seq = [int(n) for n in route[1:-1] if int(n) != depot]

    # 重複（depot除く）
    if len(seq) != len(set(seq)):
        errors.append(f"[DUP] vehicle={vehicle_id}: duplicate non-depot nodes exist")

    # PD：同一ルート内 & pickup先行（出現するものだけチェック）
    pos = {n: i for i, n in enumerate(seq)}
    for p, d in pickup_to_delivery.items():
        p = int(p); d = int(d)
        p_in = p in pos
        d_in = d in pos
        if p_in != d_in:
            # 片側だけ出るのは局所候補としても不正（候補生成の段階で潰したい）
            if p_in or d_in:
                errors.append(f"[PD] vehicle={vehicle_id}: pair has only one side in route (p={p}, d={d})")
        elif p_in and d_in and pos[p] > pos[d]:
            errors.append(f"[PD] vehicle={vehicle_id}: pickup after delivery (p={p}, d={d})")

    # depot/customer TW & service
    def _tw(cust_id: int) -> tuple[float, float]:
        c = id2c.get(cust_id)
        if c is None:
            return 0.0, float("inf")
        return float(c["ready"]), float(c["due"])

    def _service(cust_id: int) -> float:
        c = id2c.get(cust_id)
        if c is None:
            return 0.0
        return float(c["service"])

    def _demand(cust_id: int) -> float:
        c = id2c.get(cust_id)
        if c is None:
            return 0.0
        return float(c["demand"])

    def _dist(a: int, b: int) -> float:
        ca = id2c.get(a); cb = id2c.get(b)
        if ca is None or cb is None:
            return float("inf")
        ax, ay = float(ca["x"]), float(ca["y"])
        bx, by = float(cb["x"]), float(cb["y"])
        # プロジェクト側の前提（ユークリッド→切り捨て→int）に合わせる
        import math
        return float(int(math.hypot(bx - ax, by - ay)))

    # 時刻と積載をシミュレーション（service は「到着→wait→TWチェック→service加算」）
    t = 0.0
    load = 0.0

    depot_ready, depot_due = _tw(depot)
    # start depot も TW を満たす範囲に寄せる
    if t < depot_ready:
        t = depot_ready
    if t > depot_due:
        errors.append(f"[TW] vehicle={vehicle_id}: start depot violates TW (t={t}, due={depot_due})")
    t += _service(depot)

    prev = depot
    for idx, nid in enumerate(seq, start=1):
        nid = int(nid)
        if nid not in id2c:
            errors.append(f"[NODE] vehicle={vehicle_id}: unknown node id={nid}")
            prev = nid
            continue

        t += _dist(prev, nid)

        ready, due = _tw(nid)
        if t < ready:
            t = ready
        if t > due:
            errors.append(f"[TW] vehicle={vehicle_id}: node={nid} pos={idx} violates TW (t={t}, due={due})")

        t += _service(nid)

        load += _demand(nid)
        if load < -1e-9 or load > float(vehicle_capacity) + 1e-9:
            errors.append(f"[CAP] vehicle={vehicle_id}: node={nid} pos={idx} violates capacity (load={load}, cap={vehicle_capacity})")

        prev = nid

    # return to depot（帰着TWもチェック）
    t += _dist(prev, depot)
    if t < depot_ready:
        t = depot_ready
    if t > depot_due:
        errors.append(f"[TW] vehicle={vehicle_id}: depot return violates TW (t={t}, due={depot_due})")

    return (len(errors) == 0), errors

