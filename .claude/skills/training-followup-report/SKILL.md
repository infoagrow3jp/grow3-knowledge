---
name: training-followup-report
description: >-
  Generate post-training reports in two layers — a client-facing 実施後レポート
  (5 chapters) and an internal improvement record for Grow3's training OS. Use
  whenever the user asks to create a 実施報告, 研修実施後レポート, follow-up
  report, or to process post-training survey results / instructor notes, or
  mentions summarizing how a delivered training went. Never state behavior
  change as fact — write 行動定着の見立て (outlook) with risks, based only on
  observed evidence. Always produce BOTH layers unless told otherwise.
---

# 研修実施後レポート（2層テンプレート）

## 目的と2層構造

実施した研修を「売り切り」で終わらせず、①クライアントには価値ある報告と
フォロー提案を返し、②Grow3内部には研修OSの改善データを蓄積する。
**必ず2層を別ファイルで生成する。内部記録をクライアント向けに混ぜない。**

- クライアント向け：`clients/<クライアント名>/実施後レポート_<研修名>_<日付>.md`
- 内部向け：該当研修のOSファイル（例：grow3-coaching-training-os.md）への
  追記、または `内部改善記録_<研修名>_<日付>.md`

## 素材の収集（生成前に必ず行う）

1. リポジトリ内を探索：該当研修のOSファイルの実施結果記録、
   ファシリテーターガイド、タイムスケジュール、クライアントの顧客情報.md。
2. 受講後アンケート・講師所感がリポジトリにあるか確認する。
3. **素材が不足していても作業を全面停止しない。** 確認できる素材に基づく
   箇所だけドラフトを作成し、不足箇所は本文中に「（受講者反応は未確認）」等と
   明記したうえで、不足分だけを質問として切り出す。
   **素材にない受講者の反応・発言を創作しない。** 不明箇所は【要確認】。

## 管理情報の扱い（クライアント向け本文に混入させない）

提供区分・料金判断・レビュー状態は、クライアント向けレポートの
**frontmatterのみ**に置く（提出時はfrontmatterを除いた本文だけを納品する）。
本文に料金区分や内部管理の記述を表示しない。

```yaml
---
report_type: simple / detailed / followup   # 簡易／詳細／3か月フォロー
pricing_tier: standard / paid_option / separate_fee
status: draft / reviewed / final
source_date: 2026-07-08
external_review: pending / done / not_required
---
```

## ドラフトの確定禁止

生成したレポート2本は `status: draft` として保存し、**コミットおよび
確定版への変更は行わない**。出荷条件に該当する案件は別コンテキスト
レビュー後に、承認された修正だけを反映して `status: reviewed` に更新する。

## 表現の統制（最重要）

- 「行動が変わる」「定着する」と断定しない。書くのは
  **行動定着の見立て**（観察された根拠つき）と
  **定着を妨げるリスク**（職場要因・時間要因・スキル要因）。
- 見立ての根拠は必ず観察事実に紐づける
  （例：「ワーク中に◯◯の発言が複数出た → △△は定着しやすい」）。
- クライアント向けは、受講者個人を特定・評価する記述をしない
  （「一部の受講者」「複数のグループで」の粒度に留める）。

## クライアント向けレポート（5章構成）

テンプレート：`references/client-report-template.md` を必ずReadして使う。

1. 実施概要と研修目的
2. 受講者の反応・理解が進んだ点（観察事実ベース）
3. 現場定着に向けた期待と懸念（見立て＋リスク）
4. 管理者・会社側に必要な支援（具体的な行動レベル）
5. 1〜3か月後のフォロー提案（内容・時期・ねらい）

## 内部改善記録

テンプレート：`references/internal-record-template.md` を必ずReadして使う。
項目：特に刺さった内容／理解されにくかった内容／時間配分上の課題／
次回削る・残す・補強する箇所／次の商品提案につながる兆候。
記録後、該当研修のOSファイルへの反映要否を提案する（第0原則：
OS本文への反映はユーザー承認後）。

## 提供形態（3段階・frontmatterで管理し本文には書かない）

- **簡易実施報告**：標準料金内。1・2章＋5章の要点のみ、1〜2ページ。
- **詳細分析・フォロー提案**：設計料またはオプション。5章フル版。
- **3か月後フォロー**：別料金。フォロー実施＋定着状況の再報告。

ユーザーがどの段階かを指定しない場合は、どの段階で作るか確認してから
着手する（作業だけが無償で膨らむのを防ぐ）。

## 出荷条件

新規クライアントへの初回提出時は、確定前に別コンテキストレビュー
（claude.ai側または別セッション）を1回通す。生成物はmd保存とし、
出荷前検品（公開禁止事例・【要確認】残存）の対象に載せる。
