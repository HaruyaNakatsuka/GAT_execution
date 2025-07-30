## GAT-based VRP Solver

本プロジェクトは、論文「Individually Rational Collaborative Vehicle Routing through Give-And-Take Exchanges (IJCAI 2023)」に基づいて、GAT（Give-And-Take）アルゴリズムによる協調的車両経路問題（Collaborative VRP）の再現および改良実装を行ったものです。Google OR-Tools を用いて、Li & Lim (2001) のデータセット上で実験を再現しています。

## ファイル構成と機能

- `main.py`: プログラムのエントリーポイント。全体の処理フロー（データ読み込み → 初期解生成 → GATによる改善）を統括。
- `parser.py`: SINTEFのPDPTWインスタンス（例：LC2_2_1.txt）を解析し、顧客情報やpickup→delivery対応表を構造化データとして読み込む。
- `gat.py`: GATアルゴリズムの主処理を実装。初期解の生成、2車両ペア間でのGive-and-Take交換の実行、交換候補の探索などを含む。
- `flexible_vrp_solver.py`: OR-Toolsを用いて制約を柔軟にON/OFFできるVRPソルバーを提供。主に2車両VRPの最適化に使用。
- `visualizer.py`: 各LSP（車両）のルートを2次元平面上に可視化する。実験結果の直感的な把握に役立つ。

補足: データセットは [SINTEF公式サイト](https://www.sintef.no/projectweb/top/pdptw/li-lim-benchmark/) から取得。
