---
name: claude-usage
description: >-
  Claude Code CLI や Claude API を呼ぶ前に読む。claude -p の非対話実行と Messages API・SDK の現行仕様
  （モデルID・effort・権限モード・出力形式・CLAUDE.md・スキル・サブエージェント）。
  トリガー語：Claude、Anthropic、claude -p、Claude Code、Messages API、モデルID、Fable、Opus、Sonnet、Haiku。
---

## 通常の呼び出し
- CLIの非対話実行は `claude -p "指示"`。終了コード0が成功、0以外が失敗［D-claude-code-headless］
- `-p` は承認が要るツール呼び出しを拒否する。`--allowedTools "Read,Edit,Bash(git diff *)"` で列挙するか `--permission-mode auto` を付ける〔v2.1.302以降〕［D-claude-code-permission-modes、D-claude-code-headless］
- 機械で読むときは `--output-format json` を付け、本文は `result`、セッションIDは `session_id` から取る［D-claude-code-headless］
- 起動を速くしたいスクリプト・CIは `--bare` を付ける。フック・スキル・MCP・CLAUDE.md を自動で読まない（設定ファイルの権限ルールは読む）。認証は `ANTHROPIC_API_KEY` が要る［A-2026-11-20-8、D-claude-code-headless］
- APIは `/v1/messages` へPOSTし、本文に `model`・`max_tokens`・`messages`、ヘッダーに `x-api-key`・`anthropic-version: 2026-10-21`・`content-type: application/json` を送る（SDKはヘッダーを自動で付ける）［D-platform-working-with-messages、D-platform-api-versioning］

## モデルの選び方
- APIの現行モデルIDは `claude-fable-5-2`・`claude-opus-5-5`・`claude-sonnet-5-5`・`claude-haiku-5-5`。IDは固定の版で、自動では新しくならない［D-platform-models-overview］
- 迷ったら `claude-opus-5-5`。難しい推論・長時間のエージェント作業は `claude-fable-5-2`、大量・低遅延の処理は `claude-haiku-5-5`［D-platform-models-overview、D-platform-choosing-a-model］
- CLIは `--model` に別名（`fable`・`opus`・`sonnet`・`haiku`）かモデルIDを渡す。版を固定するときはモデルIDを渡す［D-claude-code-model-config］
- 考える深さはモデルを替える前に effort で調整する。CLIは `--effort low|medium|high|xhigh|max`、APIは `output_config` の `effort`［D-platform-choosing-a-model、D-claude-code-cli-reference、D-platform-prompting-best-practices］

## 指示の書き方
- 対象のファイル・症状・完了の条件を最初に具体的に書く［D-claude-code-best-practices］
- 実行してほしいことは「変更して」と明示する（「提案して」と書くと提案だけが返る）［D-platform-prompting-best-practices］
- 長い資料は冒頭に置き、質問と指示を末尾に置く［D-platform-prompting-best-practices］
- 合否が出る確認手段（テスト・ビルドのコマンド）を渡し、実行したコマンドと出力を報告させる［D-claude-code-best-practices］
- 大文字や IMPORTANT の強調、`think hard`、「最後までやれ」は書かない（過剰適用・過剰作業になる）［D-claude-code-best-practices］

## 指示ファイル・スキル
- CLAUDE.md は毎回読まれる文脈で、強制力はない。1ファイル200行未満、検証できる具体的な文で書く［D-claude-code-memory］
- 例外を許さない決まりは CLAUDE.md ではなくフックか deny ルールにする［D-claude-code-best-practices、D-claude-code-permissions］
- スキルは `.claude/skills/<名前>/SKILL.md`。frontmatter は1行目の `---` から書き、`description` の先頭に主な用途を置く［D-claude-code-skills］
- サブエージェント定義は `name` と `description` が必須。欠けるとファイルごと読み飛ばされ、未知のフィールド名も無視される［A-2026-11-20-5、D-claude-code-sub-agents］
- サブエージェントは会話履歴を見ない。必要な前提は委任の指示にすべて書く［D-claude-code-sub-agents］

## 操作別の注意
- 続きは `--continue`（直近）か `--resume <session_id>`。並行して動かすときは `session_id` を控えて `--resume` を使う［D-claude-code-headless］
- 承認者がいない無人実行は `--permission-prompts none` を付ける〔v2.1.259以降〕［D-claude-code-headless］
- 許可リストだけで動かすCIは `--permission-mode dontAsk` と `--allowedTools` を組み合わせる［D-claude-code-permission-modes］
- `--dangerously-skip-permissions` は隔離したコンテナ・VMの中だけで使う［D-claude-code-permission-modes］
- 許可ルールは `Bash(git diff *)` のように `*` の前に空白を入れる。deny は allow より常に優先される［D-claude-code-headless、D-claude-code-permissions］
- スキーマどおりのJSONは `--output-format json --json-schema '<スキーマ>'`。`structured_output` の有無を確かめてから使う［D-claude-code-headless］
- 自分で書いていないリポジトリで `-p` を使うときは `--setting-sources user` か `--bare` を付け、そのフック・MCPを読ませない［D-claude-code-permissions］
- システムプロンプトは `--append-system-prompt` で足す。`--system-prompt` は既定の指示をすべて消す［D-claude-code-cli-reference］
- API：応答は `content[0].text` と決め打ちせず、ブロックの `type` で選ぶ。`thinking` ブロックは変えずに送り返す［D-platform-fable-5-2-migration］
- API：思考のトークンも `max_tokens` に含まれる。小さいと本文の前に `stop_reason: "max_tokens"` で止まる［D-platform-fable-5-2-migration］
- API：履歴は毎回すべて送り、途中で `system`・`tools`・過去のメッセージを書き換えない（`claude-fable-5-2` では400）［D-platform-working-with-messages、D-platform-fable-5-2-migration］

## 使わないもの
- 使わない：`temperature`・`top_p`・`top_k`（代わりに指示文で調整する。APIバージョン 2026-10-21 では400）［D-platform-api-versioning、D-platform-model-deprecations］
- 使わない：assistant メッセージ末尾のプリフィル（代わりに構造化出力かシステムプロンプトの指示。4.6以降のモデルで400）［D-platform-working-with-messages］
- 使わない：`thinking` の `budget_tokens`（代わりに effort。4.7以降のモデルで400）［D-platform-prompting-best-practices］
- 使わない：`claude-fable-5-2` での `thinking: {type: "disabled"}` と `tool_choice` の `any`・`tool`（代わりに effort を下げる・`auto` にする。400）［D-platform-fable-5-2-migration］
- 使わない：`claude-sonnet-4-5-20250929`（代わりに `claude-sonnet-5-5`。2026-11-30 に提供終了）［D-platform-model-deprecations］
- 使わない：`claude-opus-4-5-20251101`・日付なしの `claude-opus-4-5`（代わりに `claude-opus-5-5`。Claude API では 2027-01-22 に提供終了）［A-2026-11-23-7、A-2026-11-24-46］
- 使わない：提供終了の `claude-opus-4-1-20250805`・`claude-opus-4-20250514`・`claude-sonnet-4-20250514`・`claude-3-7-sonnet-20250219`・`claude-3-5-haiku-20241022`・`claude-3-haiku-20240307`（代わりに現行のモデルID）［D-platform-model-deprecations］
- 使わない：`--enable-auto-mode`（代わりに `--permission-mode auto`。削除済み）［D-claude-code-cli-reference］
- 使わない：`--remote`（代わりに `--cloud`。非推奨の別名）［D-claude-code-cli-reference］

詳細は references/details.md、最近の変更は references/changelog/。
