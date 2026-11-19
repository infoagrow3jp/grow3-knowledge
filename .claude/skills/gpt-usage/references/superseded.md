# 置き換わった記述

SKILL.md・details.md から外した行を、置き換わった日・置き換え後の行と一緒に記録する（新しい順）。

| 置き換わった日 | 外した行 | 置き換え後の行 | 根拠ID |
|---|---|---|---|
| 2026-11-19 | 現行ID：`gpt-6-astra`（最難度）、`gpt-6.1-sol`（複雑な作業を低コストで）、`gpt-6.1-terra`（文章・画像）、`gpt-6-luna`（定型・大量） | 現行ID：`gpt-6.2-astra`（最難度）、`gpt-6.2-sol`（日常のコーディング・エージェント）、`gpt-6.1-terra`（文章・画像）、`gpt-6-luna`（定型・大量） | O-2026-11-19-16 |
| 2026-11-19 | API で迷ったら `gpt-6-astra`（旗艦）、知能とコストの釣り合いなら `gpt-6.1-sol`、コスト重視の大量処理なら `gpt-6-luna` | API で迷ったら `gpt-6.2-astra`（旗艦）、知能とコストの釣り合いなら `gpt-6.2-sol`、コスト重視の大量処理なら `gpt-6-luna` | O-2026-11-19-16 |
| 2026-11-19 | Codex での案内：最難度は Astra、繰り返し・長時間の作業は GPT-6.1 Sol、日常の文章と視覚は GPT-6.1 Terra、定型・大量は Luna | Codex での案内：最難度は GPT-6.2 Astra（または GPT-6 Astra）、日常のコーディング・文章・複数資料の作業は GPT-6.2 Sol、日常の文章と視覚は GPT-6.1 Terra、定型・大量は Luna | O-2026-11-19-14 |
| 2026-11-19 | Codex での出発点は、Luna なら `high`、Astra なら `low`、GPT-6.1 Sol はクライアントの既定 | Codex での出発点は、GPT-6.2 Astra・GPT-6.2 Sol ならクライアントが選ぶ強さ、Luna なら `high`、GPT-6 Astra なら `low` | O-2026-11-19-14 |
| 2026-11-19 | `gpt-6-astra` と `gpt-6.1-sol` に effort `none` を渡さない（最小は `low`。Astra は HTTP 400） | effort `none` を渡さない：`gpt-6.2-astra`・`gpt-6.2-sol` は拒否される。`gpt-6-astra` は HTTP 400、`gpt-6.1-sol` は最小が `low` | O-2026-11-19-20 |
| 2026-11-19 | API は全体の方針を `instructions`、依頼を `input` に分ける（`instructions` が優先） | API は共通の指示を `input` 先頭の `developer` メッセージ、その回だけの指示を `instructions` に置く（`instructions` が優先） | O-2026-11-19-19 |
| 2026-11-19 | API の続きは `previous_response_id`。`instructions` は引き継がれないので毎回送る | API の続きは `previous_response_id`。`instructions` は引き継がれないので、連なり全体の指示は最初の `developer` メッセージに置く | O-2026-11-19-17、O-2026-11-19-18 |
