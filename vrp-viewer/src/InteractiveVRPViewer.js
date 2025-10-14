import React, { useEffect, useState } from "react";
import FastVRPViewer from "./components/FastVRPViewer";

export default function App() {
  const [vrpData, setVrpData] = useState(null);

  useEffect(() => {
    fetch(process.env.PUBLIC_URL + "/vrp_data/case_1/step_0.json")
      .then(res => res.json())
      .then(json => setVrpData(json))
      .catch(err => console.error("データ読み込みエラー:", err));
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h2>VRP Route Viewer (react-konva)</h2>
      {vrpData ? (
        <FastVRPViewer
          customers={vrpData.customers}
          routes={vrpData.routes}
          PD_pairs={vrpData.PD_pairs}
        />
      ) : (
        <p>データを読み込んでいます...</p>
      )}
    </div>
  );
}
