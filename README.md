# mldig

[![CI](https://github.com/ichiharuto127/mldig/actions/workflows/ci.yml/badge.svg)](https://github.com/ichiharuto127/mldig/actions/workflows/ci.yml)

ML学習者のための arXiv 論文キャッチアップ CLI。指定カテゴリの新着から興味キーワードに合う論文だけを絞り込み、LLM で日本語ダイジェストを毎日1ファイル生成する。

名前の由来は dig（深掘り）× digest（ダイジェスト）。

## なぜ作ったか

ML/LLM エンジニアを目指す自分自身が、毎日増え続ける arXiv 論文のキャッチアップに追われているという実体験が出発点。SNS やまとめ記事の「評判」経由ではなく、自分の興味キーワードで一次情報を毎日拾える仕組みが欲しかった。素材が公開データなので、完成品は自分専用にならず他の ML 学習者もそのまま使える。

## 何ができるか：3段階の深掘り導線

1論文につき「浅く広く → 気になったものだけ深く」の3段階で読める：

1. **箇条書き3点**（手法・結果・意義）— ダイジェスト全体を流し読み
2. **詳細要約**（300〜400字、折りたたみ）— 気になる論文だけ開く
3. **arXiv 原文リンク** — それでも気になれば全文へ

出力サンプル: [digests/2026-07-12.md](digests/2026-07-12.md)

## 使い方

### 必要なもの

- Python 3.13+ / [uv](https://docs.astral.sh/uv/)
- OpenAI 互換の API キー

### セットアップ

```bash
git clone https://github.com/ichiharuto127/mldig.git
cd mldig
uv sync
cp .env.example .env   # OPENAI_API_KEY / MODEL_NAME を設定
```

取得カテゴリ・興味キーワード・取得上限は `config.toml` で編集する。

### 実行

```bash
uv run mldig            # 当日ダイジェストを digests/YYYY-MM-DD.md に生成
uv run mldig --dry-run  # LLMを呼ばず候補一覧のみ表示（無料）
uv run mldig --limit 5  # 要約本数を制限
```

## 設計判断とその理由

| 判断 | 理由 |
|---|---|
| ソースを arXiv 1本に絞る | 初回開発は完走優先。ソース追加はデータ形式差分の吸収が本質なので拡張フェーズに回す |
| CLI から開始（UIなし） | ロジックと表示を分離しておけば、Phase3 の Streamlit/FastAPI 化が綺麗な差分になる |
| モデルは .env で差し替え | OpenAI 互換クライアント1個 + `MODEL_NAME`/`OPENAI_BASE_URL` の差し替えで3社の日本語品質 A/B 評価（設計済み）とモデル廃止への追従を両立 |
| 予算 月¥500 ハードキャップ | プリペイド$5・Hard limit $3・`reasoning_effort="none"` 固定・`max_tokens=800` の多層防壁。真のリスクは単価ではなく「推論トークンの暴発」と「再要約による volume creep」 |
| seen.json キャッシュ | 要約済み論文の再課金を構造的に防止。1件ごとに保存し途中クラッシュにも耐える |
| digests/ をコミット | 継続利用の証跡をリポジトリ履歴に残す |

詳細な経緯と全仕様は [docs/design.md](docs/design.md)、試行錯誤の一次記録は [docs/devlog.md](docs/devlog.md) を参照。

## コスト実測

GPT-5.6 Luna（effort=none）で1本あたり入力 約400 / 出力 約480 トークン ≈ **0.5円、約3秒**。上限フル稼働（20本/日）でも月約¥300 で ¥500 キャップ内。

## 品質・開発プロセス

- ruff + pytest + GitHub Actions CI（純粋ロジックのみテスト、LLM 呼び出しはテスト対象外）
- pre-commit + gitleaks（キー漏洩防止）
- feature ブランチ + PR 運用。main は Ruleset で保護（PR 必須・CI 必須・レビュースレッド解決必須）、Copilot 自動レビュー有効
- AI に書かせたコードは PR セルフレビューで採否判断してからマージ（採否の記録は devlog）

## ロードマップ

| Phase | 内容 | 状態 |
|---|---|---|
| 1 | arXiv + LLM 要約ダイジェスト CLI | **完了（今ここ）** |
| 2 | LangChain 導入：`mldig dig <arxiv-id>`（全文深掘り）→ 興味プロファイル推薦 | 設計済み |
| 3 | Streamlit UI + FastAPI | 構想 |
| 4 | Docker + Cloud Run で公開デモ | 構想 |

## 将来構想

複数ソース化（RSS・GitHub Trending）、Notion 蓄積連携、embedding 類似度による推薦改善、日本語特化モデルの再評価。

## License

MIT
