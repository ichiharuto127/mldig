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
