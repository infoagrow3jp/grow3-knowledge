---
name: gemini-usage
description: >-
  Gemini CLI や Gemini API（Google GenAI SDK）を呼ぶ前に読む。非対話実行のフラグ、
  承認モード、モデルID、使わない旧SDK・旧モデルを公式仕様に合わせる。
  トリガー：Gemini CLI、gemini -p、ヘッドレス、Gemini API、google-genai、Interactions API、GEMINI.md。
---

## 通常の呼び出し
- CLIの非対話実行は `gemini -p "指示"`。`-p` なしの位置引数はTTYでは対話モードになる［D-gemini-cli-reference］
- 入力はパイプで渡せる（`cat file | gemini -p "指示"`）。`-p` の文は標準入力の後ろに付く［D-gemini-cli-reference］
- 機械で読むなら `--output-format json` を付け、`response` を読む。失敗時は `error` が入る［D-gemini-cli-headless］
- 終了コードを見る：0 成功、1 一般・API の失敗、42 入力エラー、53 ターン上限超過［D-gemini-cli-headless］
- 非対話では確認が要るツール呼び出しは拒否される。編集させるなら `--approval-mode auto_edit` を付ける［D-gemini-cli-policy-engine、D-gemini-cli-configuration］
- 認証情報の保存がない環境では、先に環境変数（`GEMINI_API_KEY` など）で認証を設定する［D-gemini-cli-authentication］
- APIは `google-genai`（Python）か `@google/genai`（JS）で `client.interactions.create(model=..., input=...)` を呼び、`interaction.output_text` を読む［D-gemini-api-get-started］
- APIキーは環境変数 `GEMINI_API_KEY` で渡す。RESTは `x-goog-api-key` ヘッダで `v1beta/interactions` へ POST［D-gemini-api-get-started］

## モデルの選び方
- APIはまず `gemini-4-hydrogen`。深い推論は `gemini-4-neon`・`gemini-4-carbon`・`gemini-4-argon`、大量・低コストは `gemini-3.5-flash-lite`［D-gemini-api-latest-model、G-2026-11-18-2］
- モデルIDは公式一覧の文字列をそのまま使い、停止予定の表で確かめる［D-gemini-api-models、D-gemini-api-deprecations］
- CLIは `-m` を省くと `auto`。指定するなら別名 `pro`・`flash`・`flash-lite` を使う［D-gemini-cli-reference］
- `thinking_level` はモデルで使える値が違う（Carbon・Argon は `low`〜`high`、Hydrogen・Neon は `xhigh` まで）［D-gemini-api-latest-model、G-2026-11-18-2］
- `gemini-4-carbon` で `max_output_tokens` を指定するなら 32,768 以上（思考と出力の合計の上限）［D-gemini-api-carbon］

## 指示の書き方
- 目的を直接・簡潔に書く。説得調の言い回しを入れない［D-gemini-api-prompting］
- 役割・制約・出力形式は、システム指示かプロンプトの先頭に置く［D-gemini-api-prompting］
- 長い資料は先に置き、質問・指示は最後に置く［D-gemini-api-prompting］
- 指示・資料・課題を XML風タグか Markdown 見出しで区切り、1つのプロンプトで形式を混ぜない［D-gemini-api-prompting］
- 詳しい回答が要るときは明示して頼む（既定は簡潔に答える）［D-gemini-api-prompting］
- 出力の形は例（few-shot）で示し、例どうしの書式をそろえる［D-gemini-api-prompting］

## 指示ファイル・スキル
- 常に効かせる指示は `GEMINI.md` に書く（`~/.gemini/GEMINI.md`、作業フォルダとその親）。見つかった全ファイルが毎回送られる［D-gemini-cli-gemini-md］
- スキルは `SKILL.md` 入りのフォルダを `.gemini/skills/` か `.agents/skills/` に置く（ユーザー用は `~/` の下）［D-gemini-cli-skills］
- サブエージェントは `.gemini/agents/*.md`。YAML frontmatter の `name` と `description` が必須［D-gemini-cli-subagents］
- サブエージェントから別のサブエージェントは呼べない。`tools` を省くと親セッションの全ツールを引き継ぐ［D-gemini-cli-subagents］

## 操作別の注意
- CLIのセッション再開は `gemini -r "latest" "指示"`。ID指定は `-r "<session-id>"`、一覧は `--list-sessions`（現在のプロジェクト分）［D-gemini-cli-reference］
- 全ツール自動承認（`yolo`）はコマンドラインでしか有効にできない。`security.disableYoloMode` が true なら効かない［D-gemini-cli-configuration］
- ツールごとの許可・拒否は `~/.gemini/policies/*.toml` に書く。ワークスペースの `.gemini/policies` は効かない。`argsPattern` は RE2 構文で、最上位の引数は `\x00` 区切り［D-gemini-cli-policy-engine、G-2026-11-19-4］
- フォルダの信頼が有効な環境では、未信頼フォルダでの非対話実行は失敗する。`--skip-trust` か `GEMINI_CLI_TRUST_WORKSPACE=true` を付ける［D-gemini-cli-trusted-folders］
- APIの会話継続は `previous_interaction_id`。`tools`・`system_instruction`・`generation_config` は引き継がれないので毎回指定する［D-gemini-api-interactions］
- `store=false` にすると `previous_interaction_id` とバックグラウンド実行が使えない［D-gemini-api-interactions］
- JSONで受けるなら `response_format` に `type: "text"`・`mime_type: "application/json"`・`schema` を渡す［D-gemini-api-get-started］
- 64Kトークンを超える出力は `background=True` と 65,536 超の `max_output_tokens` を指定し、`interactions.get` で完了を待つ［D-gemini-api-carbon］

## 使わないもの
- 使わない：`google-generativeai`・`@google/generative-ai`（代わりに `google-genai`・`@google/genai`）［D-gemini-api-libraries、D-gemini-api-migrate-sdk］
- 使わない：新規コードでの `generateContent`（代わりに Interactions API。既存の呼び出しは動く）［D-gemini-api-interactions］
- 使わない：`temperature`・`top_p`・`top_k`（Gemini 4 と 3.6 以降は無視する。代わりに指定を外す）［D-gemini-api-prompting］
- 使わない：`gemini-2.5-pro`・`gemini-2.5-flash`（代わりに `gemini-3.8-flash`・`gemini-3.5-flash-lite`）［D-gemini-api-deprecations］
- 使わない：停止済みの `gemini-2.0-flash`・`gemini-3-pro-preview`（代わりに `gemini-3.6-flash`・`gemini-3.1-pro-preview`）［D-gemini-api-deprecations］
- 使わない：`gemini-4-carbon` での明示キャッシュ `caches.create`・`cached_content`（代わりに既定の暗黙キャッシュ）［D-gemini-api-carbon］
- 使わない：CLIの `--yolo`・`-y`（代わりに `--approval-mode=yolo`）［D-gemini-cli-reference］
- 使わない：CLIの `--allowed-tools` と設定の `tools.exclude`（代わりにポリシーエンジンのルール）［D-gemini-cli-reference、D-gemini-cli-policy-engine］

詳細は references/details.md、最近の変更は references/changelog/。
