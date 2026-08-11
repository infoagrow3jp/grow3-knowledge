# 【無効化済み】Issue案：LINE Producer Botを診断Apps Scriptから分離する

## 2026-08-11 無効化

実査の結果、本番のLINE Producer BotはすでにRender + Claude API + Supabaseで稼働しており、本Issueの前提が誤りだったことが判明した。

診断Apps Scriptに残っていたLINE Botコードは旧実装の残骸であり、移行元ではなかった。

**以下のApps Script分離作業は実施しない。未着手の作業予定として扱わない。**

現在の構成は `README.md` を参照する。

---

## 記録として残す経緯

### 当初の観測（正しい）

2026-08-11の3診断本番移行時、診断Apps Scriptプロジェクト内にLINE Botの `doPost(e)` と
診断バックエンドの `doPost(e)` が共存し、診断POSTがLINE Bot側で処理される競合が発生した。

症状：診断validateが期待するJSONではなく `{"status":"ok"}` が返却された。

### 実施した対処（有効・完了）

- LINE Bot側の関数を `doPost(e)` → `lineBotDoPost(e)` に改名
- 診断用 `doPost(e)` を唯一のdoPostとして再デプロイ
- 3診断は本番スモークPASS済み

### 誤った推論（無効）

上記の残骸コードを「稼働中のLINE Producer Bot本体」と誤認し、別Apps Scriptプロジェクトへ移行する必要があると結論づけた。
実際の稼働先を確認せずに移行方針を立てたことが原因である。

当時の完了条件（新Apps Scriptプロジェクト作成、コード移行、`doPost(e)` 復元、Script Properties移行、Webhook URL変更、疎通確認、旧デプロイのアーカイブ、`Code.gs` の正本化）は、いずれも**実施不要**である。

### 残る作業

診断Apps Script上の残骸コードの削除。
これはLINE Bot側の作業ではなく、診断GASの掃除として別途扱う。
