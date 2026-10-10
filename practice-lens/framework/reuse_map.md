# 既存資産との対応（Reuse / Extend / New）

正本：`infoagrow3jp/grow3-knowledge` の `schemas/organization-diagnosis/common.schema.json`（2026-10-09取得・確認）

結論：**organization-diagnosis には手を入れない。** 隣に `practice-lens/` を置き、`$ref` で借りる。

`$id` は正本と同じ規約で `https://grow3.jp/schemas/practice-lens/v0.1/…` とし、common への参照は `../../organization-diagnosis/v0.1/common.schema.json`（正本の `$id` に解決される）。`$id` は論理的な識別URIなので、実ファイルを `v0.1/` フォルダに置く必要はない。検査は `tools/schema_check.py` が `$id` で解決する。

---

## Reuse（`$ref` で借りる・定義しない）

| 使うもの | 正本の定義 | カードでの用途 |
|---|---|---|
| 日時 | `common#/$defs/dateTime` | カードの `created_at` / `updated_at`、封筒の `last_updated_at`、promotion record の `recorded_at` |
| 拡張領域 | `common#/$defs/extensions` | 未定義キーはここだけ |
| 機密度 | `common#/$defs/sensitivity` | **promotion record（非公開）でだけ使う。** 参照したEvidenceの最大値を下回らせない。公開カードは持たない（公開カードは顧客Evidenceを指さないので、取りうる値が無い） |
| Evidence ID | `common#/$defs/evidenceId` | **promotion record（非公開）でだけ使う。** 公開カードは持たない |
| MTG ID | `common#/$defs/mtgSessionId` | promotion record の出所セッション |
| case ID | `common#/$defs/caseId` | promotion record の案件 |

## Reuse（語彙・規律として借りる・schemaには出ない）

- `review_status` の4値（unreviewed / spot_checked / verified / rejected）。**値だけ揃え、意味はLens側で別定義する。** Evidenceの verified は「確認手続を通った」、Lensの verified は「異なる実案件2件以上で、問いとして使って効いた」。Lensの spot_checked は同1件、unreviewed は現場での有効性が未確認（Critic通過だけでは変わらない）。同じ語に違う意味を持たせないため、Evidence側の定義を `$ref` しない
- ID不変規律（改訂は新ID、使い回し禁止、顧客名・個人名を含めない）
- 三値規律（欠落とnullを同一視しない）
- 「網羅を目標にしない。意思決定に効くものだけ残す」

## Extend（既存を変える必要があるもの）

**なし。**

GPT案は `registerType` のenumに `observation_cards` を足す方向だが、やめた方がいい。理由は2つ。
1. `common.schema.json` は stable/frozen。enumを触るとDEC（進行規律DEC-014）が要る
2. `registerEnvelope` は `case_id` 必須。**カードはcase横断なので、この封筒に入らない**

なので封筒ごと別にする。中身の部品だけ借りる。

## New（practice-lens/ に新しく置くもの）

| 定義 | 内容 |
|---|---|
| `cardId` | `LENS-NNN`（3桁以上、通し連番、不変） |
| `businessModelTag` | enum：`project_based` / `repetitive_production` / `store_retail` / `human_service` / `professional_service` |
| `valueChainStage` | enum：`intake` / `survey` / `design` / `production` / `handoff` / `install` / `close` / `after` / `support`（業種によらない共通語彙） |
| `boundary_context` | 任意。この観点が特に効く型の境目（from → to）。カードの属性ではなく適用コンテキストなので必須にしない |
| `libraryEnvelope` | `schema_version` / `library_type: practice_lens` / `last_updated_at` / `items`。`case_id` を持たない |
| カード本体 | title / observation / why_it_matters / examples / prompt / anti_pattern / sources / field_validation（cases_count のみ）/ review_status |
| `promotion.schema.json`（非公開） | Lens ↔ Evidence の紐付け。record_kind（origin＝Lensを生んだ根拠／field_use＝使って有効性を確認した記録）/ lens_id / case_id / evidence_ids / abstraction_note / sensitivity / recorded_at（記録を作った日時）。**公開カードに顧客EVDを持たせないための受け皿** |

新規は実質この7つ。

---

## Pattern register を流用しない理由（GPTの指摘を採用）

既存Patternは「distinctな出来事が2件以上反復して初めてPattern」という厳密な定義。
異業種に効く観点は、単発でも公的資料だけでも立つので、Patternに入れると定義が汚れる。
別schemaにして、PatternとLensは参照関係だけ持つ（将来 `related_pattern_ids` をextensionsで）。

## 公開／非公開の境界

既存設計では、顧客のEvidence・Pattern・Hypothesisは顧客領域、公開リポジトリは方法論・schema・fixture。
派生物のsensitivityは根拠の最大値を継承する。この2つを守ると、**顧客Evidenceを直接参照する公開カードは成立しない**
（restricted_hr のEvidenceを指した瞬間、カードもrestricted_hrになる）。

したがって、

- **公開Lens**：`field_validation: {cases_count}` だけ持つ。どの会社・どのEvidenceか、機密度は持たない
- **非公開promotion record**：`lens_id ↔ case_id ↔ evidence_ids` の紐付けと、抽象化で何を落としたか。`record_kind` で origin と field_use を分ける
- **切り出し記録（edition）**：会社の体制・方針が入るので非公開の案件領域に置く。公開側に `library/editions/` は持たない
- 抽象化した時点で顧客との紐付けが切れる。「裏側まできれいに」→「見えにくい部分まで品質対象として扱う」

## 実案件からの還流の経路

1. 打合せ → Evidence register に `EVD-` を起こす（既存スキル org-diagnosis-registers）
2. ★見どころのEvidenceから、Structurer が LENS候補を起こし、同時に **promotion record（非公開）** に `record_kind: origin` で紐付けを書く。Editor はカードを起こさない
3. Critic が rubric.md の10項目で検品。通っても公開側は `review_status: unreviewed`、`cases_count: 0` のまま。**生まれた案件は件数に数えない**（調査由来のLensと同じ出発点）
4. そのLensを別の打合せで問いとして使い、効いたら promotion record に `record_kind: field_use` を書く。公開側は1件目で `spot_checked`・`cases_count: 1`。異なる2案件目で `cases_count: 2` になり、人が認定したら `verified`（card.schema.json の if/then が `cases_count>=2` を強制する。手で `verified` にしても検証で落ちる。件数が足りても自動では上がらない）
5. 使ったが効かなかった記録は promotion に入れない。顧客側のEvidence・打合せ記録に残す

`cases_count` ＝ field_use 記録の異なる `case_id` の数。同一案件で何度使っても1件。一致は `tools/cases_count_check.py` で照合する（schemaだけでは保証されない）。

公開カードには顧客の言葉もEVD-IDも残らない。紐付けは非公開側にだけある。

## ゲートは4つ（2026-10-10追加）

| ゲート | 見るもの | 役 | いつ必須か |
|---|---|---|---|
| schema（構造） | カード（候補・正式Library）と promotion record が schema に適合するか。common は正本の `$id` で解決 | `tools/schema_check.py` | カードか promotion record を書き換えたとき。他のゲートより先 |
| rubric（内容） | 観点が一つか、場面か、問いが30秒か…の10項目。基準は `framework/rubric.md` だけ | Critic | candidates に入れるとき |
| provenance（出典） | sources[] の全名称が `framework/sources.md` にあり、URLかローカル正本と確認日を持つか | `tools/provenance_check.py` | candidates → library 昇格時 |
| cases_count（現場件数） | カードの `cases_count` が、promotion record の field_use の異なる case_id 数と一致するか。review_status と件数が合っているか | `tools/cases_count_check.py` | field_validation か review_status を変えたとき。先に promotion record を schema で検証し、違反があれば数えずに落とす。記録が無いときは `--no-records` を明示する |

Critic は根拠の所在を見ない。provenance gate は内容を見ない。
「カードとしては完璧だが、根拠の資料が台帳に無い」はここで止まる。Editor は provenance が通る前でも走ってよい（A3は candidates から切り出す）。

## 置き場所とIDの不変条件

| 置き場所 | 中身 | schema |
|---|---|---|
| `library/candidates/lens_candidates.json` | 候補。Critic を通ったが、正式採用はまだ | card.schema.json |
| `library/lens_library.json` | 正式採用したカードの正本。**最初の1枚を採用するときに作る**（空ファイルは置かない） | card.schema.json（同じ） |

- 正式Libraryへの採用を決めるのは Grow3。schema・rubric・provenance の3ゲートに加え、cases_count の整合性検査を通過したうえで採用を判断する。現場での有効性確認件数に下限は設けず、採用後も `review_status` と `cases_count` を独立して管理する（`unreviewed`・0件のカードが正式Libraryにあってよい。それは「現場で効果が確認された」という意味ではない）
- 候補の間は、同じIDのまま内容を改訂してよい。統合で消したIDは欠番にし、使い回さない
- 候補の間でも、切り出し記録や promotion record から参照されているIDは、意味を変えない
- **正式採用後はIDを不変にする。** 意味が変わる改訂・棄却では新IDを発行する
- 3本の検査スクリプトは、候補と正式Libraryの両方を読む

## 変更履歴

### 2026-10-10（アーカイブ v0.2.1）

schema_version は 0.1.0 のまま（promotion record 0件・未公開の段階での、初版確定前の修正として扱う）。

- `card.schema.json`：`reviewStatus` の4値の意味と、`cases_count` の定義（問いとして使い有効性を確認した異なる案件数）を description に明記。構造は変更なし
- `promotion.schema.json`：`record_kind`（origin / field_use）を必須で追加
- `tools/cases_count_check.py`：新規。カードの件数と field_use 記録の照合
- 還流の手順：候補を起こす役を Structurer に訂正。Critic 通過・生まれた案件は件数に数えない
- `agents/editor.md`：担当欄を置かない／promotion へ送るのは効いたカードだけ／切り出し記録は非公開の案件領域へ
- `library/editions/`：公開側から外した

### 2026-10-10（アーカイブ v0.2.2）

schema_version は 0.1.0 のまま（理由は v0.2.1 と同じ。promotion record 0件・未公開）。

- `card.schema.json`：`field_validation.status` を削除（`cases_count` から決まるうえ、「使ったが効かなかった」を表せなかった）。`sensitivity` を削除（公開カードは顧客Evidenceを指さない）。if/then は `cases_count>=2` だけに。`$id` に `v0.1/` を入れ、common への参照を正本の `$id` に解決される形に
- `promotion.schema.json`：`promoted_at` → `recorded_at`（field_use にも成り立つ名前に）。`$id`・参照を同様に修正
- `lens_candidates.json`：20枚から `status` と `sensitivity` を外した。文言は変えていない（Critic の再検品は不要）
- `tools/schema_check.py`：新規。日時・日付の形式も検査する（正本の schema gate と同じ Draft 2020-12 + format）。`agents/structurer.md` に埋め込まれていた検証手順を置き換えた（旧手順は、リポジトリ内で実行すると `schemas/organization-diagnosis/` を上書き・削除する危険があった）
- `tools/cases_count_check.py`：promotion record を schema で検証してから数える。記録なしは `--no-records` の明示が必要。正式Libraryも読む
- `tools/provenance_check.py`：存在しないカードIDを指定したら FAIL。正式Libraryも読む
- `framework/rubric.md` と `agents/critic.md`：判定の目安を rubric に移し、基準を rubric 一本に。critic は手順と記録形式だけ。「直すのは Structurer」に訂正
- 正式Libraryの置き場所（`library/lens_library.json`）と採用条件、IDが不変になる時点を明記。`agents/editor.md` の入力に正式Libraryを追加
- この文書の事実誤認を訂正（`last_reviewed` は存在しない／行数の記述）
