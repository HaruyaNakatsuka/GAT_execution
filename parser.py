def parse_lilim200(filepath, id_offset=0, time_offset=0):
    customers = []
    pickups = {}
    deliveries = {}

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
        x = float(parts[1])
        y = float(parts[2])
        demand = int(parts[3])
        ready = int(parts[4]) + time_offset
        due = int(parts[5]) + time_offset
        service = int(parts[6])
        pickup_index = int(parts[7])
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
            pickups[cust_id] = delivery_index + id_offset
        elif demand < 0 and pickup_index > 0:
            deliveries[cust_id] = pickup_index + id_offset

    return {
        'customers': customers,
        'pickup_to_delivery': pickups,
        'delivery_to_pickup': deliveries,
        'num_vehicles': num_vehicles,
        'vehicle_capacity': vehicle_capacity
    }
