# Grow3 Producer Bot — Apps Script分離メモ

## 状態

2026-08-11時点で、LINE Producer Botと3診断バックエンドが同じApps Scriptプロジェクトに同居していた。

両方が `doPost(e)` を持ったため、本番診断のPOSTがLINE Bot側で処理される競合が発生した。

## 暫定状態

本番Apps Script HEADでは、LINE Bot側の入口を

```js
function lineBotDoPost(e)
```

へ一時的に改名している。

診断バックエンドの `doPost(e)` を唯一の `doPost` としている。

既存の `LINEv1` は固定済み旧バージョンのデプロイで動作を継続するため、
現時点のLINE利用には影響しない。

ただし、現在のHEADをそのままLINE Botとして新バージョン再デプロイするとWebhook入口がなくなる。

## 恒久対応

LINE Producer Botを独立したApps Scriptプロジェクトへ移す。

### 移行手順

1. LINE Producer Bot専用の新Apps Scriptプロジェクトを作成
2. 現行LINE Botコードを新プロジェクトへコピー
3. 新プロジェクトでは入口を `doPost(e)` に戻す
4. Script Propertiesを移行
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `CLAUDE_API_KEY`
   - `SPREADSHEET_ID`
   - `CONTEXT_*`
   - 必要な `HISTORY_*`（履歴を引き継ぐ場合のみ）
5. Web Appとしてデプロイ
6. LINE Developers側Webhook URLを新Web App URLへ変更
7. Webhook検証
8. `/help`, `/context`, `/clear`, 通常会話を確認
9. 問題なければ旧 `LINEv1` をアーカイブ
10. 診断Apps ScriptプロジェクトからLINE Botコードを削除

## 原則

- 診断GASプロジェクトの `doPost` は診断専用
- LINE Botの `doPost` はLINE専用プロジェクトに置く
- 1つのApps Script Web Appで異なるWebhook/API用途を同居させない

## 正本コードについて

現行LINE BotコードはApps Script側にあり、2026-08-11時点では本リポジトリへ完全同期されていない。

分離作業時に、**新LINE Botプロジェクトで実際に疎通確認したコード**を
`integrations/line-producer-bot/Code.gs` として正本化する。

未検証の転記コードを先に正本にしない。
