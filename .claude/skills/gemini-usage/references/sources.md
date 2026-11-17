# 監視ソースと現行仕様の根拠

## 監視ソース（公式のみ）

| ソース名 | URL | 日付の取り方 |
|---|---|---|
| Gemini API | https://ai.google.dev/gemini-api/docs/changelog | 見出しの日付 |
| Gemini CLI | GitHub google-gemini/gemini-cli の Releases（stableのみ。nightly・previewは取らない）と https://geminicli.com/docs/changelogs | リリースの公開日時 |
| Geminiアプリ | https://gemini.google/release-notes/ | 見出しの日付（2026.10.13形式） |
| ドキュメント | https://ai.google.dev/gemini-api/docs/llms.txt 、https://geminicli.com/llms.txt | 検知日 |
| 記事 | https://blog.google/products/gemini/rss/ 、https://blog.google/technology/google-deepmind/rss/ 、https://developers.googleblog.com/feeds/posts/default | 記事の日付 |

## 重点ページ（現行仕様の根拠）

| 根拠ID | ページ | URL | 確認日 |
|---|---|---|---|
| D-gemini-cli-headless | Gemini CLI のヘッドレス実行（出力形式・終了コード） | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/headless.md | 2026-11-17 |
| D-gemini-cli-reference | Gemini CLI のコマンド・オプション一覧（cheatsheet） | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/cli-reference.md | 2026-11-17 |
| D-gemini-cli-configuration | Gemini CLI の設定リファレンス（settings.json・環境変数・引数） | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/reference/configuration.md | 2026-11-17 |
| D-gemini-cli-policy-engine | Gemini CLI のポリシーエンジン（承認モード・ルール） | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/reference/policy-engine.md | 2026-11-17 |
| D-gemini-cli-trusted-folders | Gemini CLI の信頼済みフォルダ | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/trusted-folders.md | 2026-11-17 |
| D-gemini-cli-authentication | Gemini CLI の認証（ヘッドレス実行時の認証） | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/get-started/authentication.mdx | 2026-11-17 |
| D-gemini-cli-gemini-md | Gemini CLI の指示ファイル（GEMINI.md） | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/gemini-md.md | 2026-11-17 |
| D-gemini-cli-skills | Gemini CLI のスキル（Agent Skills） | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/cli/skills.md | 2026-11-17 |
| D-gemini-cli-subagents | Gemini CLI のサブエージェント | https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/core/subagents.md | 2026-11-17 |
| D-gemini-api-get-started | Gemini API のはじめ方（Interactions API） | https://aistudio.google.com/docs/get-started.md | 2026-11-17 |
| D-gemini-api-interactions | Interactions API の概要 | https://aistudio.google.com/docs/interactions-overview.md | 2026-11-17 |
| D-gemini-api-models | Gemini API のモデル一覧 | https://aistudio.google.com/docs/models.md | 2026-11-17 |
| D-gemini-api-latest-model | 最新の Gemini モデル（選び方の概要） | https://aistudio.google.com/docs/latest-model.md | 2026-11-17 |
| D-gemini-api-deprecations | Gemini API の廃止予定 | https://aistudio.google.com/docs/deprecations.md | 2026-11-17 |
| D-gemini-api-libraries | Gemini API のライブラリ（Google GenAI SDK と旧ライブラリ） | https://aistudio.google.com/docs/libraries.md | 2026-11-17 |
| D-gemini-api-migrate-sdk | Google GenAI SDK への移行ガイド | https://aistudio.google.com/docs/migrate.md | 2026-11-17 |
| D-gemini-api-prompting | プロンプト設計の公式ガイド（Prompt design strategies） | https://aistudio.google.com/docs/prompting-strategies.md | 2026-11-17 |
| D-gemini-api-carbon | Gemini 4 Carbon の新機能と移行チェックリスト | https://aistudio.google.com/docs/whats-new-gemini-4-carbon.md | 2026-11-17 |
