# mldig devlog

試行錯誤・設計判断の一次記録。日付降順ではなく昇順（古い順）で追記していく。
面接で「うまくいかなかったときどう対処したか」を語る際の素材にする。

---

## 2026-07-12 モデル選定の調査と決定（実装前）

### 背景
予算「このプロジェクト単体で月 ¥500 を絶対に超えない」を制約に、性能も伴う最新モデルを選びたい。
最新 LLM の評価も兼ねたい。日本語との相性も考慮（Sakana AI Fugu 等）。

### 調べて分かったこと
- 想定ワークロード（月 600 本・1 本 ≈ 800 トークン）では、候補モデルの月コストは ¥43〜¥311。
  **どれを選んでも ¥500 に余裕で収まる**。→ 制約は単価ではなく「effort と volume の暴発」だった。
- GPT-5.6 は Sol/Terra/Luna の 3 ティア、effort 軸は none/low/medium/high/xhigh/max の 6 段階
  （2026-07-09 GA）。Luna が最安（$1/$6 per 1M）。
- 要約タスクは推論不要。effort=high にすると推論トークン（出力課金）が暴発し、
  Luna でも試算で月 ¥1,785 に達し得る（1 本 3000 推論トークン想定）。→ effort=none 必須。
- Sakana Fugu：日本語は評価が高いが、個人向けはサブスク $20/月〜で PAYG は法人のみ。
  ¥500 キャップを 6 倍超えるため不採用。

### 決めたこと
- 既定モデル＝**GPT-5.6 Luna、`reasoning_effort="none"` 固定、`max_tokens=500`**。
  理由：OpenAI 互換エコシステム（有識者メモ 2-1・LangChain 事例）に乗れる最新モデルで、
  effort を切れば ¥500 に収まる。
- `.env` の `BASE_URL`/`MODEL_NAME` で差し替え可能にする（本格抽象化は Phase2 の LangChain）。
- ¥500 enforcement：オートリチャージ OFF + プリペイド $5 + Hard limit $3 + 専用キー。

### 未検証・次にやること（TODO）
- [ ] Phase1 実装後、**Luna / Gemini 3.5 Flash / Claude 4.5 Haiku で日本語要約 A/B** を実施し、
      同一 abstract に対する要約品質・トークン消費・体感速度をこの devlog に記録する。
- [ ] その結果で最終既定モデルを確定し、design.md「3.5 モデル選定」を更新する。
- [ ] A/B の評価軸を決める（用語の訳の正確さ / 冗長さ / 事実の取りこぼし、など）。

### 出典（調査時）
- GPT-5.6 pricing: https://www.eesel.ai/blog/gpt-5-6-pricing / https://simonwillison.net/2026/Jul/9/gpt-5-6/
- Gemini 3.5 Flash: https://devtk.ai/en/models/gemini-3-5-flash/
- Grok 4.5 / DeepSeek V4 Pro: https://openrouter.ai/x-ai/grok-4.5
- Sakana Fugu 料金: https://www.ai-souken.com/article/what-is-sakana-fugu

---

## 2026-07-12〜13 Phase1 実装（PR #1〜#3）

### 実測値（設計時の想定との差分）
- `gpt-5.6-luna` はそのまま有効なモデルIDだった（要確認としていた仮置きが当たり）
- 1本あたり入力 349〜461 / 出力 454〜495 トークン、effort=none で約3秒
- 月コスト実測ベース試算 約¥300（設計時想定は¥420）。詳細要約が字数指定300〜400字に
  収まったため出力が想定より少ない
- 3カテゴリ（cs.LG/CL/CV）の直近3日分は FETCH_LIMIT=200 を大きく超える。日次実行なら
  実害なしだが days_back の意味は薄れる（要調整候補）

### Copilot レビュー運用の記録
- PR #2: 5指摘 → 4採用・1見送り。方針「バリデーションは境界（config読み込み・CLI引数）に
  集約し、内部関数は綺麗な入力を前提にする」
- PR #3: push のたびに自動再レビューが走り、計3ラウンド・8指摘 → 6採用・2見送り
  - 見送り根拠1: `str.format` はテンプレート側の波括弧のみ解釈するため、LaTeX入りabstract
    でも安全（`'{t}'.format(t='{O(n)}')` で実証）→ Copilot の false positive
  - 見送り根拠2: ラベル外の前置き定型文を detail に退避すると、ダイジェストにノイズが載る
    方が害が大きい
- 気づき: ラウンドを重ねるごとに指摘の重大度が「バグ → 設計の綺麗さ → 好み」と下がる。
  **重大度がバグ未満になったら理由を書いて Resolve し打ち切る**、を収束基準にした
- [ ] TODO（本人記入）: レビュー採否で迷った点・自分の言葉での学び

### 開発プロセスの整備
- main を Ruleset で保護（PR必須・CI必須・スレッド解決必須・force push禁止）
- Copilot 自動レビュー有効化（新規PR + 新push の再レビュー）
- [ ] TODO（本人記入）: この運用を1週間回した所感

### 次のアクション
- [ ] 3日連続で `uv run mldig` を実運用（Done基準4つ目）
- [ ] Gemini / Anthropic のキー取得 → `--ab-tag` 実装 → 3社ブラインドA/B（design.md 5）
