import matplotlib.pyplot as plt

def plot_routes(customers, routes, title="Initial Routes by LSP"):
    """
    customers: 顧客データのリスト（辞書形式）
    routes: LSPごとのルート（2次元リスト）
    """

    # 顧客IDをキーにして (x, y) 座標を取得する辞書を構築
    coord_map = {c['id']: (c['x'], c['y']) for c in customers}

    plt.figure(figsize=(10, 8))
    colors = plt.cm.get_cmap("tab10", len(routes))  # 最大10色

    for i, route in enumerate(routes):
        xs = []
        ys = []
        for cust_id in route:
            x, y = coord_map[cust_id]
            xs.append(x)
            ys.append(y)
        plt.plot(xs, ys, marker='o', color=colors(i), label=f'LSP {i+1}')

    # デポを強調
    depot_x, depot_y = coord_map[0]
    plt.scatter([depot_x], [depot_y], c='black', s=100, marker='*', label='Depot')

    plt.title(title)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
