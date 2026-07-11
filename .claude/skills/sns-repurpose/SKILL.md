---
name: sns-repurpose
description: >-
  Repurpose Grow3 blog content (the 110-article master MD) into Threads posts
  and note articles, including workshop-promotion posts. Use whenever the user
  asks to create SNS posts, Threads content, note articles, ワークショップ集客
  investments, or to repurpose blog articles for social media. This is NOT
  summarization or shortening — each medium gets a redesigned piece. Never
  attach a workshop CTA to every post; follow the 3-tier CTA rule inside.
---

# SNS再設計スキル（Threads／note）

## 大原則：短縮ではなく媒体別の再設計

ブログの要約・転載を作らない。同じ素材から、媒体の読まれ方に合わせて
**別の設計**で書き起こす。文体の正本は `grow3-blog-writing-context.md`
（表現ルールの要点は grow3-judgment の `references/writing-marketing.md`）。

## 素材と参照の探索（質問より先にやる）

1. ブログ110話統合MDをリポジトリ内で探して読む（該当話数の本文を素材にする）。
2. ワークショップ告知を作る場合、**先にリポジトリとCLAUDE.mdヒエラルキー内の
   正本（開催概要・日時・対象者・申込導線）を探す。** ユーザーへの質問は、
   ①正本が見つからない、②複数版があり最新が判定できない、
   ③開催日や申込導線が未確定、のいずれかの場合のみ行う。

## CTAの3段階（配分ルール）

すべての投稿をワークショップ告知に接続しない。発信全体が広告化するため。

- **通常発信**：CTAなし、またはブログ本編への誘導のみ。
- **テーマ接続**：本文の問題意識からワークショップのテーマへ軽く接続
  （日時・申込は書かない）。
- **直接告知**：日時・対象者・申込導線を明示。
- 配分の目安：通常6：接続3：告知1。直接告知は全体の1〜2割を超えない
  （案件都合で変える場合は配分を明示して提案する）。

## Threadsの設計

- **1投稿1論点**。1記事から3投稿作る場合、要約の3分割ではなく、
  反応が生まれやすい断面を3つ切り出す。
- 冒頭3行で「場面」か「違和感」を出す（理論・定義から始めない）。
- 補足（背景・構造・データ）は本文に詰めず、ぶら下がり投稿に回す。
- 1投稿500字以内。会話として自然な文体（です・ます崩しは可、AI語は避ける）。

## noteの設計

- ブログの転載・増補版にしない。**複数話を束ねて1テーマを再構成**する。
- 基本の流れ：経営者の場面 → 構造の見立て → 読者が考える問い。
- CTAは、記事の内容とワークショップの接続が自然な場合だけ入れる
  （接続が不自然なら通常発信として出す）。

## 出力とレビュー

- 生成物は必ずmdファイルとして保存する（`marketing/sns/` 配下を推奨）。
  ファイル化することで出荷前検品（公開禁止事例・AI語警告・読点チェック）が
  自動で掛かる。
- 採点を求められた場合は以下の媒体別5軸（各20点）を宣言して用いる。
  blog-reviewerの軸をそのまま流用しない。

**Threads採点軸**：①冒頭の停止力 ②1投稿1メッセージ ③会話としての自然さ
④小林さんの実感・手触り ⑤CTAの距離感

**note採点軸**：①再構成の必然性（束ねた意味があるか）②読み進める流れ
③具体場面と構造の接続 ④独自の示唆 ⑤CTAとの整合性

## 禁止・注意

- 公開禁止事例（grow3-judgmentの `references/brand-constraints.md`）を
  SNSにも適用する。SNSは公開物であり、例外はない。
- 実在クライアント名・個別事例は、公開許諾が確認できる記載がない限り
  匿名化する（業種・規模程度に留める）。
