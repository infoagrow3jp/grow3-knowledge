---
id: frameworks-3layer-split-20260817
type: design-note
status: approved-design
domain: [frameworks, marketing]
---

# 知識体系の3層分割（Reference／OS／Business）設計メモ

作成日：2026-08-17　状態：設計ゲート閉鎖・Phase 1 投入待ち（DEC-024 は承認済み。Phase 2 の DEC-017 改定は別途承認）　対象：`grow3-frameworks.md` とその周辺の再配置

## 1. 結論

`grow3-frameworks.md`（1,805行・約122KB）を機械的に3等分するのではなく、知識の種類で3層に再配置する。

| 層 | 中心の問い | ファイル | 今回の扱い |
| --- | --- | --- | --- |
| Reference（What） | 何を見る道具があるか | `grow3-frameworks.md`（既存） | ファイル名・本文は維持。冒頭に案内板を追記するのみ |
| OS（How／When／Why） | 今、何を見るべきか | `grow3-support-os.md`（新規・draft） | 新規作成 |
| Business（For whom／How delivered） | それをどう顧客価値にするか | `grow3-business-model.md`（新規・draft） | 新規作成 |

「3本を新規に作り、元ファイルを索引化する」という当初案は採らず、**新規はOSとBusinessの2本、Referenceは既存ファイルがそのまま該当する**とした。理由は次節。

## 2. 実ファイルに当てはめた結果（当初案からの修正点）

`grow3-frameworks.md` の内訳を数えると、第1部「発見した構造」6件（約210行）を除く第2部（A〜G・47件）と第3部（自社フレーム4件）は、すでに「その道具とは何か／何を見る道具か」に限定された道具リファレンスである。つまり現行ファイルの約85%はReference層そのものであり、Reference用に別ファイルを新設して元ファイルを索引化すると、実質的なファイル名変更になる。

ファイル名変更を避ける理由は4点ある。①`scripts/knowledge_build.py` の `MANAGED_FILES` に `grow3-frameworks.md` が名指しで固定されている（DEC-017「ここを善意で広げない」）。②リポジトリ内17ファイル（training／hr／coaching各OS、blog-concept-map、docs、diagnostics、`.claude/skills/` 3本、snapshot）が `grow3-frameworks.md` を「理論の地図・参照辞書」として参照し、`[→F:○○]` 記法で本文中エントリを指している。③DEC-020は「Routerを導入しない」と定めており、`grow3-frameworks.md` を索引ファイルにするとINDEX.mdの機能と重複する。④raw URLで外部AIから参照される正本のパスを変えると、参照側の全更新が必要になる。

一方で、OS層とBusiness層に該当する内容は現行の `grow3-frameworks.md` にはほぼ無い（`grow3-marketing-os.md` にもBMC・顧客ジャーニー・月次対話の記述は無い）。したがって新規作成が必要なのはこの2層だけであり、これは「今回の対話で生まれたものの多くはReferenceではなくOS側」という見立てと一致する。

## 3. 配置マップ

### 3.1 `grow3-frameworks.md` 第1部（発見した構造）6件

| エントリ | 役割上の所属 | 今回の扱い | 備考 |
| --- | --- | --- | --- |
| 認知の非対称性が構造的問題を引き起こす | OS（第5部：翻訳が必要になる根拠） | 正本は現位置のまま。support-os第8部から参照 | `[→F:]`参照 計10件（training-os 2、hr-os 3、skills 5） |
| 制約が余白と熱狂を生む（スポーツのメタファー） | OS（第5部：ガードレールの根拠） | 同上 | blog-concept-map・blog-writingスキルが言及 |
| GROWモデルと「任せる設計」の同型性 | OS（第6部：GROW二階建ての土台） | 同上 | `[→F:]`参照 計7件 |
| 思考特性が機能する理由 | OS寄り／道具の機構説明でもある | 同上。support-os第7部「解像」に役割を記載 | **境界事例**（下記5節） |
| ナイカイ研修の骨格構造 | 研修設計の適用事例 | 同上。support-osでは「適用事例」として言及のみ | **残り物候補**（下記5節） |
| 暗黙知を組織の力に変える循環 | OS（第3部・第9部の中核） | 同上。support-osから最も多く参照 | training-os・DECISIONSが参照 |

物理的な移管（正本の所在変更）は今回行わない。移管すると `[→F:]` 記法の意味が変わり、他OS・スキル側17箇所の更新（例：`[→F:認知の非対称性]` → `[→S:…]` 等の新記法）が必要になる。これは正本OS3本＋スキル3本への横断変更であり、第0原則により別途の承認事項とする。

### 3.2 `grow3-frameworks.md` 第2部・第3部（51件）

すべてReference層に留まる。変更なし。A〜Gの分類（知識の住所）はそのまま維持し、`grow3-support-os.md` 第7部に「役割」（レンズ／翻訳／解像／動態）の第二索引を置く。同じ道具が両方に載るのは重複ではなく、索引軸が違うため。

### 3.3 `grow3-support-os.md`（新規）に収めたもの

第0部OS概要（4原則）／基本循環と3レイヤー／3枚のレンズ・北極星二階建て・出口戦略／経営↔仕事↔人の翻訳と解像度の階段／組織学習サイクル①〜⑦・断絶3種・5問・二本の復路／統制深度①②③・ミドルの翻訳機能・4点セット／GROW二階建て・論点8群×階層・ABCD／第二索引／第1部との対応／固定しない項目と検証の進め方。各節に [現行]／[検証中]／[仮説] を付した。道具の定義は再掲せず `[→F:]` で参照している。

### 3.4 `grow3-business-model.md`（新規）に収めたもの

提供価値の定義／BMCの状態（項目別ステータス）／顧客ジャーニー（ループ）と認知変化ステージ／月次対話をハブにする商品構成／顧客選択4基準／3シグナルの営業・発信への転用と匿名化ルール／固定しない項目。公開リポジトリのため顧客名・パートナー個人名・価格等の未確定数値は入れていない。

## 4. どこにも入らなかったもの（残り物一覧）

これが次に足りない概念の候補になる。**判定：残り物は第4の知識種類を要求していない。**いずれも粒度（OS本体より細かい実務手順）か適用先（人事・研修などの実装OS）が違うだけで、Reference／OS／Businessのどれかに帰属先がある。三層が知識の種類を切れている証拠と見る。

| 項目 | 現在の所在 | 入らなかった理由 | 置き場（判定） |
| --- | --- | --- | --- |
| ナイカイ研修の骨格構造 | frameworks.md 第1部 | 道具でも一般OSでもなく、特定研修の骨格 | 適用事例。現位置維持。将来 `grow3-training-design-os.md` 第4部から参照 |
| 思考特性が機能する理由 | frameworks.md 第1部 | 道具（思考特性4象限）の機構説明と、いつ使うか（OS）の中間 | 現位置維持。第3部「思考特性4象限」の「接続するフレーム」から相互参照を足す案 |
| フレーム収集の「テンプレート」節 | frameworks.md 冒頭 | 知識でも見立てでも事業でもなく、記述規約 | 現位置維持（ファイル固有の記述規約） |
| モノサシ抽出の9段プロセス（CDM準拠、線と余白、4基準、面談用ワークシートA〜D） | GitHub未収録（対話・メモのみ） | OS層の「How」だが、支援OS本体より一段細かい実務手順 | `grow3-support-os.md` の下位実務モジュール（`references/` 等）。人事以外の判断基準抽出（JFE等）にも使うため hr-os に閉じ込めない。実案件検証後に収録 |
| 給与二階建て（人件費配分の経営判断×市場価値×役割価値×発揮）、等級＝委ねている判断の整理、スキルマップ＝任せられる判断の地図・Lv1〜4 | GitHub未収録 | 人事制度設計の型 | `grow3-hr-system-design-os.md`（Gate1〜2の間の追加解像層）。ただしLv1〜4固定化とA/B軸→給与レンジは「正本にまだ入れない」対象 |
| 研修への落とし込み（90分検証研修の構成、診断階段4段、3シグナルの証拠強度、内容と方法の同型性） | GitHub未収録 | 研修設計・研修評価の型 | `grow3-training-design-os.md`／`grow3-coaching-training-os.md`／`training-followup-report`スキル。support-osには原則のみ残した |
| 「経営＝意味を編む」理論（意味のつながり・文化＝意味のシステム） | GitHub未収録（メモのみ） | 独立した説明モデルの候補だが未検証 | 将来成立すればReference第1部（発見した構造）の候補。今は正本化しない。support-os第3部の「成果要求×意味要求」に接続点だけ置いた |
| システム原型の名称揺れ（対話「Fixes that Fail」／正本「応急処置の逆効果（Fixes that Backfire）」） | frameworks.md 第2部「構造原型」 | 内容ではなく表記の同期 | 正本の表記に揃える（support-osは「応急処置の逆効果」で記載済み） |

**新規追加ルール（再び混ざるのを防ぐ）**：今後新しく発見したものを何でも `grow3-frameworks.md` 第1部へ足す運用には戻さない。再利用可能なモデルそのものならReference（`grow3-frameworks.md`）、使い方・つなぎ方なら `grow3-support-os.md`、特定案件・特定研修の型なら各実装OS（training／hr／coaching）に置く。

## 5. 境界事例の判断基準（今回見えたもの）

道具の「機構がなぜ働くか」の説明は道具側（Reference）、「その道具をいつ使うか・使わないか」はOS側、という線を引いた。ただし「思考特性が機能する理由」のように、機構の説明そのものが「モノサシ言語化の後に自分の認知偏りを点検する」という使いどきを含む場合は、正本は道具側に置き、OS側から役割を参照する形にする。同じ知識を両方に書かない。

## 6. 参照・整合への影響

- **今回の変更（Phase 1）で更新が必要になる既存ファイルは無い。** `grow3-frameworks.md` の変更は冒頭の案内板追記のみで、H2見出し・本文エントリは不変。サンドボックスで `knowledge_build.py check` を実行したところ `STALE（構造的変化なし）` と判定され、`build` で `metadata_source_hash` が自動再生成された（STRUCTURAL_CHANGE WARNは発生しない）。
- 新規2本は frontmatter schema（DEC-017）に適合することを、リポジトリ同梱の `parse_frontmatter`／`validate_frontmatter`／`body_hash` で検証済み。INDEX.md には `os / draft / frameworks`・`os / draft / marketing` として自動掲載される。
- 同梱の `grow3-frameworks.revised.md` は `metadata_source_hash` を意図的に現行正本の値（`sha256:8ba0…`）のまま残している。本文（案内板）を変えたのに hash を先回りで書き換えると、`check` の STALE 検出と `build` の再生成記録（月次監査用の再生成回数）を経由せずに正本が変わるため。手順どおり `build` を実行すれば `sha256:401d198026d2cde2343e9184a2714d5e54e216a1ffda01a7bf7daca24e762f1b` に再生成される（サンドボックスで確認済み）。到着時点で FRESH にしたい場合は、この値を先に書き込んでもよい。
- 参考：取得時点の main では、変更を加える前の状態でも `check` が `INDEX.md`／`docs/INDEX.md` を「内容が古い」として ERROR にし、`tests/test_knowledge_build.py` の `TestRealRepositoryIsClean.test_check_passes` が失敗する（docs追加後に `build` が未実行のまま push された可能性）。今回の変更とは無関係だが、投入時に `build` を一度回せば同時に解消する。
- 任意の追随（提案。依頼範囲外のため未実施）：`grow3-training-design-os.md`・`grow3-hr-system-design-os.md`・`grow3-coaching-training-os.md` の冒頭「役割分担」行に「見立ての型は `grow3-support-os.md`」の一文を足すと、3層の案内が全OSから届く。

## 7. 未決事項（人間の判断が必要）

1. `MANAGED_FILES` の拡張（5本→7本）：DEC-017 の見直し条件「正本OSファイルが増減する」に該当する。**canonical化を待たず、draftのうちから hash／frontmatter 検査対象に入れる方が筋が通る**（root直下・`type: os`・INDEXの正本OS層に載るため）。別コミット用のパッチ `knowledge_build.managed7.patch.diff`（`MANAGED_FILES` に2行追加＋件数を書かないコメントへ修正2箇所）を同梱。サンドボックスで7本化して `check` を実行し ERROR 0／WARN 0、`tests/test_knowledge_build.py` 70件 OK を確認済み。**7本化後は `check` だけでなく必ず一度 `build` を実行する。**FRESH時の構造baselineは `check`（write=False）ではsnapshotへ保存されず、`build` 時にだけ保存される（サンドボックスで実証：check後は未記録、build後に2本とも記録）。`build` を挟まずにコミットすると、次に見出し等を変えたとき「構造baselineが未記録のため構造判定は行わない」となり、STRUCTURAL_CHANGEの比較が一回できなくなる。DEC-017の改定として記録する。
2. `domain` の値：新規2本は既存enum内（`frameworks`／`marketing`）に収めた。「支援OS」を独立domainにする必要は現時点では無いと判断。
3. 第1部の物理移管：**予定化しない**。当面は互換領域として現位置に据え置き、参照事故や検索摩擦（`logs/search-friction.yaml` の `canonical_not_found`／`multi_domain`）が実際に出たときにだけ再検討する。DEC-002「不足が起きてから最小限追加する」に合わせる。
4. `status: draft` → `canonical` の昇格は**2本で別ゲート**にする。`grow3-support-os.md` は、過去案件（KANDA等）の遡及検証＋新規案件での1判断点の前向き検証で大きな見落としが無ければ候補になれる。`grow3-business-model.md` は Grow3 自身の実商流でしか検証できないため、少なくとも「一つの接点 → 次の問い → 再接点」を実際に通し、可能なら月次対話を1〜数サイクル回してから。いずれもDEC-019により人間承認。
5. 残り物のうち「モノサシ抽出9段プロセス」の収録形式（`grow3-support-os.md` 配下の下位モジュールとして `references/` を持つか、別ファイルにするか）。

## 8. 承認手順（既存運用の延長・2ゲート）

INDEX.md／docs/INDEX.md はroot層とdocs層の実ファイル集合から毎回生成されるため、**配置をすべて終えてから `build` する**（buildの後にファイルを足すと、その時点でINDEXが再び古くなる）。

**Phase 1：3層アーキテクチャの投入**
1. `grow3-support-os.md`・`grow3-business-model.md` をリポジトリ直下に配置（`status: draft` のまま）。
2. 本メモを `docs/` に配置。
3. `grow3-frameworks.md` に案内板パッチ（`grow3-frameworks.header-patch.diff`）を適用（hashは旧値のまま）。
4. DEC-024 を DECISIONS.md に追記（本メモ9節の文面のまま。状態「確定」は2026-08-17の承認を反映する作業であり新たな判断ではない）。
5. `python scripts/knowledge_build.py check` → `grow3-frameworks.md: STALE（構造的変化なし）`、`INDEX.md`／`docs/INDEX.md` が古い、を確認。
6. `python scripts/knowledge_build.py build` → frameworks の hash 再生成、INDEX.md／docs/INDEX.md 再生成、snapshot 更新。
7. `check`（ERROR 0／WARN 0）→ `python -m unittest tests/test_knowledge_build.py` → commit。取得時点のmainに既存だったINDEX staleもこのbuildで正常化する。

**Phase 2：管理対象の7本化（別コミット）**
1. DEC-017 改定を DECISIONS.md に追記（下記10節）。
2. `knowledge_build.managed7.patch.diff` を適用（`MANAGED_FILES` 2本追加＋コメント2箇所）。
3. **`build` を実行**し、新規2本の構造baselineをsnapshotへ登録する（`check` では保存されない）。
4. `check`（新規2本が FRESH、ERROR 0／WARN 0）→ tests → commit。

## 9. DEC-024｜知識体系を Reference／OS／Business の3層に分け、OSを接続点として扱う

- 日付：2026-08-17
- 状態：確定（2026-08-17 承認。判断材料：実ファイル1,805行への分類、Reference維持の合理性、OS／Businessの既存正本不在、残り物に第4層が現れないこと、参照・build・INDEXとの互換性確認、中身のcanonical化との分離）。本DECは3層アーキテクチャという「器」の判断であり、`grow3-support-os.md`／`grow3-business-model.md` の中身の仮説を承認するものではない
- 対象：`grow3-frameworks.md`、`grow3-support-os.md`（新規）、`grow3-business-model.md`（新規）
- 決定：
  - 知識体系を Reference（What：道具の定義）／OS（How・When・Why：見立ての型）／Business（For whom・How delivered：届け方）の3層に分ける。OSがReferenceとBusinessをつなぐ接続点であり、3ファイルは横並びではない。
  - Reference層は既存の `grow3-frameworks.md` が該当し、ファイル名・第2部・第3部は変更しない。第1部「発見した構造」の正本も `grow3-frameworks.md` に置いたままとし、移管は予定化しない（参照事故・検索摩擦が出たときにだけ再検討）。
  - 新規2本は `status: draft` で追加する。canonical化は2本で別々のゲート（support-os＝遡及検証＋1判断点の前向き検証／business-model＝Grow3自身の実商流での検証）を経た人間承認による。
  - 道具の定義は Reference にのみ書き、OS・Business は `[→F:○○]` で参照する。正本は一か所、他はリンク。
  - 読む順番は OS概要 → Reference → OS本体とし、道具から入らない。
  - 新規追加ルール：再利用可能なモデルそのものはReference、使い方・つなぎ方はOS、特定案件・研修の型は各実装OSに置く。
- 理由：知識の種類（何を知っているか／どう考えるか／どう価値として届けるか）が違うものを一ファイルに置くと巨大化し、参照時に不要な文脈を読む負荷が生じるため。ファイル名変更は `MANAGED_FILES` 固定・17ファイルからの参照・DEC-020（Router不導入）と衝突するため避けた。残り物を洗った結果、第4の知識種類は現れず、粒度・適用先の違いに収まった。
- 採用しなかった案：3本を新規作成し `grow3-frameworks.md` を索引ファイルにする案（実質的なrename）／レンズ・翻訳・解像・動態の4分類でA〜Gを再編する案（分類軸が違うため第二索引として併置）／第1部を今回同時に移管する案（参照17箇所の横断変更になるため）／2本のcanonical化を同一ゲートにする案（検証手段が異なるため）。
- 付随：`MANAGED_FILES` の5本→7本化はDEC-017の改定として別コミットで扱う。
- 見直し条件：新規2本のいずれかが canonical に昇格する／`[→F:]` 参照の記法変更を伴う第1部移管を行う／canonical本数が増えて `MANAGED_FILES` の運用が変わる。

## 10. DEC-017 改定（案）｜MANAGED_FILES を7本にする

- 日付：2026-08-17
- 状態：提案（Phase 2 で確定）
- 対象：`scripts/knowledge_build.py` の `MANAGED_FILES`、`scripts/knowledge-structure-snapshot.json`
- 決定（案）：frontmatter必須・staleness検査の対象を、DEC-017の5本に `grow3-support-os.md`・`grow3-business-model.md` を加えた7本とする。draftのうちから検査対象に入れる（root直下・`type: os`・INDEXの正本OS層に載るため、検査対象外にする理由がない）。必須5項目・任意`related`・enum・抽出契約・hash算法（DEC-018）は変更しない。コードコメントは件数を書かない表現に改め、今後の増減で再びズレないようにする。
- 理由：DEC-017の見直し条件「正本OSファイルが増減する」に該当したため。`MANAGED_FILES` は7本となるが、新規2本は `status: draft` のため canonical は現時点5本であり、DEC-020のRouter検討条件（canonical 30本）には遠い。draft を canonical として数えない。
- 手順上の注意：適用後は `check` だけでなく `build` を実行し、新規2本の構造baselineをsnapshotへ登録する。
- 見直し条件：DEC-017と同じ。

