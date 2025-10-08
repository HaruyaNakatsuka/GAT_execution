import { useEffect, useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Line } from "recharts";

export default function InteractiveVRPViewer({ customers, routes, PD_pairs, depot_id_list, vehicle_num_list }) {
  const [selectedNode, setSelectedNode] = useState(null);

  const idToCoord = Object.fromEntries(customers.map(c => [c.id, { x: c.x, y: c.y }]));
  const idToType = Object.fromEntries(customers.map(c => [c.id, c.demand > 0 ? "pickup" : c.demand < 0 ? "delivery" : "depot"]));

  const handleClick = (nodeId) => {
    const partner = PD_pairs[nodeId] || Object.entries(PD_pairs).find(([p, d]) => d === nodeId)?.[0];
    if (partner) {
      setSelectedNode({
        id: nodeId,
        coord: idToCoord[nodeId],
        partnerId: Number(partner),
        partnerCoord: idToCoord[partner],
      });
    } else {
      setSelectedNode({ id: nodeId, coord: idToCoord[nodeId] });
    }
  };

  const colors = ["#007BFF", "#28A745", "#FFC107", "#DC3545", "#6F42C1"];

  const scatterData = customers.map(c => ({ id: c.id, x: c.x, y: c.y, type: idToType[c.id] }));

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-2">Interactive VRP Route Viewer</h2>
      <ScatterChart width={800} height={600}>
        <CartesianGrid />
        <XAxis type="number" dataKey="x" name="X" />
        <YAxis type="number" dataKey="y" name="Y" />
        <Tooltip cursor={{ strokeDasharray: "3 3" }} content={({ payload }) => payload?.[0] && (<div className="bg-white p-2 border rounded">ID: {payload[0].payload.id}</div>)} />

        {routes.map((route, i) => (
          <>
            <Line key={`route_${i}`} data={route.map(id => idToCoord[id])} stroke={colors[Math.floor(i / 2) % colors.length]} dot={false} />
            <Scatter
              key={`points_${i}`}
              data={route.map(id => ({ id, ...idToCoord[id] }))}
              fill={colors[Math.floor(i / 2) % colors.length]}
              onClick={(e) => handleClick(e.id)}
            />
          </>
        ))}
      </ScatterChart>

      {selectedNode && (
        <div className="mt-4 border p-3 rounded bg-gray-50">
          <h3 className="font-bold mb-2">選択されたノード情報</h3>
          <p>ID: {selectedNode.id}</p>
          <p>座標: ({selectedNode.coord.x.toFixed(2)}, {selectedNode.coord.y.toFixed(2)})</p>
          {selectedNode.partnerId && (
            <>
              <p>対応ノードID: {selectedNode.partnerId}</p>
              <p>対応ノード座標: ({selectedNode.partnerCoord.x.toFixed(2)}, {selectedNode.partnerCoord.y.toFixed(2)})</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
