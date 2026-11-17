---
name: gpt-usage
description: >-
  Codex CLI（codex exec）や OpenAI API（Responses API・SDK）で GPT を呼ぶ前に読む。
  トリガー：codex exec、Codex CLI、GPTを呼ぶ、OpenAI API、Responses API、gpt-6、AGENTS.md、config.toml。
---

## 通常の呼び出し
- CLIの非対話実行は `codex exec "指示"`。stdout には最終メッセージだけ、経過は stderr に出る［D-codex-non-interactive］
- `codex exec` の既定は読み取り専用。編集させるなら `--sandbox workspace-write` を付ける［D-codex-non-interactive］
- Git リポジトリの外では止まる。外で使うなら `--skip-git-repo-check` を付ける［D-codex-non-interactive］
- 長い指示は stdin で渡す：`cat prompt.txt | codex exec -`。引数と併用するとパイプ側は追加の文脈になる［D-codex-non-interactive］
- API は Responses API：`client.responses.create(model="<モデルID>", input="…")`、文章は `response.output_text`［D-api-quickstart］
- SDK は環境変数 `OPENAI_API_KEY` を自動で読む（引数でキーを渡さなくてよい）［D-api-quickstart］

## モデルの選び方
- 現行ID：`gpt-6-astra`（最難度）、`gpt-6.1-sol`（複雑な作業を低コストで）、`gpt-6.1-terra`（文章・画像）、`gpt-6-luna`（定型・大量）［D-api-models］
- Codex は `-m <モデルID>` で指定する。`gpt-6.1-terra` は〔v0.159.0以降〕［D-codex-models］
- 推論の強さは API が `reasoning.effort`、Codex が `-c model_reasoning_effort=<値>`［D-api-reasoning、D-codex-config-reference］
- `gpt-6-astra` と `gpt-6.1-sol` に effort `none` を渡さない（最小は `low`。Astra は HTTP 400）［D-api-reasoning、D-api-gpt6-guide］
- effort が `none` 以外のとき `temperature`・`top_p`・`top_logprobs` を送らない［D-api-gpt6-guide］

## 指示の書き方
- 目的・文脈・出力の形・守る境界・確かめ方を書く。細かい手順は要るときだけ［D-codex-prompting］
- CLI は開いているファイルを自動で見ない。対象のパスを指示に明記する［D-codex-prompting］
- `gpt-6-astra` は質問して止まりやすい。非対話では「意図を推し量り完了まで進める」と書く［D-api-gpt6-guide］
- API は全体の方針を `instructions`、依頼を `input` に分ける（`instructions` が優先）［D-api-text］
- `max_output_tokens` は推論分を含む。25,000 以上を確保し、`status` が `incomplete` でないか見る［D-api-reasoning、D-api-responses-create］

## 指示ファイル・スキル
- Codex は実行ごとに `AGENTS.md` を読む（ホーム → ルート → 現在のフォルダの順に連結、近いほうが優先）［D-codex-agents-md］
- 合計 32 KiB を超えた分は読まれない。同じフォルダの `AGENTS.override.md` が `AGENTS.md` より先に採られる［D-codex-agents-md］
- プロジェクトの `.codex/config.toml` は信頼済みのときだけ読まれる。`codex exec --trust` で信頼を保存する［D-codex-config-basic、D-codex-non-interactive］
- スキルは `.agents/skills/<名前>/SKILL.md`（`name`・`description` 必須）。`$スキル名` で明示的に呼ぶ［D-codex-skills］
- サブエージェントは頼んだときだけ起動する。分け方・全員を待つか・返す要約を指示に書く［D-codex-subagents］
- `gpt-6-astra` は `AGENTS.md`・スキルの記述に敏感。矛盾を点検し、利用者の指示が優先と書く［D-api-gpt6-guide］

## 操作別の注意
- 続きは `codex exec resume --last "指示"`（現在のフォルダの直近）か `codex exec resume <SESSION_ID>`［D-codex-non-interactive、D-codex-cli-reference］
- `workspace-write` でもネットワークは切れ、`.git`・`.agents`・`.codex`・`.aws` は読み取り専用［D-codex-approvals］
- ネットワークが要るなら `-c 'sandbox_workspace_write.network_access=true'` を付ける［D-codex-approvals］
- 書き込み先を増やすなら `--add-dir <パス>`。`danger-full-access`・`--yolo` は隔離環境だけ［D-codex-cli-reference、D-codex-non-interactive］
- 非対話で新たな承認が要る操作は失敗する。権限は起動時に指定する（`codex exec` の表に `--ask-for-approval` はない）［D-codex-subagents、D-codex-cli-reference］
- 機械で読むなら `--json`、最終メッセージだけなら `-o <ファイル>`、形を固定するなら `--output-schema <schema.json>`［D-codex-non-interactive］
- API の続きは `previous_response_id`。`instructions` は引き継がれないので毎回送る（`conversation` と併用不可）［D-api-responses-create］
- API の構造化出力は `response_format` ではなく `text.format` で指定する［D-api-migrate-responses］

## 使わないもの
- 使わない：`codex exec --full-auto`（代わりに `--sandbox workspace-write`、自動審査つきは `--approve-for-me`）［D-codex-non-interactive］
- 使わない：`approval_policy` の `untrusted`・`on-failure`（代わりに `on-request` か `never`）［D-codex-approvals、D-codex-config-reference］
- 使わない：Codex の `wire_api = "chat"`（代わりに Responses API 互換のエンドポイント）［D-codex-models］
- 使わない：ChatGPT サインインの Codex での `gpt-5.5`・`gpt-5.4`・`gpt-5.3-codex`（代わりに `gpt-6.1-sol` など現行ID）［D-codex-models］
- 使わない：新規実装とツール呼び出しでの Chat Completions（代わりに Responses API）［D-api-migrate-responses、D-api-gpt6-guide］
- 使わない：Assistants API（停止済み。代わりに Responses API と Conversations API）［D-api-deprecations］
- 使わない：`/v1/prompts` の保存済みプロンプト（2026-11-30 停止。代わりにプロンプトをコードに置く）［D-api-deprecations］
- 使わない：`gpt-5`・`o3`・`gpt-5-mini`・`gpt-5-nano`（2026-12-11 停止。代わりに `gpt-6.1-sol`・`gpt-6.1-terra`・`gpt-6-luna`）［D-api-deprecations］
- 使わない：GPT-4o・GPT-4.1 系（2027-01-14 停止。代わりに `gpt-6-luna`）、`gpt-5.1`（2027-04-01 停止。代わりに `gpt-6-sol`）［D-api-deprecations］

詳細は references/details.md、最近の変更は references/changelog/。
