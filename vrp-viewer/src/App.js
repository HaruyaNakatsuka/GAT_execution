import React, { useEffect, useState } from "react";
import InteractiveVRPViewer from "./InteractiveVRPViewer";

export default function App() {
  const [caseList, setCaseList] = useState([]);        // 正規化後: [{name, steps}, ...]
  const [selectedCase, setSelectedCase] = useState(null);
  const [stepList, setStepList] = useState([]);        // 正規化後: ["step_0.json", ...]
  const [selectedStep, setSelectedStep] = useState(null);
  const [data, setData] = useState(null);

  // ユーティリティ: 入力JSONを正規化して {name, steps} の配列にする
  const normalizeIndexJson = (json) => {
    // 1) 既に { cases: [...] } 形式で来た場合
    if (json && Array.isArray(json.cases)) {
      return json.cases.map((c) => {
        if (typeof c === "string") return { name: c, steps: [] };
        if (typeof c === "object" && c.name) return { name: c.name, steps: c.steps || [] };
        return null;
      }).filter(Boolean);
    }
    // 2) 単純な配列 ["case_1.json", ...] が来た場合
    if (Array.isArray(json)) {
      return json.map((fname) => {
        const base = fname.replace(/\.json$/, "");
        return { name: base, steps: [] };
      });
    }
    // 3) それ以外は空
    return [];
  };

  // 初回：index.json を取得して正規化
  useEffect(() => {
    fetch(process.env.PUBLIC_URL + "/vrp_data/index.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json) => {
        const cases = normalizeIndexJson(json);
        setCaseList(cases);
        if (cases.length > 0) {
          setSelectedCase(cases[0].name);
          // もし steps が既に含まれていればそれを設定
          if (cases[0].steps && cases[0].steps.length > 0) {
            setStepList(cases[0].steps);
            setSelectedStep(cases[0].steps[0]);
          }
        }
      })
      .catch((err) => {
        console.error("index.json 読み込みエラー:", err);
        setCaseList([]);
      });
  }, []);

  // selectedCase が変わったら、その case の step index を読む（case_x/index.json 形式を期待）
  useEffect(() => {
    if (!selectedCase) return;
    // まずは caseList の中に steps があれば利用
    const caseObj = caseList.find((c) => c.name === selectedCase);
    if (caseObj && caseObj.steps && caseObj.steps.length > 0) {
      setStepList(caseObj.steps);
      setSelectedStep(caseObj.steps[0]);
      return;
    }
    // ないなら case フォルダ内の index.json をフェッチして取得
    fetch(process.env.PUBLIC_URL + `/vrp_data/${selectedCase}/index.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`Case index not found: ${res.status}`);
        return res.json();
      })
      .then((json) => {
        // json.steps を期待
        if (Array.isArray(json.steps)) {
          setStepList(json.steps);
          setSelectedStep(json.steps[0] || null);
        } else if (Array.isArray(json)) {
          // もし単純配列が返ってきたらそのまま使う
          setStepList(json);
          setSelectedStep(json[0] || null);
        } else {
          setStepList([]);
          setSelectedStep(null);
        }
      })
      .catch((err) => {
        console.warn("case 内の index.json 読み込みに失敗:", err);
        setStepList([]);
        setSelectedStep(null);
      });
  }, [selectedCase, caseList]);

  // selectedCase と selectedStep が揃ったら実データを読み込む
  useEffect(() => {
    if (!selectedCase || !selectedStep) return;
    fetch(process.env.PUBLIC_URL + `/vrp_data/${selectedCase}/${selectedStep}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Data not found: ${res.status}`);
        return res.json();
      })
      .then((json) => setData(json))
      .catch((err) => {
        console.error("VRPデータ読み込みエラー:", err);
        setData(null);
      });
  }, [selectedCase, selectedStep]);

  return (
    <div style={{ padding: 16 }}>
      <h1>VRP Route Viewer</h1>

      <div style={{ margin: "12px 0" }}>
        <label style={{ marginRight: 8 }}>Case:</label>
        <select
          value={selectedCase || ""}
          onChange={(e) => setSelectedCase(e.target.value)}
        >
          {/* caseList の要素は {name, steps} というオブジェクトに統一済み */}
          {caseList.map((c, idx) => (
            // key はユニークな文字列（name がユニークである前提、無ければ idx 併用）
            <option key={`${c.name}-${idx}`} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>

        <label style={{ marginLeft: 16, marginRight: 8 }}>Step:</label>
        <select
          value={selectedStep || ""}
          onChange={(e) => setSelectedStep(e.target.value)}
        >
          {stepList.map((s, idx) => (
            <option key={`${s}-${idx}`} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div>
        {data ? (
          <InteractiveVRPViewer
            customers={data.customers}
            routes={data.routes}
            PD_pairs={data.PD_pairs}
            depot_id_list={data.depot_id_list}
            vehicle_num_list={data.vehicle_num_list}
          />
        ) : (
          <div>データを読み込み中、またはデータが見つかりません。</div>
        )}
      </div>
    </div>
  );
}
