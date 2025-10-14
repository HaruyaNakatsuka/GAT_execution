
import { useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Line,
  ResponsiveContainer,
} from "recharts";

export default function InteractiveVRPViewer({
  customers,
  routes,
  PD_pairs,
  depot_id_list,
  vehicle_num_list,
}) {
  const [selectedNode, setSelectedNode] = useState(null);

  // === データ整理 ===
  const idToCoord = Object.fromEntries(customers.map((c) => [c.id, { x: c.x, y: c.y }]));
  const idToType = Object.fromEntries(
    customers.map((c) => [
      c.id,
      c.demand > 0 ? "pickup" : c.demand < 0 ? "delivery" : "depot",
    ])
  );

  // === クリック時に対応ノードを表示 ===
  const handleClick = (nodeId) => {
    const partner =
      PD_pairs[nodeId] ||
      Object.entries(PD_pairs).find(([p, d]) => Number(d) === Number(nodeId))?.[0];
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

  // === LSPごとに色を変える ===
  const colors = ["#007BFF", "#28A745", "#FFC107", "#DC3545", "#6F42C1", "#FF6F61"];

  // === グラフ描画 ===
  return (
    <div style={{ padding: "1rem" }}>
      <h3 className="font-semibold mb-2">Interactive VRP Route Viewer</h3>
      <ResponsiveContainer width="100%" height={600}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid />
          <XAxis type="number" dataKey="x" name="X" />
          <YAxis type="number" dataKey="y" name="Y" />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ payload }) =>
              payload?.[0] && (
                <div className="bg-white p-2 border rounded">
                  <p>ID: {payload[0].payload.id}</p>
                  <p>({payload[0].payload.x.toFixed(1)}, {payload[0].payload.y.toFixed(1)})</p>
                </div>
              )
            }
          />

          {routes.map((route, i) => {
            if (route.length <= 2) return null; // デポのみの車両はスキップ
            const color = colors[Math.floor(i / vehicle_num_list[0]) % colors.length];
            const lineData = route.map((id) => idToCoord[id]);
            const scatterData = route.map((id) => ({
              id,
              ...idToCoord[id],
              type: idToType[id],
            }));

            return (
              <g key={`route_${i}`}>
                <Line
                  data={lineData}
                  type="monotone"
                  dataKey="y"
                  stroke={color}
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Scatter
                  data={scatterData}
                  fill={color}
                  onClick={(e) => handleClick(e.id)}
                />
              </g>
            );
          })}
        </ScatterChart>
      </ResponsiveContainer>

      {/* === ノード情報表示 === */}
      {selectedNode && (
        <div
          style={{
            marginTop: "1rem",
            border: "1px solid #ddd",
            padding: "10px",
            borderRadius: "8px",
            background: "#f9f9f9",
            maxWidth: "400px",
          }}
        >
          <h4 style={{ marginBottom: "8px" }}>選択されたノード情報</h4>
          <p>ID: {selectedNode.id}</p>
          <p>
            座標: ({selectedNode.coord.x.toFixed(2)}, {selectedNode.coord.y.toFixed(2)})
          </p>
          {selectedNode.partnerId && (
            <>
              <hr style={{ margin: "8px 0" }} />
              <p>対応ノード ID: {selectedNode.partnerId}</p>
              <p>
                対応ノード座標: (
                {selectedNode.partnerCoord.x.toFixed(2)},{" "}
                {selectedNode.partnerCoord.y.toFixed(2)})
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}


