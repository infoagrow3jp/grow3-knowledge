# 監視ソースと現行仕様の根拠

## 監視ソース（公式のみ）
| ソース名 | URL | 日付の取り方 |
|---|---|---|
| Claude Platform（API・SDK） | https://platform.claude.com/docs/en/release-notes/overview.md | 見出しの日付 |
| Claudeアプリ | https://support.claude.com/en/articles/12138966-release-notes.md | 見出しの日付 |
| Claude Code | https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md | npmレジストリ（https://registry.npmjs.org/@anthropic-ai/claude-code）の time["<version>"] |
| Claude Codeドキュメント | https://code.claude.com/docs/llms.txt | 検知日 |
| Platformドキュメント | https://platform.claude.com/llms.txt | 検知日 |
| 記事 | https://www.anthropic.com/news 、https://www.anthropic.com/engineering 、https://claude.com/blog | 記事の日付 |

## 重点ページ（現行仕様の根拠）
| 根拠ID | ページ | URL | 確認日 |
|---|---|---|---|
| D-claude-code-headless | Claude Code の非対話実行 | https://code.claude.com/docs/en/headless.md | 2026-11-25 |
| D-claude-code-cli-reference | Claude Code の CLI リファレンス | https://code.claude.com/docs/en/cli-reference.md | 2026-11-25 |
| D-claude-code-permission-modes | Claude Code の権限モード | https://code.claude.com/docs/en/permission-modes.md | 2026-11-25 |
| D-claude-code-permissions | Claude Code の権限ルール | https://code.claude.com/docs/en/permissions.md | 2026-11-20 |
| D-claude-code-settings | Claude Code の設定ファイルと優先順位 | https://code.claude.com/docs/en/settings.md | 2026-11-25 |
| D-claude-code-memory | Claude Code の指示ファイル（CLAUDE.md・AGENTS.md） | https://code.claude.com/docs/en/memory.md | 2026-11-17 |
| D-claude-code-skills | Claude Code のスキル | https://code.claude.com/docs/en/skills.md | 2026-11-25 |
| D-claude-code-sub-agents | Claude Code のサブエージェント | https://code.claude.com/docs/en/sub-agents.md | 2026-11-20 |
| D-claude-code-model-config | Claude Code のモデル設定（別名・effort） | https://code.claude.com/docs/en/model-config.md | 2026-11-20 |
| D-claude-code-best-practices | Claude Code のベストプラクティス | https://code.claude.com/docs/en/best-practices.md | 2026-11-20 |
| D-platform-models-overview | モデル一覧 | https://platform.claude.com/docs/en/models/overview.md | 2026-11-17 |
| D-platform-choosing-a-model | モデルの選び方 | https://platform.claude.com/docs/en/about-claude/models/choosing-a-model.md | 2026-11-17 |
| D-platform-model-deprecations | モデルとAPIパラメータの非推奨・提供終了 | https://platform.claude.com/docs/en/about-claude/model-deprecations.md | 2026-11-24 |
| D-platform-fable-5-2-migration | Claude Fable 5.2・Mythos 5.2 の移行ガイド | https://platform.claude.com/docs/en/models/fable-5-2/migration-guide.md | 2026-11-17 |
| D-platform-prompting-best-practices | プロンプトの書き方の公式ガイド | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices.md | 2026-11-22 |
| D-platform-api-versioning | APIバージョン（anthropic-version） | https://platform.claude.com/docs/en/api/versioning.md | 2026-11-17 |
| D-platform-working-with-messages | Messages API の使い方 | https://platform.claude.com/docs/en/build-with-claude/working-with-messages.md | 2026-11-25 |
