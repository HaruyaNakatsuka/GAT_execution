import React from "react";
import FastVRPViewer from "./components/FastVRPViewer";

/**
 * props:
 * - customers
 * - routes
 * - PD_pairs
 * - depot_id_list
 * - vehicle_num_list
 */
export default function InteractiveVRPViewer({ customers, routes, PD_pairs, depot_id_list, vehicle_num_list }) {
  // 受け取った props をそのまま FastVRPViewer に渡す
  if (!customers || !routes) {
    return <div>データがありません</div>;
  }

  return (
    <div style={{ padding: "20px" }}>
      <h2>VRP Route Viewer (react-konva)</h2>
      <FastVRPViewer
        customers={customers}
        routes={routes}
        PD_pairs={PD_pairs || {}}
        depot_id_list={depot_id_list || []}
        vehicle_num_list={vehicle_num_list || []}
      />
    </div>
  );
}

