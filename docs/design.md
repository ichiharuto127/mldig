# mldig 設計メモ（Phase0：題材決定セッションの成果物）

作成日：2026-07-12（/grill-me セッションで確定）
リポジトリ：`~/dev/personal/mldig`（GitHub public 公開予定：ichiharuto127/mldig）

---

## 1. 何を作るか

**ML学習者のための論文・技術情報キャッチアップアプリ「mldig」**

- 名前の由来：dig（深掘り）× digest（ダイジェスト）のダブルミーニング
- Phase1 の形：CLI ツール
  `arXiv 新着取得 → 興味キーワードで絞り込み → LLM で日本語要約 → Markdown ダイジェスト出力`

### Phase1 スコープ（やること）
- arXiv API で指定カテゴリ（cs.LG / cs.CL / cs.CV 等、設定で変更可）の新着論文を取得
- 興味キーワード（設定ファイルで管理）でフィルタリング
- LLM API で日本語要約（既定 GPT-5.6 Luna・effort=none 固定。詳細は「3.5 モデル選定」）
- `digests/YYYY-MM-DD.md` 形式でダイジェスト出力
- 軽量品質基盤：ruff + pytest（LLM 呼び出しを含まない純粋ロジックのみ）+ GitHub Actions CI
- pre-commit + gitleaks（個人開発の標準装備、確定済み方針）

### Phase1 スコープ外（やらないこと）
- UI（Phase3 で Streamlit）
- LangChain（Phase2 で導入）
- 複数ソース対応（RSS・GitHub Trending 等は将来構想。X API は有料化のため対象外）
- Notion への蓄積連携（README の将来構想に書くだけ。実装しない）
- cron 等の自動実行（手動実行で開始。自動化は後続フェーズ）
- Provider の本格抽象化（基底クラス・ファクトリ等）は Phase2 の LangChain 導入に回す。
  Phase1 は「OpenAI 互換クライアント 1 個 + `.env` で `BASE_URL`/`MODEL_NAME` を差し替え」の
  軽量スワップに留める（3 社の日本語 A/B 評価に必要な最小限だけ）

---

## 2. なぜそれか（面接で語る差別化 3 点）

### 課題設定
ML/LLM エンジニア志望の自分自身が、毎日増える arXiv 論文・技術情報のキャッチアップに
追われているという実体験が出発点。公開データが素材なので、完成品は自分専用にならず
他の ML 学習者もそのまま使える（＝Phase4 の一般公開デモと相性が良い）。

> Playbox で学んだ教訓「面白い問題ではなく、誰かがずっと待っていた問題を探せ」とも整合。

### 技術選定の理由
| 選定 | 理由 |
|---|---|
| ソースを arXiv 1 本に絞る | 実績ゼロからの初回開発は完走優先。ソースごとのデータ形式差分の吸収は拡張フェーズに回す（スコープ管理の判断として語る） |
| LLM は既定 GPT-5.6 Luna（effort=none） | 詳細は「3.5 モデル選定」。要約は推論不要なので effort を切る。OpenAI 互換エコシステム（有識者メモ 2-1・LangChain 事例）に乗れる最新モデル |
| モデル名・API キーは .env 管理 | モデル廃止・切り替えに 1 行で追従（有識者メモ 2-1 の方針）。プリペイド $5 + 使用上限設定で事故防止 |
| CLI から開始（UI なし） | ロジックと表示を分離しておくと Phase3 の Streamlit/FastAPI 化が差分として綺麗に見える |
| uv / WSL2 / ~/dev/personal | 前回セッションで確定済みの個人開発標準環境 |

### 試行錯誤の跡の残し方
- README「設計判断とその理由」セクション
- `docs/devlog.md`：日付付きの試行錯誤ログ（うまくいかなかったこと・対処を一次記録）
- PR 説明文：変更理由を書く（feature ブランチ + PR 運用は確定済み方針）
- Notion への転記は任意（必須にしない。記録は継続できる仕組みを優先）

### プラスアルファ（優先度低）
AI（Claude Code 等）に書かせたコードは PR セルフレビューで中身を理解してからマージする。
理解できなかった箇所は devlog に書き、調べた結果を追記する習慣にする。

---

## 3. どう進めるか

### 全体ロードマップ（1 プロダクト進化型・同一リポジトリ）
| Phase | 内容 | 対応する有識者メモ |
|---|---|---|
| 1 | arXiv + LLM 要約ダイジェスト CLI、GitHub 公開、軽量 CI | 2-1（OpenAI API） |
| 2 | LangChain 導入（要約チェーン・興味プロファイルによる推薦） | 2-1 の発展 |
| 3 | Streamlit UI + FastAPI で API 化 | 2-2（Streamlit） |
| 4 | Docker 化 + Cloud Run デプロイ（GitHub Actions 自動デプロイ） | 2-3・2-4 |

将来構想（README に記載のみ）：複数ソース化（RSS・GitHub Trending）、Notion 蓄積連携、
推薦精度の改善（embedding 類似度）。

### 3.5 モデル選定（2026-07-12 調査で決定）

**予算：このプロジェクト単体で月 ¥500 を絶対に超えない。**

想定ワークロード（1 日 20 本要約 × 30 日 = 月 600 本、1 本 ≈ 入力 500 + 出力 300 トークン）
では、下表のどのモデルでも ¥500 に余裕で収まる。つまり単価ではなく「日本語品質 × 最新性」
で選べる状況。¥150/$ 換算・effort を切った前提の月コスト：

| モデル | 入力/出力(per 1M) | 月コスト | 日本語 | 備考 |
|---|---|---|---|---|
| DeepSeek V4 Pro | $0.44 / $0.87 | 約¥43 | ○ | 最安帯・オープン系 |
| Gemini 3.1 Flash-Lite | $0.25 / $1.50 | 約¥52 | ◎ | 最安×日本語強い |
| Claude 4.5 Haiku | $1 / $5 | 約¥180 | ◎ | 日本語◎・Claude 系一貫 |
| **GPT-5.6 Luna（既定）** | $1 / $6 | 約¥207 | ○〜◎ | 最新・エコシステム最強 |
| Grok 4.5 | $2 / $6 | 約¥252 | ○ | 高いが最新 eval 対象 |
| Gemini 3.5 Flash | $1.50 / $9 | 約¥311 | ◎ | 日本語◎・最新非推論 |

**既定＝GPT-5.6 Luna（`reasoning_effort="none"` 固定）。**
`.env` の `BASE_URL`/`MODEL_NAME` で差し替え可能にし、Phase1 中に
**Luna / Gemini 3.5 Flash / Claude 4.5 Haiku の日本語要約 3 社 A/B を devlog に記録**して、
勝った 1 つを最終既定に確定する（＝モデル選定自体を差別化ポイント 3＝試行錯誤の跡にする）。

**¥500 を破る 2 つの地雷（単価ではなくこれが本当の制約）：**
1. **推論 effort の暴発**：GPT-5.6・Grok は推論モデル。要約で `high` にすると推論トークン
   （出力課金）が 1 本数千発生し得る。例：Luna effort=high で 1 本 3000 推論トークン →
   月 $11.9 ≈ ¥1,785 で超過。**要約は effort=none/low + `max_tokens=500` で封じる。**
2. **volume creep**：「全件を毎回再要約」「取得本数の無制限化」（メモ 2-1 の事故フロー）。
   取得本数を設定で上限管理し、要約済みはキャッシュしてスキップする。

**¥500 ハードキャップの enforcement（OpenAI）：**
- オートリチャージ OFF ＋ プリペイド $5 のみ（使い切ったら停止。青天井を構造的に封じる）
- Hard usage limit を月 $3（≒¥450）に設定
- `reasoning_effort="none"` ＋ `max_tokens=500`
- mldig 専用 API キーで消費を可視化・隔離

**不採用：Sakana AI「Fugu」**（日本語は良いが個人向けはサブスク $20/月〜＝¥500 の 6 倍超、
PAYG は法人のみ）。英語 abstract → 日本語要約は Gemini Flash/Claude Haiku で十分な品質が出る
ため、現時点で $20/月を払う価値はない。将来、日本語生成の質がボトルネックになったら再検討
（README の将来構想に記載のみ）。

### Phase1 の Done 基準
- [x] `uv run` 一発で当日のダイジェスト Markdown が生成される（2026-07-12 実走確認）
- [x] GitHub に public 公開済み、CI（ruff + pytest）がグリーン
- [x] README に課題設定・設計判断・将来ロードマップが書かれている（PR #5）
- [ ] 自分が 3 日連続で実際に使う（使わなかったら理由を devlog に記録＝最初の試行錯誤ネタ）

### 実装前の準備（Phase1 セッション冒頭でやること）
1. OpenAI Platform でプリペイド $5 チャージ + オートリチャージ OFF + Hard limit $3 + mldig 専用 API キー発行
   （A/B 用に Gemini・Anthropic のキーも取るなら同様に上限設定。ただし合計で ¥500 を超えない運用）
2. `~/dev/personal/mldig` で `uv init` → git init → GitHub リポジトリ作成（gh CLI）
3. pre-commit + gitleaks 設定（Python_study・ian と同じ構成を流用）
4. `.env` / `.gitignore` を最初に整備（キー漏洩対策を Day1 から）

### 次回セッションの始め方
WSL2 側で本ファイルを読ませてから開始する：
「`~/dev/personal/mldig/docs/design.md` を読んで、Phase1 の実装を計画から始めて」

---

## 4. Phase1 実装仕様（2026-07-12 実装計画セッションで確定）

### 要約フォーマット：3段階の深掘り導線
「一覧で流し読み → 気になる論文だけ詳細 → 原文へ」の段階的構成。1論文あたり：

1. **短い要約**：箇条書き3点（手法／結果／意義）
2. **詳細要約**：`<details>` 折りたたみ内に300〜400字（背景・手法・結果・限界）。
   追加のAPI呼び出しはせず、1回の要約呼び出しで短い要約と同時に生成する
3. **原文リンク**：arXiv abs ページ

コスト影響：`max_tokens` を 500→**800** に変更（「3.5」の記述を上書き）。上限フル稼働
（20本/日）の月試算は約¥420（Luna）で ¥500 キャップ・Hard limit $3 の内側。実運用は
フィルタ後 5〜10 本/日想定でさらに低い。全文ベースの本当に深い要約は Phase2 の
`mldig dig <arxiv-id>`（LangChain のドキュメントローダー＋要約チェーンの導入題材）に
位置づける。

### 確定した細部仕様
| 項目 | 決定 |
|---|---|
| 「新着」の定義 | 直近 `days_back=3` 日を取得。土日の announce 停止分も月曜にまとめて拾える |
| 再実行の扱い | `data/seen.json`（arXiv ID キー）で要約済みをスキップ。同日再実行は同ファイル上書き（冪等）。0件の日も「0件」と明記して出力 |
| フィルタ | title + abstract を小文字化して部分一致、キーワード間は OR。マッチ語をダイジェストに表示 |
| 取得上限 | `max_papers=20`/日（予算試算と一致）。超過分はタイトル+リンクのみ掲載 |
| 設定の分離 | `config.toml`＝categories / keywords / max_papers / days_back（stdlib tomllib）、`.env`＝APIキー・BASE_URL・MODEL_NAME |
| LLM失敗時 | リトライ2回 → 失敗論文はタイトル+リンクのみで続行（1本の失敗で全体を止めない） |
| reasoning_effort | gpt系モデルのときのみ付与（Gemini/Anthropic のOpenAI互換エンドポイントは非対応の可能性。A/B時の注意点） |
| usage記録 | API応答の usage を `data/usage.jsonl` に追記（3社A/Bの素材＋volume creep監視） |
| digests/ | git にコミットする（継続利用の証跡として残す） |
| 依存 | `arxiv` / `openai` / `python-dotenv`。dev：ruff / pytest / pre-commit |
| その他 | Python 3.13 / MIT License / CLI は argparse（`--dry-run`・`--limit`）。Typer は Phase3 で検討 |

### PR分割（各PR終了時点で動く状態を保つ）
1. `chore/scaffold`：uv足場・pre-commit + gitleaks・ruff・pytest・GitHub Actions CI・public公開
2. `feat/fetch-filter`：config 読み込み → arXiv 取得 → フィルタ → キャッシュ（`--dry-run` で候補一覧まで）
3. `feat/summarize-digest`：要約 → Markdown レンダリング → CLI 完成（`uv run mldig` 一発）
4. `docs/readme`：README（課題設定・設計判断・ロードマップ）→ 実走 → devlog 記録 → Done 基準チェック

---

## 5. 3社A/B評価設計（2026-07-13 確定）

「Geminiは日本語が強い」等の世間の評判ではなく、自分のタスク（ML論文abstract→日本語要約）
での実測で既定モデルを決める。design.md 差別化ポイント3（モデル選定を試行錯誤の跡にする）の実体。

### 方式：ブラインド評価
- 対象：GPT-5.6 Luna（現既定）/ Gemini 3.5 Flash / Claude 4.5 Haiku
- 同一の5論文 × 3モデル = 15要約。**モデル名を伏せてシャッフル提示**し採点（先入観バイアス排除）。
  シャッフル役・開票役はClaude、採点者は本人
- 補助指標（自動集計）：トークン消費・応答速度（data/usage.jsonl から）

### 評価軸（各1〜5点）
| 軸 | 見るもの |
|---|---|
| 事実の正確さ | abstract にない内容の捏造・重要な結果の取りこぼしがないか |
| 専門用語の扱い | 無理な直訳をせず、カタカナ/英語のまま残す判断が適切か |
| 読みやすさ | 冗長でないか・日本語として自然か |
| 形式遵守 | 【手法】〜形式と字数指定を守るか（守らないモデルは運用コスト増） |

### 判定ルール
合計点で決定。同点タイなら現既定の Luna を維持（OpenAI エコシステム優位のため）。
コストは3社とも ¥500 キャップ内のためタイブレーカーとしてのみ使う。

### 実行の仕組み：`--ab-tag` オプション（実装は後続PR）
`uv run mldig --ab-tag luna --limit 5` の形式。挙動：
- data/seen.json を**読まない・書かない**（同一論文を3回要約できる。退避ミスによる再課金事故を構造的に防ぐ）
- 出力先は `digests/ab/YYYY-MM-DD-<tag>.md`（日次ダイジェストと混ざらない）
- usage.jsonl への記録は通常どおり行う（A/Bの補助指標に使う）
- モデル切り替えは .env の MODEL_NAME / OPENAI_BASE_URL / OPENAI_API_KEY を差し替えて3回実行
- **3回は同日に連続実行する**（arXiv取得結果のズレを防ぐ）。実行後に3ファイルの論文集合が
  一致しているか確認し、ズレていたら共通部分のみで採点する

### 手順
1. Gemini / Anthropic のAPIキーを取得し、各社でも使用上限を設定
2. .env を差し替えながら `--ab-tag` で3回実行（同日連続）
3. Claude がモデル名を伏せてシャッフル提示 → 4軸×15要約を採点
4. 開票。合計点・トークン・速度を集計して devlog に記録
5. 勝者を .env の既定にし、本節と「3.5」の結論を更新

---

## 6. Phase2 設計骨子（2026-07-13 確定。詳細設計は Phase2 開始時に別セッションで）

### スコープ：案A「dig コマンドのみ LangChain 新設」
- 動いている日次要約（summarizer.py）は**触らない**。全文深掘りの `mldig dig` だけを
  LangChain で新規実装する（「必然性のある場所にだけ導入し、効果を見てから移行判断」）
- 日次要約の LangChain 移行は dig 完成後に別PRで判断し、比較材料を devlog に残す
- 推薦（興味プロファイル）は Phase2 後半の別PR。dig した論文＝興味の最良シグナルなので dig が先

### `mldig dig <arxiv-id>` の仕様概要
- 全文取得：arXiv HTML 優先 → PDF フォールバック（LangChain のドキュメントローダー）
- 処理：分割（text splitter）→ 深掘り要約チェーン
- 出力：`digests/deep/<arxiv-id>.md`（背景・手法詳細・実験結果・限界・位置づけ、800〜1200字目安）
- 3段階導線の先に「第4段階=AIによる全文解説」が挟まる形で Phase1 と一直線につながる

### コスト試算
入力 2〜3万トークン/本 ≈ ¥4/本（Luna）。月30本掘っても約¥120で ¥500 キャップ内。

### Phase2 の Done 基準（案）
- [ ] `uv run mldig dig <arxiv-id>` 一発で深掘り Markdown が生成される
- [ ] LangChain を dig に限定導入した理由と効果を devlog に記録
- [ ] 日次要約を LangChain に移行するか否かの判断と根拠を devlog に記録
