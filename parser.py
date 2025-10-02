def parse_lilim200(filepath, x_offset=0, y_offset=0, id_offset=0, time_offset=0):
    customers = []
    P_to_D = {}

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # 1行目から車両数・容量を読み取る
    header_parts = lines[0].strip().split()
    num_vehicles = int(header_parts[0])
    vehicle_capacity = int(header_parts[1])

    # 2行目以降のノード情報を処理
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) < 9:
            continue

        cust_id = int(parts[0]) + id_offset
        x = float(parts[1]) + x_offset
        y = float(parts[2]) + y_offset
        demand = int(parts[3])
        ready = int(parts[4]) + time_offset
        due = int(parts[5]) + time_offset
        service = int(parts[6])
        if int(parts[7]) > 0:
            pickup_index = int(parts[7]) + id_offset
        else:
            pickup_index = int(parts[7])
        if int(parts[8]) > 0:
            delivery_index = int(parts[8]) + id_offset
        else:
            delivery_index = int(parts[8])

        node = {
            'id': cust_id,
            'x': x,
            'y': y,
            'demand': demand,
            'ready': ready,
            'due': due,
            'service': service,
            'pickup_index': pickup_index,
            'delivery_index': delivery_index
        }

        customers.append(node)

        if demand > 0 and delivery_index > 0:
            P_to_D[cust_id] = delivery_index

    return {
        'customers': customers,
        'PD_pairs': P_to_D,
        'num_vehicles': num_vehicles,
        'vehicle_capacity': vehicle_capacity,
        'depot_id': customers[0]['id'],
        'depot_coord': (customers[0]['x'], customers[0]['y'])
    }
