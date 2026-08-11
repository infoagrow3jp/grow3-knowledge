# Grow3 Producer Bot — 構成メモ

## 位置づけ

このファイルは、Grow3全体から見た「LINE Producer Botという外部システムがどこにあり、何を担い、どこまで実装されているか」を記録する。

**実装の正本はこのリポジトリにはない。**
コード・スキーマ・運用手順の正本は別リポジトリ `infoagrow3jp/grow3-producer-bot` にある。

---

## 本番構成（2026-08-11時点）

```text
LINE
 ↓
Render（サービス名: grow3-producer-bot-1）
 ↓
Claude API
 ↓
Supabase
```

LINE DevelopersのWebhook URL:

`https://grow3-producer-bot-1.onrender.com/webhook`

実装はPython（Flask）。Renderのauto-deployが有効で、`grow3-producer-bot` の
`main` へpushすると再デプロイされる。

環境変数はRenderのEnvironment Variablesで管理する。
コードへ秘密情報を書かない。

---

## Apps Scriptとの関係

**LINE Producer BotはApps Scriptでは動いていない。**

2026-08-11の3診断本番移行時、診断Apps Scriptプロジェクト内にLINE Botの `doPost(e)` が
存在し、診断のPOSTがそちらで処理される競合が起きた。
対処として当該関数を `lineBotDoPost(e)` へ改名し、診断用 `doPost(e)` を唯一の入口とした。

その後の実査で、このApps Script上のLINE Botコードは**旧実装の残骸**であり、本番のProducer BotはすでにRenderで稼働していたことが判明した。

したがって、かつて記録していた「LINE Producer Botを別Apps Scriptプロジェクトへ移行する」
という方針は誤りであり、実施しない。経緯は `ISSUE.md` に無効化記録として残している。

診断Apps Script側に残っている残骸コードの削除は、診断側の掃除として別途扱う。
診断GASプロジェクトへ診断以外の `doPost` を追加しないという原則は維持する。

---

## Phase 1（Seed採集）— 2026-08-11本番化

「後で考え直す価値がある発言をSeedとしてSupabaseへ構造化保存する」機能を追加した。

### 本人指定によるSeed化

- `/seed <本文>` — 本文をそのままSeed化する
- `/seed` 単独送信 — 直前のユーザー発言をSeed化する
- `残して` / `これ残して` — 同上

### AI判定によるSeed化

通常メッセージでは、通常回答とは独立にSeed判定を行う。
残す価値があると判定された場合だけ保存し、通常回答の末尾に通知を1行追加する。

Seed判定・Seed保存の失敗は通常のLINE返信を止めない。
判定が所定時間内に完了しない場合は、そのメッセージを拾わない（本体の応答速度を優先する）。

---

## データの境界

| テーブル | 役割 | `/clear` |
|---|---|---|
| `chat_history` | Claudeへ渡す会話コンテキスト兼ログ | 削除される |
| `knowledge_seeds` | 後で育てる価値がある思考の記録 | 削除されない |

`/clear` は「会話コンテキストを忘れる」操作であり、Seedを消す操作ではない。

`title` / `summary` / `themes` は匿名化して保存する。原文は `source_text` として
Supabase内にのみ保持する。

---

## 未実装（Phase 2候補）

以下は実装していない。

- Obsidianへの自動書き出し
- GitHub `grow3-knowledge` の検索・照合
- 既存概念との一致・差分・矛盾の提示
- developing / candidate / canonical への自動昇格

GitHubのcanonical昇格は人間判断を必須とする方針を維持する。

---

## 現在の段階

2026-08-11から1〜2週間、Seed採集の実運用を観察する段階にある。

観察して判断する項目は、manual Seedが期待どおり残るか、AIの拾い漏れと拾いすぎ、titleの粒度、summaryの質、themesの揺れ、reason_codeが役に立つか、顧客情報の匿名化が十分か、実際にSeedを読み返したか、Obsidianへ流したいという実需が生じたか。

この観察で実需が確認された場合のみPhase 2へ進む。
