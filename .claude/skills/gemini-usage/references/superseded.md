# 置き換わった記述

SKILL.md・details.md から外した行を、置き換わった日・置き換え後の行と一緒に記録する（新しい順）。

| 置き換わった日 | 外した行 | 置き換え後の行 | 根拠ID |
|---|---|---|---|
| 2026-11-21 | リアルタイムの対話型の世界生成は `models/genie-4`（2026年11月19日に一般提供。…）（details.md） | リアルタイムの対話型の世界生成は `genie-4`（2026年11月19日に一般提供。…） | G-2026-11-21-4、G-2026-11-21-5 |
| 2026-11-20 | 使わない：`gemini-4-carbon` での明示キャッシュ `caches.create`・`cached_content`（代わりに既定の暗黙キャッシュ） | 使わない：`gemini-4-carbon`・`gemini-4-neon` での明示キャッシュ `caches.create`・`cached_content`（代わりに既定の暗黙キャッシュ） | G-2026-11-20-4 |
| 2026-11-20 | `thinking_level` はモデルで使える値が違う（Carbon・Argon は `low`〜`high`、Hydrogen・Neon は `xhigh` まで） | `thinking_level` はモデルで使える値が違う（Carbon・Argon は `low`〜`high`、Hydrogen・Neon は `xhigh` まで。Gemini 4 は `minimal` 不可） | G-2026-11-20-5 |
| 2026-11-20 | `thinking_level` の使える値は、…`gemini-3.5-flash-lite` が `minimal`（既定）・`low`・`medium`・`high`（details.md） | 同じ行の末尾に「`minimal` は Gemini 4 では使えず、指定するとエラーになる」を追加 | G-2026-11-20-5 |
| 2026-11-20 | `gemini-4-carbon` は明示キャッシュ（`cachedContents`・`caches.create`）に対応しない。…（details.md） | `gemini-4-carbon` と `gemini-4-neon` は明示キャッシュ（`cachedContents`・`caches.create`）に対応しない。… | G-2026-11-20-4 |
| 2026-11-19 | APIはまず `gemini-4-hydrogen`。深い推論は `gemini-4-carbon` か `gemini-4-argon`、大量・低コストは `gemini-3.5-flash-lite` | APIはまず `gemini-4-hydrogen`。深い推論は `gemini-4-neon`・`gemini-4-carbon`・`gemini-4-argon`、大量・低コストは `gemini-3.5-flash-lite` | G-2026-11-18-2 |
| 2026-11-19 | `thinking_level` はモデルで使える値が違う（Carbon・Argon は `low`〜`high`、Hydrogen は `xhigh` まで） | `thinking_level` はモデルで使える値が違う（Carbon・Argon は `low`〜`high`、Hydrogen・Neon は `xhigh` まで） | G-2026-11-18-2 |
| 2026-11-19 | Gemini 4 の3モデルはコンテキストが100万トークン、出力は既定64K・ロングデコードで最大100万トークン | Gemini 4 の各モデルはコンテキストが100万トークン、出力は既定64K・ロングデコードで最大100万トークン | G-2026-11-18-2 |
