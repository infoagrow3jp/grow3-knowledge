# 監視ソースと現行仕様の根拠

## 監視ソース（公式のみ）

| ソース名 | URL | 日付の取り方 |
|---|---|---|
| OpenAI API | https://developers.openai.com/api/docs/changelog.md | 見出しの日付（年はページ内の年の区切りから決める） |
| Codex | https://developers.openai.com/codex/changelog | 項目の日付（CLIのバージョンは npmレジストリ https://registry.npmjs.org/@openai/codex の time で補う） |
| ChatGPTアプリ | https://learn.chatgpt.com/docs/whats-new.md | 週単位の見出し（公開日は不明扱い）。https://help.openai.com/en/articles/6825453-chatgpt-release-notes は自動取得を拒否されるため使えていない |
| ドキュメント | https://developers.openai.com/api/docs/llms.txt 、https://developers.openai.com/codex/llms.txt | 検知日 |
| 記事 | https://openai.com/news/rss.xml | 記事の日付 |

## 重点ページ（現行仕様の根拠）

| 根拠ID | ページ | URL | 確認日 |
|---|---|---|---|
| D-codex-non-interactive | Codex の非対話実行 | https://learn.chatgpt.com/docs/non-interactive-mode.md | 2026-11-17 |
| D-codex-cli-reference | Codex CLI のコマンドとオプションの一覧（オプション表は .md に出ず、HTML版 https://learn.chatgpt.com/docs/developer-commands?surface=cli に載る） | https://learn.chatgpt.com/docs/developer-commands.md?surface=cli | 2026-11-17 |
| D-codex-approvals | Codex の承認とセキュリティ | https://learn.chatgpt.com/docs/agent-approvals-security.md | 2026-11-17 |
| D-codex-config-basic | Codex の設定ファイルの基本 | https://learn.chatgpt.com/docs/config-file/config-basic.md | 2026-11-17 |
| D-codex-config-reference | Codex の設定リファレンス | https://learn.chatgpt.com/docs/config-file/config-reference.md | 2026-11-17 |
| D-codex-agents-md | AGENTS.md による指示 | https://learn.chatgpt.com/docs/agent-configuration/agents-md.md | 2026-11-17 |
| D-codex-subagents | Codex のサブエージェント | https://learn.chatgpt.com/docs/agent-configuration/subagents.md | 2026-11-17 |
| D-codex-skills | スキルの作り方 | https://learn.chatgpt.com/docs/build-skills.md | 2026-11-17 |
| D-codex-prompting | プロンプトの書き方（ChatGPT・Codex） | https://learn.chatgpt.com/docs/prompting.md | 2026-11-17 |
| D-codex-models | Codex のモデル | https://learn.chatgpt.com/docs/models.md | 2026-11-19 |
| D-api-quickstart | API のクイックスタート | https://developers.openai.com/api/docs/quickstart.md | 2026-11-19 |
| D-api-models | API のモデル一覧 | https://developers.openai.com/api/docs/models.md | 2026-11-19 |
| D-api-deprecations | API の廃止・非推奨 | https://developers.openai.com/api/docs/deprecations.md | 2026-11-17 |
| D-api-responses-create | Responses API の作成リファレンス | https://developers.openai.com/api/reference/resources/responses/methods/create.md | 2026-11-19 |
| D-api-migrate-responses | Responses API への移行ガイド | https://developers.openai.com/api/docs/guides/migrate-to-responses.md | 2026-11-19 |
| D-api-gpt6-guide | GPT-6 の使い方（最新モデル向けのプロンプトと移行） | https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md | 2026-11-17 |
| D-api-text | テキスト生成ガイド | https://developers.openai.com/api/docs/guides/text.md | 2026-11-19 |
| D-api-reasoning | 推論モデルのガイド | https://developers.openai.com/api/docs/guides/reasoning.md | 2026-11-19 |
