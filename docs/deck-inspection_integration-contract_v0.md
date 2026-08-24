---
status: approved
version: v0
基準日: 2026-08-22
種別: integration-contract
domain: deck-inspection
確定者: 小林裕司（2026-08-22承認：暫定確定案①〜③・判断事項6件・v0-draft-3全変更）
見直し: DEFERRED_BY_CONTRACT／EVIDENCE_PENDING の解消時に該当節を改訂する（改訂は standards-authoring 工程を最初から適用する）
改訂履歴: v0-draft-1（初稿）→ v0-draft-2（レポート所有境界の4区分分離・H1/H2分割・版系列分離・未解決3分類・R7）→ v0-draft-3（GATE集約の出力元別語彙化・必須検査2集合分割・統合処理責任・第2層exception_id方式・B4/E1統合・R8）→ v0（B1〜B4 CLOSED・§8.2有効結果条項追記・§13 V5実行失敗記録追記・正本化）
---

# Deck Inspection Integration Contract v0

## 0. 文書管理

- 名称：Deck Inspection Integration Contract v0（確定版）
- 承認記録：暫定確定案①〜③、6件の判断事項、v0-draft-3の全変更を小林裕司が2026-08-22に承認。v0-draft-3の別コンテキスト差分レビュー合格済み。B1〜B4はすべてCLOSED（§13）。
- 現物確認済み事実（B4・2026-08-22）：
  - ZIP：`office-artifact-validation-v0.1.0.zip`
  - SHA-256：`697b17e340c088287753470303f65f814b767aebde7cd38492e210f01104b0db`
  - Schema version：`0.1`（validation-common `$defs/schema_version` の const）
  - TOOL_VERSION：`0.1.0`（engine.py）
  - check_id：enum固定・計31件（invariant 10／heuristic 7／contract 9／system 5）
- 上位参照：Deck Inspection 接続表（Step 0）v0.6（停止資料・本リポジトリ未収録。矛盾・不足の指摘一覧は接続表側の課題として別管理）／A7 `scripts/pre-delivery-check.sh`＋`scripts/pre-delivery-intentional-uncertainty.tsv`／A8 `.claude/agents/training-reviewer.md`／A9 `schemas/organization-diagnosis/common.schema.json`
- 関連文書：第1層一式 `skills/office-artifact-validation/`（由来は同ディレクトリのPROVENANCE.md）／E2照合記録 `docs/deck-inspection_e2-check-catalog-layer-allocation.md`／V2マッピング表 `docs/deck-inspection_v2-check-id-mapping.md`

## 1. 目的・適用範囲・用語

本Contractは、研修デッキ検品（deck-inspection）の責任構造・check_id体系・レポート所有境界・実行契約・配置と盲検隔離を定める。接続表§2の8決定点に対応する。

**スコープ外**：Learning Design Review（§11で予約のみ）。第1層一式のリポジトリ投入作業そのもの（§9に工程のみ定める）。実装の内部設計（本ContractはContract上の所有境界・決定・決定手続きのみを定める）。

**用語**：

- **preflight**＝pre-delivery-check.sh（リポジトリ投入の入口検査）
- **第1層**＝office-artifact-validation runner による構造検査（機械判定・ValidationReport出力）
- **第2層**＝deck-inspector（読取専用エージェント）による内容・設計整合検査
- **CONSULT／GATE**＝第2層の2実行モード（助言／出荷判定）
- **DeckInspectionReport**（仮称）＝第1層・第2層の結果を統合する外側レポート。4区分構造＋最小メタデータ（§4）
- **統合処理**＝DeckInspectionReportを組み立てる外側の処理。個別検査の判定は生成・改変せず、集約規則に従うgate_status生成とレポート間整合検査を担う（§2）
- **deck-contract／revision-vN／known-exceptions**＝全案件共通基準／案件・版固有基準／承認済み恒常例外の3台帳。known-exceptionsは**第2層 `exception_id` 方式の正本**（§8）
- **identity束**＝スライド同定キーの束（slide_id・revision_hint・類似度キー・並び順）
- **BLOCKING／DEFERRED_BY_CONTRACT／EVIDENCE_PENDING**＝未解決事項の3状態分類（§13）

## 2. 責任構造（決定点1）

「preflight＋2検査層」で構成する。「3層」とは呼ばない。

| 段 | 実体 | 判定水準 | 出力 |
|---|---|---|---|
| preflight | pre-delivery-check.sh（--staged） | テキスト水準（検知語・台帳照合・公開禁止パターン・stagedのOffice抽出検査） | 終了コード 0／1（FAILで投入不可） |
| 第1層 | office-artifact-validation runner | 機械判定可能な構造・表記・整合 | ValidationReport（Schema 0.1・第1層が所有） |
| 第2層 | deck-inspector | 内容・設計整合・意味判断 | deck_inspection_results（第2層専用Schemaが所有） |
| 統合処理 | DeckInspectionReport組み立て | 下記責任文のとおり | DeckInspectionReport（gate_status・integration_errors含む） |

**統合処理の責任**：統合処理は個別検査の判定を生成・改変しない。Contractに定めた集約規則（§8）に従ってgate_statusを生成し、レポート間の整合性を検査する。

**境界文**：第1層は機械判定可能な検査のみを担い、内容の設計整合・意味判断を行わない。第2層は第1層の対象外宣言に列挙された領域と設計整合を担い、第1層と同一観点の重複判定を行わない。
→ 境界文の妥当性はcheck-catalog 31件の層割り当て照合で検証する（EVIDENCE_PENDING-E2。照合記録は `docs/deck-inspection_e2-check-catalog-layer-allocation.md`）。

## 3. check_id体系（決定点2）

**確定（承認済み）：ハイブリッド方式を採用する。**

- **機械判定系**（必須語・禁止語・枚数・残留・派生関係）：既存 `contract.*`（9件・0.x間互換性非保証）のうち**意味が一致するものだけ再利用**。破棄も全引き取りもしない。
- **デッキ固有レビュー**（答え漏洩・設計意図・講師ノート整合 等）：`deck.*` を新設。
- **意味一致の判定手続き（3点照合）**：①判定対象 ②判定方法 ③判定結果の意味、の3点がcheck-catalog現物と一致する場合のみ再利用。1点でも異なれば `deck.*` 新設とする。
- **deck.\* 採番規則**：A9先例（prefix＋定義の一箇所管理）に準拠。`deck.<カテゴリ>.<名称>` 形式・英小文字・ドット区切り。カテゴリ語彙は個別マッピングと同時に確定。0.x間互換性非保証の方針を継承。
- **所有の分離**：`deck.*` の結果は第2層専用Schema（`deck_inspection_results`）に置く。**既存ValidationReportのcheck_id enumやcheck_class制約へ適合させない**（§4）。

→ 個別マッピング表は **DEFERRED-V2**（`docs/deck-inspection_v2-check-id-mapping.md`）。照合結果の証拠部分は EVIDENCE_PENDING-E3。

## 4. レポート所有境界と意味対応（決定点3）

### 4.1 DeckInspectionReport の最小構造（4区分＋最小メタデータ）

| 区分 | 内容 | 所有者 |
|---|---|---|
| `structural_validation_report` | 第1層が生成した既存ValidationReport。**外側からフィールド・値を変更しない** | 第1層（Schema 0.1） |
| `deck_inspection_results` | 第2層の `deck.*` 結果。判定、check_id、証拠、スライド位置、confidence、判定不能理由などを保持。承認済み例外の適用時は `exception_id` を付与（§8） | 第2層専用Schema（既存ValidationReportとは別のSchema所有） |
| `gate_status` | 第1層と第2層の結果を外側で集約した状態（§8） | 統合処理 |
| `integration_errors` | 原因結果の欠落、レポート間不整合、入力参照不整合、例外参照不整合など、統合処理が検出したエラー | 統合処理 |

`summary.blocked` の所有者は**第1層のみ**である。統合処理はこれを再計算・上書きしない（検証はR7）。

**最小メタデータ**：DeckInspectionReportは4区分に加えて最低限次を持つ。フィールド型・詳細SchemaはDEFERRED-V5の決定範囲に残す。

- `schema_version`
- `mode: CONSULT | GATE`
- `run_id`
- currentファイルの参照情報とSHA-256
- baseline使用時の参照情報とSHA-256
- deck-contract／revision-vN／known-exceptionsのバージョンまたはhash
- 第1層runner・第2層deck-inspector・統合処理のバージョン
- 実行日時

### 4.2 判定語彙の所有と意味対応表（説明用）

- **PASS／WARN／FAIL／ERROR／SKIP**は第1層ValidationReportの語彙である。
- **PASS／REVIEW／FAIL／UNVERIFIABLE**は第2層 `deck_inspection_results` の語彙である。
- 以下の意味対応表は**説明用**であり、格納仕様ではなく、**GATE集約の入力変換にも使用しない**（集約は§8で出力元別に直接定義する）。

| 第2層判定 | 意味上の近縁（第1層語彙） |
|---|---|
| PASS | PASS |
| REVIEW | WARN（意味＝人の判断が必要・不変） |
| FAIL | FAIL |
| UNVERIFIABLE | SKIP（insufficient_data） |

同一検査でFAILとREVIEWが両立するケースも、第2層専用Schemaで表現する（既存Schemaに背負わせない）。

### 4.3 Schema 0.1を版上げしない根拠（確定）

- gate_statusは外側（DeckInspectionReport）にある
- `deck.*` は第2層専用Schemaにある
- FAILとREVIEWの両立も第2層専用Schemaで表現する

したがって、既存ValidationReportの版上げ条件（①gate_statusの既存Report内格納 ②新check_id追加 ③同一検査のFAIL・REVIEW両立）へ**構造的に到達しない**。

前提の裏づけ（B4・現物確認済み）：check_idはvalidation-common Schemaのenumが機械的正本（enum固定）。statusは5値。check_classごとの許容statusはSchemaのallOf条件分岐で機械担保。構造を持つ全オブジェクトは `additionalProperties: false`（意図的な自由領域は `finding.evidence`・`expected`／`actual`・`run.environment` のみ）。**前提との差異はなかった**が、仮に将来の現物確認で差異が出た場合でも、レポート所有境界の分離は維持し、改訂対象は本節の根拠記述および現物事実に依存する箇所に限定する。

## 5. 案件基準の継承（決定点4）

**振り分け規則**：全案件・全版で不変→deck-contract／案件・版に依存→revision-vN／基準違反だが承認済み→known-exceptions（**第2層 `exception_id` 方式の正本**・§8）。

**deck-contract 初版リスト**：

1. 投影フォント基準：本文24pt中心・最小18pt・注記14〜16pt〔出典区分：**記録由来**（A5）〕
2. A4点検8項目の意味系＋「後方から読めるか」原則〔出典区分：**記録由来**（A4）〕
3. ノートと投影本文の分離〔合意済み・§6のスナップショット構造と整合〕

**revision-vN（案件固有）初版候補**：用語対照表／匿名化／二段階開示／答え漏洩条件／グループ構成。

**出典条項（手続き確定済み）**：A4・A5由来の基準には出典区分「記録由来（正本ファイル未特定）」を付す。**criteria-schema着手前まで**既存正本を探索し（EVIDENCE_PENDING-E5）、見つからない場合は接続表v0.6の記録由来文から正本候補を作成し、小林裕司の**再承認日以降**その文書を新正本とする。いずれの場合も「記録由来・旧正本未特定」という来歴は残す（DEFERRED-D4）。

## 6. スナップショット形式（決定点5）

**構造契約**：source（元ファイル参照＋hash）＋canvas本文／table／grouped／notesの分離＋identity束。

**抽出要件（3点・必須）**：①表・グループは再帰走査 ②実効フォントは継承解決 ③PDF側フォント名は判定根拠に使用禁止。

**正規化規則**（Unicode・全半角・空白・記号・走査順・ノート管理ラベル）は**本Contractで机上確定しない**。決定手続きのみ契約化する：**調整用版対（9/3 WSスライドの多版系列・§10）**の実スナップショットで規則候補を比較し、意味のない差分ノイズが最小となる組を採用して追補する（DEFERRED-V3）。**JFE盲検版対を調整に使用してはならない。**

## 7. 版間照合＋confidence（決定点6）

- identity束による照合。優先順位：slide_id → revision_hint → 類似度 → 並び順。
- **スライド番号キー単独での照合は禁止**（根拠：JFE v8の40枚→45枚系列で番号キー不成立の実例）。
- confidenceは3段階。名称・各キーの一致閾値・`unmatched`→REVIEWの条件は、**調整用版対および事前検証用版対（§10）**での試行で決定する（DEFERRED-V4）。**JFE盲検版対を閾値調整に使用してはならない。**

## 8. CONSULT／GATE実行契約（決定点7）

### 8.1 起動時検証（GATE）

必須検査集合は**所有者別に2本**持つ。

```text
GATE.required_structural_check_ids
  ⊆ structural_runner.implemented_check_ids
GATE.required_deck_check_ids
  ⊆ deck_inspector.implemented_check_ids
```

- 既存 `contract.*` 再利用分はstructural側、新設 `deck.*` はdeck側に属する。
- 両方について、必須設定・必要入力の充足を起動時に検証する。
- いずれかの包含関係または必須設定が成立しなければ、設定・能力不整合として **ERROR停止**する。
- 能力台帳による一元化は採用しない。

### 8.2 集約規則（出力元別の直接定義・評価順序＝優先順位：ERROR＞BLOCKED＞HOLD＞READY）

| gate_status | 条件 |
|---|---|
| ERROR | 第1層のERROR／`integration_errors`非空／第2層の実行失敗 |
| BLOCKED | 第1層のFAIL／有効な承認済み例外が適用されていない第2層FAIL |
| HOLD | 第1層WARN／実装済み必須第1層検査のSKIP-insufficient_data／第2層REVIEW／必須第2層検査のUNVERIFIABLE |
| READY | 上記のいずれも存在しない |

- 集約は出力元の語彙を**直接**参照する。§4.2の意味対応表を経由した共通語彙への射影は行わない。
- **第1層の有効結果**：第1層のERROR／FAILとは、第1層runnerが自身のSchema・抑制（suppressions／disabled）・SKIP規則に従って確定し、ValidationReportのresultsに記録した有効結果を指す。統合処理は、第1層の`summary.blocked`に寄与しない結果を、BLOCKED要因として再評価しない。抑制の適用状況は`suppressed_count`および`suppression_resolutions`を参照する。
- `prerequisite_failed` は原因側のFAIL／ERRORで集約する。**原因結果の欠落を統合処理が検出した場合**は `integration_errors` へ格納し `gate_status: ERROR` とする。このとき `summary.blocked` は第1層の所有物であり、統合処理は変更しない（ケースH1）。**第1層自身が原因欠落等をERROR結果として出力した場合**は `summary.blocked: true` となる（ケースH2）。
- HOLDの経路は表のとおり4種（第1層WARN／必須第1層検査の証拠不足SKIP／第2層REVIEW／必須第2層検査のUNVERIFIABLE）。
- CONSULTでは未実装検査を `SKIP/not_implemented` として報告できる。

### 8.3 承認済み例外（第2層のみ・`exception_id`方式）

`exception_id` 方式を適用するのは、Schemaを自家所有する**第2層のみ**である。

- 第2層FAILをPASSやUNVERIFIABLEへ**変更しない**。元のFAIL結果は `deck_inspection_results` に残す。
- known-exceptions台帳に登録済みの有効な `exception_id` を当該結果へ付与する。
- **有効な例外が適用されたFAILのみ**、gate集約のBLOCKED条件から除外する。
- `exception_id` が存在しない／台帳に存在しない／対象check_id・案件・版・適用範囲と一致しない場合は、除外を成立させない。無効な例外参照のFAILはBLOCKED要因として残る。
- 除外済みと記録されているのに有効な例外を確認できない場合は、レポート不整合として `integration_errors` へ格納する（→gate_status: ERROR）。

**第1層の承認済み例外・SKIP・suppression等の挙動は、既存Schema 0.1および第1層runnerの所有とし、本Contractから変更しない。**

### 8.4 検算ケース表

| ケース | 状況 | gate_status | summary.blocked |
|---|---|---|---|
| A | 第1層PASS×2 | READY | false |
| B | 第1層PASS＋WARN | HOLD | false |
| C | 第1層FAIL＋WARN | BLOCKED | true |
| D | 第1層PASS＋SKIP(insufficient_data・実装済み必須) | HOLD | false |
| E | 第1層PASS＋SKIP(not_applicable) | READY | false |
| F | 第1層ERROR＋FAIL | ERROR | true |
| G | prerequisite_failed＋原因FAIL | BLOCKED | true |
| H1 | 統合処理が prerequisite_failed の原因結果欠落を検出（`integration_errors`へ格納） | ERROR | false |
| H2 | 第1層自身が原因欠落等をERROR結果としてValidationReportへ出力 | ERROR | true |
| I | 第1層PASS＋第2層REVIEW | HOLD | false |
| J | 第1層PASS＋第2層FAIL（known-exceptions登録済みの有効な`exception_id`あり。元のFAILは`deck_inspection_results`に残る） | READY | false |

H1／H2は `summary.blocked`（第1層所有）とgate_status（統合処理所有）が別の集約関数であることの、I／Jは第2層語彙が第1層レポートを経由せず直接集約されることの最小の証明となる（R2でテスト化）。

### 8.5 必須集合の選定規則（確定）

以下5条件を**すべて**満たす検査のみ必須集合（structural／deck各側）へ入れる：

1. 実装済みである
2. 対象デッキへ適用可能である
3. 必要な入力・設定が存在する
4. 未検出のまま納品すると案件契約または研修進行を損なう
5. 全判定状態の処理が定義済みである

未実装検査、通常は証拠を用意できない検査、Learning Design Reviewは必須集合へ入れない。**`required_structural_check_ids`／`required_deck_check_ids` の具体的ID一覧は、V2の結果を受けてdeck-contractで確定する**（DEFERRED-D1）。

## 9. 配置・同期・盲検隔離（決定点8）

- **前処理ランナー方式**：抽出・レンダリングは前処理ランナーが一時領域へ生成。deck-inspector本体は `tools: Read, Grep, Glob` のみ＋修正禁止明文（A8 training-reviewerと同型・境界を構造的に担保）。
- **画像入口**：Claude側＝画像対応Read／OpenAI側＝PNGを画像入力として渡すアダプター（CodexのPNG/JPEG画像入力は公式仕様）。
- **同期方式（確定）**：正本＝`skills/deck-inspection/`。生成先＝Claude Code向け `.claude/skills/deck-inspection/`・Codex向け `.agents/skills/deck-inspection/`。既存同期ワークフローによる**決定的な自動コピー**とし、CIで正本と生成先の乖離を検出する。**生成先の直接編集は禁止。シンボリックリンクは採用しない。** 具体的なスクリプト変更は実装工程へ委譲する（DEFERRED-D2）。
- **正解ラベル**：読取境界外に配置（リポジトリ非収録・評価側で恒久保持）。本Contractにも詳細を収録しない。
- **ZIP配置（確定）**：ZIPはリポジトリ外の固定入力ディレクトリへ置く。実配置：`C:\Users\yksr3\Projects\deck-inspection-inputs\office-artifact-validation-v0.1.0.zip`。期待SHA-256：`697b17e340c088287753470303f65f814b767aebde7cd38492e210f01104b0db`。**不一致の場合は展開せず停止し、実測値を報告する。** 展開先は一時領域とし、正本リポジトリを直接上書きしない。
- **第1層投入工程（順序固定）**：①ZIPを固定入力ディレクトリへ配置しSHA-256照合→②依存関係定義（requirements.txt等）追加→③jsonschema導入→④同梱テスト全群実行→⑤決定点1〜3の現物照合（B4完了条件・E2の裏づけ取得）。V2マッピング表はその後の工程で作成し、E3の証拠を残す。

## 10. 盲検データの扱いと版系列運用

**隔離原則**：隔離対象は**正解ラベルのみ**。入力PPTX・抽出スナップショット・レンダリング画像は検品側へ渡す。各試行でエージェントのコンテキスト・作業領域・前回出力を初期化する。正解ラベルと具体的な事故内容は検品側へ渡さない。

**版系列の使い分け（確定）**：

| 用途 | 版系列 |
|---|---|
| 調整用（正規化規則・照合方式・閾値） | 9/3 WSスライドの多版系列 |
| 事前検証用 | 丸五デッキの版系列 |
| 最終盲検 | 実事故6件の正解ラベルを作成した**正確なJFE v7→v8版対** |

v8の40枚→45枚系列は、同じ正解ラベルに対応しない限り最終盲検には使用しない。

**運用順序**：①9/3 WS系列で正規化規則・照合方式・閾値を調整 →②丸五系列で事前検証 →③規則・閾値・コード・criteriaを固定 →④JFE版対を**一度だけ**盲検実行。丸五で問題が見つかり調整へ戻った場合は、修正後に**別の未使用版対**で再検証してからJFEへ進む。

**JFE版対の同定**：評価側で旧版・新版それぞれのファイル名とSHA-256を記録する（EVIDENCE_PENDING-E4）。

## 11. Deferred extension予約（Learning Design Review）

本節は予約のみでスコープを変更しない。**禁止2件を本Contractの禁止事項として引き取る**：①`deck.*`配下に学習系の検査を置かない ②WARNの意味論に学習リスクを混ぜない。同拡張の所見は既存ValidationReportにも `deck_inspection_results` にも混ぜず、独立の判定語彙を持つ別レポートに置く。GATE必須集合には将来も入れない（§8.5選定規則の除外と整合）。名前空間・所見フォーマットは、JFEまたは次案件で構成段階CONSULTを一度手動で回した後に決める。

## 12. 回帰条件

- R1：4判定各1件を含むfixtureで、`deck_inspection_results` の判定と§4.2意味対応表（説明用）の対応が保たれていることの検査（第2層実装後にテスト追加）
- R2：§8.4検算ケースA〜Jのテストケース化（B・D・H1・H2・I・Jの乖離ケースを必須含有）
- R3：contract.\*再利用の各件に3点照合の記録を残す（V2確定時。記録先は `docs/deck-inspection_v2-check-id-mapping.md`）
- R4：正規化規則確定時に調整用版対の回帰スナップショットをfixtures化
- R5：`deck.*`名前空間への学習系ID混入がないことの静的検査（§11禁止①の機械化）
- R6：既存ValidationReport（`structural_validation_report`）内にgate_statusが存在しないことの検査（版上げ回避の担保）
- R7：**structural_validation_report内容同一性検査**——DeckInspectionReportへの格納前後で、既存ValidationReportのフィールドと値が変更されていないことを検証する。JSONオブジェクトとして埋め込む場合はcanonical JSONによるhash一致などで内容同一性を検証し、ファイル参照方式を採用する場合は元ファイルのSHA-256一致で検証する。空白・改行・キー順による単純なバイト差は改変と判定しない。統合処理による `summary.blocked` の再計算・上書きを禁止する
- R8：**第2層例外除外の正当性検査**——gate集約のBLOCKED条件から、承認済み例外を理由に除外されたすべての**第2層FAIL**について次を検証する：①`exception_id`が存在する ②known-exceptions台帳に登録されている ③対象check_idと一致する ④対象案件・版・スコープに適用可能である ⑤失効・取消状態ではない。いずれかを満たさないFAILは除外してはならない。除外済みレポートで不一致を検出した場合は `integration_errors` へ格納し `gate_status: ERROR` とする。**R8は第2層専用であり、第1層ValidationReportの例外処理を再判定・変更してはならない**

## 13. 未解決事項の3分類

### BLOCKING（全件CLOSED・2026-08-22）

| ID | 事項 | 状態 |
|---|---|---|
| B1 | レポート所有境界の修正 | **CLOSED**（v0-draft-2/3反映・差分レビュー合格） |
| B2 | `summary.blocked`所有権とH1／H2の確定 | **CLOSED**（同上） |
| B3 | 暫定確定案①〜③の条件付き承認 | **CLOSED**（小林裕司 2026-08-22承認） |
| B4 | ZIP配置・SHA-256照合・Claude側Schema現物確認（旧E1を統合） | **CLOSED**（SHA-256一致・5現物確認・enum/status/check_class制約記録・前提との差異なし・差分レビュー完了） |

### DEFERRED_BY_CONTRACT（後続成果物・工程へ決定権を委譲）

| ID | 事項 | 決定主体 | 決定工程 | 成果物 |
|---|---|---|---|---|
| D1 | `required_structural_check_ids`／`required_deck_check_ids` の具体的ID一覧 | 小林裕司（Claude起案） | V2確定後のdeck-contract作成時 | deck-contractの必須検査節（2集合） |
| D2 | 既存同期ワークフローへの実装追加 | 小林裕司（Claude実装・提案） | 第1層投入後の実装工程 | 同期スクリプト変更＋CI乖離検査 |
| V2 | `contract.*`／`deck.*`個別マッピング表 | 小林裕司（Claude起案） | ZIP現物確認・E2完了後 | check_idマッピング表＋各再利用候補の3点照合記録（`docs/deck-inspection_v2-check-id-mapping.md`）〔関係：証拠部分がE3。V2の結果を受けてD1の具体的必須ID一覧を確定〕 |
| V3 | 正規化規則の具体値 | 小林裕司（Claude起案） | 9/3 WS系列での調整工程 | 本Contract §6追補＋回帰fixtures（R4） |
| V4 | 照合閾値・unmatched条件 | 小林裕司（Claude起案） | 9/3 WS調整→丸五事前検証の工程 | 本Contract §7追補＋テスト |
| V5 | DeckInspectionReportの詳細Schema（第2層専用Schema・§4.1メタデータの型定義を含む）。**第2層の実行失敗はDeckInspectionReportの`integration_errors`内へ構造化して記録する。少なくとも、エラーの発生元、エラーコード、メッセージ、関連する実行・入力参照、gate_statusへの影響を識別できる構造をV5成果物に含める**（専用フィールドは新設しない。詳細な型定義はV5へ委譲） | 小林裕司（Claude作成） | 第1層投入後・V2と同時期 | schemaファイル一式 |
| D4 | A4・A5正本探索および必要時の再正本化実施 | 小林裕司（再承認） | criteria-schema着手前 | 正本特定記録、または来歴付き新正本文書 |

### EVIDENCE_PENDING（方針は決定済み・現物/実測による裏づけ待ち）

E1は**B4へ統合済み**（欠番として維持）。E2〜E5は追跡性のため既存番号を維持する。

| ID | 事項 | 検証方法 | 停止条件 |
|---|---|---|---|
| E2 | check-catalog 31件の層割り当て | 第1層投入工程⑤で境界文（§2）と照合。照合記録は `docs/deck-inspection_e2-check-catalog-layer-allocation.md` | 矛盾する割り当てが出た場合、境界文を改訂しレビューへ戻す |
| E3 | `contract.*`の3点照合結果 | V2マッピング表作成時に個別照合・記録（R3） | 一致0件でも手続きは維持（全件 `deck.*` 新設へ） |
| E4 | JFE盲検版対のファイルhash | 評価側で旧版・新版のファイル名とSHA-256を記録 | 正解ラベル作成元版対との同一性が確認できない場合、盲検を開始しない |
| E5 | A4・A5正本ファイルの探索結果 | D4工程で既存正本を探索 | 発見できない場合、§5の再正本化手続き（記録由来文→再承認）へ移行 |

### v0確定の記録

v0確定条件（BLOCKING 0件／DEFERRED全項目に決定主体・時期・成果物／EVIDENCE_PENDING全項目に検証方法・停止条件／最新draftの別コンテキスト差分レビュー完了）は、2026-08-22時点ですべて充足済み。本書をもってContract v0を確定とする。
