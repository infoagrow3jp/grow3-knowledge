# Issue案：LINE Producer Botを診断Apps Scriptから分離する

## 背景

2026-08-11の3診断本番移行時、同一Apps Scriptプロジェクト内にLINE Producer Botの `doPost(e)` と診断バックエンドの `doPost(e)` が共存し、診断POSTがLINE Bot側で処理される競合が発生した。

症状：診断validateが期待するJSONではなく `{"status":"ok"}` が返却された。

## 暫定対応

- LINE Bot側HEADを `doPost(e)` → `lineBotDoPost(e)` に変更
- 診断用 `doPost(e)` を唯一のdoPostとして再デプロイ
- 3診断は本番スモークPASS済み
- 既存 `LINEv1` は固定済み旧バージョンで稼働継続

## 完了条件

- [ ] LINE Producer Bot専用Apps Scriptプロジェクトを作成
- [ ] LINE Botコードを移行
- [ ] 新プロジェクトで `doPost(e)` を復元
- [ ] Script Propertiesを移行
- [ ] LINE Webhook URLを新Web Appへ変更
- [ ] `/help`, `/context`, `/clear`, 通常会話の疎通確認
- [ ] 旧 `LINEv1` をアーカイブ
- [ ] 診断GASからLINE Botコードを削除
- [ ] 疎通確認済みCode.gsをリポジトリへ正本化
