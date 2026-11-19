# 置き換わった記述

SKILL.md・details.md から外した行を、置き換わった日・置き換え後の行と一緒に記録する（新しい順）。

| 置き換わった日 | 外した行 | 置き換え後の行 | 根拠ID |
|---|---|---|---|
| 2026-11-19 | APIはまず `gemini-4-hydrogen`。深い推論は `gemini-4-carbon` か `gemini-4-argon`、大量・低コストは `gemini-3.5-flash-lite` | APIはまず `gemini-4-hydrogen`。深い推論は `gemini-4-neon`・`gemini-4-carbon`・`gemini-4-argon`、大量・低コストは `gemini-3.5-flash-lite` | G-2026-11-18-2 |
| 2026-11-19 | `thinking_level` はモデルで使える値が違う（Carbon・Argon は `low`〜`high`、Hydrogen は `xhigh` まで） | `thinking_level` はモデルで使える値が違う（Carbon・Argon は `low`〜`high`、Hydrogen・Neon は `xhigh` まで） | G-2026-11-18-2 |
| 2026-11-19 | Gemini 4 の3モデルはコンテキストが100万トークン、出力は既定64K・ロングデコードで最大100万トークン | Gemini 4 の各モデルはコンテキストが100万トークン、出力は既定64K・ロングデコードで最大100万トークン | G-2026-11-18-2 |
