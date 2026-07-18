---
status: draft
文書全体: draft
思想層: frozen
パラメータ層: implementation-time decision
version: 0.1
基準日: 2026-07-13
思想層凍結日: 2026-07-18
作成者: validator責務棚卸し（AI支援）
確定者: 小林裕司
改訂履歴: v0.1 draft（9 schema責務集約・責務マトリクス・6段階実装ルート案）→ v0.1思想層凍結（思想層frozen・文書全体はdraft・パラメータ層は実装段階確定・v0.1実装境界100責務／NJ対象外・独立Python実行基盤・三層結果モデル・DEC-015）
参照: docs/organization-diagnosis_設計メモ_v0.1.md（frozen）、docs/organization-diagnosis_schema設計メモ_v0.1.md（frozen）、DECISIONS.md DEC-008〜012・DEC-015、schemas/organization-diagnosis/*.schema.json（9本）
---

# organization-diagnosis validator設計メモ v0.1

本書は、organization-diagnosis v0.1の**validator責務棚卸し**と、将来のvalidator実装の設計基準である。

| 層 | ステータス | 意味 |
|---|---|---|
| 文書全体 | draft | 実装時パラメータが確定するまで文書全体はdraft。パラメータ確定後に文書全体をfrozenへ移行する |
| 思想層 | frozen | 責務境界・実装対象・実行基盤方針・結果モデル分離は変更しない |
| パラメータ層 | implementation-time decision | CLI・JSON schema・enum・error code等は実装段階で確定する |

- 凍結済み設計メモ・schema設計メモ・DECISION・9 schemaを正本とする。
- **確定済み100責務と実装思想は凍結されている。**
- **NJ-01〜NJ-09はv0.1実装対象外である。**
- **実装時パラメータが確定するまで、文書全体はdraftである。**
- **パラメータ確定後に文書全体をfrozenへ移行する。**
- **文書全体がdraftであることは、思想層を実装から変更してよいことを意味しない。**
- **思想層はfrozenである。パラメータ層のimplementation-time decisionを仮決めして検品上の警告を消してはならない。**
- **NJをコード側で先取りして確定してはならない。**
- **思想層凍結後も、同一作業内でvalidator実装へ自動着手してはならない（別途承認）。**

---

## 1. 目的

organization-diagnosis v0.1において、9 schemaが検査しない横断規則を**一箇所に集約**し、validator実装の範囲・段階・停止論点を明確にする。

validatorの目的は、財務分析における検算に相当する**出典照合と形式的追跡可能性**の機械検査であり、Evidenceの真実性やHypothesisの正しさの保証ではない（設計メモ§18、DEC-008/009）。

---

## 2. 適用範囲

| 対象 | 含む | 含まない |
|---|---|---|
| データ | `_org_diagnosis/`配下のregister JSON、MTG input snapshot、Manifest、brief Markdown frontmatter | brief本文の意味検査（v0.1 schema外） |
| 検査 | schema gate後の決定論的規則、filesystem/hash、参照整合、出力境界 | LLMルーブリック、裕司さんの価値判断 |
| 環境 | Publicリポジトリの架空fixture、将来の顧客Dropbox実データ | 実顧客情報のPublic保存 |

---

## 3. 正本・責務境界

| 層 | 正本 | 役割 |
|---|---|---|
| register JSON | 診断内容の正本 | schema + validator |
| MTG input snapshot | 入力不変記録 | schema + validator |
| brief frontmatter | brief生成情報の正本 | extractor/parser + schema + validator |
| brief Markdown本文 | registerからの生成物 | generator + validator（出力境界）+ 人間 |
| Manifest | 非正本の再構築可能索引 | schema + validator（cache照合のみ） |

**mutation方針（合成判断）：** DEC-011に基づき、validatorは検出・報告のみ行い、register・Manifest・snapshot・brief・frontmatterを**自動修正しない**（DEC-011 L234、schema設計メモ§18-2の運用含意）。

---

## 4. 9 schemaから回収したvalidator責務

### 4-1. 抽出方法

次から責務を抽出した。

- 9 schemaの`description`および`$defs`内のvalidator言及
- schema設計メモ§7-4、§11〜§19、§18-2
- 設計メモ§18〜§19、§21（Case 1〜12）、§22
- DEC-008〜012の責務境界記述

### 4-2. 集計（3層）

| 区分 | 件数 |
|---|---|
| **確定済みvalidator責務** | **100** |
| 　既存凍結仕様 | 72 |
| 　合成判断 | 28 |
| **新規判断候補** | **9** |
| **棚卸し総項目** | **109** |

**定義：**

- **確定済みvalidator責務：** 凍結仕様または既存仕様から一意に導ける、validatorが将来実装対象とする規則
- **新規判断候補：** 人間の決定またはDECISIONがなければ、validator責務として確定できない停止論点
- **棚卸し総項目：** 確定済みvalidator責務と新規判断候補の合計

新規判断候補9件は§34に別表。責務マトリクス（§5-1）には含めない。NJ-01〜NJ-09を責務マトリクスへ二重計上しない。

**整合条件：** 72+28=100／NJ=9／棚卸し=109／責務マトリクス行数=100／NJ表行数=9

### 4-2-1. v0.1実装境界（DEC-015）

| 区分 | 件数・扱い |
|---|---|
| 確定済みvalidator責務 | **100件** |
| 新規判断候補 | **NJ-01〜NJ-09の9件**（§34に将来判断の記録として残す。削除しない） |
| 棚卸し総項目 | **109件** |
| **v0.1実装対象** | **確定済み100責務** |
| **v0.1実装対象外** | **NJ-01〜NJ-09** |

- NJは新規判断候補であり、本思想層凍結では採用・実装しない。
- NJに関連する事項は、現在の凍結仕様を優先する。
- 特にhash不一致は、凍結仕様どおり **hash不一致を警告する** をv0.1の正とする（§20、NJ-08詳細）。
- NJ-08に記載の後続利用阻害・自動整合回復・新snapshot作成等は、v0.1では実装しない。
- NJをvalidatorコードで先取りして確定してはならない。

### 4-3. 6カテゴリ別件数（確定済み責務100件）

| カテゴリ | 件数 |
|---|---|
| Cat1 基盤・読み込み・schema gate | 13 |
| Cat2 ファイル構成・Manifest・case境界 | 13 |
| Cat3 ID・参照整合・入力来歴 | 23 |
| Cat4 Evidence・Pattern・Hypothesis規則 | 32 |
| Cat5 Causal・Verification Action・履歴 | 12 |
| Cat6 Brief・出力境界・安全性 | 7 |
| **合計** | **100** |
---

## 5. 責務マトリクス

`rule_id`は棚卸し用仮番号。**正式error codeではない。**

確定済み責務100件を記載。NJ9件は§34別表。Cat1–6の省略なし。

### 5-0. 列定義

| 列 | 意味 |
|---|---|
| 取り得るevaluation outcome候補 | 層A：規則評価の1回あたりの内部結果候補（`／`区切り。finding emissionとは別） |
| 適合条件／違反条件／検査不能条件／非該当条件／未実施条件 | 各resultが成立する前提（規則の固定属性。実行結果そのものではない） |
| 違反時severity候補／違反時severity根拠 | 違反が成立した場合の影響度候補（正式enumではない） |
| 検査不能時の影響候補／検査不能時の影響根拠 | 検査不能時の後続利用への影響候補（severityとは別軸） |
| 実装可能性_主分類 | A〜Gの主分類（1責務1つ。Gは凍結仕様のv0.1将来送りのみ） |
| 実装可能性_副分類 | 複合性質（例：B+F）。集計に含めない |
| 未確定事項 | 人間判断待ちの論点。`NJ-xx参照`または`—` |

**候補値（正式enum前）：** 阻害候補／注意候補／情報候補／適用なし／未確定

**原則（層A）：**

- evaluation outcomeは検査実行ごとに1つが成立する（候補列は起こり得る集合）
- 検査不能はseverityではない。検査不能だからseverity適用なし、とは限らない
- 非該当・未実施に原則severityを付けない
- severity／影響候補は層B（finding）向けラベル（§5-4）

### 5-0-1. 三層の結果モデル（混同禁止）

次の3つは**別概念**である。相互に名称や値を流用しない。

```text
validator全体の三値
≠
個々のrule evaluation outcome
≠
finding emission
```

| 層 | 概念 | 候補（正式名称・enumではない） | 役割 |
|---|---|---|---|
| 0 | validator全体の実行結果 | PASS／FAIL／UNVERIFIABLE | 呼び出し側が解釈する集約結果 |
| A | rule evaluation outcome | 適合／違反／検査不能／非該当／未実施 | 個々の規則評価の内部結果（本マトリクス列） |
| B | finding emission | violation／unable-to-check／warning・notice／findingなし 等 | 利用者向けまたはmachine-readableへ出す診断項目 |

本マトリクスの`取り得るevaluation outcome候補`列は**層Aのみ**を表す。validator全体のPASS／FAIL／UNVERIFIABLEを、個々のrule outcomeへ流用しない（§17）。

**原則：**

- 規則が適合したことと、適合findingを出力することは別
- ruleが適合してもfindingを出さない場合がある
- 違反や検査不能をfindingとして出す場合がある
- 検査不能は違反ではない（findingとして報告し得る。出力契約の詳細はNJ-09／実装段階）
- severityはfinding側の属性候補であり、rule evaluation outcomeそのものではない
- 正式なfinding schema・enum・error codeは実装段階で確定する（パラメータ層）

**evaluation outcomeの型（§5-1）：**

| 型 | 典型のevaluation outcome候補 |
|---|---|
| 通常の検査規則（実装済み想定） | 適合／違反／検査不能 |
| 条件付き・schema委譲 | 非該当 |
| 将来送り（G） | 未実施 |
| 収集・表示のみ（例：V-C1-008） | 適合／検査不能 |

### 5-1. 確定済み責務100件

| rule_id | カテゴリ | 規則 | 根拠ファイル | 根拠節・行 | 参照元 | 参照先 | schema検査済み | validator必要 | 検査前提 | 前提不成立例 | 違反確定条件 | 検査不能条件 | 非該当条件 | 検査不能時継続 | PASS禁止 | Det | FS | Hist | Body | Hum | 実装可能性_主分類 | 実装可能性_副分類 | 取り得るevaluation outcome候補 | 適合条件 | 違反条件 | 検査不能条件 | 非該当条件 | 未実施条件 | 違反時severity候補 | 違反時severity根拠 | 検査不能時の影響候補 | 検査不能時の影響根拠 | Phase | 未確定事項 | fixture | 実データ |
| V-C1-001 | Cat1 | register JSONをparseしDraft2020-12+formatでschema gate | organization-diagnosis_schema設計メモ_v0.1.md | §18-1 | 対象ファイル/register | schema gate結果 | 部分 | はい | ファイル読取可 | parse不能 | schema invalid | 文字コード不明 | 対象外ファイル | 当該ファイルの参照規則のみ停止 | はい | はい | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | schema invalid | 文字コード不明 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 1 | — | Stage1 | 可 |
| V-C1-002 | Cat1 | frontmatter抽出（`---`開始/終了、BOM・先頭空行拒否） | DECISIONS.md | DEC-012 frontmatter契約 | 対象ファイル/register | schema gate結果 | いいえ | はい | Markdown brief | frontmatter欠落 | 区切り不正 | ファイル未読 | 非brief | 当該briefのschema gate未実施 | はい | はい | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 区切り不正 | ファイル未読 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 1 | — | Stage1 | 可 |
| V-C1-003 | Cat1 | YAML safe parse、duplicate key拒否、mapping root | DECISIONS.md | DEC-012 | 対象ファイル/register | schema gate結果 | いいえ | はい | 抽出済みYAML | malformed/duplicate | parse失敗 | — | JSON register | 当該briefのみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | parse失敗 | 検査前提不成立 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 1 | — | Stage1 | 可 |
| V-C1-004 | Cat1 | YAML値のJSON互換正規化（datetime→ISO文字列） | DECISIONS.md | DEC-012 | 対象ファイル/register | schema gate結果 | いいえ | はい | parse成功 | 非JSON型残存 | 変換不能型 | — | — | 当該briefのみ | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 変換不能型 | 検査前提不成立 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 1 | — | Stage1 | 可 |
| V-C1-005 | Cat1 | 対象schema選択（register種別/Manifest/snapshot/brief） | organization-diagnosis_schema設計メモ_v0.1.md | §5 | 対象ファイル/register | schema gate結果 | はい | はい | ファイル種別判明 | 未知種別 | schema未定 | — | — | 当該ファイルのみ | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | schema未定 | 検査前提不成立 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 1 | — | Stage1 | 可 |
| V-C1-007 | Cat1 | $ref解決（common含む9 schema） | DECISIONS.md | DEC-010 | 対象ファイル/register | schema gate結果 | はい | はい | schemaファイル存在 | $id不一致 | 解決失敗 | — | — | schema gate全体停止 | はい | はい | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 解決失敗 | 検査前提不成立 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 1 | — | Stage1 | 可 |
| V-C1-008 | Cat1 | schema gate結果の収集表示（再実装ではなくvalidator収集） | organization-diagnosis_validator設計メモ_v0.1.md | 合成 | 対象ファイル/register | schema gate結果 | はい | はい | validator実装 | — | — | — | — | — | はい | はい | いいえ | いいえ | いいえ | いいえ | A | — | 適合／検査不能 | validator実装済み | — | validator未実装等 | — | — | — | — | — | — | 1 | — | Stage1 | 可 |
| V-C1-009 | Cat1 | registerEnvelope・case_id等の非該当ファイル拒否 | organization-diagnosis_validator設計メモ_v0.1.md | 各schema | 対象ファイル/register | schema gate結果 | はい | はい | 種別確定 | — | 混入フィールド | — | — | — | はい | はい | いいえ | いいえ | いいえ | いいえ | A | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 混入フィールド | 検査前提不成立 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 1 | — | Stage1 | 可 |
| V-C1-010 | Cat1 | extensions内への必須項目逃がし検出 | organization-diagnosis_validator設計メモ_v0.1.md | 各schema | 対象ファイル/register | schema gate結果 | はい | はい | schema適用後 | — | required欠落 | — | — | — | はい | はい | いいえ | いいえ | いいえ | いいえ | A | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | required欠落 | 検査前提不成立 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 1 | — | Stage1 | 可 |
| V-C1-011 | Cat1 | nullable/conditionalのschema結果をvalidatorが上書きしない | organization-diagnosis_schema設計メモ_v0.1.md | §18-1 | 対象ファイル/register | schema gate結果 | はい | いいえ | schema valid | — | — | — | — | — | はい | はい | いいえ | いいえ | いいえ | いいえ | A | — | 非該当 | — | — | — | — | — | — | — | — | — | 1 | — | Stage1 | 可 |
| V-C1-012 | Cat1 | evidence_type別conditional requiredのschema委譲 | schemas/organization-diagnosis/evidence.schema | — | 対象ファイル/register | schema gate結果 | はい | 部分 | schema valid | — | 追加semantic | — | — | — | はい | はい | いいえ | いいえ | いいえ | いいえ | A | — | 非該当 | — | — | — | — | — | — | — | — | — | 1 | — | Stage1 | 可 |
| V-C1-013 | Cat1 | status別Hypothesis件数条件のschema委譲 | schemas/organization-diagnosis/hypothesis.schema | — | 対象ファイル/register | schema gate結果 | はい | 部分 | schema valid | — | primary選定等 | — | — | — | はい | はい | いいえ | いいえ | いいえ | いいえ | A | — | 非該当 | — | — | — | — | — | — | — | — | — | 1 | — | Stage1 | 可 |
| V-C1-014 | Cat1 | brief本文をschemaへ渡さない | DECISIONS.md | DEC-012 | 対象ファイル/register | schema gate結果 | いいえ | はい | brief検査 | — | — | — | register | — | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 非該当 | — | — | — | register | — | — | — | — | — | 1 | — | Stage1 | 可 |
| V-C2-001 | Cat2 | 固定5 register path実在 | DECISIONS.md | DEC-011 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | case root確定 | root不明（NJ-02） | ファイル不存在 | root不明 | — | 参照規則依存停止 | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | ファイル不存在 | root不明 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 2 | NJ-02参照 | Stage1 | 可 |
| V-C2-002 | Cat2 | Manifest schema valid | DECISIONS.md | DEC-011 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | Manifest存在 | 不存在 | invalid | parse不能 | manifest省略運用 | Cat2以降Manifest依存停止 | はい | はい | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | invalid | parse不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 2 | — | Stage1 | 可 |
| V-C2-003 | Cat2 | Manifest registers 5キーrequired・固定relative_path | DECISIONS.md | DEC-011 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | Manifest valid | — | path不一致 | — | — | — | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | path不一致 | 検査前提不成立 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 2 | — | Stage1 | 可 |
| V-C2-004 | Cat2 | mtg_sessions IDがsnapshot実在と整合 | DECISIONS.md | DEC-011 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | Manifest+snapshot | snapshot未読 | ID不在 | Manifest invalid | — | 当該MTG依存停止 | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | ID不在 | Manifest invalid | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 2 | — | Stage1 | 可 |
| V-C2-005 | Cat2 | briefs[].relative_path実在 | DECISIONS.md | DEC-011 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | Manifest valid | — | brief不存在 | — | briefs空 | — | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | brief不存在 | 検査前提不成立 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 2 | — | Stage1 | 可 |
| V-C2-006 | Cat2 | Manifest briefs[].generated_at == frontmatter generated_at | DECISIONS.md | DEC-011/012 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | 両方読取可 | frontmatter未抽出 | 不一致 | brief未読 | — | 当該briefのみ | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 両方読取かつ一致 | 不一致 | brief未読等 | — | — | 注意候補 | cache/hash/時点不一致・再取得で解消可 | 注意候補 | 読取不能時は当該brief規則未検査 | 2 | — | Stage1 | 可 |
| V-C2-007 | Cat2 | register last_updated_at cache vs body | DECISIONS.md | DEC-011 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | 両方読取 | register invalid | 不一致 | — | — | — | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 両方読取かつ一致 | 不一致 | register invalid等 | — | — | 注意候補 | cache/hash/時点不一致・再取得で解消可 | 注意候補 | 読取不能時は当該register規則未検査 | 2 | — | Stage1 | 可 |
| V-C2-008 | Cat2 | 未索引ファイル検出（bodyあり・Manifestなし） | DECISIONS.md | DEC-011 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | いいえ | はい | ディレクトリ走査可 | 走査方針未定（NJ-03） | 未登録 | 走査不能 | — | — | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | Manifest索引に存在 | 未登録 | 走査不能 | — | — | 注意候補 | 非正本索引・走査方針未定時は修復推奨 | 注意候補 | 走査不能時は当該規則のみ未検査 | 2 | NJ-03参照 | Stage2 | Stage2 |
| V-C2-009 | Cat2 | 索引先不存在→ERROR候補 | DECISIONS.md | DEC-011 L242 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | いいえ | はい | Manifest valid | — | 不存在 | — | — | — | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 不存在 | 検査前提不成立 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 2 | — | Stage1 | 可 |
| V-C2-010 | Cat2 | case_id整合（Manifest vs register envelope） | DECISIONS.md | DEC-011 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | 全register読取 | — | 不一致 | register未読 | — | 当該register依存停止 | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 不一致 | register未読 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 2 | — | Stage1 | 可 |
| V-C2-011 | Cat2 | snapshotファイル名 `inputs/{mtg_session_id}.json` | organization-diagnosis_schema設計メモ_v0.1.md | §7-4 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | MTG ID確定 | — | 不一致 | — | — | — | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 不一致 | 検査前提不成立 | — | — | 注意候補 | cache/hash/時点不一致・再取得で解消可 | — | — | 2 | — | Stage1 | 可 |
| V-C2-012 | Cat2 | relative_pathが_org_diagnosis/外へ出ない | schemas/organization-diagnosis/mtg_input_snapshot | — | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | path+root確定 | root不明（NJ-02） | traversal | root不明 | — | 当該path依存停止 | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | traversal | root不明 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 2 | NJ-02参照 | Stage1 | 可 |
| V-C2-018 | Cat2 | created_atはManifest固有・再構築時保持 | DECISIONS.md | DEC-011 | _org_diagnosis/・Manifest | 実ファイル・Manifest索引 | はい | はい | Manifest存在 | — | 喪失時のみ新規 | — | — | — | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反 | DEC-011どおり保持 | 喪失時のみ新規 | — | — | — | 注意候補 | 非正本cache・再構築時メタ保持（DEC-011） | — | — | 2 | — | Stage1 | 可 |
| V-C3-001 | Cat3 | register横断ID重複禁止 | organization-diagnosis_schema設計メモ_v0.1.md | §5-2 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 全register schema valid | register未読 | 同一ID重複 | index未構築 | 単一registerのみ | 当該ID依存規則停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 同一ID重複 | index未構築 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-002 | Cat3 | ID再発行・再利用禁止 | schemas/organization-diagnosis/common.schema | — | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | ID再発行・再利用禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | ID再発行・再利用禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-003 | Cat3 | Evidence.mtg_session_id→snapshot存在 | organization-diagnosis_設計メモ_v0.1.md | §19 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | Evidence.mtg_session_id→snapshot存在 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Evidence.mtg_session_id→snapshot存在 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-004 | Cat3 | Evidence.source_file→snapshot input_files | organization-diagnosis_設計メモ_v0.1.md | §19 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | Evidence.source_file→snapshot input_files | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Evidence.source_file→snapshot input_files | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-005 | Cat3 | input file content_sha256 vs 実ファイル | organization-diagnosis_設計メモ_v0.1.md | §7-4-1 | register横断・snapshot | 参照先ID/ファイル | 部分 | はい | 前提データ読取可 | 依存未読 | hash不一致 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | hash一致 | hash不一致 | ファイル読取不能等 | 規則対象外 | — | 注意候補 | 凍結仕様§7-4-1・hash不一致は警告 | 阻害候補 | 正本入力ファイル読取不能時は来歴検証不可 | 3 | NJ-08参照 | Stage2 | Stage2 |
| V-C3-006 | Cat3 | input file size_bytes vs 実ファイル | schemas/organization-diagnosis/mtg_input_snapshot | — | register横断・snapshot | 参照先ID/ファイル | 部分 | はい | 前提データ読取可 | 依存未読 | size不一致 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | size一致 | size不一致 | ファイル読取不能等 | 規則対象外 | — | 注意候補 | 凍結仕様§7-4-1・size不一致は警告 | 阻害候補 | 正本入力ファイル読取不能時は来歴検証不可 | 3 | NJ-08参照 | Stage2 | Stage2 |
| V-C3-007 | Cat3 | derived_summary source_evidence_ids存在 | organization-diagnosis_設計メモ_v0.1.md | §18-2 | register横断・snapshot | 参照先ID/ファイル | はい | はい | 前提データ読取可 | 依存未読 | derived_summary source_evidence_ids存在 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | derived_summary source_evidence_ids存在 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-008 | Cat3 | Pattern→Evidence存在・case scope | organization-diagnosis_設計メモ_v0.1.md | §19 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | Pattern→Evidence存在・case scope | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Pattern→Evidence存在・case scope | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-009 | Cat3 | Pattern distinct occurrence_key≥2 | organization-diagnosis_設計メモ_v0.1.md | §19-6 | register横断・snapshot | 参照先ID/ファイル | 部分 | はい | 前提データ読取可 | 依存未読 | Pattern distinct occurrence_key≥2 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Pattern distinct occurrence_key≥2 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-010 | Cat3 | occurrence_count==distinct keys | schemas/organization-diagnosis/pattern.schema | — | register横断・snapshot | 参照先ID/ファイル | 部分 | はい | 前提データ読取可 | 依存未読 | occurrence_count==distinct keys | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | occurrence_count==distinct keys | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-011 | Cat3 | Hypothesis→Evidence/Pattern存在 | organization-diagnosis_設計メモ_v0.1.md | §19 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | Hypothesis→Evidence/Pattern存在 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Hypothesis→Evidence/Pattern存在 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-012 | Cat3 | primary ⊆ supporting | organization-diagnosis_設計メモ_v0.1.md | §19 L853 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | primary ⊆ supporting | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | primary ⊆ supporting | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-013 | Cat3 | supersedes↔superseded_by双方向 | organization-diagnosis_設計メモ_v0.1.md | §22 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | supersedes↔superseded_by双方向 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | supersedes↔superseded_by双方向 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-014 | Cat3 | Causal→Evidence/Hypothesis/edge存在 | organization-diagnosis_設計メモ_v0.1.md | §19-8 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | Causal→Evidence/Hypothesis/edge存在 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Causal→Evidence/Hypothesis/edge存在 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-015 | Cat3 | verification_action→Hypothesis | organization-diagnosis_設計メモ_v0.1.md | §19-9 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | verification_action→Hypothesis | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | verification_action→Hypothesis | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-016 | Cat3 | 参照先不在 vs 参照元未読の区別 | organization-diagnosis_validator設計メモ_v0.1.md | 合成 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 参照元・参照先の読取状態が判別可能 | 両方未読で区別不可 | 参照先不在確定 | 不在vs未読区別不能 | 参照なし | 当該参照依存のみ停止 | はい | いいえ | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 参照先不在と未読を区別可能 | 参照先不在確定 | 不在vs未読区別不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | 阻害候補 | 参照不在と未読の区別不能時は追跡判断不可 | 3 | — | Stage2 | Stage2 |
| V-C3-017 | Cat3 | 同一relative_path重複（snapshot内） | schemas/organization-diagnosis/mtg_input_snapshot | — | register横断・snapshot | 参照先ID/ファイル | はい | はい | 前提データ読取可 | 依存未読 | 同一relative_path重複（snapshot内） | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 同一relative_path重複（snapshot内） | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-019 | Cat3 | register_snapshot_hash算法照合 | DECISIONS.md | DEC-012 | register横断・snapshot | 参照先ID/ファイル | はい | いいえ | 前提データ読取可 | 依存未読 | register_snapshot_hash算法照合 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | いいえ | いいえ | いいえ | いいえ | G | — | 未実施 | — | — | — | v0.1未実装（DEC-012将来送り） | brief_generator算法確定前 | — | — | — | — | 6 | — | 未 | 要 |
| V-C3-020 | Cat3 | brief source_mtg_session_ids→snapshot | DECISIONS.md | DEC-012 | register横断・snapshot | 参照先ID/ファイル | はい | はい | 前提データ読取可 | 依存未読 | brief source_mtg_session_ids→snapshot | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | はい | いいえ | いいえ | いいえ | C | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | brief source_mtg_session_ids→snapshot | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 6 | — | Stage1 | 可 |
| V-C3-021 | Cat3 | generated_from_registers_at≤generated_at | DECISIONS.md | DEC-012 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | generated_from_registers_at≤generated_at | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | generated_from_registers_at≤generated_at | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 6 | — | Stage1 | 可 |
| V-C3-022 | Cat3 | generated_from_registers_at vs register更新時点 | DECISIONS.md | DEC-012 | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | 時点不整合 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 時点不整合 | 前提不足で判定不能 | — | — | 注意候補 | cache/hash/時点不一致・再取得で解消可 | — | — | 6 | — | Stage1 | 可 |
| V-C3-023 | Cat3 | Evidence ID register内一意 | schemas/organization-diagnosis/evidence.schema | — | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | Evidence ID register内一意 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Evidence ID register内一意 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C3-024 | Cat3 | case scope外ID参照 | schemas/organization-diagnosis/common.schema | — | register横断・snapshot | 参照先ID/ファイル | いいえ | はい | 前提データ読取可 | 依存未読 | case scope外ID参照 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | case scope外ID参照 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 3 | — | Stage1 | 可 |
| V-C4-001 | Cat4 | rejected Evidence参照禁止（全register） | organization-diagnosis_設計メモ_v0.1.md | §19-1 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | rejected Evidence参照禁止（全register） | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | rejected Evidence参照禁止（全register） | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-002 | Cat4 | exclude_from_org_diagnosis参照禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-1 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | exclude_from_org_diagnosis参照禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | exclude_from_org_diagnosis参照禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-003 | Cat4 | 非REPORTEDに話者欠落でエラーにしない | organization-diagnosis_設計メモ_v0.1.md | §19-2 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | はい | いいえ | evidence_type≠REPORTED | — | — | — | 話者欠落をREPORTED以外では違反にしない | 他規則継続 | いいえ | はい | いいえ | いいえ | いいえ | いいえ | A | — | 非該当 | — | — | — | 話者欠落をREPORTED以外では違反にしない | — | — | — | — | — | 4 | — | Stage1 | 可 |
| V-C4-004 | Cat4 | leading_question相槌のみで主要根拠化禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-2 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | leading_question相槌のみで主要根拠化禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | はい | B | F | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | leading_question相槌のみで主要根拠化禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-005 | Cat4 | consultant発言のみで顧客構造仮説支持禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-2 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | consultant発言のみで顧客構造仮説支持禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | はい | B | F | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | consultant発言のみで顧客構造仮説支持禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-006 | Cat4 | MEASUREDから人格・文化・因果へ直接飛躍禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-5 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | MEASUREDから人格・文化・因果へ直接飛躍禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | いいえ | いいえ | いいえ | はい | F | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | MEASUREDから人格・文化・因果へ直接飛躍禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-007 | Cat4 | MEASUREDのみでPattern成立禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-5 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | MEASUREDのみでPattern成立禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | MEASUREDのみでPattern成立禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-008 | Cat4 | 単発EvidenceのPattern化禁止（Case2） | organization-diagnosis_設計メモ_v0.1.md | §21 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | 単発EvidenceのPattern化禁止（Case2） | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 単発EvidenceのPattern化禁止（Case2） | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-009 | Cat4 | corroborated event≠Pattern（Case10） | organization-diagnosis_設計メモ_v0.1.md | §21 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | corroborated event≠Pattern（Case10） | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | corroborated event≠Pattern（Case10） | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-010 | Cat4 | distinct occurrence<2でPattern拒否 | organization-diagnosis_設計メモ_v0.1.md | §19-6 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | distinct occurrence<2でPattern拒否 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | distinct occurrence<2でPattern拒否 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-011 | Cat4 | 同一occurrence複数EvidenceをPattern扱い禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-6 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | 同一occurrence複数EvidenceをPattern扱い禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 同一occurrence複数EvidenceをPattern扱い禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-012 | Cat4 | Pattern sensitivity継承（根拠最大未満禁止） | organization-diagnosis_設計メモ_v0.1.md | §19-6 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | Pattern sensitivity継承（根拠最大未満禁止） | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Pattern sensitivity継承（根拠最大未満禁止） | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-013 | Cat4 | Hypothesis Evidence参照必須（status別） | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | Hypothesis Evidence参照必須（status別） | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Hypothesis Evidence参照必須（status別） | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-014 | Cat4 | mental_modelの事実表現化禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | mental_modelの事実表現化禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | いいえ | いいえ | いいえ | はい | F | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | mental_modelの事実表現化禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-015 | Cat4 | counter_evidence_review not_reviewedで最終出力禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | counter_evidence_review not_reviewedで最終出力禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | counter_evidence_review not_reviewedで最終出力禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-016 | Cat4 | SUPPORTEDでprimary必須 | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | SUPPORTEDでprimary必須 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | SUPPORTEDでprimary必須 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-017 | Cat4 | SUPPORTED同一Evidence条件 | organization-diagnosis_設計メモ_v0.1.md | §18 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | SUPPORTED同一Evidence条件 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | はい | B | F | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | SUPPORTED同一Evidence条件 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-018 | Cat4 | REPORTED-primary: verified+speaker verified | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | REPORTED-primary: verified+speaker verified | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | REPORTED-primary: verified+speaker verified | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-019 | Cat4 | DOC/OBS/MEAS-primary: review verified | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | DOC/OBS/MEAS-primary: review verified | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | DOC/OBS/MEAS-primary: review verified | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-020 | Cat4 | REVISEDをstatusに使用禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | はい | いいえ | 前提データ読取可 | 依存未読 | REVISEDをstatusに使用禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | A | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | REVISEDをstatusに使用禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-021 | Cat4 | REJECTEDにreason/evidence必須 | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | REJECTEDにreason/evidence必須 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | REJECTEDにreason/evidence必須 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-022 | Cat4 | REJECTED→TO_CONFIRM直接復活禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | REJECTED→TO_CONFIRM直接復活禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | はい | いいえ | いいえ | D | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | REJECTED→TO_CONFIRM直接復活禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-023 | Cat4 | 照合レンズ起点をEvidence未確認でTO_CONFIRM禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | 照合レンズ起点をEvidence未確認でTO_CONFIRM禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 照合レンズ起点をEvidence未確認でTO_CONFIRM禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-024 | Cat4 | Hypothesis sensitivity継承 | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | Hypothesis sensitivity継承 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Hypothesis sensitivity継承 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-025 | Cat4 | primaryからconsultant speaker除外 | organization-diagnosis_設計メモ_v0.1.md | §14-2 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | primaryからconsultant speaker除外 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | primaryからconsultant speaker除外 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-026 | Cat4 | primaryからleading_question nod除外 | organization-diagnosis_設計メモ_v0.1.md | §14-2 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | primaryからleading_question nod除外 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | primaryからleading_question nod除外 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-027 | Cat4 | DRAFT空配列許可・TO_CONFIRM以降件数 | organization-diagnosis_設計メモ_v0.1.md | §14-1 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | DRAFT空配列許可・TO_CONFIRM以降件数 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | DRAFT空配列許可・TO_CONFIRM以降件数 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-028 | Cat4 | Case6: SUPERSEDED改訂フロー | organization-diagnosis_設計メモ_v0.1.md | §21 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | Case6: SUPERSEDED改訂フロー | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | はい | いいえ | いいえ | D | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Case6: SUPERSEDED改訂フロー | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-029 | Cat4 | Case7: 話者不明で過度前進禁止 | organization-diagnosis_設計メモ_v0.1.md | §21 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | Case7: 話者不明で過度前進禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | いいえ | いいえ | いいえ | はい | F | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Case7: 話者不明で過度前進禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-030 | Cat4 | Case8: 誘導質問相槌を自発Evidence扱い禁止 | organization-diagnosis_設計メモ_v0.1.md | §21 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | Case8: 誘導質問相槌を自発Evidence扱い禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | いいえ | いいえ | いいえ | はい | F | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Case8: 誘導質問相槌を自発Evidence扱い禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-031 | Cat4 | Case9: レンズ気づきはDRAFT留保 | organization-diagnosis_設計メモ_v0.1.md | §21 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | Case9: レンズ気づきはDRAFT留保 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Case9: レンズ気づきはDRAFT留保 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C4-032 | Cat4 | Case12: rejectedを支持・反証・棄却根拠に使用禁止 | organization-diagnosis_設計メモ_v0.1.md | §21 | Evidence/Pattern/Hypothesis register | 参照先Evidence等 | いいえ | はい | 前提データ読取可 | 依存未読 | Case12: rejectedを支持・反証・棄却根拠に使用禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Case12: rejectedを支持・反証・棄却根拠に使用禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 4 | — | Stage1 | 可 |
| V-C5-001 | Cat5 | causal edge根拠必須 | organization-diagnosis_設計メモ_v0.1.md | §19-8 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | causal edge根拠必須 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | causal edge根拠必須 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-002 | Cat5 | polarity=unknownをloopに含めない | organization-diagnosis_設計メモ_v0.1.md | §19-8 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | polarity=unknownをloopに含めない | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | polarity=unknownをloopに含めない | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-003 | Cat5 | 非閉鎖をloop登録禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-8 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | 非閉鎖をloop登録禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 非閉鎖をloop登録禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-004 | Cat5 | negative edge数とreinforcing/balancing一致 | organization-diagnosis_設計メモ_v0.1.md | §19-8/15-2 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | negative edge数とreinforcing/balancing一致 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | negative edge数とreinforcing/balancing一致 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-005 | Cat5 | causal_type=loopかつINVALID_FORM禁止 | organization-diagnosis_設計メモ_v0.1.md | §15-2 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | causal_type=loopかつINVALID_FORM禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | A | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | causal_type=loopかつINVALID_FORM禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-006 | Cat5 | loop_candidate/INVALID_FORMを通常briefでloop出力禁止 | organization-diagnosis_設計メモ_v0.1.md | §15-2 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | loop_candidate/INVALID_FORMを通常briefでloop出力禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | はい | いいえ | E | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | loop_candidate/INVALID_FORMを通常briefでloop出力禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-007 | Cat5 | VALID_FORM loopのedge存在・閉鎖 | organization-diagnosis_設計メモ_v0.1.md | §19 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | VALID_FORM loopのedge存在・閉鎖 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | VALID_FORM loopのedge存在・閉鎖 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-008 | Cat5 | verification_action必須項目・target存在 | organization-diagnosis_設計メモ_v0.1.md | §19-9 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | verification_action必須項目・target存在 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | verification_action必須項目・target存在 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-009 | Cat5 | verification_action sensitivity継承 | organization-diagnosis_設計メモ_v0.1.md | §19-9 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | verification_action sensitivity継承 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | verification_action sensitivity継承 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-010 | Cat5 | exclude対象へのverification_action禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-9 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | exclude対象へのverification_action禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | いいえ | いいえ | B | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | exclude対象へのverification_action禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-011 | Cat5 | Pattern/Causal/Hypothesis status遷移履歴 | organization-diagnosis_validator設計メモ_v0.1.md | 各schema | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 前提データ読取可 | 依存未読 | Pattern/Causal/Hypothesis status遷移履歴 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | はい | いいえ | いいえ | D | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Pattern/Causal/Hypothesis status遷移履歴 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 5 | — | Stage1 | 可 |
| V-C5-012 | Cat5 | REJECTED直接復活検査（比較対象要） | organization-diagnosis_設計メモ_v0.1.md | §19-7 | Causal/verification_action register | edge/target Hypothesis | いいえ | はい | 履歴比較対象register存在 | 比較対象なし | REJECTED→TO_CONFIRM直接復活 | 履歴入力不足 | 初回register | 当該Hypothesis依存停止 | はい | はい | いいえ | はい | いいえ | いいえ | D | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | REJECTED→TO_CONFIRM直接復活 | 履歴入力不足 | 初回register | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | 阻害候補 | 履歴比較不能時はREJECTED復活判定不可・後続利用阻害候補 | 5 | NJ-06参照 | 要 | 要 |
| V-C6-001 | Cat6 | restricted_hrを通常ブリーフへ出力禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-9/10 | brief Markdown・frontmatter | brief出力・Public境界 | いいえ | はい | 前提データ読取可 | 依存未読 | restricted_hrを通常ブリーフへ出力禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | はい | はい | E | F | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | restricted_hrを通常ブリーフへ出力禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 6 | — | Stage1 | 可 |
| V-C6-002 | Cat6 | exclude_from_org_diagnosis通常出力禁止 | organization-diagnosis_設計メモ_v0.1.md | §19-10 | brief Markdown・frontmatter | brief出力・Public境界 | いいえ | はい | 前提データ読取可 | 依存未読 | exclude_from_org_diagnosis通常出力禁止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | はい | いいえ | E | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | exclude_from_org_diagnosis通常出力禁止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 6 | — | Stage1 | 可 |
| V-C6-003 | Cat6 | confirmation_questions通常brief禁止（Case11） | organization-diagnosis_設計メモ_v0.1.md | §21 | brief Markdown・frontmatter | brief出力・Public境界 | いいえ | はい | 前提データ読取可 | 依存未読 | confirmation_questions通常brief禁止（Case11） | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | いいえ | いいえ | はい | いいえ | E | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | confirmation_questions通常brief禁止（Case11） | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 6 | — | Stage1 | 可 |
| V-C6-004 | Cat6 | register内容とbrief本文整合 | organization-diagnosis_設計メモ_v0.1.md | §6-2 | brief Markdown・frontmatter | brief出力・Public境界 | いいえ | はい | brief本文とregister機械対応可能 | 本文未読/追跡不能 | registerと本文不整合 | 決定論的整合検査不能 | — | 当該briefのみ | はい | はい | いいえ | いいえ | はい | はい | E | F | 適合／違反／検査不能 | registerと本文が機械的に整合 | registerと本文不整合 | 決定論的整合検査不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | 注意候補 | 本文-register機械追跡不能・frontmatter規則は継続可 | 6 | — | 要 | 要 |
| V-C6-005 | Cat6 | Public repoへ実顧客情報混入防止 | organization-diagnosis_設計メモ_v0.1.md | §19-10 | brief Markdown・frontmatter | brief出力・Public境界 | いいえ | はい | 前提データ読取可 | 依存未読 | Public repoへ実顧客情報混入防止 | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | はい | はい | いいえ | はい | はい | C | F | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | Public repoへ実顧客情報混入防止 | 前提不足で判定不能 | — | — | 阻害候補 | 設計メモ§14・追跡/禁止/必須欠落 | — | — | 6 | — | Stage1 | Stage2 |
| V-C6-006 | Cat6 | 実名らしき文字列フラグ | organization-diagnosis_設計メモ_v0.1.md | §19-10 | brief Markdown・frontmatter | brief出力・Public境界 | いいえ | はい | 前提データ読取可 | 依存未読 | 実名らしき文字列フラグ | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | いいえ | いいえ | はい | はい | F | — | 適合／違反／検査不能 | 違反条件不成立（前提充足時） | 実名らしき文字列フラグ | 前提不足で判定不能 | — | — | 注意候補 | cache/hash/時点不一致・再取得で解消可 | — | — | 6 | — | Stage1 | 可 |
| V-C6-007 | Cat6 | source_form意味的妥当性（派生系） | DECISIONS.md | DEC-012 | brief Markdown・frontmatter | brief出力・Public境界 | いいえ | はい | 前提データ読取可 | 依存未読 | — | 前提不足で判定不能 | 規則対象外 | 依存規則のみ停止 | はい | いいえ | いいえ | いいえ | はい | はい | F | — | 適合／検査不能／非該当 | 妥当性確認完了 | — | 依存未読 | 規則対象外 | — | — | — | 適用なし | 意味判断は人間/LLM | 6 | — | Stage1 | 可 |

### 5-2. 実装可能性_主分類集計（確定済み責務100件）

| 分類 | 件数 | 意味 |
|---|---|---|
| A schema完結 | 9 | JSON Schemaのみ。validatorは収集表示 |
| B 現JSON集合で決定論的 | 56 | ID index・参照・subset等 |
| C filesystem要 | 19 | 実在・hash・size |
| D 過去状態要 | 4 | 状態遷移・SUPERSEDED比較 |
| E brief本文/生成メタ要 | 5 | 出力境界 |
| F LLM/人間要 | 6 | 意味・真実性・再識別 |
| G 将来送り | 1 | 既存凍結仕様でv0.1将来送りと決まった責務のみ |
| **合計** | **100** | |
| 副分類件数（集計外） | 6 | B+F等 |
| **分類対象外（NJ）** | **9** | §34の新規判断候補。A〜Gに含めない |

**分類変更したrule_id（主分類）：** V-C1-002(C←B), V-C1-003(C←B), V-C1-005(B←A), V-C1-007(C←A), V-C1-008(A←B), V-C1-009(A←B), V-C2-003(B←C), V-C2-018(B←C), V-C3-017(B←C), V-C3-005/006(違反時severity→注意候補・凍結仕様整合), V-C3-019(Gのみ・人間判断待ちNJから分離)

**rule_idの欠番：** 過去レビューとの追跡性を維持するため許可（例：V-C1-006, V-C2-013〜016, V-C2-017, V-C3-018, V-C6-008はNJ表へ移管）。**欠番の意味：** 規則欠落を意味しない。

### 5-3. rule evaluation outcomeの集計（確定済み責務100件・重複許可）

**対象：** 層A（rule evaluation outcome）のみ。finding emissionの件数ではない。

| 集計軸 | 規則数 |
|---|---|
| 適合を取り得る規則数 | 94 |
| 違反を取り得る規則数 | 92 |
| 検査不能を取り得る規則数 | 93 |
| 非該当を取り得る規則数 | 6 |
| 未実施となる規則数 | 1 |

**原則：**

- 適用可能で実装済みの検査規則は、通常**適合と違反の両方**を取り得る（問題なし時は内部評価として適合）
- 1規則が複数のoutcome候補を持ってよい
- 合計を100へ合わせる必要はない（上表は重複集計）
- findingを出さない設計（案B）でも、内部評価として適合は成立し得る（NJ-09）

**evaluation outcomeとfinding／severityの分離：**

- 検査不能はseverityではない
- 非該当・未実施に原則severityを付けない
- 検査不能時の影響は`検査不能時の影響候補`列で別管理（一律適用なしにしない）
- `違反時severity候補`はevaluation outcomeが**違反**のときのみ意味を持つ

### 5-4. severity・影響候補の集計（distinct rule数とassignment数）

**対象：** findingへ付き得る候補ラベル（正式severity体系ではない）。rule evaluation outcomeそのものではない。

**違反時severity（evaluation outcome＝違反のとき）：**

| 集計軸 | 件数 |
|---|---|
| 違反を取り得るdistinct rule数 | 92 |
| 違反時severity assignment数 | 92 |
| 複数severity候補を持つrule数 | 0 |
| 複数候補を持つrule_id | — |

| 候補ラベル | assignment数 |
|---|---|
| 阻害候補 | 83 |
| 注意候補 | 9 |
| 情報候補 | 0 |
| 未確定 | 0 |

**検査不能時の影響（evaluation outcome＝検査不能のとき）：**

| 集計軸 | 件数 |
|---|---|
| 検査不能を取り得るdistinct rule数（影響assignment付き） | 9 |
| 検査不能時影響 assignment数 | 9 |
| 複数影響候補を持つrule数 | 0 |
| 複数候補を持つrule_id | — |

| 候補ラベル | assignment数 |
|---|---|
| 阻害候補 | 4 |
| 注意候補 | 4 |
| 情報候補 | 0 |
| 適用なし | 1 |
| 未確定 | 0 |

**注記：** 現行マトリクスは1規則1assignment（違反時1列・検査不能時1列）。assignment数＞distinct rule数となる多重割当は現時点**なし**。将来、失敗条件別に複数severity候補を持たせる場合はrule_id単位で列を増やすか別表で管理する。

---

## 6. 6カテゴリ分類

§5の表がカテゴリ分類の正本。各規則は1カテゴリに主帰属。Cat4の意味判断要素（F副分類）はvalidatorが完全自動化しない。

---

## 7. 実装可能性分類（A〜G）

§5-2が正本。主分類は1責務1つ。副分類は§5の`実装可能性_副分類`列（集計外）。

| 分類 | 件数（主分類） | 意味 |
|---|---|---|
| A schema完結 | 9 | JSON Schemaのみ。validatorは収集表示 |
| B 現JSON集合で決定論的 | 56 | ID index・参照・subset等 |
| C filesystem要 | 19 | 実在・hash・size |
| D 過去状態要 | 4 | 状態遷移・SUPERSEDED比較 |
| E brief本文/生成メタ要 | 5 | 出力境界 |
| F LLM/人間要 | 6 | 意味・真実性・再識別 |
| G 将来送り | 1 | 既存凍結仕様でv0.1将来送りと決まった責務のみ |
| **合計** | **100** | |

**Gの範囲：** 人間判断待ちのNJ項目をGへ入れない。現時点のGは`V-C3-019`（register_snapshot_hash算法照合・DEC-012将来送り）のみ。
---

## 8. 実データ未取得時点での設計前提

- 現時点では初弾実案件の実データを取得・投入していない。
- 本validatorは、**架空fixtureで骨格と決定論的規則を検証した後**、初弾実案件データで実地検証する二段階を前提とする。
- 架空fixtureだけで実運用上の妥当性が完成したとは判断しない。
- 実データ検証で判明した論点を、設計失敗として無限に遡及修正せず、**実地検証から得られた新しい発見**として還流する（DEC-008/009の運用と同型）。

---

## 9. 二段階検証モデル

思想層として、架空fixture検証の後に実案件で検証する二段階を採用する（DEC-015）。

### Stage 1：架空fixture検証

- 対象：schema gate、ID重複、参照存在、subset、双方向参照、sensitivity継承、distinct occurrence、SUPPORTED同一Evidence、loop閉鎖、polarity、Manifest整合、path論理制約
- 目的：決定論的規則とvalidator骨格の再現可能な検証

### Stage 2：初弾実案件による実地検証

- 対象：実ファイル実在・hash・size、Dropbox同期、連続2回MTG状態更新、supersedes運用、実brief生成・出力制御、restricted_hr漏えい防止、役割ラベル再識別、作成・検証時間、裕司さんの見立てへの価値
- 目的：架空fixtureでは表現しきれない入力の汚さ、運用負荷、出力境界、価値の実地確認

**Stage 2未実施はvalidator v0.1の限界**として本書に明記する。

---

## 10. 実データ検証時の観察項目

次は**現時点で新仕様として確定しない**観察項目である。

- hashを取得できない、または読取不能な入力
- Dropboxのオンラインのみ／placeholder状態
- 同期途中でsizeやhashが変化するファイル
- path表記ゆれ
- 参照先ファイルの一時欠落
- 旧運用から移行した不完全register
- source_fileとsnapshot input_filesの表記差
- 文字コードや改行コード
- 想定外のYAML scalar型
- 役割ラベルが実名へ近すぎるケース
- 小規模組織での再識別可能性
- 人間には同一出来事だがID上は分断されたoccurrence
- 人間には別の出来事だが同一occurrenceへまとめられたケース
- 連続MTGでの改訂・棄却・SUPERSEDED運用の現実的な揺れ
- brief本文に機械追跡用IDがないことによる検査限界

---

## 11. 検査前提

各規則の検査前提・前提不成立・違反確定・検査不能・非該当・継続範囲は§5マトリクス列に記載。

混同禁止：

1. 規則違反を確認した
2. 検査前提が崩れ適否判定不能（**検査不能**）
3. 当該規則が適用されない（**非該当**）

棚卸し仮分類：検査済み・適合／検査済み・違反／検査不能／非該当／未実施 — **正式validator出力契約ではない**。

### 11-2. 検査不能となり得る場面の棚卸し

次は**規則違反ではなく前提不成立・判定不能**の候補一覧（**43件**）。正式error code・状態名は未確定。

凡例：違反確定＝前提が満たされたうえで違反と言える／検査不能＝適否判定不能／非該当＝当該規則の対象外

#### 読み込み・schema（12件）

| # | 場面 | 違反確定 | 検査不能 | 依存後続 | 無関係続行 | 人間確認 | 新規判断 |
|---|---|---|---|---|---|---|---|
| U-01 | JSONファイルが存在しない | ○（正本期待時） | — | 当該register参照規則 | 他register schema gate | — | — |
| U-02 | JSONをparseできない | ○ | — | 当該ファイル参照規則 | 他ファイル | — | — |
| U-03 | 文字コードのため読み取れない | — | ○ | 当該ファイル全規則 | 他ファイル | 要 | — |
| U-04 | schemaファイルが存在しない | — | ○ | schema gate全体 | — | — | — |
| U-05 | schema自体がinvalid | — | ○ | schema gate全体 | — | — | — |
| U-06 | $refを解決できない | — | ○ | schema gate全体 | — | — | — |
| U-07 | 対象schemaを決定できない | — | ○ | 当該ファイル後続 | 他ファイル | 要 | ○ |
| U-08 | Markdown frontmatterが存在しない | ○（brief期待時） | — | 当該brief後続 | 他ファイル | — | — |
| U-09 | frontmatter終了区切りがない | ○ | — | 当該brief後続 | 他ファイル | — | — |
| U-10 | YAML parseに失敗する | ○ | — | 当該brief後続 | 他ファイル | — | — |
| U-11 | duplicate keyがある | ○ | — | 当該brief後続 | 他ファイル | — | — |
| U-12 | YAML値をJSON互換型へ変換できない | ○ | — | 当該brief schema gate | 他ファイル | — | — |

#### Manifest・case境界（8件）

| # | 場面 | 違反確定 | 検査不能 | 依存後続 | 無関係続行 | 人間確認 | 新規判断 |
|---|---|---|---|---|---|---|---|
| U-13 | Manifestが存在しない | 運用次第 | ○ | Manifest依存Cat2 | register直読のみなら続行可 | 要 | ○ |
| U-14 | Manifestがschema invalid | ○ | — | Manifest依存Cat2 | 他ファイル | — | — |
| U-15 | register pathが存在しない | ○ | — | 当該register参照 | 他register | — | — |
| U-16 | brief pathが存在しない | ○ | — | 当該brief規則 | 他brief | — | — |
| U-17 | snapshot pathを一意に決定できない | — | ○ | MTG来歴規則 | 非MTG規則 | 要 | ○ |
| U-18 | case rootを決定できない | — | ○ | case全体 | — | 要 | ○ |
| U-19 | case_idが一致しない | ○ | — | case境界規則 | — | — | — |
| U-20 | symlink／junctionでroot外へ解決 | — | ○ | path containment規則 | — | 要 | ○ |

#### 参照整合（4件）

| # | 場面 | 違反確定 | 検査不能 | 依存後続 | 無関係続行 | 人間確認 | 新規判断 |
|---|---|---|---|---|---|---|---|
| U-21 | 参照元ファイルがschema invalid | — | ○ | 当該ファイル発参照規則 | 非依存規則 | — | — |
| U-22 | 参照先registerが読み取れない | — | ○ | 当該参照依存規則 | 非依存 | — | — |
| U-23 | ID indexを完全に作れない | — | ○ | Cat3-4参照規則群 | Cat1-2 | — | — |
| U-24 | 参照先不在 vs 未読の区別不能 | — | ○ | 当該参照規則 | 非依存 | 要 | — |

#### filesystem・hash（9件）

| # | 場面 | 違反確定 | 検査不能 | 依存後続 | 無関係続行 | 人間確認 | 新規判断 |
|---|---|---|---|---|---|---|---|
| U-25 | 入力ファイルが存在しない | ○ | — | hash/size規則 | 論理参照のみ | — | — |
| U-26 | 権限不足で読み取れない | — | ○ | hash/size規則 | 論理参照 | 要 | — |
| U-27 | Dropbox placeholderで実体なし | — | ○ | hash/size規則 | 論理参照 | 要 | — |
| U-28 | hash計算中にファイルが変更された | — | ○ | hash照合規則 | 論理参照 | 要 | ○ |
| U-29 | size取得後にファイルが変更された | — | ○ | size照合規則 | 論理参照 | 要 | ○ |
| U-30 | ファイルがロックされている | — | ○ | hash/size規則 | 論理参照 | 要 | — |
| U-31 | 相対pathの解決rootが未確定 | — | ○ | path規則群 | — | 要 | ○ |
| U-32 | hash算法が未確定 | — | 非該当 | register_snapshot_hash照合 | 他規則 | — | ○ |
| U-33 | register_snapshot_hash検証算法が未確定 | — | 非該当 | V-C3-019 | 他規則 | — | ○ |

#### 状態・履歴（5件）

| # | 場面 | 違反確定 | 検査不能 | 依存後続 | 無関係続行 | 人間確認 | 新規判断 |
|---|---|---|---|---|---|---|---|
| U-34 | 前回状態がない | — | 非該当/検査不能 | 遷移比較規則 | 現状態のみ規則 | 要 | ○ |
| U-35 | 比較対象registerがない | — | 検査不能 | REJECTED復活等 | 現状態規則 | 要 | ○ |
| U-36 | 直前版の特定不能 | — | 検査不能 | 遷移規則 | 現状態規則 | 要 | ○ |
| U-37 | last_reviewed_at更新判断不能 | — | 検査不能 | 一部履歴規則 | 他規則 | 要 | ○ |
| U-38 | REJECTED直接復活の判断不能 | — | 検査不能 | V-C4-022,C5-012 | 他規則 | 要 | ○ |

#### Brief・安全性（5件）

| # | 場面 | 違反確定 | 検査不能 | 依存後続 | 無関係続行 | 人間確認 | 新規判断 |
|---|---|---|---|---|---|---|---|
| U-39 | 本文に出力元register IDがない | — | 検査不能 | 本文-register対応 | frontmatter規則 | 要 | — |
| U-40 | 本文とregisterの機械追跡不能 | — | 検査不能 | V-C6-004 | frontmatter規則 | 要 | — |
| U-41 | 通常/HR限定ブリーフの判定不能 | — | 検査不能 | 出力境界規則 | frontmatter規則 | 要 | ○ |
| U-42 | restricted_hr混入の決定論的検査不能 | — | 検査不能 | V-C6-001 | frontmatter規則 | 要 | ○ |
| U-43 | 役割ラベル再識別の機械判定不能 | — | 検査不能 | V-C6-006 | 他規則 | 要 | ○ |

**領域別件数：** 読み込み・schema 12／Manifest・case 8／参照整合 4／filesystem・hash 9／状態・履歴 5／Brief・安全性 5。

---

## 12. 検査不能時の挙動とフェイルセーフ

- validatorは検査前提を満たせない場合、推測・補完で合格判定を作らない。
- 検査できなかった規則を適合として扱わない。validator全体結果もPASSにしない。
- データ違反と検査不能を区別する。
- 検査不能の理由・対象・未検査規則を明示する。
- 1件の検査不能で無関係検査を善意に中止しない。
- 基礎データ破損で後続の意味が成立しない場合は、依存後続を未検査で止める。
- 欠落値・参照先・hash・ID・statusを自動補完しない。
- 検査不能をWARNへ自動丸めしない。
- 全体停止／ファイル単位停止／依存規則のみ停止は原因と依存で分ける（§13）。

financial-analysisで確立した規律（必須データ欠落・取得失敗・前提不成立→判定不能で止める）との**思想対応**は認めるが、正式状態名・error codeの転用はしない（DEC-005〜007の運用参照）。

**検査不能となった規則を、合格または問題なしとして扱ってはならない。**

---

## 13. 部分失敗時の検査継続

| 案 | 概要 | 誤PASS | 情報損失 | 複雑性 | 推奨 |
|---|---|---|---|---|---|
| A case全体停止 | 基礎失敗でcase全中止 | 低 | 高 | 低 | — |
| B ファイル単位停止 | invalidファイルのみ後続停止 | 低 | 中 | 中 | **推奨案** |
| C 依存関係単位停止 | 依存規則のみ未検査 | 低 | 低 | 高 | 併用候補 |

**推奨：** 案Bを主とし、ID index構築不能など基盤失敗時は案Cで依存規則を未検査明示。**人間確定が必要な新規判断候補。**

---

## 14. severityを決める原理

ERROR／WARN／INFOの正式名称・段階数は**未確定**。

| 原理 | 例 |
|---|---|
| 阻害候補 | 正本形式不成立、追跡不能、禁止データ使用、sensitivity破壊、必須入力欠落で検査成立不可 |
| 注意候補 | 非正本cache不一致、再構築可能索引の古さ、修復推奨だが正本追跡可 |
| 情報候補 | 非該当、任意省略、将来送り、人間確認通知 |

**注意：**

- ファイル不存在は常に同一severityではない（正本不存在 vs 索引未登録）。
- hash不一致の違反時severityは凍結仕様どおり警告（注意候補）。後続利用を阻害するかはNJ-08。
- 検査不能を一律WARNにしない。
- severityは「重要そうか」ではなく、正本性・追跡可能性・安全性・後続利用可能性から導く。

§5の`違反時severity候補`／`検査不能時の影響候補`列はこの原理に基づく候補ラベル（resultとは別軸）。

**resultとseverityの分離（§5-3参照）：**

- 検査不能はseverityではない
- 非該当・未実施に原則severityを付けない
- 検査不能時の影響は別列で管理し、一律適用なしにしない
- result集計とseverity／影響集計を混ぜない


| 規則種別 | severity判断 |
|---|---|
| hash不一致（V-C3-005/006） | **違反時：注意候補**（凍結仕様§7-4-1・警告）。後続利用を阻害するかは**NJ-08**（現時点は警告を正） |
| 正本register不存在 | 阻害候補 |
| Manifest索引のみ未登録 | 注意候補 |
| Manifest cache日時不一致 | 注意候補（DEC-011） |

---

## 15. validator実行単位

**新規判断候補（停止事項）：**

| 論点 | 選択肢 | 推奨案 | 人間確定 |
|---|---|---|---|
| 実行単位 | case一括／単一register／単一ファイル | case一括（_org_diagnosis/） | 要 |
| 最小入力 | Manifest必須か任意か | Manifest推奨・省略時走査 | 要 |

凍結根拠なし。本節は候補列挙のみ。

---

## 16. ファイル発見方式

**新規判断候補：** Manifest起点索引 vs 固定ディレクトリ走査（DEC-011は両立可能だが手順未固定）。§13案Bと整合させる。

---

## 17. 診断結果モデル（三層）

### 17-1. 三層モデル（思想層・frozen）

| 層 | 名称 | 候補 | 役割 | 正式化 |
|---|---|---|---|---|
| 0 | validator全体の実行結果 | PASS／FAIL／UNVERIFIABLE | 呼び出し側が解釈する集約結果 | 三値の存在は思想層で確定。集約規則の細部は実装段階 |
| A | rule evaluation outcome | 適合／違反／検査不能／非該当／未実施 | 個々の規則の内部評価結果 | 5状態の存在は思想層で確定。正式enum名は**未確定**（§5-3候補・実装段階） |
| B | finding emission | findingを出す／出さない、および種別候補 | 利用者向けまたはmachine-readableへの出力項目 | 正式finding schemaは**未確定**（**NJ-09**・実装段階） |

```text
validator全体の三値
≠
個々のrule evaluation outcome
≠
finding emission
```

**混同禁止：**

- validator全体のPASS／FAIL／UNVERIFIABLEを、個々のrule evaluation outcomeへ流用しない
- 層Aの「適合」≠ 層Bの「findingなし」が必ずしも同時とは限らない
- 層Aの「検査不能」は層Bのunable-to-check findingになり得るが、同一ではない
- severityは層Bのfindingに付く候補。層Aのoutcomeそのものではない
- 検査不能をseverityへ丸めない（§5-3、§5-4、§12）

### 17-2. finding emission（出力層）

- ruleが適合してもfindingを出さない場合がある
- 違反や検査不能をfindingとして出す場合がある
- severityはfinding側の属性候補である
- 正式なfinding schema、enum、error codeは実装段階で確定する

### 17-3. パラメータ層へ残す事項（NJ-09等・実装段階）

次は思想層の凍結対象ではなく、実装段階または将来判断で確定する。

- 正式状態名・enum名称
- finding種別の正式名称
- 1規則1評価 vs ファイル単位集約の出力契約
- machine-readable JSON reportの正式schema
- 診断結果の並び順
- human-readable出力粒度

## 18. 実行基盤・CLI・出力（DEC-015）

### 18-1. 実行基盤方針（思想層・frozen）

v0.1 validatorは、**独立実行可能なPythonスクリプト**として実装する。

| 項目 | 方針 |
|---|---|
| 形態 | 独立実行可能なPythonスクリプト |
| pre-commit連携 | **しない** |
| 入力 | リポジトリ外の顧客データを明示的に指定して実行する |
| 入力変更 | **入力データを変更しない**（検出・報告のみ） |
| machine-readable出力 | JSON結果を出力する |
| human-readable表示 | 実装段階で確定する |

**候補パス（今回ファイルは作成しない）：** 既存構成では決定論的計算核がリポジトリ直下の`financial_calc.py`として置かれている。これに合わせ、候補はリポジトリ直下の`organization_diagnosis_validator.py`とする。想定する実行単位の呼称は`validator.py`。正式配置はパラメータ層（実装段階）で確定する。

**pre-delivery-checkとの役割分離：**

| ツール | 役割 |
|---|---|
| pre-delivery-check | リポジトリ内成果物の検品 |
| organization-diagnosis validator | 顧客case内のschema、ファイル、参照、来歴、出力境界の検証 |

**pre-commitへ接続しない理由：**

- リポジトリ外の顧客フォルダへアクセスするため
- Dropbox等のfilesystem状態に依存するため
- commitごとの実行には重すぎるため
- 公開成果物の検品と顧客データ検証を混在させないため

### 18-2. パラメータ層（実装段階で確定）

次は思想層の凍結対象ではない。実装段階で確定する。

- Pythonファイルの正式配置
- CLI引数
- JSON出力の正式schema
- enumの正式名称
- error code
- human-readable report形式
- exit code
- ログ形式
- performance上限
- filesystem timeout等の具体値

schema invalid時の後続検査継続は§13と連動し、継続モデルの最終選択は**未確定**（NJ-04）。NJ-01のCLI詳細も本節のパラメータ層に含み、v0.1実装対象外の新規判断候補として§34に残す。

---

## 19. Manifest・case境界

DEC-011確定事項をvalidator責務として実装候補に含める（§5 Cat2）。矛盾時は本体を正としManifestを上書きしない。

---

## 20. path・filesystem・hash

mtg_input_snapshot・DEC-011/012より：実在、path containment、hash/size照合、snapshotファイル名規則、日付整合。

hash不一致・size不一致は凍結仕様§7-4-1どおり **hash不一致を警告する** をv0.1の正とする。NJ-08の後続利用阻害・自動整合回復・新snapshot作成等はv0.1実装対象外（コードで先取りしない）。

---

## 21. ID・参照整合

§5 Cat3。JSON Schemaだけで保証できない参照はすべてvalidator（schema設計メモ§19 L863）。

---

## 22. Evidence・Pattern・Hypothesis規則

§5 Cat4。設計メモ§19が正本。REPORTED以外への話者必須エラーは**非該当**（§19-2 L1067）。

---

## 23. Causal・Verification Action・履歴

§5 Cat5。状態遷移は**現状態のみでは不十分**な規則あり（V-C5-012）。比較対象の履歴入力は新規判断候補。

---

## 24. Brief・出力境界

§5 Cat6。frontmatterはDEC-012。本文はschema外。機械可読IDがないため完全決定論的な本文-register対応は**v0.1では限界**（§10）。

Phase 6分割案：

| 区分 | 内容 |
|---|---|
| 6A | frontmatter／Manifest決定論的検査 |
| 6B | brief_generator導入後の本文出力検査 |
| 6C | LLM／人間による内容・安全性評価 |

---

## 25. Public repository安全性

§19-10。fixture・成果物への実顧客情報混入検出は決定論的候補＋人間最終確認。氏名検出・再識別可能性の完全機械化は**保証しない**（設計メモ§19-10 L1154-1155）。

---

## 26. mutation方針

validatorは検出・報告のみ。自動fix禁止（§3、DEC-011合成）。

---

## 27. 6段階実装ルート

| Phase | 内容 | 規則数候補 |
| 1 | 基盤・読み込み・schema gate | 13 |
| 2 | ファイル構成・Manifest・case境界 | 13 |
| 3 | ID index・参照整合・入力来歴 | 23 |
| 4 | Evidence・Pattern・Hypothesis規則 | 32 |
| 5 | Causal・Verification Action・履歴 | 12 |
| 6 | Brief・出力境界・統合（6A/6B/6C） | 7+ |

---

## 28. 各Phaseの完了条件（要約）

### Phase 1

- **目的：** 全対象ファイルのschema gateと読み込みパイプライン確立
- **成功条件：** 架空fixtureでJSON/YAML/frontmatterのVALID/INVALID再現、schema error収集、検査不能と違反の区別
- **停止条件：** case root・schema選択・partial failure方針が未確定のまま実装開始
- **次Phase前提：** 案B/Cの継続モデル仮決定

### Phase 2

- **目的：** Manifest・固定path・case_id・cache照合
- **成功条件：** 架空`_org_diagnosis/`で索引・実在・cache WARN/ERROR候補の再現
- **対象外：** register内容の意味規則
- **実データ：** Dropbox placeholderはStage 2

### Phase 3

- **目的：** ID indexと参照グラフ
- **成功条件：** Case 12等で参照不在・重複・subset検出
- **依存：** Phase 1-2の読み込み成功

### Phase 4

- **目的：** ドメイン規則（EPH）
- **成功条件：** Case 2/6/10/12の架空再現。Case 11はPhase 4（sensitivity）・Phase 5（verification_action）を含む
- **実データ：** 連続MTG改訂はStage 2

### Phase 5

- **目的：** Causal・verification_action・履歴
- **成功条件：** loop閉鎖・polarity・INVALID_FORM分離
- **停止条件：** 履歴入力方式未確定時のREJECTED復活検査

### Phase 6

- **目的：** brief frontmatter・出力境界
- **成功条件：** 6Aの決定論的項目、6B/Cはgenerator・実案件後
- **fixture：** brief Markdown + frontmatter

**新規ファイル候補（実装時・今回は作成しない）：** 候補パス`organization_diagnosis_validator.py`（リポジトリ直下・`financial_calc.py`と同型）、`tests/test_org_diagnosis_validator.py`、`tests/fixtures/org_diagnosis/`。正式配置はパラメータ層。

**依存候補：** `jsonschema[format-nongpl]`、将来`ruamel.yaml` — **今回追加しない。**

---

## 29. Case 1〜12対応

| Case | 主な論点 | validator規則（例） | Phase | 架空fixture | 実データ要 | 人間/LLM | 連続2MTG |
|---|---|---|---|---|---|---|---|
| 1 | 構造仮説成立 | V-C4-013,017 | 4 | ○ | 一部 | 一部 | 否 |
| 2 | 単発Pattern禁止 | V-C4-008 | 4 | ○ | — | — | 否 |
| 3 | 因果断定不可 | V-C5-001 | 5 | ○ | — | ○ | 否 |
| 4 | 非閉鎖loop禁止 | V-C5-003 | 5 | ○ | — | — | 否 |
| 5 | ハラスメント別経路 | V-C4-002 | 4 | ○ | ○ | ○ | 否 |
| 6 | WEAKENED/REJECTED/SUPERSEDED | V-C4-028,C5-011,012 | 4-5 | 部分 | ○ | ○ | **要** |
| 7 | 話者不明 | V-C4-029 | 4 | ○ | ○ | ○ | 否 |
| 8 | 誘導質問相槌 | V-C4-004,030 | 4 | ○ | — | F | 否 |
| 9 | レンズ気づきDRAFT | V-C4-023,031 | 4 | ○ | — | ○ | 否 |
| 10 | corroborated event | V-C4-009 | 4 | ○ | ○ | ○ | 否 |
| 11 | restricted_hr・confirmation_questions・verification_action・sensitivity | V-C4-012,024,V-C5-009,010,V-C6-001,003 | Phase 4–6（主Phase 6） | 部分 | ○ | ○ | 否 |
| 12 | rejected参照禁止 | V-C4-001,032 | 4 | ○ | — | — | 否 |

---

## 30. 初弾実案件との接続

| 範囲 | 内容 |
|---|---|
| 実案件なしで設計可能 | Phase 1-5の決定論的規則、mutation禁止、schema境界 |
| 架空fixtureで検証可能 | Case 2/8/10/12中心、参照・subset・loop形式 |
| filesystem架空で検証可能 | hash/size/path（ローカルコピー） |
| 連続2回MTG必要 | Case 6、supersedes、REJECTED復活 |
| 実brief生成必要 | 6B本文出力境界 |
| 裕司さん価値評価必要 | Stage 2全体、F分類規則 |

### 案A/B/C比較

| 案 | 概要 | 長所 | 短所 |
|---|---|---|---|
| A | Phase1-5先行→6を実案件接続 | 早期に骨格完成 | 出力境界は後回し |
| B | Phase1-3のみ先行 | リスク低 | ドメイン規則遅延 |
| C | 全保留 | — | 学習遅い |

**推奨：案A** — schema 9本完了済み、架空Caseが揃っており、Stage1で決定論的規則を固めてからStage2で実地検証する二段階モデルと整合。**今回は実行しない。**

---

## 31. schema責務との境界

| 担い手 | 内容 |
|---|---|
| schema | 1ファイル内の型・enum・required・pattern・conditional・null・件数・未知項目拒否 |
| validator | ファイル間参照、ID一意、filesystem、hash/size、sensitivity継承、状態履歴、Manifest cache、loop形式、出力境界 |
| LLM/人間 | 意味妥当性、真実性、仮説の質、誘導性、再識別、顧客提示可否 |

確定済み責務100件は上記に漏れなく配置（G・NJを除く）。棚卸し総項目109件のうちNJ9件は§34。

---

## 32. 既存凍結仕様

設計メモ§18-19、schema設計メモ§18-19、DEC-008〜012に**直接記載**されたvalidator責務（72件相当）。本書§5で`根拠`列にファイル・節を明示。

---

## 33. 合成判断

- validatorは検出・報告のみ（DEC-011から一般化）
- schema gate結果収集とsemantic検査の分離
- financial-analysis型の「推測で判定を作らない」フェイルセーフの適用（状態名は別）
- 二段階検証（架空→実地）
- 案Bファイル単位partial failure推奨

---

## 34. 新規判断候補（別表・9件）

責務マトリクス外。A〜G分類・evaluation outcome集計・severity集計の対象外。

| # | 論点 | 関連（旧rule_id等） | 推奨案 | 人間確定 |
|---|---|---|---|---|
| NJ-01 | CLI契約の詳細（正式配置・引数・exit code・human-readable形式） | §18 | 実行基盤は独立Pythonスクリプトで確定済み。詳細は実装段階 | 要（詳細のみ） |
| NJ-02 | 実行単位・case root・brief種別境界 | V-C2-014, V-C2-016, V-C6-008 | case一括（_org_diagnosis/） | 要 |
| NJ-03 | file discovery（Manifest優先・走査・symlink） | V-C2-013, V-C2-015, V-C2-008 | Manifest優先+走査補完 | 要 |
| NJ-04 | partial failure（継続モデル） | V-C1-006, §13 | 案B+C | 要 |
| NJ-05 | severity/error code正式体系 | §14, §17 | 原理先行・体系後 | 要 |
| NJ-06 | 履歴入力（状態遷移比較対象） | V-C5-012, §23 | 前回registerスナップショット比較 | 要 |
| NJ-07 | 正式YAML parser | V-C1-003, §18 | ruamel.yaml safeをv0.1候補 | 要 |
| NJ-08 | hash不一致の後続利用・解消方法 | V-C3-005/006, §14, §20 | 下記詳細 | 要 |
| NJ-09 | rule evaluation outcomeとfinding出力契約 | §17, §5-0-1 | 案C（下記） | 要 |

### NJ-08 詳細（hash不一致）

**既存凍結仕様（schema設計メモ§7-4-1）：** hash不一致は**警告する**（入力がスナップショット以降に変更された）。

**論点：** 警告だけで後続診断利用を継続してよいか。

**懸念：** 現在ファイルとsnapshot取得時点の入力が一致しないため、Evidence来歴の検証可能性が低下する。

**選択肢：**

- A. 警告のみで検査継続
- B. 当該入力に依存する後続規則を未検査にする
- C. case全体を阻害する
- D. 裕司さんによる明示承認がある場合のみ継続

**扱い：** 人間確定が必要。**v0.1の正は凍結仕様の「hash不一致を警告する」である。** 阻害化・自動整合回復・新snapshot作成等は本NJに分離し、v0.1では採用・実装しない。NJをコード側で先取りして確定してはならない。

**hash不一致の解消方法：** v0.1では未確定（パラメータ層／将来判断）。

**現時点で安全に言えること：** 旧snapshotと異なる現在ファイルを、同一入力であるとみなして自動的に整合回復してはならない。

**候補（v0.1ではいずれも採用しない）：**

- 元のファイル内容を復元する
- 新しいcapture識別方式を将来追加する
- snapshot versionを将来追加する
- 再取得を別MTG sessionとして扱う
- 人間承認付きの移行手順を設ける
- 後続利用を阻害する
- 新しいMTG input snapshotを自動作成する

input snapshotは不変で、`mtg_session_id`がsnapshot識別子を兼ねる。同一MTGの更新ファイルに対し「新しいMTG input snapshotを作成する」だけでは、mtg_session_idの再使用可否・旧Evidenceの扱い・複数snapshot許容などが決まらない。

**本NJは将来判断の記録として残す。v0.1実装対象外（DEC-015）。**

### NJ-09 詳細（finding出力契約）

**論点：**

- 全規則の評価結果をreportへ出すか
- 違反・検査不能だけをfindingとして出すか
- 適合結果をsummaryだけに出すか
- 非該当・未実施をreportへ出すか
- 検査不能findingへseverityとは別の状態を持たせるか
- human-readableとmachine-readableで出力粒度を変えるか

**選択肢：**

| 案 | 概要 | 長所 | 短所 |
|---|---|---|---|
| A | 全規則について評価結果を出力 | 監査・再現性が高い | ノイズ大、report肥大 |
| B | 違反・検査不能等のfindingだけを出力 | 利用者が読みやすい | 内部適合の追跡は別経路が必要 |
| C | machine-readableでは全評価結果、human-readableではfindingのみ | 両立 | 実装・テストが複雑 |

**推奨案：** 案C — schema設計メモでもvalidator出力契約詳細は次工程。内部は層Aを保持し、利用者向けは層Bに絞る二段構成がfinancial-analysis型の検算モデルに近い。

**人間確定が必要。** 今回は確定しない。

---

## 35. 停止事項

§34の新規判断候補（NJ-09含む）

---

## 36. 前工程からの申し送り

- **横断diff恒久ルールが未了**である（基準commitから最終commitまでの全変更を凍結前検査する運用が未記録）。
- validator実装開始前に**独立して閉じる**ことを推奨する。
- validator設計判断と混ぜない。

例外台帳運用（`scripts/pre-delivery-intentional-uncertainty.tsv`）：運用自体は完了済み。本書パラメータ層の意図的未確定表記は、WARNを消す目的での仮決め・削除をしない。文書全体をdraftのまま思想層のみ凍結するため、台帳への即時登録は行わない。

---

## 37. 思想層凍結の範囲と対象外（DEC-015）

validator設計メモv0.1の**思想層をfrozen**とする。**文書全体は実装パラメータ確定までdraft**とする。

### 思想層として凍結するもの

- validatorとLLM・人間の責務分離
- 確定済み100責務
- 6Phaseの実装順
- rule evaluation outcomeとfinding emissionの分離
- validator全体の三値との分離
- 検査不能の扱い
- 入力非変更
- 架空fixture→実データ検証の二段階
- NJを実装で先取りしないこと
- pre-commit非連携

### パラメータ層（実装段階で確定）

- Pythonファイルの正式配置
- CLI引数
- JSON出力の正式schema
- enumの正式名称
- error code
- human-readable report形式
- exit code
- ログ形式
- performance上限
- filesystem timeout等の具体値

### v0.1実装境界

- 実装対象：確定済み100責務
- 実装対象外：NJ-01〜NJ-09
- 棚卸し総項目：109件（100＋9）は記録として維持

### 本工程で実施しないもの

- validator実装、validator骨格、CLI実装、schema gate実装、参照整合実装、filesystem検査、fixture、unit test、brief parser、dependency追加
- NJの採用・実装
- 正式CLI／JSON schema／enum／error codeの確定（パラメータ層）
- 文書全体のfrozen化（パラメータ確定後に移行）

**検査不能となった規則を、適合または問題なしとして扱ってはならない。**
**validator全体結果を、検査不能のままPASSにしてはならない。**

**思想層は実装から変更しない。思想層の変更が必要な場合は新しい設計判断を経る。**
**次ゲートはvalidator実装ではなく、別途承認を要する。**

---

*本ファイルは organization-diagnosis validator v0.1 の設計メモです。思想層はfrozen。文書全体はdraft。パラメータ層はimplementation-time decision。schema正本・顧客データの代替ではありません。*
