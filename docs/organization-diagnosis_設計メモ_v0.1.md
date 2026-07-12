---
status: frozen
version: 0.1
基準日: 2026-07-12
確定者: 小林裕司
改訂履歴: v0.1（初版）→ v0.1改訂（Evidence型別項目、source_form統一、occurrence_pattern／corroborated event分離、Hypothesis状態遷移・改訂操作、verification_action、§23未確定16項目統合）→ v0.1確定（Evidence型別管理、解釈の由来管理、Hypothesis状態遷移、因果表現の制約、秘匿性継承、validatorと人間確認の役割分担、未確定16項目のschema段階への送出）
---

# organization-diagnosis 設計メモ v0.1

> よい組織診断とは、もっともらしい構造を描くことではない。
> どの証拠から、どこまで言えて、どこから先は仮説なのかを追跡できることである。

financial-analysisでは、数値の由来と判定可能範囲を管理した。
organization-diagnosisでは、その考え方を「解釈の由来管理」へ展開する。

この領域には、financial_calc.pyのような決定論的な計算核は置けない。

代わりに、

- Evidence ledger
- Pattern register
- Hypothesis register
- Causal edge / loop register
- validator

によって、解釈までの追跡可能性と形式的一貫性を検査する。

ただし、validatorが保証するのは形式的な追跡可能性であり、
証拠内容の真実性や仮説そのものの正しさではない。

このスキルの存在価値は、形式的に整った診断ブリーフを作ることではなく、
裕司さんの見立てに、安全に新しい視点を加えることである。

---

## 1. 背景と目的

組織開発では、財務分析のように決定論的な計算結果を出すことはできません。

そのため、品質の中心を、

- 解釈が正しいように見えること
- フレームワークへきれいに当てはまること
- もっともらしい因果ループを描けること

には置きません。

品質の中心は、次に置きます。

- どの記述が確認済みのEvidenceか
- どの記述が複数Evidenceから確認されたPatternか
- どこからが構造仮説・メンタルモデル仮説か
- どの因果edgeがどのEvidenceに支えられているか
- どの範囲まで確認済みで、どこが未確認か
- 仮説がどのように支持・弱化・棄却・改訂されたか

この設計の目的は、組織の構造を断定することではなく、
証拠・解釈・未確認事項を分離した内部診断ブリーフを作ることです。

financial-analysis基盤を参照元とし、
organization-diagnosisはその「解釈版」として位置づけます。

---

## 2. financial-analysisから継承する設計原則

financial-analysis（`.claude/skills/financial-analysis/SKILL.md`、
`docs/financial-analysis_指標定義書_v0.2.md`、`financial_calc.py`、DEC-005〜007）から、
次の原則を継承します。

- 正本を一本化する
- 定義やフレームワーク本文をスキルへ複製しない
- 入力の由来を明示する
- 正式判断できる条件と、参考・暫定扱いの条件を分ける
- 不明な入力を善意に補完しない
- 未確認事項は未確認のまま表示する
- 実顧客データをPublicリポジトリへ保存しない
- 機械検査と人間確認の役割を分ける
- 顧客提示版の最終確定は裕司さんが行う

financial-analysisにおける「数値の由来管理」に対応するものが、
organization-diagnosisにおける「解釈の由来管理」です。

**概念対応（TO_CONFIRMをformal相当として扱わない）：**

| 観点 | financial-analysis | organization-diagnosis |
|---|---|---|
| 入力の由来 | scheduled、actual_proxy、missing 等 | Evidence type、speaker attribution、elicitation context 等 |
| 判断可能範囲 | formal条件を満たす | Hypothesisの状態進行条件を満たす（SUPPORTED等。§12参照） |
| 未確定・参考 | screening_only | DRAFT、TO_CONFIRM |
| 出典追跡 | calculation trace、出典照合 | source_pointer、verbatim_excerpt、review_status |
| 人間確認後の内部採用 | 小林レビュー | SUPPORTED／WEAKENED等への更新＋裕司さん確認 |

TO_CONFIRMは「確認待ちの仮説」であり、financial-analysisのformal判定に相当する正式判断ではありません。

---

## 3. 組織診断固有の本質的な違い

財務分析では、正しい入力が与えられれば、
計算核によって計算結果の再現性を高められます。

組織診断では、Evidenceが揃っていても、
仮説そのものの真実性を機械的に保証できません。

また、Evidence ledgerに出典IDが付いていても、

- Evidenceの内容自体が誤って抽出されている
- Whisper文字起こしが不正確である
- 話者帰属が間違っている
- 発言者の認識が事実と異なる
- 要約時に文脈が失われている

可能性があります。

したがって、validatorは真実判定装置ではありません。

validatorは、

- 必須項目
- 参照整合性
- 状態管理
- 因果表現の形式
- 出典への追跡可能性
- 保存境界
- 禁止事項

を確認するものとします。

財務分析における検算の対応物は、
組織診断では出典照合です。

証拠IDがあること自体を、
証拠内容が正しいことの保証として扱ってはいけません。

---

## 4. v0.1の対象範囲

v0.1は次に限定します。

**入力：**

- MTG文字起こし
- MTG議事録
- 必要に応じ、思考特性診断・行動スタイル診断・欲求プロフィール等の集計値

**処理：**

- 証拠抽出
- 出来事と反復Patternの整理
- 構造仮説・メンタルモデル仮説の作成
- 確認質問の作成
- 小さな検証案の作成
- 適切な設計OS・専門業務へのルーティング

**出力：**

- 顧客提示用の最終診断書ではなく、裕司さん確認用の内部診断ブリーフ

v0.1では、次を自動確定しません。

- 顧客への正式な診断結果
- 介入の実行判断
- 顧客向けスライド
- 研修設計
- 人事制度設計
- 個別労務案件への対応方針
- ハラスメント、不調、懲戒、個別評価等の判断
- 顧客への説明文言
- 組織のメンタルモデルの断定
- 経営判断

---

## 5. 対象外

次はorganization-diagnosis v0.1の対象外とします。

- 個人の心理診断
- 医学的・臨床的な診断
- ハラスメント事実認定
- メンタル不調の判定
- 懲戒判断
- 個人評価
- 法的責任の判断
- 労務トラブルへの対応方針確定
- 研修カリキュラムの完成
- 人事制度の完成
- 顧客提示版の確定
- 介入施策の自動実行
- 経営判断の代行

対象外の情報が含まれる場合は、
一般的な組織構造へ丸めて吸収せず、
別業務へルーティングしてください（§16参照）。

---

## 6. 正本・参照庫・顧客データの役割分担

**grow3-frameworks.md：**

- 理論・フレームワークの唯一の正本
- SSR、7S、システム思考、因果ループ、構造原型等の定義元

**organization-diagnosis設計メモ／将来のOS：**

- 診断の手順
- Evidence管理
- Pattern管理
- Hypothesis管理
- 因果edge管理
- 出力契約
- 安全規律
- 他OSへのルーティング

**grow3-training-design-os.md：**

- 研修・ワークショップの設計手順
- organization-diagnosisの出口候補の一つ

**grow3-hr-system-design-os.md：**

- 人事制度の設計手順
- organization-diagnosisの出口候補の一つ

**Notion：**

- 書籍DB
- 一般化した事例庫
- 過去コンテンツ
- 一般化された質問例
- 匿名化・抽象化された知見
- 索引

**Dropbox顧客フォルダ：**

- 実際の文字起こし
- 議事録
- Evidence ledger
- Pattern register
- Hypothesis register
- Causal register
- 内部診断ブリーフ
- 仮説更新履歴

**Public GitHub：**

- 方法論
- schema
- validator
- 架空fixture
- test
- skill
- eval

実顧客の企業名、個人名、発言、組織構造、数値、Dropbox実パス等は、
Public GitHubへ保存しません。

フレームワークの定義本文を本設計メモへ複製しないでください。
必要な場合は `grow3-frameworks.md` の該当項目を参照してください（`[→F:…]` 記法）。

---

## 7. 入力契約

v0.1の標準入力を、MTG文字起こしまたはMTG議事録に固定します。

必要に応じて、診断結果の集計値を追加できます。

**1回のMTGあたりの処理量の目安：**

| 種別 | 目安 |
|---|---|
| Evidence | 10〜20件 |
| Pattern（occurrence_pattern） | 最大5件 |
| 構造仮説・メンタルモデル仮説 | 合計1〜3件 |
| 因果ループ | 0〜1件 |
| 確認質問 | 5〜8件 |
| 小さな検証案（verification_action） | 最大3件 |

網羅性を目標にしません。
意思決定に重要なEvidence・Pattern・Hypothesisへ絞ります。

「必ずループを作る」は禁止です。
閉じた構造にならない場合は、因果連鎖仮説のままとしてください。

入力ファイルに話者分離がない場合、
話者を善意に推定して確定しないでください。

---

## 8. Evidence ledger

Evidenceは、少なくとも次の種類を持たせます。

| evidence_type | 意味 |
|---|---|
| REPORTED | 関係者が発言した内容 |
| DOCUMENTED | 規程、組織図、制度資料等、文書自体に記載された内容 |
| OBSERVED | 裕司さんまたは担当者が直接観察した内容 |
| MEASURED | 診断、アンケート、数値等による測定結果 |

**原則：測定値は証拠であって、意味づけは仮説である。**

MEASUREDから、因果、性格、関係性、組織文化等へ直接飛躍してはいけません。

### 8-1. Evidence共通項目

全Evidence共通の必須項目：

| 項目 | 説明 |
|---|---|
| evidence_id | 一意ID |
| evidence_type | REPORTED／DOCUMENTED／OBSERVED／MEASURED |
| source_file | 出典ファイル（Dropbox内） |
| source_date | 出典日 |
| source_pointer | 位置ポインタ（§8-8） |
| normalized_statement | 正規化した記述 |
| source_form | 出典の物理形態（§8-9） |
| review_status | レビュー状態（§8-9） |
| sensitivity | 秘匿性（§17） |
| notes | 補足 |

occurrence_patternの根拠として使用する場合は、後述の `occurrence_key` も使用します。

### 8-2. REPORTED固有項目

REPORTEDに必須とする項目：

- verbatim_excerpt
- speaker_category
- speaker_role_label
- speaker_attribution_status
- elicitation_context

**speaker_category（正式値）：** client_manager / client_member / consultant / unknown

**speaker_role_label：** 分かる場合に限り営業部長、店舗管理者、管理職A等。分からない場合は `unknown`。

**speaker_attribution_status：**

| 値 | 意味 |
|---|---|
| verified | 原音、議事録等から話者を確認済み |
| inferred | 会話の流れ等から推定 |
| unattributed | 話者を特定できない |

Whisper文字起こしでは話者分離ができない場合があるため、
speaker_categoryやspeaker_role_labelを常に確定できる前提にしません。

裕司さんその他コンサルタント側の発言は `speaker_category: consultant` として区別します。
consultantの発言そのものは、顧客組織の構造仮説を支持するEvidenceとして原則使用しません。
質問、要約、仮説提示、確認等の会話文脈として扱います。

**elicitation_context：**

| 値 | 意味 |
|---|---|
| spontaneous | 顧客側から自発的に語られた |
| open_question | 開かれた質問への回答 |
| leading_question | 仮説や答えを含む誘導的な質問への回答 |
| unknown | 判定不能 |

leading_questionへの相槌・短い同意だけを、
構造仮説やメンタルモデル仮説の主要根拠にしてはいけません。

### 8-3. DOCUMENTED固有項目

DOCUMENTEDに必須とする項目：

- verbatim_excerpt
- document_type
- document_issuer

**分類基準：**

議事録に記載されていても、内容が誰かの発言であればREPORTEDとして扱います。
DOCUMENTEDは、規程、組織図、制度資料、方針文書等、文書自体の内容をEvidenceとする場合に使用します。
議事録に書かれているという理由だけで、主観的な発言をDOCUMENTEDへ格上げしてはいけません。

### 8-4. OBSERVED固有項目

OBSERVEDに必須とする項目：

- observation_record
- observer_category（consultant / client_observer / external_observer / unknown）
- observed_at

### 8-5. MEASURED固有項目

MEASUREDに必須とする項目：

- raw_measurement
- instrument_name
- instrument_version
- measurement_date
- population
- value
- unit

診断結果、サーベイ、件数、比率等の測定値はEvidenceです。
測定値から意味づけへ移る場合は、Hypothesisとして分離してください。

### 8-6. 適用対象外項目

Evidence type上、適用しない項目は、善意に `unknown` を埋めないでください。
`null` または `not_applicable` を正式に認めます。

REPORTED以外のEvidenceに、話者項目やelicitation_contextを無条件に要求しないでください。

### 8-7. occurrence_key

`occurrence_key` は、出来事の反復を示す occurrence_pattern を形成するための識別子です。

occurrence_patternの根拠として使用する REPORTED／DOCUMENTED／OBSERVED Evidence には、
`occurrence_key` を必須としてください。

ただし、DOCUMENTEDであっても、規程・組織図・制度資料等の静的な文書内容であり、
出来事の発生単位を表さない場合は `not_applicable` を認めます。

MEASUREDは原則として `occurrence_key` を `not_applicable` とします。

**同一 `occurrence_key` を持つ複数Evidenceは、corroborated eventとして扱い、反復Patternとは扱いません。**

### 8-8. 出典ポインタ

REPORTED／DOCUMENTEDでは、出典からの逐語引用と位置ポインタを必須とします。

- 音声・文字起こし：タイムスタンプ
- 議事録：見出し、段落、行番号
- 資料：ファイル名、ページ、該当項目
- 診断データ：診断名、バージョン、測定日、対象人数、値、単位

### 8-9. source_formとreview_status

**`source_quality` という名称は使用せず、`source_form` へ統一します。**
**`transcript_unverified`、`transcript_verified` は廃止します。**

**source_form 候補：**

- original_audio
- verbatim_transcript
- summary_minutes
- original_document
- observer_note
- measured_raw
- derived_summary

**review_status：**

- unreviewed
- spot_checked
- verified
- rejected

次のように、source_formとreview_statusの組合せで表現します。

例：`source_form: verbatim_transcript` / `review_status: spot_checked`

**比例原則：**
仮説を強く支えるEvidenceほど、原音・原文照合の優先度を高くします。
重要な構造仮説やメンタルモデル仮説を支えるEvidenceは、
裕司さんによる原音・原文の抜き取り照合を優先してください。

**review_status=rejected のEvidence：**

履歴・監査記録として残しますが、次のいずれにも使用してはいけません。

- Patternの成立根拠
- Hypothesisの支持Evidence
- primary_supporting_evidence_ids
- counter_evidence
- alternative hypothesisの根拠
- Causal edge / loopの根拠
- verification_actionの根拠
- 介入案の根拠

rejected Evidenceは、支持にも反証にも使用できません。

---

## 9. Pattern register

§9のPatternは、原則として **occurrence_pattern** を扱います。

occurrence_patternは、単発の発言や出来事と分離します。

**occurrence_patternと呼べる条件：**

- 複数のEvidenceがあるだけではなく、**distinctな occurrence_key が2件以上**ある
- 異なる時点、場面、人物等で反復している
- 反復範囲が記録されている

同じ出来事を複数の人物・資料が語っている場合、Evidenceは複数でも単一occurrenceです。
これは **corroborated event** であり、Patternではありません。

**必須項目案：**

| 項目 | 説明 |
|---|---|
| pattern_id | 一意ID |
| pattern_type | v0.1では occurrence_pattern を基本 |
| claim | Patternの記述 |
| supporting_evidence_ids | 根拠Evidence |
| supporting_occurrence_keys | distinctな occurrence_key（2件以上） |
| occurrence_count | 確認回数 |
| time_span | 反復期間 |
| scope | 対象範囲 |
| status | 状態（語彙・遷移は§23未確定） |
| sensitivity | 根拠Evidenceの最大sensitivityを継承（§17-3） |
| notes | 補足 |

MEASURED単独では、出来事や行動の反復を意味する occurrence_pattern を成立させてはいけません。

離職率、サーベイ得点、確認件数等の異なる測定時点における数値傾向は、
**measured_trend** として occurrence_pattern と分離してください。
measured_trendをv0.1へ含めるか、Pattern register内の別種別とするか、別registerとするかは、
§23の未確定事項として扱います。

単発の発言は event / single_report / isolated_observation 等としてEvidence側に残し、
反復Patternであるかのように表現してはいけません。

---

## 10. Hypothesis register

Hypothesisは次の層を持たせます。

- structure（構造仮説）
- mental_model（メンタルモデル仮説）

構造・メンタルモデルは、事実ではなく仮説です。

氷山モデルの4層（`grow3-frameworks.md` 参照）へ、
最初からすべてを埋めることは禁止します。
できごととPatternを整理した後に、構造・メンタルモデルを仮説として起票してください。

**必須項目案：**

| 項目 | 説明 |
|---|---|
| hypothesis_id | 一意ID |
| layer | structure / mental_model |
| claim | 仮説の記述 |
| supporting_evidence_ids | 関連する支持Evidence全体 |
| primary_supporting_evidence_ids | 状態進行を判断する主要根拠 |
| supporting_pattern_ids | 根拠Pattern |
| counter_evidence_review | 反証検討（§10-2） |
| alternative_hypothesis_review | 代替仮説検討（§10-3） |
| status | DRAFT／TO_CONFIRM／SUPPORTED／WEAKENED／REJECTED／SUPERSEDED |
| sensitivity | 根拠の最大sensitivityを継承（§17-3） |
| confirmation_questions | 確認質問 |
| next_review_trigger | 次回レビュートリガー |
| created_at | 作成日時 |
| last_reviewed_at | 最終レビュー日時 |
| supersedes | 置き換え元hypothesis_id |
| superseded_by | 置き換え先hypothesis_id |
| revision_reason | 改訂理由 |

**REJECTED時の条件付き必須項目：**

- rejection_reason
- rejection_evidence_ids
- last_reviewed_at

### 10-1. supporting Evidence

`supporting_evidence_ids` は、Hypothesisに関連する支持Evidence全体を記録します。

`primary_supporting_evidence_ids` は、そのHypothesisの**状態進行を判断する主要根拠**を記録します。

`review_status=rejected` のEvidenceは、いずれにも含めてはいけません。

### 10-2. counter_evidence_review

反証情報は「存在」を必須にせず、「検討したこと」を必須とします。

| status | 意味 |
|---|---|
| found | 反証を確認した |
| none_found_in_reviewed_sources | 確認した範囲では見つからなかった |
| not_reviewed | 未検討 |

必須サブ項目：status、reviewed_sources、note

validatorが失格とするのは、反証が見つからないことではなく、
検討状態や確認範囲が記録されていないことです。

`review_status=rejected` のEvidenceはcounter_evidenceとして使用できません。

### 10-3. alternative_hypothesis_review

| status | 意味 |
|---|---|
| considered | 代替仮説を検討した |
| none_identified_after_review | 確認した範囲では特定できなかった |
| not_reviewed | 未検討 |

必要に応じて：reviewed_sources、alternatives、note

存在しない反証や代替仮説を、要件充足のために創作してはいけません。
「見つからなかった」と書く場合は、確認範囲を追跡可能にしてください。

### 10-4. confirmation_questions

confirmation_questionsは、所属するHypothesisのsensitivityを継承します。

restricted_hrを継承したconfirmation_questionsは、通常の内部診断ブリーフへ出力しません。

exclude_from_org_diagnosisの情報を確認するためのconfirmation_questionsは、
organization-diagnosis内では作成しません。
別業務へのルーティング情報としてのみ扱ってください。

---

## 11. Causal edge / loop register

因果関係は、まずedge単位で管理します。

**必須項目案：**

| 項目 | 説明 |
|---|---|
| edge_id | 一意ID |
| from_variable | 起点変数 |
| to_variable | 終点変数 |
| polarity | positive / negative / unknown |
| delay | none / possible / confirmed / unknown |
| supporting_evidence_ids | 根拠Evidence |
| supporting_hypothesis_ids | 根拠Hypothesis |
| status | 状態（語彙・遷移は§23未確定） |
| sensitivity | 根拠の最大sensitivityを継承（§17-3） |
| notes | 補足 |

因果edgeは、原則としてHYPOTHESISとして扱います。

**ループと呼べる条件：**

- 全edgeに根拠がある
- 全edgeのpolarityが positive または negative で確定している
- **polarity=unknown のedgeが含まれていない**
- 最初の変数へ戻り、閉じている
- 強化ループまたはバランスループとして成立する

polarity=unknown のedgeを1件でも含む場合は、loopとして登録・分類できません。
その場合は causal_chain または causal_hypothesis に留めてください。

**loop分類規則：**

- negative edgeが偶数：reinforcing
- negative edgeが奇数：balancing

閉じていないものは causal_chain / causal_hypothesis として扱い、loopとは表記しないでください。

因果関係が確認できていない要素を、
説明の見栄えをよくするために矢印で結んではいけません。

「同時に起きている変化」と「根拠が紐づいた因果仮説」を区別してください。

---

## 12. 仮説の状態遷移

**Hypothesisの正式な状態：**

- DRAFT
- TO_CONFIRM
- SUPPORTED
- WEAKENED
- REJECTED
- SUPERSEDED

**CONFIRMEDは使用しません。**

**REVISEDは状態として使用しません。**
REVISEDは**改訂操作**として扱います（§12-1）。

**基本的な進行：**

```
DRAFT → TO_CONFIRM → SUPPORTED / WEAKENED / REJECTED / SUPERSEDED
```

状態遷移は一方向の階段ではありません。少なくとも次を認めます。

- TO_CONFIRM → SUPPORTED / WEAKENED / REJECTED / SUPERSEDED
- SUPPORTED → WEAKENED / REJECTED / SUPERSEDED
- WEAKENED → SUPPORTED / REJECTED / SUPERSEDED

### 12-1. 改訂操作

仮説を改訂する場合は、次の方式とします（REVISEDは操作名であり、statusではない）。

1. 新しい hypothesis_id を発行する
2. 旧仮説を SUPERSEDED へ変更する
3. 旧仮説の superseded_by へ新IDを記録する
4. 新仮説の supersedes へ旧IDを記録する
5. 新仮説は DRAFT または TO_CONFIRM から開始する
6. revision_reason に改訂理由と新Evidenceを記録する

旧仮説を上書きして履歴を消してはいけません。

### 12-2. REJECTED仮説の再起票

REJECTEDとなったHypothesisを、REJECTEDからTO_CONFIRM等へ直接遷移させてはいけません。

新しいEvidenceによって棄却済み仮説が再浮上した場合は、**改訂操作**として新しい hypothesis_id を発行してください。

- 新仮説の supersedes に旧REJECTED仮説のIDを記録する
- 旧仮説の superseded_by に新仮説のIDを記録する
- 新仮説は DRAFT または TO_CONFIRM から開始する
- revision_reason に再起票理由と新Evidenceを記録する

旧REJECTED仮説は削除・上書きしません。

### 12-3. SUPPORTEDへの進行条件

speaker_categoryが `unknown`、または speaker_attribution_statusが `unattributed` のEvidenceのみを根拠とする仮説は、TO_CONFIRMより先へ進めません。

Hypothesisを SUPPORTED へ進める場合は、**primary_supporting_evidence_ids のうち、少なくとも1件のEvidenceが review_status=verified であること**を必須とします。

その verified Evidence 自体が REPORTED である場合は、**同一Evidenceが speaker_attribution_status=verified も満たす必要**があります。

**別々のEvidenceを組み合わせてSUPPORTED条件を満たしたことにはしません。**

例（不可）：

- Evidence A：review_status=verified、speaker_attribution_status=inferred
- Evidence B：review_status=spot_checked、speaker_attribution_status=verified

→ 組み合わせても SUPPORTED 条件を満たさない。

REPORTEDを主要根拠とする場合は、**同一Evidence**において、

- review_status=verified
- speaker_attribution_status=verified

の両方を満たしてください。

DOCUMENTED、OBSERVED、MEASUREDの場合は speaker_attribution_status を要求しませんが、
**同一の主要Evidenceが review_status=verified を満たす必要**があります。

裕司さん確認前に SUPPORTED を正式判断として扱ってはいけません。

### 12-4. REJECTEDへの進行条件

Hypothesisを REJECTED へ変更する場合は、少なくとも次を必須とします。

- rejection_reason
- rejection_evidence_ids
- last_reviewed_at

rejection_evidence_ids には、棄却判断の根拠となったEvidenceを記録してください。
`review_status=rejected` のEvidenceを、Hypothesisを棄却する根拠として使用してはいけません。

REJECTEDへの変更は、単なる印象や帰属不明の伝聞1件だけで行わないでください。

裕司さん確認前に REJECTED を最終確定として扱ってはいけません。

---

## 13. 診断プロセス

| Step | 内容 |
|---|---|
| Step 0 | 意思決定の問いを定義する（次回MTGで何を確認するか、研修が必要か、権限設計が論点か、追加ヒアリングが必要か、現時点では介入しない方がよいか 等） |
| Step 1 | フレームワークを使わずEvidenceを抽出する（SSR、7S、構造原型、思考特性等で内容を補完しない） |
| Step 2 | 出来事とPatternを整理する（単発Evidence、corroborated event、occurrence_patternを分離） |
| Step 3 | 構造・メンタルモデルの仮説を作る（根拠、主要根拠、反証検討、代替仮説検討、確認質問をセット） |
| Step 4 | 因果edgeを作る（条件を満たす場合だけloop化。閉じていない、またはpolarity不明な場合は causal_chain / causal_hypothesis のまま） |
| Step 5 | SSR・7S・構造原型等で照合する（必須適用しない。§14） |
| Step 6 | 検証可能な次の一手を作る（verification_action。§15-1） |
| Step 7 | 適切なOS・業務へルーティングする（§16） |

---

## 14. フレームワークの参照規律

SSR、7S、構造原型、思考特性、行動スタイル、欲求プロフィール等は、
仮説を生成するための必須チェックリストではなく、
作成済みの仮説を照合するレンズとして使用します。
定義の正本は `grow3-frameworks.md` です。

**正式な選択肢：**

- 該当フレームなし
- 情報不足のため照合不能
- 複数フレームに部分的に該当
- 現時点ではフレーム適用不要

フレームワークを使うために、
顧客が語っていない因果やメンタルモデルを補完してはいけません。

照合中に新しい構造や論点へ気づくこと自体は認めます。
ただし、照合によって生じた気づきを、そのまま診断結果やTO_CONFIRM仮説へ追加してはいけません。
照合起点の気づきは、まず DRAFT 仮説として起票してください。

その後、通常の仮説と同じく、

- Evidenceの抽出
- Patternの確認
- supporting_evidence_idsの紐付け
- primary_supporting_evidence_idsの選定
- 反証検討
- 代替仮説検討

を経た場合のみ TO_CONFIRM へ進めてください。

---

## 15. 出力契約

**内部診断ブリーフの標準構成：**

1. 分析目的
2. 対象資料
3. 確認済みEvidence
4. corroborated event
5. 反復Pattern
6. 構造仮説・メンタルモデル仮説
7. 各仮説の根拠・主要根拠
8. 反証検討・代替仮説検討
9. 因果連鎖または因果ループ
10. 未確認事項
11. 次回MTGの確認質問
12. 小さな検証案（verification_action）
13. 推奨ルーティング
14. 裕司さん確認欄

顧客提示用の断定表現は使用しません。

「この組織は○○である」ではなく、

- ○○の可能性がある
- 現時点のEvidenceでは○○が示唆される
- ○○かどうかを次回確認する
- 現時点では判断できない
- 別の仮説も残っている

という書き方を基本とします。

内部診断ブリーフも、裕司さんの確認前に正式判断として扱ってはいけません。

### 15-1. verification_action

§13 Step 6 および内部診断ブリーフの「小さな検証案」は、**verification_action** として構造化します。

v0.1では、新たな独立registerを確定せず、**内部診断ブリーフ内の構造化リスト**として扱う案とします（独立register化は§23未確定）。

**最低限の項目：**

| 項目 | 説明 |
|---|---|
| action_id | 検証案の一意ID |
| action_type | confirmation_question / small_experiment / additional_interview / data_collection / observation |
| action_description | 実際に何を行うか |
| target_hypothesis_ids | どのHypothesisを検証するための行動か |
| support_signal | 何が確認されればHypothesisが支持される方向へ動くか |
| weaken_signal | 何が確認されればHypothesisが弱まる、または棄却される方向へ動くか |
| next_review_trigger | いつ、または何が起きた時点で結果を確認するか |
| sensitivity | 対象Hypothesisから継承した秘匿レベル（§17-3） |

organization-diagnosis v0.1では、介入の実行判断ではなく**仮説検証**が目的です。
正式名称は verification_action または「検証案」とします。

### 15-2. 確認質問の設計規律

確認質問は、仮説を直接肯定させる形ではなく、**開かれた形**を基本とします。

**避ける例：**

- 判断基準が共有されていないから、確認が集中しているのですよね
- 管理職が部下を信用していないということですか
- 制度に問題があると思いませんか

**推奨例：**

- 判断が上司へ戻るのは、どのような場面が多いですか
- 部下へ任せる際、どのような基準を共有していますか
- 確認が必要な仕事と、本人判断で進められる仕事はどう分かれていますか
- 最近、同じようなことが起きた具体的な場面はありますか

開かれた確認質問への回答は `elicitation_context=open_question` として記録し、
Hypothesis更新のEvidenceとして使用できます。

ただし、質問文自体が開かれていても、直前にコンサルタントが仮説を断定的に提示している場合は、
会話全体として leading_question に相当する可能性があります。
elicitation_contextの判定では、質問の一文だけでなく、直前の要約・仮説提示を含む会話文脈も確認してください。

仮説文言をそのまま提示して同意を求めた回答や、
leading_questionへの相槌・短い同意は、
Hypothesisを SUPPORTED へ進める主要根拠には使用できません。

---

## 16. 他OS・他業務へのルーティング

**出口候補：**

- training-design（`grow3-training-design-os.md`）
- hr-system-design（`grow3-hr-system-design-os.md`）
- 業務プロセス・権限設計
- 経営者・幹部との対話
- 追加ヒアリング
- 追加データ収集
- 現時点では介入しない
- 社労士業務・労務対応
- 法務対応
- 健康・メンタルヘルス対応

個別のハラスメント、不調、懲戒、個人評価等を、
組織開発上の一般論へ吸収してはいけません。

個別対応の緊急性がある場合は、
組織診断を止め、別経路へルーティングしてください。

研修や人事制度は、組織診断の自動的な出口ではありません。
EvidenceとHypothesisから研修・制度が適切な介入であると判断できない場合は、
追加確認／業務設計／対話／現時点では介入しない を選択できるようにします。

---

## 17. 秘匿性・匿名化・保存境界

顧客内部のEvidenceには、従業員個人に関する情報が含まれる可能性があります。

内部ブリーフでも、原則として実名を使用せず、役割ラベルで記録します。

役割ラベルは実名回避の措置であり、完全な匿名化を保証するものではありません。
小規模組織等では役割ラベルから本人を識別できる可能性があるため、
役割ラベル化した情報も秘匿性が低下したものとして扱ってはいけません。

### 17-1. 通常の秘匿レベル

通常の秘匿レベルの順序：**internal < restricted_hr**

| 値 | 扱い |
|---|---|
| internal | 通常の内部診断対象。通常の内部診断ブリーフへ出力可能 |
| restricted_hr | 一般の組織診断ブリーフへ出力しない |

### 17-2. 強制除外値

**exclude_from_org_diagnosis は、通常の秘匿レベルの最上位ではありません。**
組織診断処理への使用を禁止する、**順序外の強制除外値**です。

exclude_from_org_diagnosis のEvidenceは、次のいずれにも使用してはいけません。

- Pattern形成
- Hypothesis形成
- counter_evidence
- alternative hypothesis
- Causal edge / loop形成
- confirmation_questions作成
- verification_action作成
- 通常ブリーフへの出力

別業務へのルーティング情報としてのみ保持してください。

### 17-3. sensitivityの継承規則

| 対象 | 継承ルール |
|---|---|
| Pattern | 支持Evidenceの最も高いsensitivityを継承 |
| Hypothesis | 支持Evidence／Patternの最も高いsensitivityを継承 |
| Causal edge / loop | 根拠Evidence／Hypothesisの最も高いsensitivityを継承 |
| confirmation_questions | 所属Hypothesisのsensitivityを継承 |
| verification_action | target_hypothesis_ids の最大sensitivityを継承 |

複数Hypothesisを対象とする場合も、秘匿レベルの低い方へ**緩和してはいけません**。

restricted_hrを継承した次の情報は、通常ブリーフへ出力しません。

- Hypothesis
- confirmation_questions
- verification_action（action_description、support_signal、weaken_signalを含む）
- Causal edge / loop
- Pattern

exclude_from_org_diagnosis を参照する verification_action は、**作成自体を禁止**します。

### 17-4. 保存境界

| 場所 | 保存してよいもの |
|---|---|
| Public GitHub | 方法論、schema、validator、架空fixture、test、skill、eval |
| Dropbox顧客フォルダ | 実Evidence、文字起こし、議事録、各register、診断ブリーフ、仮説更新履歴 |
| Notion | 匿名化・一般化した事例、索引、再利用可能な質問、一般化された知見 |

Notionへ事例化する場合は、役割ラベル化だけでは不十分です。
役職・業種・組織規模の抽象化、日付・地域・固有制度の削除、発言の一般化等を行い、
再識別できない状態にした場合のみ保存可能とします。

実名、生の個人発言、健康情報、懲戒情報等は、Notionへ保存しません。

---

## 18. validatorが保証すること／保証しないこと

### validatorが保証できるもの

- 必須項目の存在
- Evidence、Pattern、Hypothesis、Causal edgeの参照整合性
- source_pointerの存在
- review状態の記録
- 仮説の状態遷移
- 因果loopの閉鎖性
- polarityによるloop分類
- 反証・代替仮説を検討した記録
- 顧客情報境界に関する禁止パターン
- 出力契約の形式
- unattributedな話者Evidenceだけで仮説を過度に進めていないこと
- restricted_hr情報を通常ブリーフへ出していないこと
- exclude_from_org_diagnosisが組織診断処理へ使用されていないこと
- SUPPORTED条件が**同一Evidence**で満たされていること

### validatorが保証できないもの

- 引用内容が真実か
- 発言者が正しい認識を持っているか
- Whisper文字起こしが正確か
- 話者推定が正しいか
- 仮説が実際の組織構造を正しく表しているか
- 介入案・検証案が成功するか
- 顧客にとって受け入れ可能か
- 役割ラベルから個人を再識別できないか
- 顧客提示時の適切性

財務分析における検算の対応物として、
組織診断では出典照合を必須とします。

---

## 19. 機械検査項目

将来のvalidatorで検査する候補を、Evidence type別の条件付きで整理します。

### 19-1. 全Evidence共通

- Evidence ID重複
- evidence_type欠落
- source_file欠落
- source_date欠落
- source_pointer欠落
- normalized_statement欠落
- source_form欠落
- review_status欠落
- sensitivity欠落
- review_status=rejected のEvidenceが支持・反証・Pattern・Causal edge等へ参照されている
- exclude_from_org_diagnosis のEvidenceが組織診断処理へ参照されている

### 19-2. REPORTED

REPORTEDにおいて検査する項目：

- verbatim_excerpt欠落
- speaker_category欠落
- speaker_role_label欠落（確認できない場合は unknown を認める）
- speaker_attribution_status欠落
- elicitation_context欠落
- leading_questionへの相槌だけを主要根拠にしている
- consultant発言だけで顧客構造仮説を支持している

**REPORTED以外のEvidenceに、話者項目やelicitation_contextがないことを理由としてvalidatorエラーにしてはいけません。**

### 19-3. DOCUMENTED

- verbatim_excerpt欠落
- document_type欠落
- document_issuer欠落

### 19-4. OBSERVED

- observation_record欠落
- observer_category欠落
- observed_at欠落

### 19-5. MEASURED

- raw_measurement欠落
- instrument_name欠落
- instrument_version欠落
- measurement_date欠落
- population欠落
- value欠落
- unit欠落
- MEASUREDから人格、文化、因果へ直接飛躍している
- MEASUREDだけでoccurrence_patternを成立させている

### 19-6. Pattern

- supporting_evidence_ids不足
- distinctな supporting_occurrence_keys が2件未満
- 同一occurrenceの複数EvidenceをPattern扱いしている
- rejected EvidenceがPattern根拠に含まれている
- sensitivity継承が根拠Evidenceより低い
- exclude_from_org_diagnosisがPattern形成に使われている

### 19-7. Hypothesis

- HypothesisにEvidence参照がない
- mental_model仮説が事実表現になっている
- counter_evidence_reviewがnot_reviewedのまま最終出力されている
- alternative_hypothesis_reviewが未記載
- reviewed_sourcesが空欄
- rejected Evidenceがsupporting_evidence_idsへ含まれている
- rejected Evidenceがcounter_evidenceへ含まれている
- SUPPORTEDなのにprimary_supporting_evidence_idsがない
- SUPPORTEDなのに、同一主要Evidenceで必要条件を満たしていない
- REPORTEDを主要根拠とするSUPPORTED仮説で、同一Evidenceが review_status=verified かつ speaker_attribution_status=verified を満たしていない
- DOCUMENTED／OBSERVED／MEASUREDを主要根拠とするSUPPORTED仮説で、同一Evidenceが review_status=verified を満たしていない
- **REVISEDをHypothesisのstatusとして使用している**
- REJECTEDなのにrejection_reasonがない
- REJECTEDなのにrejection_evidence_idsがない
- rejection_evidence_idsにreview_status=rejectedのEvidenceが含まれている
- REJECTEDなのにlast_reviewed_atが更新されていない
- REJECTEDからTO_CONFIRM等へ直接復活している
- 照合レンズ起点の仮説がEvidence確認なしでTO_CONFIRMになっている
- sensitivity継承が根拠Evidence／Patternより低い

### 19-8. Causal edge / loop

- 因果edgeに根拠がない
- polarity未記載
- polarity=unknownを含む構造をloopとして登録している
- 閉じていない構造をloopとして登録している
- negative edgeの数とreinforcing／balancing分類が一致しない
- rejected EvidenceがCausal edge根拠に含まれている
- sensitivity継承が根拠より低い
- exclude_from_org_diagnosisがCausal edge / loop形成に使われている

### 19-9. verification_action・confirmation_questions

- verification_actionにaction_idがない
- verification_actionにtarget_hypothesis_idsがない
- support_signalがない
- weaken_signalがない
- next_review_triggerがない
- restricted_hrのHypothesisに属するconfirmation_questionsが通常ブリーフへ含まれている
- restricted_hrのHypothesisを対象とするverification_actionが通常ブリーフへ含まれている
- verification_actionのsensitivityがtarget Hypothesisの最大sensitivityより低い
- exclude_from_org_diagnosisのEvidenceまたはHypothesisを対象としてverification_actionが作成されている

### 19-10. 顧客情報境界

- restricted_hr情報が一般ブリーフへ含まれている
- exclude_from_org_diagnosis情報が通常出力されている
- 実名らしき文字列が含まれている
- 顧客名、Dropbox実パス、実案件ログ等がfixtureへ混入している

氏名検出、再識別可能性、文脈上の誘導性等は完全には機械検出できません。
最終的な人間確認が必要であることを明記します。

---

## 20. LLMルーブリックと失格条件

### ルーブリック候補

- 事実と仮説が分離されている
- Evidenceから言える範囲を超えていない
- 単発EvidenceをPattern扱いしていない
- corroborated eventとPatternを区別している
- 代替仮説を検討している
- 反証情報を無理に創作していない
- rejected Evidenceを支持・反証に使っていない
- フレームワークを当てはめすぎていない
- 照合レンズから生まれた気づきをEvidence確認なしで採用していない
- 確認質問が実務で使用できる
- 確認質問が誘導的でない
- verification_actionがHypothesisと接続している
- support_signal／weaken_signalが検証可能である
- 個人の責任追及ではなく構造を扱っている
- 対象外案件を適切にルーティングしている
- 話者帰属の不確実性を適切に扱っている
- 誘導質問への同意を強いEvidenceとして扱っていない
- restricted_hr情報を間接的にも漏らしていない
- 裕司さんの確認前に顧客向け断定をしていない

### 失格条件

1. 語られていないメンタルモデルを断定する
2. 根拠のない因果edgeを作る
3. 閉じていないものをloopと表示する
4. polarity=unknownを含む構造をloopとして分類する
5. 反証・代替仮説を要件充足のために創作する
6. rejected Evidenceを支持または反証に使用する
7. すべてのケースへSSR・7S等を強制適用する
8. MEASUREDから因果や人格特性へ直接飛躍する
9. MEASUREDだけでoccurrence_patternを作る
10. 個別労務案件を組織開発へ吸収する
11. restricted_hr情報を通常ブリーフへ出力する
12. restricted_hrのconfirmation_questionsやverification_actionを通常ブリーフへ出力する
13. exclude_from_org_diagnosisをPattern、Hypothesis、Causal edge、verification_actionへ使用する
14. 顧客提示版または実行判断を裕司さん確認なしで確定する
15. 実顧客情報をPublicリポジトリへ保存する
16. unattributedな発言だけで仮説をSUPPORTED等へ進める
17. consultant側の発言を顧客構造の主要Evidenceとして使用する
18. 誘導質問への相槌だけでメンタルモデルを推定する
19. フレームワーク照合で生まれた仮説を証拠確認なしで採用する
20. REVISEDをHypothesisのstatusとして使用する
21. REJECTED仮説を履歴なしに直接復活させる
22. SUPPORTED条件を別々のEvidenceの組合せで形式的に満たす
23. 実顧客情報を架空fixtureへ転用する

---

## 21. 架空fixtureの設計

将来のfixtureはすべて架空ケースとします。

| Case | 目的 |
|---|---|
| Case 1 | 上司への確認集中・抱え込み。一部Evidenceから構造仮説を作れる |
| Case 2 | 単発の不満発言だけでPattern化してはいけない |
| Case 3 | 診断データはあるが、因果を断定できない |
| Case 4 | 因果連鎖は作れるが、閉じたloopにはならない |
| Case 5 | ハラスメント・不調等が含まれ、別経路へルーティングすべき |
| Case 6 | 既存仮説が次回MTGでWEAKENED／REJECTEDとなる、または改訂操作で新IDへ置き換えられる継続診断 |
| Case 7 | Whisper文字起こしで話者が不明 |
| Case 8 | コンサルタントの誘導質問への相槌を、顧客の自発的Evidenceとして扱ってはいけない |
| Case 9 | 7S照合中に新仮説へ気づくが、Evidence未確認のためDRAFTに留める |
| Case 10 | 同じ一件の出来事を複数人・複数資料が語っているが、Patternにはならない（corroborated event） |
| Case 11 | restricted_hrのHypothesisから確認質問・検証案が生成されるが、通常ブリーフへ出してはいけない |
| Case 12 | rejected Evidenceを支持・反証・棄却根拠へ使用してはいけない |

実顧客の数値、発言、組織名、役職構成を、そのままfixtureへ転用しないでください。

---

## 22. 初弾実案件での検証手順

**初弾ユースケース：**
顧問先のMTG文字起こし・議事録から、裕司さん確認用の内部診断ブリーフを作る。
可能な限り、同一顧問先の連続する2回のMTGを対象とします。

**検証手順：**

1. 1回目のMTG記録から初回診断ブリーフを作成する
2. 次回MTGで確認質問を実際に使用する
3. 2回目のMTG記録を追加する
4. HypothesisをSUPPORTED／WEAKENED／REJECTEDへ更新する
5. 改訂が必要な場合は、旧仮説をSUPERSEDEDとし、新IDでDRAFT／TO_CONFIRMを起票する（改訂操作。§12-1）
6. 棄却・改訂理由を記録する
7. supersedes／superseded_byの接続を確認する
8. 1回目と2回目の差分を確認する

**検証するもの：**

- 事実と仮説が分離できたか
- 発言にない因果を創作していないか
- 次回MTGで使える確認質問を作れたか
- 確認質問が誘導的になっていないか
- 次回MTG後にHypothesisを更新できたか
- 作成・確認時間が実務上許容できるか
- 裕司さんの見立てへ新しい視点を加えられたか
- 話者不明Evidenceを過大評価していないか
- 誘導質問への同意を過大評価していないか
- restricted_hr情報を通常ブリーフへ出していないか

**人間による価値評価：**

- 確認質問のうち、実際に使用した、または使用価値があると判断した割合
- 裕司さんが「自分では明確に捉えていなかった」と感じた構造仮説があったか
- 「もっともらしいが、Evidenceからは言えない」と感じた仮説がなかったか
- 次回MTG後に状態更新を無理なく行えたか
- 最初から裕司さん自身で作る場合より、確認・修正時間が短かったか

初弾では割合目標を固定せず、実測値を基準線とします。

**最低合格条件：**

- 裕司さんにとって新しい気づきが1件以上ある
- 根拠のない因果・メンタルモデルの断定が0件である

---

## 23. v0.1の完了条件

**将来のv0.1完了条件候補：**

1. 設計メモ確定
2. schema確定
3. validator実装
4. validator unit test成功
5. 架空fixture作成
6. スキル作成
7. smoke test成功
8. LLM eval成功
9. 初弾実案件での内部検証
10. 裕司さんによる価値評価
11. 実顧客情報がPublicリポジトリにないことを確認
12. 必要なDECISION記録
13. git statusクリーン

**今回（2026-07-12改訂）の到達点：**
上記のうち「設計メモの作成・改訂」のみ。
schema、validator、fixture、スキル、test、evalは作成しない。

### 未確定事項（v0.1設計メモ時点・本節に統合）

以下は善意に推測して確定しません。選択肢、長所、短所、次工程で決める論点のみを記載します。

#### 1. 各registerの保存形式（JSON／YAML／Markdown／ハイブリッド等）

| 選択肢 | 長所 | 短所 |
|---|---|---|
| JSON | validator・schemaとの親和性が高い | 人間可読性が低い |
| YAML | 構造化＋コメント可能 | インデント事故、大規模diffの可読性 |
| Markdown（frontmatter＋本文） | ブリーフと一体で読める | 参照整合性の機械検査が弱い |
| ハイブリッド（register=JSON/YAML、ブリーフ=Markdown） | 機械検査と人間可読性を分離 | 同期ルール・ファイル数の設計が必要 |

#### 2. Dropbox顧客フォルダ内の配置規約

| 選択肢 | 長所 | 短所 |
|---|---|---|
| `_org_diagnosis/` サブフォルダ | 発見しやすい | 既存MTG・財務フォルダとの命名要調整 |
| MTG資料と同階層 | 出典とregisterが近い | 継続診断の横断参照が弱い |
| 顧問契約単位の `組織診断/` トップ | 継続案件向き | 1MTG作業との距離 |

#### 3. 1顧客1ファイルか、MTG単位のファイルか

| 選択肢 | 長所 | 短所 |
|---|---|---|
| 1顧客1register（追記型） | superseded_by追跡が一箇所で完結 | ファイル肥大化 |
| MTGごとスナップショット | 作業単位が明確 | 横断統合ルールが必要 |
| 顧客マスタ＋MTGデルタ | 両方の利点 | マージロジックが複雑 |

#### 4. 複数MTG時の追記・版管理・更新方法

- Evidence追記のみか、訂正・rejectedも許すか
- Hypothesis更新はインプレースか、新ID＋superseded_byか（設計上は後者推奨、ファイル運用は未確定）
- ブリーフの版番号を付けるか
- 差分の自動生成か手動比較か

#### 5. 内部診断ブリーフと各registerの正本関係

| 選択肢 | 長所 | 短所 |
|---|---|---|
| ブリーフはregisterから生成 | 正本がregisterに集約 | 生成パイプラインが必要 |
| ブリーフとregisterを独立保持＋validator整合 | 初期実装がシンプル | ズレリスク |
| ブリーフのみ（register埋込） | 閲覧が簡単 | 継続更新・検査が弱い |

#### 6. mtg_pipeline.py・打合せDBとの接続方法

- grow3-knowledge内に `mtg_pipeline.py` および打合せDBの実装は**現時点で存在しない**（2026-07-12確認）
- 自動取込／手動エクスポート／将来MCP等は未確定
- 暫定：Dropboxから手動で入力契約に載せる

#### 7. Pattern registerのstatus語彙と状態遷移

- active／deprecated／superseded 等の候補
- Hypothesis状態との連動要否

#### 8. Causal edge / loop registerのstatus語彙と状態遷移

- draft／confirmed／rejected 等の候補
- loopとchainで語彙を分けるか

#### 9. measured_trendをv0.1へ含めるか

- 含める：数値傾向も診断の入力として扱える
- 含めない：occurrence_patternに集中し、v0.2以降へ延期

#### 10. measured_trendの配置と成立条件

- Pattern register内の別 pattern_type とするか
- 別registerとするか
- 成立条件：測定回数、測定間隔、同一母集団性、instrument versionの一致等

#### 11. verification_actionを独立registerとするか

- 独立register：継続追跡・状態管理しやすい
- ブリーフ内構造化リスト（v0.1案）：実装が軽い

#### 12. verification_actionの状態管理

- 未実施／実施中／完了／中止等を持たせるか
- v0.1では状態なしでよいか

#### 13. occurrence_keyの粒度

- 例：1人が1回のMTGで過去3件の異なる事例を語った場合、occurrenceを3件と数えるか
- 同一場面・同一事象の再言及と、別事象の連続発言の境界

#### 14. 同一出来事の複数証言・複数資料の統合ルール

- 文字起こし、議事録、観察記録等の重複をどう扱うか
- corroborated eventの代表Evidenceを1件にまとめるか、全件保持か

#### 15. primary_supporting_evidence_idsの選定基準

- 最も review_status が高いEvidenceを選ぶか
- 最も elicitation_context が spontaneous に近いものを選ぶか
- 複数主要根拠を許すか1件に限定するか

#### 16. 帰属確度とHypothesis進行条件について、将来的な重み付け・例外承認を設けるか

- 現行：同一Evidenceでの verified 充足を硬直ルールとする
- 将来：複数弱Evidenceの合成、裕司さんによる例外承認フラグ等を設けるか

---

*本ファイルは organization-diagnosis v0.1 の設計メモです。フレームワーク定義の正本は `grow3-frameworks.md` です。schema・validator・skillの実装正本ではありません。*
