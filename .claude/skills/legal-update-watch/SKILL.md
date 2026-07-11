---
name: legal-update-watch
description: >-
  Monthly discovery of Japanese labor/social-insurance law changes, subsidies
  (助成金・補助金), and administrative updates relevant to Grow3's SME clients
  (30-100 employees, mainly Okayama). Use whenever the user asks to research,
  watch, or summarize 法改正・助成金・補助金・制度変更, run the monthly legal
  watch, or update references/legal-updates/. This skill DISCOVERS candidates;
  it never confirms them — confirmation is delegated to the legal-fact-checker
  subagent. Discovered-but-unverified items must never be written as facts.
---

# 法改正・助成金ウォッチ（探索スキル）

## 役割分担（最重要）

- **本スキル＝探索**：新しい情報を広く集め、状態を付けて候補リストにする。
- **legal-fact-checker（サブエージェント）＝検証**：候補を一次情報で確定させる。
- 探索段階の情報を「確定した事実」として成果物・規程・研修資料に書かない。
  検証を通過したものだけが `topics/` に昇格する。

## ファイル構成

```
references/legal-updates/
├─ 2026-07.md          … 月次の発見ログ（検証前を含む。状態を必ず明記）
├─ topics/
│  ├─ 育児介護休業法.md … テーマ別の確定情報（検証済みのみ）
│  ├─ 同一労働同一賃金.md
│  └─ 助成金・補助金.md
└─ sources.md          … 定点観測先リスト
```

月をまたぐ改正は月次ファイルではなく `topics/` 側で追う。月次ファイルは
「その月に何を発見・検証したか」のログに徹する。

## 状態区分（全項目に必須）

`検討・審議中` ／ `公布・決定済み` ／ `施行待ち` ／ `施行済み` ／
`実務運用・様式更新` ／ `自治体独自制度`

## 項目フォーマット（月次・topics共通）

```
### 項目名
- 状態：
- 基準日：（この情報がいつ時点のものか）
- 公布日・施行日：
- 対象事業者：（規模要件・業種要件）
- 実務への影響：
- 今すぐ必要な対応：（なし／様式差し替え／規程改定／クライアント通知 等）
- 根拠（一次情報URL）：
- 最終確認日：
- 検証：未検証／検証済み（legal-fact-checker YYYY-MM-DD）
```

## 実行手順（月次ウォッチ）

1. `sources.md` の観測先を巡回し、前回の最終確認日以降の更新を探索する。
2. 発見した候補を上記フォーマットで月次ファイルに「検証：未検証」として記録。
3. クライアント業務に影響しうる候補（施行待ち・施行済み・助成金の公募開始）を
   優先度順に選び、**legal-fact-checkerに検証を依頼**する。
4. 検証済みの項目のみ `topics/` の該当ファイルに転記し、月次側の検証欄を更新。
5. 最後にサマリを返す：新規発見◯件／検証済み◯件／クライアント対応が必要な項目。

## 探索の観点

- 対象は中小企業（30〜100名）の実務に影響するもの。大企業限定の制度は
  「参考」扱いに留める。
- 助成金・補助金は、公募期間・予算枠の消化状況・岡山県/岡山労働局の
  独自制度を必ず確認する。
- 「行政資料の様式だけ更新された」ケースは状態＝実務運用・様式更新として
  区別する（法改正と混ぜない）。

## sources.md の初期観測先（初回実行時に生成する）

厚生労働省 報道発表・審議会資料／e-Gov（法令・パブコメ）／日本年金機構／
協会けんぽ（岡山支部の料率）／岡山労働局／ミラサポplus・中小企業庁（補助金）／
岡山県・市町村の産業支援制度。巡回して有用だった先はsources.mdに追記していく。
