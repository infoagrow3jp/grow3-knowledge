# Grow3 Knowledge OS 設計判断ログ

このファイルは、Grow3 Knowledge OSの構成・境界・運用に関する重要な設計判断と、その理由を記録する。
理論の定義、実務手順、各OS本文の内容はここに再掲しない。

## 記録形式

### DEC-XXX｜判断タイトル
- 日付：
- 状態：確定／保留／廃止
- 対象：
- 決定：
- 理由：
- 採用しなかった案：
- 見直し条件：

## 判断ログ

### DEC-001｜Knowledgeと設計判断を分離する
- 日付：2026-07-10
- 状態：確定
- 対象：リポジトリ全体構成
- 決定：汎用知識（理論・運用ルール）本体と、その構成に関する設計判断を別に管理する。設計判断はDECISIONS.mdに記録し、既存7ファイルの本文には含めない。
- 理由：知識本体と「なぜその構成にしたか」という経緯が同じファイルに混在すると、実務参照時に不要な文脈を読む負荷が生じ、複数AIが手順と方針を混同する原因になるため。
- 採用しなかった案：各*-os.mdファイルの末尾に改訂履歴・設計判断欄を持たせる案。
- 見直し条件：DECISIONS.mdの運用実績が積み重なり、対象ファイルごとの参照性を高める必要が生じた場合。

### DEC-002｜新ルールは実務上の不足を確認してから最小限追加する
- 日付：2026-07-10
- 状態：確定
- 対象：ルール追記の運用方針
- 決定：AI向けルールやテンプレートを事前に大量整備せず、実務で使用した結果、既存ファイルに不足が確認された場合のみ最小限追記する。
- 理由：一度の成功例をすぐ共通ルールに昇格させると、個別事情に基づく判断が誤って一般化されるリスクがあるため。
- 採用しなかった案：CLAUDE.md、AGENTS.md、.cursor/rules等を先行して整備する案。
- 見直し条件：複数案件で同一の不足が繰り返し確認され、その都度追記するコストが無視できなくなった場合。

### DEC-003｜研修時間の検算ルールはgrow3-training-design-os.mdに置く
- 日付：2026-07-10
- 状態：確定
- 対象：時間設計パターン（grow3-training-design-os.md 第3部）
- 決定：研修時間の検算ルールは、DECISIONSではなく、実行時に参照するgrow3-training-design-os.mdに記載する。
- 理由：検算は研修設計のたびに確認すべき運用ルールであり、設計判断ログに置くと実務上の参照動線から外れるため。
- 採用しなかった案：検算手順をDECISIONS.mdに記載する案。
- 見直し条件：同じ検算ルールが複数の設計OSで共通利用され、横断ルールとして切り出す必要が生じた場合。

### DEC-004｜確定した区分名称・判定文言は言い換えず原文のまま採用する
- 日付：2026-07-12
- 状態：確定
- 対象：financial-analysis 指標定義書（CF自走性の安全余裕度区分。閾値表を伴う基準書全般に準用）
- 決定：ユーザーが確定した閾値の区分名称・判定文言は、一般的なレーティング表現（例：危険／標準／良好／優良）に言い換えず、確定した原文の名称をそのまま採用する。名称が伝える診断トーンの強さは、数値閾値と同じく確定判断の一部として扱う。参考として、本件で確定したCF自走性の区分名称4つを確定値として記録する：**要改善（1.0未満）／ぎりぎり（1.0以上1.2未満）／標準（1.2以上1.5未満）／余裕（1.5以上）**。
- 理由：2026-07-12、CF自走性の安全余裕度閾値をv0.2指標定義書に統合した際、Cursor側が確定名称を「危険／標準／良好／優良」という一般的なレーティング語に善意で置き換えた。結果、1.0〜1.2帯（自走はしているがショック耐性がない帯）が「標準」と表示され、確定内容（「ぎりぎり」＝警告帯）より一段甘い診断トーンになる誤りが発生した。これは第0原則（依頼範囲外を善意で変更しない）が防ごうとしている典型パターンであり、名称・文言は「表現の自由度が高い部分」ではなく確定事項として扱う必要がある。
- 採用しなかった案：区分名称は表現上の裁量とみなし、AIが文脈に応じて自然な言い回しに整えることを許容する案。
- 見直し条件：同様の名称置き換えが再発した場合、standards-authoringスキル等の共通ルールに明文化して昇格させる。

### DEC-005｜financial-analysisを独立した5体目のサブエージェントとして新設し、正本参照原則を適用する
- 日付：2026-07-12
- 状態：確定
- 対象：`.claude/agents/financial-analysis.md`、`.claude/skills/financial-analysis/SKILL.md`、`docs/financial-analysis_指標定義書_v0.2.md`、`financial_calc.py`
- 決定：
  - 決算書の持続可能性分析を、既存4体と同一のfrontmatter規約に従う、独立した5体目のカスタムサブエージェント`financial-analysis`として新設する。
  - 指標の算式・閾値・区分名称の唯一の正本は指標定義書v0.2とし、`financial_calc.py`をその実行形とする。SKILL.mdおよびサブエージェント定義には、算式・閾値・区分名称を複製しない。
  - 営業CFは、実績営業CF、推計営業CF、簡易営業CFの優先順位で解決する。簡易営業CFはスクリーニング専用とし、正式判定には使用しない。
  - レポートは、第1層フロー（CF自走性）、第2層ストック（債務償還年数）、第3層バッファ（余剰現預金）の順で構成する。
  - `judgment_status=screening_only`の場合、CF自走性の正式な判定区分を表示しない。参考計算値、スクリーニング値である旨、正式判定を行っていない理由、警告コード、追加必要資料のみを表示する。
  - BASTベンチマークはリポジトリへ保存せず、実行の都度Webで速報版を参照する。取得不能時は、記憶、過去値、他年度値で補完しない。BASTは内部判定を上書きしない。
  - `financial_calc.py`の実行失敗または必須メタデータ欠落を検知した場合、手計算、推測、独自ロジックで補完せず、分析を中断する。
  - 本サブエージェントの出力は下書きであり、顧問先送付版の最終確定は小林裕司が行う。
- 採用しなかった案：算式・閾値をスキルまたはサブエージェント定義へ複製する案。改訂時に正本とのズレが生じるため不採用とした。
- 補足：運用上の正式登録およびeval合格状況はDEC-006を参照する。

### DEC-006｜financial-analysis Eタスクの正式合格を、Taskツールへの登録確認まで保留する
- 日付：2026-07-12
- 状態：保留
- 対象：`.claude/skills/grow3-judgment/evals/evals.json`のfinancial-analysis Eタスク
- 決定：
  - `generalPurpose`による代替実行では、E-1、E-2、E-3a、E-3b、E-4、E-5の6ケースについて、6/6 PASS、120/120、修正後の致命的不合格0件を確認済みである。
  - ただし、代替実行の結果は正式合格として扱わない。
  - 正式合格は、Taskツールで`subagent_type: financial-analysis`を直接指定できる環境において、既存のeval定義、fixture、期待値および失格条件を変更せずに6ケースを再実行し、全件合格した時点で確定する。
- 理由：
  - 複数の新規トップレベルチャットで、Taskツールへ`financial-analysis`を直接指定したが、`Invalid enum value`で拒否された。
  - ファイル配置、ファイル名、frontmatter、YAML構文、改行コード、リポジトリ同期状態を確認したが、登録済みの既存4体との差異や客観的な不備は確認できなかった。
  - このため、原因はTaskツール側の登録・キャッシュ機構またはCursor環境側にあると判断し、定義ファイルへの推測的な変更は行わない。
  - Cursorアプリの完全終了・再起動後、新規トップレベルAgentチャットで再確認したが、`financial-analysis`はTaskツールの`subagent_type`一覧へ登録されなかった。
  - `Invalid enum value`で拒否され、許可一覧には既存4体のみが表示された。
  - ファイル側に新たな不備は確認されなかったため、定義ファイルの追加修正は行わない。
  - 参考評価6/6 PASS・120/120・修正後の致命的不合格0件は維持するが、正式登録経由ではないため正式合格とはしない。
- 採用しなかった案：`generalPurpose`による代替実行の120/120を正式合格として確定する案。
- 見直し条件：
  - CursorまたはTaskツールの仕様更新により、リポジトリ内の新規カスタムサブエージェントが`subagent_type`へ登録可能になった場合。
  - 既存4体の登録方法や設定場所に、新たな客観的情報が判明した場合。
  - 上記いずれかの時点で正式登録を再確認し、登録された場合のみ既存Eタスク6ケースを正式実行する。

### DEC-007｜のぞみ薬局初回適用で判明した入力由来管理をfinancial-analysis標準仕様へ還流する
- 日付：2026-07-12
- 状態：確定
- 対象：`docs/financial-analysis_指標定義書_v0.2.md` §18、`financial_calc.py`（`calc_cf_self_sufficiency`・`resolve_annual_principal_repayment`・`resolve_maintenance_investment`）、`.claude/skills/financial-analysis/SKILL.md`、`tests/`配下のfixture・回帰テスト
- 決定：
  - 年間元本返済予定額は、返済予定表に基づく正式値（`scheduled`）・当期実績返済額の代用値（`actual_proxy`）・手動見積額（`manual_estimate`）・欠落（`missing`）を入力項目として分離する。formal判定は`scheduled`が入力された場合に限り、それ以外は`judgment_status=screening_only`とし、由来ごとに警告コードを分ける（`actual_proxy`と`missing`は別警告）。
  - 維持投資の実額は、維持・更新投資として確認済みの場合のみ`capex_source=maintenance_actual`とする。旧称`actual`は廃止する。成長投資混在の疑いがある総capexは`total_capex_proxy`として保守参考シナリオ専用とし、基本計算・正式判定（`judgment`・`judgment_status`）を上書きしない。
  - CF自走性の正式判定は、営業CFが`actual`または`estimated`であり、かつ返済額が`scheduled`である場合に限る。`simplified`営業CFは正式判定に使用しない（既存ルールを維持）。
  - 顧客データ・実数・BAST参照実数・Dropboxパス・分析ドラフトはgrow3-knowledgeへ保存しない。回帰テスト・fixture・eval素材は架空データのみとする。
- 理由：
  - のぞみ薬局への初回適用で、返済予定表未提供の実績返済額を分母に代入したまま`judgment_status=formal`相当の表示に近づく誤り、および固定資産増減実額を「維持投資確認済み」とみなしすぎるリスクが顕在化した。入力の由来と判定可否をAPI・定義書・テストで機械的に分離しないと、初回スクリーニング段階で正式判定に見える出力が生成される。
  - 本判断はorganization-diagnosis設計の参照元となるfinancial-analysis基盤の確定条件であり、個別案件の分析結論そのものではない。
- 採用しなかった案：
  - 返済額・capexの由来をレポート文言のみで区別し、`financial_calc.py`の入出力契約は変更しない案（後工程・別コンテキストで再発するため不採用）。
  - `actual_proxy`でも参考値が算出できれば、警告なしでゾーン名を表示する案（正式判定の定義と矛盾するため不採用）。
- 見直し条件：
  - 返済予定表・固定資産台帳等の入力契約をorganization-diagnosis側へ拡張する際、本仕様と矛盾する要求が生じた場合。
  - 同種の由来混同が別指標で再発した場合、standards-authoring経由で横断ルールへ昇格させる。

### DEC-008｜organization-diagnosis設計メモv0.1を確定し、「解釈の由来管理」を組織診断基盤の中核原則として採用する
- 日付：2026-07-12
- 状態：確定
- 対象：`docs/organization-diagnosis_設計メモ_v0.1.md`（将来のOS、schema、validator、skillの設計基準）
- 決定：
  - organization-diagnosis設計メモv0.1を、将来のOS、schema、validator、skillの設計基準として確定する（status: frozen）。
  - 中核構造として次を採用する：Evidence ledger、Pattern register、Hypothesis register、Causal edge / loop register、verification_action、validator。
  - **中核原則**
    - 事実、反復Pattern、構造仮説、メンタルモデル仮説を分離する。
    - 語られていない因果やメンタルモデルを創作しない。
    - validatorは形式的追跡可能性を保証するが、真実性は保証しない。
    - 出典照合を財務分析における検算の対応物とする。
    - MEASUREDは証拠であり、意味づけは仮説とする。
    - フレームワークは仮説生成の必須チェックリストではなく照合レンズとする。
    - 顧客提示版と最終判断は小林裕司が確定する。
    - 実顧客情報をPublicリポジトリへ保存しない。
  - **安全規律**
    - 話者帰属と質問文脈を管理する。
    - rejected Evidenceを支持・反証・棄却根拠に使用しない。
    - restricted_hrの秘匿性を派生物へ継承する。
    - exclude_from_org_diagnosisを順序外の強制除外値とする。
    - 個別労務、法務、健康情報等を一般の組織診断へ吸収しない。
  - **仮説管理**
    - CONFIRMEDは使用しない。
    - SUPPORTED／WEAKENED等の慎重な状態語彙を使用する。
    - REVISEDは状態ではなく改訂操作とする。
    - 棄却・改訂された仮説も履歴として残す。
    - SUPPORTEDの主要根拠には確認済みEvidenceを要求する。
  - **未確定事項**
    - 保存形式、Dropbox配置、各registerのstatus、measured_trend、verification_actionのregister化、occurrence_keyの粒度等の16項目は、善意に確定せずschema段階へ送る。
  - **今後の扱い**
    - schema段階で新しく判明した論点は、設計メモの失敗として無限に遡及修正せず、schema設計から得られた新しい発見として管理する。
- 理由：
  - financial-analysis（DEC-005〜007）では、数値の由来と判定可能範囲を管理する設計を確立した。組織診断では決定論的な計算核を置けないため、同じ考え方を「解釈の由来管理」へ展開する必要があった。
  - 組織診断の品質中心を「もっともらしい構造の提示」ではなく、Evidence・Pattern・Hypothesis・因果edgeの追跡可能性と、未確認事項の明示に置くことで、裕司さんの見立てへ安全に新しい視点を加える基盤とする。
- 採用しなかった案：
  - 決定論的計算核（organization_calc.py相当）を置き、仮説の真実性を機械保証する案。
  - SSR・7S等のフレームワークを仮説生成の必須チェックリストとして全案件に強制適用する案。
  - §23の未確定16項目を設計メモ段階で善意に確定する案。
- 見直し条件：
  - schema設計段階で設計メモと矛盾する論点が判明した場合（設計メモの無限遡及修正は行わず、schema設計の発見として管理する）。
  - 初弾実案件検証（設計メモ§22）で、設計メモv0.1の運用限界が確認された場合。

### DEC-009｜organization-diagnosis schema設計メモv0.1を確定し、「解釈の由来管理」を実装可能なregister構造として採用する
- 日付：2026-07-12
- 状態：確定
- 対象：`docs/organization-diagnosis_schema設計メモ_v0.1.md`（JSON Schema・validator・fixture実装の設計基準）
- 決定：
  - `docs/organization-diagnosis_schema設計メモ_v0.1.md` をv0.1として凍結する（status: frozen）。
  - organization-diagnosisでは、Evidence、Pattern、Hypothesis、Causal Structure、Verification Action等を分離したregister構造を採用する。
  - 顧客master register、MTG input snapshot、manifest索引によって、解釈と入力データの追跡可能性を確保する。
  - JSON SchemaはDraft 2020-12を使用し、9ファイルへ分割する。
  - registerはJSONを正本とし、内部診断ブリーフはMarkdown生成物とする。
  - `mtg_session_id` をinput snapshotの識別子として使用する。
  - Evidenceの出典ファイルは、相対パス、SHA-256、取得日時、ファイルサイズによって追跡する。
  - derived_summaryは元Evidenceへ遡れる場合のみ認める。
  - validatorは形式的な追跡可能性と横断整合性を検査するが、Evidenceの真実性やHypothesisの正しさまでは保証しない。
  - schema実装中に発見された新論点は、凍結済み設計メモの失敗として遡及修正せず、実装段階の新しい発見として管理する。
- 理由：
  - 凍結済みのorganization-diagnosis設計メモ（DEC-008）で定めた「解釈の由来管理」を、実データとして保存・検証できる構造へ落とす必要がある。
  - Evidenceと解釈を分離し、どの入力から、どの判断を経て、どの仮説や因果構造が生成されたかを追跡できるようにするため。
  - schemaとvalidatorの責務を分け、形式的整合性と内容上の妥当性を混同しないため。
- 採用しなかった案：
  - registerをMarkdown/YAMLで保持し、schema検証を後回しにする案。
  - 単一巨大JSON Schemaですべてのregisterを定義する案。
  - input snapshotを相対パスのみで保持し、内容ハッシュを記録しない案。
- 見直し条件：
  - schema JSON実装段階で、凍結済みschema設計メモと矛盾する論点が判明した場合（設計メモの無限遡及修正は行わず、実装段階の発見として管理する）。
  - validator初弾実装後、register envelopeまたはMTG snapshotの運用限界が確認された場合。

### DEC-010｜organization-diagnosis schemaの$id名前空間に管理可能なgrow3.jpドメインを採用する
- 日付：2026-07-12
- 状態：確定
- 対象：`schemas/organization-diagnosis/common.schema.json` および将来の organization-diagnosis schema群（9ファイル分割）
- 決定：
  - organization-diagnosis schema群の `$id` 基底URIを次とする：`https://grow3.jp/schemas/organization-diagnosis/v0.1/`
  - `common.schema.json` の `$id` は次とする：`https://grow3.jp/schemas/organization-diagnosis/v0.1/common.schema.json`
  - schema間の参照には、原則として同一ディレクトリを基準とする相対 `$ref` を使用する（例：`common.schema.json#/$defs/registerEnvelope`）。
  - 凍結済みschema設計メモ§5-3の `grow3.dev` 例示は、名前空間が未指定だった修正過程で追加され、管理根拠の確認されていない値だった。
  - `grow3.dev` を株式会社グロウスリーが管理する根拠は確認できないため、schema識別子には採用しない。
  - 管理下にある公式ドメイン `grow3.jp` を、リポジトリ名やブランチ構成に依存しない安定した名前空間として採用する。
  - 凍結済み設計メモは遡及修正せず、schema実装段階で判明した新しい横断的判断として本DECISIONに記録する。
  - common schemaを開いた抽象基底とし、各具体register schemaのルートで `unevaluatedProperties: false` を使用する合成方式が、Draft 2020-12 validator（jsonschema）による実行検証で成立した。
- 理由：
  - `$id` はschema識別子および相対 `$ref` 解決の基点となるため、管理主体が明確な安定した名前空間が必要。
  - 管理根拠のない、もっともらしいドメインを推測で採用しないため。
  - 凍結文書内の例示であっても、出典や管理根拠のない値を実装上の正本へ昇格させないため。
  - schema実装で発見した新論点を、凍結文書の遡及変更ではなくDECISIONとして管理するため。
- 採用しなかった案：
  - 凍結済みschema設計メモ§5-3の `grow3.dev` 例示を、そのまま実装上の正本URIとして採用する案（管理根拠が確認できないため不採用）。
  - `$id` をリポジトリ相対パスまたは `file://` URI のみとし、HTTP名前空間を使わない案（相対 `$ref` の解決基点として `$id` URI を使う現行方針と整合しないため不採用）。
- 見直し条件：
  - organization-diagnosis schema群の公開配布方針が変わり、別の公式名前空間へ移行する必要が生じた場合。
  - 相対 `$ref` 解決が、採用validatorまたは配布環境で再現不能と判明した場合。

### DEC-011｜organization-diagnosis Manifestを非正本の再構築可能索引として固定する
- 日付：2026-07-13
- 状態：確定
- 対象：`organization_diagnosis_manifest.schema.json`、将来のManifest validator／builder、mtg_input_snapshot／brief_metadataとの責務境界
- 決定：

  **既存凍結仕様（schema設計メモv0.1・DEC-008/009より。今回新規発明ではない）：**
  - Manifestは顧客単位の索引であり、内容の正本ではない。
  - Manifestなしでもregister単体のschema検査が可能である。
  - トップレベル管理項目は `schema_version` / `case_id` / `registers` / `mtg_sessions` / `briefs` / `created_at` の6項目である。
  - `registers` は各registerファイルパスと `last_updated_at`（RFC3339）を持つ。
  - `briefs` はブリーフファイルパスと `generated_at` を持つ。
  - `created_at` はManifest初回作成日時である。
  - `mtg_session_id` はinput snapshotの識別子を兼ねる。snapshotファイル名は `inputs/MTG-YYYYMMDD-NNN.json` である。
  - Manifestはcommonの `registerEnvelope` を使用しない。
  - `last_seq` はv0.1 Manifestの正式管理項目リストに含まれない（§8-2の連番方式比較表の「manifestまたはregister内」は実装コスト候補の併記であり、Manifest採用を意味しない）。
  - `register_snapshot_hash` と `generated_from_registers_at` はbrief frontmatter側の項目である。

  **今回の合成判断（凍結規則の組み合わせ）：**
  - register JSON本体、mtg_input_snapshot JSON本体、brief frontmatterが各情報の正本である。
  - Manifestに記録する `relative_path` / `last_updated_at` / `mtg_session_id` / `generated_at` は発見性・一覧性のための非正本キャッシュである。矛盾時は常に本体を正とし、Manifest値で本体を上書きしない。
  - Manifestの索引内容（registers／mtg_sessions／briefsの構成）は本体ファイルとディレクトリ構成から再構築可能とする。byte-for-byte完全一致の再生成は要求しない。
  - `mtg_sessions` はMTG session ID文字列の配列とする。snapshot path・session_date・input_files等はsnapshot本体に存在するためManifestへ重複保持しない。
  - register entryの `last_updated_at` およびbrief entryの `generated_at` は本体値のキャッシュである。

  **今回の新規判断（凍結文書に具体構造がなく人間判断で確定）：**
  - `created_at` のみManifest固有の運用メタデータとする。再構築時は既存の有効な `created_at` を保持する。ファイル喪失時のみ新しい `created_at` を記録する。
  - v0.1ではManifestの手動作成・手動修復を許可する。将来の専用builderが索引内容の再構築を担当する。validatorは不一致を検出・報告するのみで、Manifestや本体を自動変更しない。
  - `registers` は固定5キーobject（`evidence` / `patterns` / `hypotheses` / `causal` / `verification_actions`）とし、5キーすべてをrequiredとする。
  - 各register entryは `relative_path` と `last_updated_at` をrequiredとし、パスフィールド名を `relative_path` とする。
  - 各registerの `relative_path` は `_org_diagnosis/` 基準の固定値とする（`registers/evidence.json` 等）。
  - `briefs` は `relative_path` と `generated_at` の最小object配列とする。brief pathは `^briefs/[^/\\]+\.md$` パターンとする。
  - `mtg_sessions` と `briefs` は空配列を許可する（`minItems` は設けない）。
  - rootの `extensions` のみ許可し、register／mtg／brief entry単位のextensionsは許可しない。
  - Manifestトップに `last_updated_at` / `updated_at` / 再生成日時を追加しない。
  - キャッシュ日時不一致・未索引ファイルは原則WARN候補。参照先ファイル不存在・case／ID不一致はManifest整合性ERROR候補とする。

- 理由：
  - 二重管理された真実を作らないため。
  - Manifest破損が診断データ本体の喪失にならないようにするため。
  - snapshot／brief metadataとの責務重複を避けるため。
  - fixed structureにより重複registerや表記ゆれをschemaで防ぐため。
  - 将来のManifest builder実装を可能にするため。
- 採用しなかった案：
  - Manifestを独立した内容正本とする。
  - registersを自由配列にする。
  - MTG snapshot pathやsession_dateをManifestへ複製する。
  - brief entryへMTG関連情報やregister hashを追加する。
  - ManifestへID採番用 `last_seq` を置く。
  - entryごとにextensionsを許可する。
- 見直し条件：
  - register種類が5種類から変更される。
  - データファイル配置規則が変更される。
  - Manifest builderの実装で固定パス運用が困難と判明する。
  - 複数brief階層が必要になる。
  - Manifestを外部システムとの同期正本として使用する必要が生じる。

### DEC-012｜organization-diagnosis brief metadataをfrontmatter生成情報に限定する
- 日付：2026-07-13
- 状態：確定
- 対象：`brief_metadata.schema.json`、将来のbrief generator／validator／frontmatter extractor／YAML parser、Manifestとの責務境界
- 決定：

  **既存凍結仕様（schema設計メモv0.1・DEC-011より。今回新規発明ではない）：**
  - 内部診断ブリーフはMarkdown生成物であり、register JSONが診断内容の正本である。
  - brief_metadataはMarkdown本文ではなくfrontmatter用schemaである。
  - frontmatterに `generated_from_registers_at` を付与する。
  - frontmatterに `register_snapshot_hash` を置く構想がある。
  - `register_snapshot_hash` の算法はbrief_generator実装時に確定する。
  - 本文構造schemaの要否はbrief_generator実装時の将来判断である。
  - briefs/の粒度はMTGまたは診断サイクル単位である。
  - restricted_hr継承項目は通常ブリーフへ出力しない。
  - 秘匿情報の出力制御はbrief_generator＋validator責務である。

  **今回の合成判断（凍結規則の組み合わせ）：**
  - DEC-011によりManifest `briefs[].generated_at` は本体値の非正本キャッシュである。
  - brief frontmatterがbrief生成情報の正本である。
  - よってfrontmatterに `generated_at` を必須で持たせる。
  - `generated_at` はブリーフを生成した日時である。
  - `generated_from_registers_at` は、生成に使用したregister集合の基準時点である。
  - `generated_at` と `generated_from_registers_at` は別の意味を持つ。
  - Manifestには `generated_at` だけをキャッシュし、`generated_from_registers_at` やhashを複製しない。

  **今回の新規判断（凍結文書に具体構造がなく人間判断で確定）：**
  - schemaの必須項目を `schema_version` / `generated_at` / `generated_from_registers_at` / `brief_scope` / `source_mtg_session_ids` とする。
  - `brief_scope` は `mtg_session` / `diagnosis_cycle` の2値とする。
  - `mtg_session` の場合、`source_mtg_session_ids` は1件だけとする。
  - `diagnosis_cycle` の場合、`source_mtg_session_ids` は1件以上とする。
  - brief固有IDと `diagnosis_cycle_id` はv0.1では追加しない。
  - briefはManifest内の `relative_path` によって識別する。
  - `register_snapshot_hash` は任意で、少なくとも1文字の非空白文字を含むopaque stringとして場所だけ予約する。空白のみは認めない。
  - hash算法、対象register、結合順、canonicalization、encodingは固定しない。
  - `case_id` / `relative_path` / `sensitivity` / `filter_profile` 等をfrontmatterへ追加しない。
  - root `extensions` のみ許可する。
  - schemaはYAML parse後のJSON互換objectだけを検査する。
  - Markdown本文はschema検査対象外とする。
  - frontmatterはブリーフファイル先頭に必須とする。
  - frontmatter抽出・YAML構文・duplicate key検出はschema外責務とする。

  **frontmatter抽出契約（v0.1確定・extractor実装は別工程）：**
  - brief metadataを検査するMarkdownはfrontmatter必須。
  - UTF-8テキストとして扱う。
  - 1行目は単独の `---`。
  - BOM、先頭空行、先頭コメントは許可しない。
  - 次に現れる単独行の `---` を終了区切りとする。
  - 終了区切り欠落はextractor ERROR。
  - 空frontmatterはINVALID。
  - frontmatterはYAML mappingでなければINVALID。
  - 本文中に後から現れる `---` はMarkdown本文として扱う。
  - 2つ目以降のfrontmatter風ブロックは再抽出しない。
  - Markdown本文は空でもよい。

- 理由：
  - registerとブリーフを独立正本にしないため。
  - Manifestを再構築可能な索引として維持するため。
  - hash算法を凍結文書に反して先取りしないため。
  - 新しいdiagnosis_cycle ID体系を善意に増やさないため。
  - Markdown本文構造をv0.1 schemaへ膨張させないため。
  - frontmatterへ実顧客情報や機微情報を重複保持しないため。
- 採用しなかった案：
  - `register_snapshot_hash` を必須にする。
  - `register_snapshot_hash` をSHA-256へ固定する。
  - common schemaへhash定義を追加する。
  - `brief_id` を新設する。
  - `diagnosis_cycle_id` を新設する。
  - `case_id` をfrontmatterへ複製する。
  - sensitivityやfilter結果をfrontmatterへ持たせる。
  - Markdown本文をschema対象にする。
  - registerEnvelopeを使用する。
- 見直し条件：
  - brief_generatorを実装する。
  - register_snapshot_hash算法を正式決定する。
  - 診断サイクル固有IDが必要になる。
  - 顧客提示版／HR限定版等の複数brief種別を正式運用する。
  - Markdown本文構造を機械検査する必要が生じる。
  - frontmatter parserの正式実装を決定する。

## 2026-07-11 AI運用の判断基準を grow3-judgment スキルとして確立
1. 承認済み最新版を正とし、依頼範囲外を善意で変更しない（第0原則）。
   改善案は本文反映ではなく別途提案とする。
2. 採点は常時発動しない。明示依頼、複数案比較、または点数化が判断を
   明確にする場合に限定し、可否確認・違和感確認では結論と理由から
   直接答える。
3. 研修レビューの評価軸は固定しない。参加型はcoaching-trainingの3軸、
   知識習得型は汎用5軸を、タイプ判定後に選択する。
