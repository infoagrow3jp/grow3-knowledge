---
status: frozen
version: 0.1
基準日: 2026-07-12
確定者: 小林裕司
改訂履歴: v0.1（初版・設計メモ§23未確定16項目のうちschema開始に必要な10判断を確定）→ v0.1整合修正（ID規則・loop_candidate分離・null/applicability整理・DRAFT Hypothesis・JSON Schema共通契約・出典追跡）→ v0.1確定（occurrence_date正本整理・loop出力条件明文化）
参照: docs/organization-diagnosis_設計メモ_v0.1.md（frozen）、DECISIONS.md DEC-008
---

# organization-diagnosis schema設計メモ v0.1

本書は、凍結済み `docs/organization-diagnosis_設計メモ_v0.1.md`（DEC-008）を
変更せずに、JSON Schema・validator実装へ進むために必要な判断だけを確定する
schema段階の設計判断メモである。

---

## 1. 背景と目的

organization-diagnosis設計メモv0.1（コミット `6498fa9`）は、
「解釈の由来管理」を中核原則として凍結された。

設計メモ§23には、schema実装前に判断が必要な16項目が残されていた。
本書は、そのうち**schema実装を開始するために必要な10判断**を確定し、
残りは引き続き未確定またはv0.2候補として管理する。

financial-analysis（指標定義書v0.2、`financial_calc.py`、boundary fixture）から
継承する規律：

- 正本を一本化する
- 欠落とゼロ（本領域では欠落と明示的null）を区別する
- 不明入力を善意に補完しない
- 機械検査（schema／validator）と人間確認の役割を分ける
- 実顧客データをPublicリポジトリへ保存しない

---

## 2. 凍結済み設計メモとの関係

| 層 | ファイル | 役割 |
|---|---|---|
| 設計メモ（frozen） | `docs/organization-diagnosis_設計メモ_v0.1.md` | 診断手順、Evidence管理、仮説管理、安全規律、出力契約 |
| schema設計メモ（本書） | `docs/organization-diagnosis_schema設計メモ_v0.1.md` | 保存形式、ファイル構成、ID、型表現、schema分割、validator責務 |
| 将来のschema正本 | `schemas/organization-diagnosis/*.schema.json` | JSON Schema実装 |
| 将来のvalidator | `organization_diagnosis_validator.py` 等 | 参照整合性・状態遷移・境界検査 |

**原則：**

- 凍結済み設計メモを遡及修正しない。
- schema段階で新しく判明した論点は、本書§22「schema段階で判明した新規論点」に記録する。
- 設計メモと矛盾する場合は、設計メモを正とし、schema側を調整する。
  設計メモ自体の改訂が必要と判明した場合は、別DECISION＋設計メモ改訂版として扱う。

---

## 3. 今回確定する範囲

設計メモ§23未確定16項目のうち、今回確定する10項目：

| # | 項目 | 本書での確定 |
|---|---|---|
| 1 | registerの保存形式 | §6 → **JSON** |
| 2 | registerと内部診断ブリーフの正本関係 | §6 → **register正本、ブリーフ生成物** |
| 3 | 顧客・MTG・registerのファイル構成 | §7 |
| 4 | occurrence_keyの粒度 | §12 |
| 5 | Pattern registerのstatus語彙 | §13 → **DRAFT／ACTIVE／WEAKENED／REJECTED／SUPERSEDED** |
| 6 | Causal edge／loop registerのstatus語彙 | §15 |
| 7 | verification_actionの格納位置 | §16 → **独立register（JSON）** |
| 8 | primary_supporting_evidence_idsの選定基準 | §14 |
| 9 | ID体系 | §8 |
| 10 | 日付・時刻・null・not_applicableの表現規則 | §9・§10 |

---

## 4. 今回確定しない範囲

| 項目 | 扱い |
|---|---|
| measured_trendの実装 | v0.2候補（§22参照） |
| mtg_pipeline.pyとの自動接続 | 未確定（§22参照） |
| 打合せDBとの接続 | 未確定（§22参照） |
| 裕司さんによる例外承認の重み付け | 未確定（§22参照） |
| 顧客向け最終出力 | 対象外（設計メモ§4・§5のまま） |
| validatorのエラーコード詳細 | 次工程（validator実装時） |
| skill／subagent構成 | 次工程 |
| verification_actionの状態管理（未実施／完了等） | v0.1 schemaでは**状態フィールドなし**（§22参照） |
| 複数MTG時の差分自動生成 | 未確定（§22参照） |
| corroborated eventの代表Evidence統合 | v0.1は**全件保持**（§22参照） |

---

## 5. schema全体構成

### 5-1. 分割案（v0.1採用案）

| ファイル | 対象 |
|---|---|
| `organization_diagnosis_manifest.schema.json` | manifest（索引・version・ファイル配置） |
| `evidence.schema.json` | Evidence ledger（型別conditional required含む） |
| `pattern.schema.json` | Pattern register |
| `hypothesis.schema.json` | Hypothesis register |
| `causal.schema.json` | Causal edge + loop（同一ファイル内でtype分岐） |
| `verification_action.schema.json` | verification_action register |
| `brief_metadata.schema.json` | ブリーフfrontmatter（生成物メタのみ） |
| `mtg_input_snapshot.schema.json` | MTG入力スナップショット（inputs/） |
| `common.schema.json` | 共通定義（ID pattern、日付、enum、sensitivity等） |

**採用理由：**

- 設計メモのregister単位と1:1で対応し、validatorの段階的実装が可能。
- Evidenceの型別conditional requiredを独立ファイルに閉じ込められる。
- financial-analysisのfixture分割（本体3期＋boundary_cases）と同様、
  境界値テストをregister単位で追加しやすい。

### 5-2. 単一巨大schemaとの比較

| 観点 | 分割schema | 単一巨大schema |
|---|---|---|
| 可読性 | 高い | 低い（1400行超の設計メモ相当が1ファイルに集中） |
| 変更影響 | register単位で限定 | 1箇所の変更が全体レビューを要する |
| $refの複雑性 | common.schema.jsonへの参照が必要 | 参照不要だが内部が肥大 |
| validator実装 | registerファイル単位で段階的に検査可能 | 全体を一度に読む必要 |
| 初期実装コスト | やや高い（$ref整備） | 低い |

**v0.1判断：分割schemaを採用する。**

### 5-3. JSON Schema共通契約（v0.1確定）

| 項目 | 採用値 |
|---|---|
| JSON Schema draft | **Draft 2020-12** |
| `$schema` | 各schemaファイルに `"https://json-schema.org/draft/2020-12/schema"` |
| `$id` | 各schemaに一意URI（例：`https://grow3.dev/schemas/organization-diagnosis/v0.1/evidence.schema.json`） |
| `$ref`解決 | `common.schema.json` を基準定義とし、相対パス `$ref` で参照 |
| schema_version（データ） | **`0.1.0`**（v0.1固定） |
| 未知フィールド | 原則 **`additionalProperties: false`** |
| 将来拡張 | 自由記述ではなく **`extensions` オブジェクト** に限定 |
| ID重複 | **validator責務**（schema単体では検査不可） |

**register共通envelope（全register JSONのトップレベル）：**

```json
{
  "schema_version": "0.1.0",
  "case_id": "CASE-ORG-001",
  "register_type": "evidence",
  "last_updated_at": "2026-07-12T12:00:00+09:00",
  "items": []
}
```

| フィールド | 説明 |
|---|---|
| schema_version | 使用schemaバージョン（`0.1.0`） |
| case_id | 顧客名・個人名を含まない内部識別子 |
| register_type | evidence / patterns / hypotheses / causal / verification_actions |
| last_updated_at | register最終更新（RFC3339） |
| items | registerエントリの配列 |

manifestなしでも、envelope＋items構造によりregister単体のschema検査が可能。

---

## 6. 保存形式と正本関係

### 6-1. 保存形式の比較

| 選択肢 | 長所 | 短所 | v0.1 |
|---|---|---|---|
| **JSON（register）** | schema・validator・参照整合性に最適 | 人間可読性が低い | **採用** |
| YAML（register） | コメント可能 | インデント事故、schema検証ツールとの相性 | 不採用 |
| Markdown（register） | 閲覧しやすい | 参照整合性の機械検査が弱い | 不採用 |
| **Markdown（ブリーフ）** | 裕司さんの通読・修正に最適 | 構造データの正本には不向き | **採用（生成物）** |
| ハイブリッド | 機械検査と可読性を分離 | 同期ルールが必要 | **採用（register=JSON、brief=MD）** |

### 6-2. 正本関係（v0.1確定）

```
register（JSON） ＝ 正本
    ↓ 生成（将来のbrief_generator）
内部診断ブリーフ（Markdown） ＝ 生成物（人間通読・確認用）
manifest.json ＝ 索引（内容の正本ではない）
MTG input snapshot ＝ 入力の不変スナップショット（Evidence抽出元）
```

**採用理由：**

- 二重管理（registerとブリーフを独立に手編集）によるズレを避ける。
- 設計メモ§23-5の「ブリーフはregisterから生成」案を採用。
- v0.1ではbrief_generatorは未実装。手動生成＋validator整合検査から開始する。

**v0.1での暫定運用：**

- registerを先に更新し、ブリーフはregister内容を反映して作成する。
- ブリーフfrontmatterに `generated_from_registers_at`（RFC3339）と
  `register_snapshot_hash`（将来）を付与し、生成時点を追跡する。

---

## 7. 顧客・MTG・ファイル構成

### 7-1. ディレクトリ構成（架空例）

顧客Dropbox内の一般例。実顧客名・実パスは使用しない。

```
_org_diagnosis/
  manifest.json
  inputs/
    MTG-20260701-001.json      # MTG入力スナップショット
    MTG-20260801-001.json
  registers/
    evidence.json
    patterns.json
    hypotheses.json
    causal.json
    verification_actions.json
  briefs/
    2026-07-01_brief.md
    2026-08-01_brief.md
```

### 7-2. 構成の判断

| 層 | 粒度 | 役割 |
|---|---|---|
| **registers/** | 顧客単位master（追記・改訂型） | 継続診断の正本。Hypothesisのsupersedes等を横断管理 |
| **inputs/** | MTG単位スナップショット | そのMTG時点の入力を不変保存。Evidenceの抽出元 |
| **briefs/** | MTGまたは診断サイクル単位 | 裕司さん確認用の生成物 |
| **manifest.json** | 顧客単位 | 索引。内容の正本ではない |

**設計メモ§23-3「1顧客1register＋MTGデルタ」案を採用する。**

- registers/ は顧客契約期間を通じたmaster register（追記型）。
- inputs/ はMTGごとの不変スナップショット。
- MTG後のEvidence追記・Hypothesis更新は registers/ へ反映する。

### 7-3. manifest.jsonの役割

manifest.jsonは**実データの内容を重複保持しない索引**とする。

**v0.1で管理する項目：**

| 項目 | 説明 |
|---|---|
| schema_version | 使用schemaのバージョン（例：`0.1.0`） |
| case_id | 顧客名・個人名を含まない内部識別子（例：`CASE-ORG-001`） |
| registers | registerファイルパスと `last_updated_at`（RFC3339） |
| mtg_sessions | MTG session一覧（§7-4） |
| briefs | ブリーフファイルパスと `generated_at` |
| created_at | manifest初回作成日時 |

**manifestに持たせないもの：**

- Evidence／Hypothesis等の実データ本体
- 顧客名、個人名、実発言

**単一障害点リスク：**

- manifest破損時に全体の索引が失われるリスクがある。
- 対策：各registerファイルは自己完結的なID参照を持ち、
  manifestなしでもregister単体のvalidator検査は可能とする。
- manifestは「発見性・運用便利」のための索引であり、正本ではない。

### 7-4. MTG sessionとinput snapshot

**MTG session ID：** `MTG-YYYYMMDD-NNN`（例：`MTG-20260701-001`）

**input snapshotファイル：** `inputs/MTG-20260701-001.json`

input snapshotの必須項目（`mtg_input_snapshot.schema.json`）：

| 項目 | 説明 |
|---|---|
| mtg_session_id | MTG session ID |
| session_date | MTG日（YYYY-MM-DD） |
| session_started_at | 開始日時（RFC3339、タイムゾーン付き） |
| session_ended_at | 終了日時（RFC3339、任意） |
| input_files | 入力ファイル一覧（§7-4-1） |
| extraction_notes | 抽出時の補足（任意） |
| schema_version | 使用schemaバージョン |

**Evidence → MTG session の遡及参照（v0.1確定）：**

各Evidenceに `mtg_session_id` を必須とする。

| フィールド | 採否 | 理由 |
|---|---|---|
| `mtg_session_id` | **採用** | manifest・input snapshotとの参照が明確 |
| `source_snapshot_id` | 不採用（v0.1） | **mtg_session_idがinput snapshotの識別子を兼ねるため** |

### 7-4-1. input_filesの不変性（v0.1確定）

input snapshotは「不変」とするため、各 `input_files` 要素に次を必須とする。

| 項目 | 説明 |
|---|---|
| relative_path | `_org_diagnosis/` からの相対パス |
| source_form | original_audio / verbatim_transcript / summary_minutes 等 |
| content_sha256 | スナップショット取得時点のファイル内容ハッシュ |
| captured_at | ハッシュ取得日時（RFC3339） |
| size_bytes | ファイルサイズ（バイト） |

**validator責務（§18-2）：**

- Evidenceの `source_file` が、Evidenceの `mtg_session_id` に対応する
  input snapshotの `input_files[].relative_path` に存在すること。
- 検査実行時、実ファイルのhashが `content_sha256` と一致すること。
  不一致の場合は「入力がスナップショット以降に変更された」として警告する。

`source_snapshot_id` を追加する必要はない。
理由は1:1だからではなく、**mtg_session_idがinput snapshotの識別子を兼ねるため**である。

**同一Evidenceが複数入力ファイルにまたがる場合：**

- 1 Evidence = 1 mtg_session_id（抽出を行ったMTG session）。
- 文字起こしと議事録を併用する場合、**同一MTG session内の別source_file**として
  別Evidenceを起票する（corroborated event = 同一occurrence_key、別evidence_id）。
- 1 Evidenceに複数mtg_session_idは持たせない。

---

## 8. ID体系

### 8-1. prefix一覧（v0.1確定）

| 対象 | prefix | 例 |
|---|---|---|
| Evidence | `EVD-` | `EVD-20260701-001` |
| occurrence | `OCC-` | `OCC-20260515-001` |
| Pattern | `PAT-` | `PAT-001` |
| Hypothesis | `HYP-` | `HYP-001` |
| Causal edge | `CED-` | `CED-001` |
| Causal loop | `CLP-` | `CLP-001` |
| verification action | `ACT-` | `ACT-001` |
| MTG session | `MTG-` | `MTG-20260701-001` |
| case（manifest内部識別） | `CASE-ORG-` | `CASE-ORG-001` |

**禁止：** IDに顧客名、部署名、個人名を含めない。

### 8-2. 連番 vs UUID

| 観点 | 連番（prefix＋日付＋連番） | UUID |
|---|---|---|
| 人間可読性 | 高い | 低い |
| 衝突防止 | register内連番管理が必要 | 高い |
| diff可読性 | 高い（`EVD-20260701-003`が追加されたと分かる） | 低い |
| 複数MTG横断 | 日付入りIDで時系列が読める | 時系列が読めない |
| 実装コスト | manifestまたはregister内のlast_seq管理 | 生成のみ |

**v0.1判断：連番（prefix＋日付＋3桁連番）を採用する。**

- Evidence・occurrence・MTG session：日付入り（`EVD-YYYYMMDD-NNN`）。
- Pattern・Hypothesis・edge・loop・action：register内通し連番（`PAT-NNN`）。
  改訂時は新ID発行（設計メモ§12-1）のため、連番の使い回しはしない。

**JSON Schema pattern例：**

```
^EVD-[0-9]{8}-[0-9]{3}$
^OCC-(?:[0-9]{8}|UNKNOWN)-[0-9]{3}$
^PAT-[0-9]{3,}$
^HYP-[0-9]{3,}$
^CED-[0-9]{3,}$
^CLP-[0-9]{3,}$
^ACT-[0-9]{3,}$
^MTG-[0-9]{8}-[0-9]{3}$
```

### 8-3. IDの日付部分の意味と不変性（v0.1確定）

| prefix | 日付部分の意味 |
|---|---|
| `MTG-` | **MTG実施日** |
| `EVD-` | **Evidenceを抽出したMTG session日**（= 紐づく `mtg_session_id` の日付部分） |
| `OCC-` | **出来事の発生日**（判明している場合）。判明しない場合は `UNKNOWN` |

**ID不変規律：**

- すべてのIDは**発行後変更しない**。
- `OCC-UNKNOWN-001` の発生日が後から判明しても、**IDを改名しない**。
  判明した発生日は **`occurrence_date` に記録する**（§12-4）。`notes` は代替にしない。
- 改訂・棄却・再定義時も、**IDの使い回しを禁止**する（新IDを発行する）。

---

## 9. null／not_applicable／unknown

financial-analysis §1-1-5「欠落とゼロの区別」に対応する規律として、
本領域では**フィールド欠落と明示的nullを同一視しない**。

### 9-1. 4状態の定義（v0.1確定）

| 状態 | JSON表現 | 意味 |
|---|---|---|
| **フィールド欠落** | キー自体が存在しない | required項目なら**schema違反**。optionalなら「未使用」 |
| **明示的null** | `"field": null` | **まだ確認・レビューしていない** |
| **unknown** | `"field": "unknown"`（enum値） | **確認したが特定できなかった** |
| **not_applicable** | `{field}_applicability: "not_applicable"` | **その項目が適用対象外** |

**nullとunknownは重ねない：**

- `null` ＝ 未確認・未レビュー
- `unknown` ＝ 確認した結果、特定不能

### 9-2. applicability別フィールドの適用範囲

`{field}_applicability` は、**同一evidence_type内でも適用有無が変わる項目に限定**する。

| 項目 | applicability |
|---|---|
| `occurrence_key` 等 | **使用**（Pattern根拠か静的文書かで変わる） |
| REPORTEDのspeaker項目 | **不使用**（常に適用対象） |
| REPORTEDのelicitation_context | **不使用**（常に適用対象） |
| 非REPORTEDのspeaker項目 | **conditional schemaでフィールド自体を禁止** |

**REPORTEDのspeaker項目・elicitation_context：**

- 常に適用対象。`not_applicable` に**できない**。
- 分からない場合は `unknown`（speaker_category等）または
  `unattributed`（speaker_attribution_status）を使用する。

**非REPORTED Evidence：**

- speaker項目・elicitation_contextは**フィールド自体を持たせない**。
- evidence_type conditional schema（if/then）で禁止する。

### 9-3. required項目とnullの扱い

| 項目種別 | フィールド欠落 | 明示的null | unknown |
|---|---|---|---|
| 共通必須（evidence_id等） | schema違反 | schema違反（null不可） | 該当enum項目のみ可 |
| REPORTED必須（speaker_*等） | schema違反 | 許可（未確認を明示） | enum値として許可 |
| occurrence_key（applicable時） | schema違反 | 許可 | — |
| occurrence_key（not_applicable時） | applicabilityフィールド必須、値フィールド省略 | 値フィールド存在はschema違反 | — |
| optional項目 | 省略＝未使用 | null＝未確認 | enum値として許可 |

**善意に値を補完してschemaを通してはいけない。**

---

## 10. 日付・時刻・source pointer

### 10-1. 日付・時刻規則（v0.1確定）

| 用途 | 形式 | 例 |
|---|---|---|
| 日付のみ | `YYYY-MM-DD` | `2026-07-01` |
| 日時 | RFC3339（タイムゾーン必須） | `2026-07-01T14:30:00+09:00` |
| register更新 | RFC3339 | `last_updated_at` |
| Hypothesis作成・レビュー | RFC3339 | `created_at`, `last_reviewed_at` |

**デフォルトタイムゾーン：** `+09:00`（日本標準時）。
input snapshot・Evidenceのsource_dateは日付のみ、
session_started_at等はRFC3339とする。

### 10-2. source_pointer

source_pointerは**オブジェクト**とし、source_formに応じた型を持つ。

| source_form | source_pointer構造 |
|---|---|
| verbatim_transcript / original_audio | `{ "type": "timestamp", "start": "HH:MM:SS", "end": "HH:MM:SS" }` |
| summary_minutes | `{ "type": "minutes", "section": "...", "paragraph": N, "line": N }` |
| original_document | `{ "type": "document", "page": N, "item": "..." }` |
| observer_note | `{ "type": "note", "section": "..." }` |
| measured_raw | `{ "type": "measurement", "instrument": "...", "field": "..." }` |
| derived_summary | `{ "type": "derived", "source_evidence_ids": ["EVD-20260701-001"] }` |

**derived_summary：**

- `source_form=derived_summary` のEvidenceは、**元Evidenceへ遡れる** `source_pointer` を必須とする。
- `source_evidence_ids` に参照先Evidence IDを1件以上記録する。
- 元Evidenceへ遡れない derived_summary を認めない。

タイムスタンプはMTG session内の相対時刻（HH:MM:SS）とし、
絶対日時は `source_date` + `session_started_at`（input snapshot）から導出する。

---

## 11. Evidence schema方針

設計メモ§8の型別必須項目をJSON Schemaの `if/then`（conditional schema）で実装する。

### 11-1. 共通必須

evidence_id, evidence_type, mtg_session_id, source_file, source_date,
source_pointer, normalized_statement, source_form, review_status,
sensitivity, notes（notesは空文字可）

### 11-2. 型別conditional required

| evidence_type | 追加必須 |
|---|---|
| REPORTED | verbatim_excerpt, speaker_category, speaker_role_label, speaker_attribution_status, elicitation_context（すべて常に適用対象。§9-2） |
| DOCUMENTED | verbatim_excerpt, document_type, document_issuer |
| OBSERVED | observation_record, observer_category, observed_at |
| MEASURED | raw_measurement, instrument_name, instrument_version, measurement_date, population, value, unit |

非REPORTED Evidenceにspeaker項目・elicitation_contextを要求しない（conditional schemaで禁止）。

### 11-3. occurrence_key

| 条件 | occurrence_key |
|---|---|
| occurrence_pattern根拠の REPORTED/DOCUMENTED/OBSERVED | required（OCC- ID） |
| 静的DOCUMENTED / MEASURED | `occurrence_key_applicability: not_applicable` |
| 単発Evidence（Pattern根拠にしない） | optional（省略可） |

### 11-4. review_status=rejected

schema上は `review_status: rejected` を許可する（履歴保持）。
validatorが、rejected Evidenceの参照禁止を検査する（§18・§19）。

---

## 12. occurrence_key

### 12-1. 基本原則（v0.1確定）

**発言回数ではなく、出来事の発生単位にoccurrence_keyを付ける。**

occurrence_key（`OCC-YYYYMMDD-NNN`）は、
「組織内で一度発生した出来事」を表す識別子である。
同一出来事に対する複数Evidenceは、同一occurrence_keyを共有する（corroborated event）。

### 12-2. 場面別規則

| 場面 | occurrence_keyの付け方 |
|---|---|
| 同じ出来事を複数人が語った | **同一OCC**（corroborated event） |
| 同じ出来事が文字起こしと議事録に重複 | **同一OCC**、Evidenceは別ID |
| 1人が1回のMTGで過去3件の別事例を語った | **OCCを3件**（別事象） |
| 同じ種類の出来事が別の日に発生した | **OCCを別日付で別件** |
| 発生日が不明な過去事例 | `OCC-UNKNOWN-NNN`（日付不明プレフィックス） |

**発生単位を特定できない場合：**

- 複数OCCへ**善意に分割しない**。
- 1 OCCにまとめ、`notes` に「発生単位不明」と記録する。
- Pattern根拠に使用する場合は、validatorがdistinct occurrence_key数を検査する。

### 12-3. OCC-UNKNOWN の扱い

- 日付不明の過去事例用プレフィックス `OCC-UNKNOWN-` を設ける。
- 発生日が後から判明しても **IDは改名しない**（§8-3）。
  判明した発生日は **`occurrence_date` に記録する**（§12-4）。`notes` は代替にしない。
- Pattern成立時、OCC-UNKNOWN同士は**同一日の別件とみなさない**。
  2件以上のdistinct OCC-UNKNOWNが必要な場合、
  事象内容が異なることを `notes` に明記する（validatorは件数のみ検査）。

### 12-4. occurrence_date（v0.1確定）

出来事発生日の**構造化された正本**は `occurrence_date` とする。
`notes` は補足説明に使用できるが、`occurrence_date` の代替にはしない。

**追加理由：** `occurrence_key`（OCC- ID）の日付部分は発行時点の符号であり、
`OCC-UNKNOWN` から後日判明した発生日を構造化して保持するフィールドが設計メモに存在しなかった。
Evidenceの `source_date` は出典日であり、出来事発生日ではない。

| 項目 | 定義 |
|---|---|
| 所属 | Evidence item（`occurrence_key_applicability: applicable` の場合のみ） |
| 型 | string（`YYYY-MM-DD`）または `null` |
| 必須／任意 | **任意**（occurrence_keyが applicable のときのみ出現可） |
| null | **まだ確認・レビューしていない**（§9-1） |
| unknown（確認したが特定不能） | `occurrence_date` は設定しない。特定不能は `occurrence_key` の `OCC-UNKNOWN` プレフィックスで表現する |
| 判明後 | `occurrence_date` に `YYYY-MM-DD` を設定。**OCC- IDは改名しない** |

**既存フィールドとの関係：**

- `source_date`（Evidence）：出典資料の日付。出来事発生日ではない。
- `time_span`（Pattern）：反復期間。単一出来事の発生日ではない。
- 同一役割の既存フィールドはない。

---

## 13. Pattern schema方針

### 13-1. status語彙（v0.1確定）

Patternは解釈仮説ではなく**反復確認の状態**である。
Hypothesis statusをそのままコピーしない。

| status | 意味 |
|---|---|
| DRAFT | 起票直後。occurrence_key数等が未確認 |
| ACTIVE | 反復が確認された状態 |
| WEAKENED | 反復が弱まった、または反証が示された |
| REJECTED | 反復ではないと判断 |
| SUPERSEDED | 改訂・再定義により置き換え |

**採用しなかった語彙：** CONFIRMED（設計メモ§12と同理由）、TO_CONFIRM（Patternは仮説ではないため）。

### 13-2. 状態遷移（最小限）

```
DRAFT → ACTIVE / REJECTED
ACTIVE → WEAKENED / REJECTED / SUPERSEDED
WEAKENED → ACTIVE / REJECTED / SUPERSEDED
```

validator責務。schema上はenum定義のみ。

### 13-3. 必須項目

pattern_id, pattern_type（v0.1: `occurrence_pattern` のみ）,
claim, supporting_evidence_ids, supporting_occurrence_keys,
occurrence_count, time_span, scope, status, sensitivity, notes

schema：`supporting_occurrence_keys` の `minItems: 2`（distinct保証はvalidator）。

---

## 14. Hypothesis schema方針

設計メモ§10・§12の項目をそのままschema化する。状態enum・改訂フィールド含む。

### 14-1. status別Evidence件数（v0.1確定）

| status | supporting_evidence_ids | primary_supporting_evidence_ids |
|---|---|---|
| DRAFT | **空配列可** | **空配列可** |
| TO_CONFIRM | 1件以上 | 1件以上 |
| SUPPORTED | 1件以上 | **1〜3件**（同一Evidence verified条件適用） |
| WEAKENED | 既存根拠を保持 | 1件以上（弱化理由と併存） |
| REJECTED | rejection_evidence_ids必須 | — |
| SUPERSEDED | 既存履歴を保持 | 既存履歴を保持 |

**DRAFTの意味：**

- フレームワーク照合起点の気づき等、Evidence確認前の起票を許可する（設計メモ§14）。
- DRAFT段階でprimaryを必須にすると、この経路がschema上拒否されるため、空配列可とする。

REJECTED時の条件付き必須：rejection_reason, rejection_evidence_ids, last_reviewed_at

### 14-2. primary_supporting_evidence_idsの選定基準（v0.1確定）

**Evidence数の多さだけで選ばない。** TO_CONFIRM以降で選定する。

`primary_supporting_evidence_ids` は **1〜3件**（DRAFTは0件可、SUPPORTEDは1〜3件必須）。

**優先順位（上から適用）：**

| 順位 | 基準 | 説明 |
|---|---|---|
| 1 | 仮説claimとの直接性 | claimの核心を直接支持する記述 |
| 2 | review_status | verified > spot_checked > unreviewed |
| 3 | elicitation_context | spontaneous > open_question > unknown > leading_question |
| 4 | speaker_attribution_status（REPORTED） | verified > inferred > unattributed |
| 5 | source_form | original_audio/verbatim_transcript > summary_minutes > derived_summary |
| 6 | evidence_type | DOCUMENTED/OBSERVED/MEASURED（verified）はREPORTED（inferred）より優先 |
| 7 | 同一occurrence重複排除 | 同一occurrence_keyの複数Evidenceからは**最も優先度の高い1件**のみ |

**除外条件（primaryに選ばない）：**

- review_status=rejected
- speaker_category=consultant（顧客構造の主要根拠に不可）
- elicitation_context=leading_question かつ相槌・短い同意のみ
- exclude_from_org_diagnosis のEvidence

**SUPPORTED進行条件（設計メモ§12-3）との関係：**

- primary_supporting_evidence_ids のうち少なくとも1件が
  review_status=verified を満たす必要がある。
- REPORTEDの場合、**同一Evidence**で speaker_attribution_status=verified も必要。
- 選定基準とSUPPORTED条件は別：選定は「主要根拠の指名」、
  SUPPORTED条件は「指名されたEvidenceがverified要件を満たすか」の検査。

validatorが primary の件数・除外条件・SUPPORTED同一Evidence条件を検査する。

---

## 15. Causal schema方針

### 15-1. edge status（v0.1確定）

| status | 意味 |
|---|---|
| DRAFT | 起票直後 |
| TO_CONFIRM | 確認待ち |
| SUPPORTED | **現時点のEvidenceにより因果仮説が支持されている。ただし真実性を保証しない** |
| WEAKENED | 根拠が弱まった |
| REJECTED | 因果関係なしと判断 |
| SUPERSEDED | 改訂により置き換え |

形式条件（閉鎖性・polarity確定等）を示すのは **loop の VALID_FORM** であり、
edge の SUPPORTED ではない。

Hypothesisと同系統だが、Causal edgeは独立registerで管理する。

### 15-2. loop_candidate と loop の分離（v0.1確定）

凍結済み設計メモ§11では、形式不成立の構造を**loopとして登録・分類してはいけない**。
これに整合するため、`causal_type` を分離する。

| causal_type | status | 意味 |
|---|---|---|
| **loop_candidate** | DRAFT / INVALID_FORM / SUPERSEDED | 形式検査前または形式不成立の候補 |
| **loop** | VALID_FORM / SUPERSEDED | 形式条件を満たしたループのみ |

**通常ブリーフへのloop出力（v0.1確定）：**

通常の診断ブリーフへloopとして出力できるのは、
`causal_type=loop` かつ `status=VALID_FORM` の項目に限る。

**禁止：**

- `causal_type=loop` かつ `status=INVALID_FORM` — **認めない**
- INVALID_FORM または loop_candidate を通常ブリーフで **loopとして出力** — validator失格

**VALID_FORMの意味（設計メモ§11準拠・内容の真実性ではない）：**

- 全edgeに根拠がある
- 全edgeのpolarityが positive または negative
- polarity=unknown のedgeがない
- 閉じている
- negative edge数とreinforcing/balancing分類が一致

loop_candidateからloopへ進める条件：`status` が VALID_FORM に遷移可能な形式検査合格時のみ。
不合格の場合は loop_candidate のまま INVALID_FORM とする。

### 15-3. chain / hypothesis

- `causal_type: chain` — edge列。loop statusは持たない
- `causal_type: hypothesis` — 単一方向の因果仮説。edgeのみ

schema上は `causal.json` 内で `causal_type` により分岐する。

---

## 16. verification_action schema方針

### 16-1. 格納位置（v0.1確定）

**独立register（`registers/verification_actions.json`）を採用する。**

| 選択肢 | 長所 | 短所 | v0.1 |
|---|---|---|---|
| **独立register** | 複数MTG横断追跡、参照整合性検査、restricted_hr継承検査 | ファイル・schemaが1つ増える | **採用** |
| ブリーフ内構造化リスト | 初期実装が軽い | 継続追跡・横断参照が弱い | 不採用 |

**採用理由：**

- 設計メモ§22の2回MTG検証手順で、確認質問の実施→Hypothesis更新を追跡する必要がある。
- target_hypothesis_ids との参照整合性をvalidatorで検査できる。
- restricted_hr の継承を機械検査できる。

### 16-2. 必須項目

action_id, action_type, action_description, target_hypothesis_ids,
support_signal, weaken_signal, next_review_trigger, sensitivity,
created_at, mtg_session_id（起票元MTG）

### 16-3. v0.1で持たない項目

- 状態（未実施／実施中／完了／中止）→ §22未確定としてv0.2候補
- 実施結果 → 将来追加

---

## 17. sensitivity・強制除外

設計メモ§17をschema enumとして実装する。

| 値 | 順序 |
|---|---|
| internal | 低 |
| restricted_hr | 高 |
| exclude_from_org_diagnosis | **順序外・強制除外** |

**schema方針：**

- sensitivity enum: `internal` / `restricted_hr` / `exclude_from_org_diagnosis`
- exclude_from_org_diagnosis のEvidenceは、
  Pattern/Hypothesis/Causal/verification_action への参照を
  schema上は禁止できない（ID参照は文字列）ため、**validator責務**とする。

**継承規則（validator責務）：**

- Pattern/Hypothesis/Causal/verification_action の sensitivity は、
  根拠の最大 sensitivity を下回ってはならない。
- restricted_hr 継承の confirmation_questions / verification_action は
  通常ブリーフへ出力しない（brief_generator + validator）。

---

## 18. schemaとvalidatorの責務分離

### 18-1. JSON Schemaで検査するもの

- 型（string, number, object, array）
- enum値
- 必須項目（required）
- pattern（ID形式、日付形式）
- conditional required（if/then：evidence_type別、status別）
- 配列の最小件数（minItems）— status別条件は§14-1等参照
- null許可／不許可（type定義）
- applicabilityフィールドの整合（occurrence_key等、§9-2）
- register共通envelope（§5-3）
- `additionalProperties: false`（extensions除く）

### 18-2. validatorで検査するもの

- ファイル間参照整合性（ID存在確認）
- **ID重複**（register横断）
- Evidence → mtg_session_id → input snapshot存在
- **Evidence.source_file → input snapshot input_files存在**
- **input fileの現在hash ↔ content_sha256一致**
- Pattern → Evidence, Pattern → distinct occurrence_key（≥2）
- Hypothesis → Evidence, Hypothesis → Pattern
- Hypothesis → supersedes / superseded_by 双方向整合
- Hypothesis状態遷移の合法性
- **DRAFT Hypothesisの空配列許可、TO_CONFIRM以降の件数要件**
- SUPPORTEDの同一Evidence条件（primary_supporting_evidence_ids）
- primary_supporting_evidence_ids選定基準（件数・除外条件）
- rejected Evidenceの参照禁止
- exclude_from_org_diagnosisの参照禁止
- sensitivityの最大値継承
- **loop_candidate / loop の分離**（causal_type=loopかつINVALID_FORM禁止）
- **loop_candidateまたはINVALID_FORMを通常ブリーフでloopとして出力**
- Causal loop（VALID_FORM）の閉鎖性・polarity・reinforcing/balancing分類
- **derived_summaryのsource_evidence_ids存在**
- verification_action → Hypothesis参照
- 顧客情報境界（restricted_hrの通常ブリーフ出力禁止）
- corroborated event vs occurrence_pattern の区別

### 18-3. LLM／人間が確認するもの

- Evidence抽出の正確性
- 引用文脈・verbatim_excerptの妥当性
- 仮説の妥当性
- 誘導質問かどうか（elicitation_context判定）
- 新しい視点として価値があるか
- 裕司さんによる原音・原文照合

---

## 19. 参照整合性

将来のschema／validatorで機械的に保証する参照関係：

| 参照元 | 参照先 | 検査層 |
|---|---|---|
| Evidence | mtg_session_id → input snapshot | validator |
| Evidence | source_file → input snapshot input_files | validator |
| Evidence | derived_summary → source_evidence_ids | validator |
| Pattern | supporting_evidence_ids | validator |
| Pattern | supporting_occurrence_keys | validator（distinct ≥2） |
| Hypothesis | supporting_evidence_ids | validator |
| Hypothesis | primary_supporting_evidence_ids（status別件数） | validator |
| Hypothesis | supporting_pattern_ids | validator |
| Hypothesis | primary_supporting_evidence_ids ⊆ supporting_evidence_ids | validator |
| Hypothesis | supersedes / superseded_by | validator（双方向） |
| Causal edge | supporting_evidence_ids, supporting_hypothesis_ids | validator |
| loop（VALID_FORM） | edge_ids（全edge存在・閉鎖） | validator |
| loop_candidate | INVALID_FORM時のloop出力禁止 | validator |
| verification_action | target_hypothesis_ids | validator |
| 全register | sensitivity継承 | validator |
| 全register | rejected Evidence参照禁止 | validator |
| 全register | exclude_from_org_diagnosis参照禁止 | validator |

**JSON Schemaだけで保証できないものはすべてvalidator責務**とする。

---

## 20. v0.1で採用する判断

| # | 判断 | 採用値 |
|---|---|---|
| 1 | register保存形式 | JSON |
| 2 | ブリーフ保存形式 | Markdown（生成物） |
| 3 | 正本 | register（JSON） |
| 4 | ファイル構成 | 顧客master register + MTG input snapshot |
| 5 | manifest.json | 索引（内容非保持） |
| 6 | Evidence → MTG | mtg_session_id必須 |
| 7 | schema分割 | 9ファイル（common含む） |
| 8 | ID | prefix + 連番。OCC-UNKNOWN対応。発行後不変 |
| 9 | null規則 | 欠落≠null。null≠unknown。applicabilityはoccurrence_key等に限定 |
| 10 | 日付 | YYYY-MM-DD / RFC3339+TZ |
| 11 | occurrence_key | 出来事発生単位。OCC-UNKNOWN対応。ID不変 |
| 12 | Pattern status | DRAFT/ACTIVE/WEAKENED/REJECTED/SUPERSEDED |
| 13 | Causal edge status | DRAFT/TO_CONFIRM/SUPPORTED/WEAKENED/REJECTED/SUPERSEDED |
| 14 | Causal loop | loop_candidate（DRAFT/INVALID_FORM/SUPERSEDED）+ loop（VALID_FORM/SUPERSEDED） |
| 15 | JSON Schema | Draft 2020-12、register envelope、additionalProperties:false |
| 16 | input snapshot | content_sha256等で不変性を実体化 |
| 17 | derived_summary | source_pointer.type=derived + source_evidence_ids |
| 18 | DRAFT Hypothesis | supporting/primary空配列可 |
| 19 | verification_action | 独立register |
| 20 | primary選定 | 優先順位7段。TO_CONFIRM以降1〜3件 |
| 21 | measured_trend | v0.1対象外 |
| 22 | corroborated event | 全Evidence保持（統合しない） |

---

## 21. 採用しない案

| 案 | 不採用理由 |
|---|---|
| registerをYAML/Markdownで保持 | schema検証・参照整合性が弱い |
| ブリーフを正本とする | 継続診断・supersedes追跡が困難 |
| 単一巨大schema | 変更影響が大きく、段階的実装不可 |
| UUID ID | diff可読性・時系列読取が低い |
| not_applicableを値文字列で表現 | enum/nullと混同しやすい |
| verification_actionをブリーフ内のみ | 2回MTG検証手順に不十分 |
| measured_trendをv0.1に含める | 成立条件が未確定。MEASURED Evidenceは別途扱う |
| Hypothesis statusをPatternにコピー | Patternは反復確認であり仮説ではない |
| source_snapshot_id（mtg_session_idと併存） | mtg_session_idがinput snapshotの識別子を兼ねるため |
| causal_type=loopかつINVALID_FORM | 凍結済み設計メモ§11と矛盾。loop_candidateへ分離 |
| 1 Evidenceに複数mtg_session_id | 抽出単位が不明確になる |

---

## 22. schema段階で判明した新規論点

凍結済み設計メモを変更せず、schema設計中に新たに判明した論点。

### 22-1. applicability別フィールド方式

- **論点：** 設計メモ§8-6はnull/not_applicableを認めるが、
  JSON Schema上の表現方法は未定義だった。
- **v0.1判断：** `{field}_applicability` は occurrence_key 等、
  同一evidence_type内で適用有無が変わる項目に限定。
  REPORTEDのspeaker項目は常に適用対象（conditional schemaで非REPORTED禁止）。
- **将来見直し条件：** schema実装時にoneOf方式の方が簡潔と判明した場合。

### 22-2. loop_candidateの導入

- **論点：** schema初版では `causal_type=loop` + `INVALID_FORM` を認めていたが、
  凍結済み設計メモ§11（形式不成立をloopとして登録しない）と矛盾。
- **v0.1判断：** loop_candidate を新設し、INVALID_FORMはloop_candidateのみに置く。
- **将来見直し条件：** 初弾実案件でloop_candidate運用が過剰と判明した場合。

### 22-3. OCC-UNKNOWNプレフィックス

- **論点：** 発生日不明の過去事例のoccurrence_key表現が設計メモに明示されていなかった。
- **v0.1暫定判断：** `OCC-UNKNOWN-NNN` を導入。
- **将来見直し条件：** 初弾実案件で日付不明事例が多い場合、粒度規則を見直す。

### 22-4. brief_metadata.schema.json

- **論点：** ブリーフ生成物にも最低限のメタデータschemaが必要。
- **v0.1暫定判断：** frontmatter用schemaを追加（§6-2参照）。
- **将来見直し条件：** brief_generator実装時に本文構造schemaの要否を判断。

### 22-5. mtg_input_snapshot.schema.json

- **論点：** 設計メモ§23-6はmtg_pipeline接続を未確定としていたが、
  Evidence → MTG session参照にはinput snapshot定義が必要。
- **v0.1暫定判断：** 手動配置のinput snapshot schemaを定義。pipeline接続は未確定のまま。
- **将来見直し条件：** mtg_pipeline実装時に自動生成フィールドを追加。

### 22-6. 引き続き未確定とした事項

| 項目 | 状態 |
|---|---|
| measured_trend | v0.2候補 |
| mtg_pipeline.py自動接続 | 未確定 |
| 打合せDB接続 | 未確定 |
| verification_action状態管理 | v0.2候補 |
| 裕司さん例外承認の重み付け | 未確定 |
| 複数MTG差分自動生成 | 未確定 |
| validatorエラーコード体系 | 次工程 |
| register_snapshot_hash算法 | brief_generator実装時 |
| corroborated event代表Evidence統合 | v0.1は全件保持で確定。統合ルールは不要と判断 |

---

## 23. 次工程

schema設計メモv0.1確定後の実装順序（本コミットでは着手しない）：

1. `schemas/organization-diagnosis/common.schema.json` 作成
2. 各register schema作成（evidence → pattern → hypothesis → causal → verification_action）
3. manifest.schema.json / mtg_input_snapshot.schema.json 作成
4. `organization_diagnosis_validator.py` 骨格実装
5. 架空fixture作成（設計メモ§21 Case 1〜12）
6. validator unit test
7. brief_metadata.schema.json + 手動ブリーフ運用
8. スキル・eval（設計メモ§23完了条件の残り）

---

## 24. 完了条件

**本schema設計メモv0.1の完了条件：**

- [x] schema実装に必要な10判断が明示されている（§20）
- [x] 凍結済み設計メモを変更していない
- [x] measured_trendを善意に実装対象へ追加していない
- [x] 実顧客情報を使用していない
- [x] schemaとvalidatorの責務が分離されている（§18）
- [x] 未確定事項を勝手に埋めていない（§4・§22-5）
- [x] 次のschema実装指示へ落とせる粒度（§5 ID enum、§7 ファイル構成、§9 null規則、§23 次工程）

**次のゲート：** 本メモの通読確認 → 凍結 → DECISION記録 → schema JSON実装着手。

---

*本ファイルは organization-diagnosis v0.1 のschema設計判断メモです。
凍結済み設計メモ（`docs/organization-diagnosis_設計メモ_v0.1.md`）の正本ではありません。
JSON Schema実装の正本は将来 `schemas/organization-diagnosis/` 配下に置きます。*
