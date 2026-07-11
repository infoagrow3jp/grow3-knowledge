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

1. ブログ110話統合MDを読む（該当話数の本文を素材にする）。
   正本パス：`marketing/blog/grow3-blog-110-full.md`
   （Dropbox側の原本がある場合は更新日を比較し、新しい方を正とする）
2. ワークショップ告知を作る場合、**先に `workshop_source` を読む。**
   現行の正本は `marketing/workshop/workshop-master.md`。
   リポジトリとCLAUDE.mdヒエラルキー内の開催概要・日時・対象者・申込導線も確認する。
   ユーザーへの質問は、①正本が見つからない、②複数版があり最新が判定できない、
   ③開催日や申込導線が未確定、のいずれかの場合のみ行う。

## CTAの3段階（配分ルール）

すべての投稿をワークショップ告知に接続しない。発信全体が広告化するため。

- **通常発信**（`cta_level: none`）：CTAなし、またはブログ本編への誘導のみ。
- **テーマ接続**（`cta_level: theme`）：本文の問題意識からワークショップのテーマへ軽く接続
  （日時・申込は書かない）。
- **直接告知**（`cta_level: direct`）：日時・対象者・申込導線を明示。
- 配分の目安：通常6：接続3：告知1。直接告知は全体の1〜2割を超えない
  （案件都合で変える場合は配分を明示して提案する）。

## Threadsの設計

### 出力構造（固定）

1本のThreadsは次の構造で出す。

1. **親投稿**：3行以内のフック。完結させない。続きを読む理由を残す。
2. **ぶら下げ投稿**：2〜3本。本文の分割（要約の再分割ではなく、親で開いた論点の続き）。

- **1スレッド1論点**。1記事から複数スレッドを作る場合は、反応が生まれやすい断面を切り出す。
- 冒頭（親）は「場面」か「違和感」から入る（理論・定義から始めない）。
- 1投稿（親／ぶら下げ各々）500字以内。会話として自然な文体（です・ます崩しは可、AI語は避ける）。

### 画像方針

画像はあれば強い、なければフックで勝負。実態と乖離した素材写真は使わない。

候補は次の3種のみ。

| image_variant | 内容 |
|---|---|
| A | 本人が写る実写真 |
| B | フック一文の引用カード（Grow3 Blue `#0F3D96`） |
| C | テキストのみ（画像なし） |

`image_idea` には**既存写真の指定のみ**を書く。新規制作の指示は書かない。

## noteの設計

- ブログの転載・増補版にしない。**複数話を束ねて1テーマを再構成**する。
- 基本の流れ：経営者の場面 → 構造の見立て → 読者が考える問い。
- CTAは、記事の内容とワークショップの接続が自然な場合だけ入れる
  （接続が不自然なら通常発信として出す）。

## 出力ファイルと frontmatter

生成物は必ずmdファイルとして保存する（`marketing/sns/` 配下を推奨）。
ファイル化することで出荷前検品が自動で掛かる。

### frontmatterスキーマ（必須）

```yaml
---
title: # 人間が識別できる短い題名
status: draft | reviewed | final
channel: threads | note
cta_level: none | theme | direct
series: # 例: ws20260903-wave1
source_articles: # 配列。title / url / id
blog_master: marketing/blog/grow3-blog-110-full.md
workshop_source: marketing/workshop/workshop-master.md  # WS接続時
image_variant: A | B | C   # Threadsのみ。noteは省略可
image_idea: # 既存写真の指定のみ。新規制作指示は書かない
created: YYYY-MM-DD
---
```

Threads本文は次の見出しで区切る。

```markdown
## 親投稿
...
## ぶら下げ1
...
## ぶら下げ2
...
## ぶら下げ3   # 任意
```

## 採点（求められた場合のみ）

**Threads採点軸**：①冒頭の停止力 ②1投稿1メッセージ ③会話としての自然さ
④小林さんの実感・手触り ⑤CTAの距離感

**note採点軸**：①再構成の必然性（束ねた意味があるか）②読み進める流れ
③具体場面と構造の接続 ④独自の示唆 ⑤CTAとの整合性

## 禁止・注意

- 公開禁止事例（grow3-judgmentの `references/brand-constraints.md`）を
  SNSにも適用する。SNSは公開物であり、例外はない。
- 実在クライアント名・個別事例は、公開許諾が確認できる記載がない限り
  匿名化する（業種・規模程度に留める）。
- 実験ログは `marketing/sns/experiment-log.md`。各条件3〜4本たまるまで結論を出さない。
