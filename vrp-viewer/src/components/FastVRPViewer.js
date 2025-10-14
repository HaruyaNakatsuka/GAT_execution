import React, { useState } from "react";
import { Stage, Layer, Line, Circle, Text } from "react-konva";

/**
 * VRP経路の高速可視化ビューア
 * props:
 * - customers: [{id, x, y, demand}]
 * - routes: [[1, 5, 9, 0, ...], [...]]
 * - PD_pairs: {pickup_id: delivery_id, ...}
 */
export default function FastVRPViewer({ customers, routes, PD_pairs }) {
  const [selected, setSelected] = useState(null);
  const scale = 4.0; // スケール倍率（座標が大きい場合に調整）

  const stageWidth = 800;
  const stageHeight = 600;

  // 座標と種類を辞書化
  const idToCoord = Object.fromEntries(customers.map(c => [c.id, { x: c.x, y: c.y }]));
  const idToType = Object.fromEntries(
    customers.map(c => [c.id, c.demand > 0 ? "pickup" : c.demand < 0 ? "delivery" : "depot"])
  );

  const colors = ["#007BFF", "#28A745", "#FFC107", "#DC3545", "#6F42C1", "#20C997"];

  const handleClick = (node) => {
    const partnerId =
      PD_pairs[node.id] ||
      Object.entries(PD_pairs).find(([p, d]) => d === node.id)?.[0];

    setSelected({
      ...node,
      partnerId: partnerId ? Number(partnerId) : null,
      partnerCoord: partnerId ? idToCoord[partnerId] : null,
    });
  };

  return (
    <div style={{ display: "flex", gap: "20px" }}>
      {/* === 左: VRP可視化エリア === */}
      <Stage width={stageWidth} height={stageHeight} style={{ border: "1px solid #ccc" }}>
        <Layer>
          {/* 経路（直線） */}
          {routes.map((route, i) => (
            <Line
              key={`route_${i}`}
              points={route.flatMap(id => [
                idToCoord[id].x * scale,
                stageHeight - idToCoord[id].y * scale, // ← 修正
              ])}
              stroke={colors[i % colors.length]}
              strokeWidth={2}
              lineJoin="round"
              lineCap="round"
            />
          ))}

          {/* ノード（クリック可能） */}
          {customers.map(c => (
            <Circle
              key={c.id}
              x={c.x * scale}
              y={stageHeight - c.y * scale} // ← 修正
              radius={4}
              fill={
                idToType[c.id] === "pickup"
                  ? "#28A745"
                  : idToType[c.id] === "delivery"
                  ? "#FFC107"
                  : "#007BFF"
              }
              onClick={() => handleClick(c)}
            />
          ))}

          {/* 選択ノード表示 */}
          {selected && (
            <>
              <Circle
                x={selected.x * scale}
                y={stageHeight - selected.y * scale} // ← 修正
                radius={6}
                stroke="black"
                strokeWidth={2}
              />
              {selected.partnerCoord && (
                <Line
                  points={[
                    selected.x * scale,
                    stageHeight - selected.y * scale, // ← 修正
                    selected.partnerCoord.x * scale,
                    stageHeight - selected.partnerCoord.y * scale, // ← 修正
                  ]}
                  stroke="#ff0000"
                  strokeWidth={1.5}
                  dash={[4, 4]}
                />
              )}
            </>
          )}
        </Layer>
      </Stage>

      {/* === 右: 情報パネル === */}
      <div
        style={{
          width: "280px",
          padding: "10px",
          border: "1px solid #ccc",
          borderRadius: "10px",
          background: "#f9f9f9",
          height: "fit-content",
        }}
      >
        <h3>ノード情報</h3>
        {selected ? (
          <>
            <p><b>ID:</b> {selected.id}</p>
            <p>
              <b>座標:</b> ({selected.x.toFixed(1)}, {selected.y.toFixed(1)})
            </p>
            <p><b>種類:</b> {idToType[selected.id]}</p>
            {selected.partnerId && (
              <>
                <p><b>対応ノードID:</b> {selected.partnerId}</p>
                <p>
                  <b>対応ノード座標:</b> (
                  {selected.partnerCoord.x.toFixed(1)}, {selected.partnerCoord.y.toFixed(1)})
                </p>
              </>
            )}
          </>
        ) : (
          <p>ノードをクリックしてください。</p>
        )}
      </div>
    </div>
  );
}
