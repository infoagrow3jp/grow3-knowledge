---
status: draft
version: 0.1
基準日: 2026-07-18
作成者: 例外台帳・凍結検品ルール設計（AI支援）
改訂履歴: v0.1 draft → レビュー前修正 → 凍結前最終修正 → 凍結前最終清書（文書状態確定・§9受容済み限界・snapshotに台帳含む・classification意味・test契約明確化・読点推敲・Stop空白パス・Office index注記）
参照: scripts/pre-delivery-check.sh、scripts/pre-delivery-intentional-uncertainty.tsv、scripts/test-pre-delivery-check.sh、.githooks/pre-commit、scripts/stop-hook-check.sh、DECISIONS.md DEC-004／DEC-014／DEC-015
---

# pre-delivery-check 例外台帳設計メモ v0.1（draft）

本書は、リポジトリ出荷前検品（`pre-delivery-check`）における**意図的保留表記の例外台帳**と、**draft／frozenに応じた判定ルール**の設計draftである。

- 文書全体は、実装パラメータが未反映のため`status: draft`を維持する
- 本レビューで承認された設計判断は、次ゲートのDECISIONで凍結する
- 文書全体がdraftであっても、凍結後に実装が設計判断を変更してよいことを意味しない
- **本設計メモの作成後、同一作業内で実装・台帳変更・commitへ進んではならない（DEC-014）。**

---

## 0. 責務境界（必須）

| ツール | 役割 |
|---|---|
| **pre-delivery-check** | リポジトリ内の文書、schema、script等の成果物を検品する |
| **organization-diagnosis validator** | リポジトリ外を含む顧客caseのschema、ファイル、参照、来歴、出力境界を検証する |

本書が扱う例外台帳は**pre-delivery-check用**である。

organization-diagnosis validatorの次とは**別概念**であり、共通化しない。

- rule evaluation outcome
- finding
- severity
- 検査不能
- 顧客データの例外

将来共通部品化を検討する場合も、**別の設計判断**を要する。

### 0-1. 検出定義と説明文書の責務分離

| 責務 | 役割 |
|---|---|
| 説明文書（本書を含む） | 検出文字列そのものではなく、**rule名または分類名**で参照する |
| 検出器・語彙定義 | 実際の検出文字列を保持する |
| test fixture（実装ゲートで作成） | 実際の検出文字列を用いて検証する |

```text
現時点の検出文字列の正本:
  scripts/pre-delivery-check.sh

実装ゲート完了後の正本:
  scripts/pre-delivery-check.sh
  検出語彙を分離した場合はその語彙定義ファイル
  test fixtureは正本を検証するためのtest入力（正本そのものではない）
```

- 説明文書へ検出文字列を重複記載しない。
- これは検出回避ではなく、**検出定義と説明文書の責務分離**である。
- 説明文書で分類名を使っても、通常成果物の検出規則は緩和しない。
- WARN級の説明的自己参照も、同じ責務分離の対象とする。
- 説明的自己参照の置換によるWARN減少は、検品逃れではない。
- 禁止するのはWARN件数削減を目的とした曖昧化や削除である。
- 責務分離の結果として自己参照ノイズが減ることは正当である。
- 設計判断が未了の事項はWARNとして維持する。
- §9の語彙外表現の限界は**受容済みの既知の限界**であり、その本文記載に伴うWARNは、文書全体がdraftのため現時点では例外台帳へ登録しない。

### 0-2. 設計上の分類名（仮称）と衝突確認

現行コードに正式rule名はない。次を**設計上の仮称**とする。

| 仮称 | 対応する現行検出区分（正本はスクリプト） | 台帳 |
|---|---|---|
| `soft-uncertainty-term` | 行単位・固定部分一致・status連動・台帳あり | あり |
| `review-required-marker` | ファイル単位・固定部分一致・status連動 | なし |
| `task-reminder-term` | ファイル単位・固定部分一致・status連動 | なし |
| `temporary-placeholder-term` | ファイル単位・固定部分一致・status連動 | なし |
| `hard-placeholder-symbol-pair` | ファイル単位・固定部分一致・**常時FAIL** | なし |
| `hard-placeholder-triple-x` | ファイル単位・固定部分一致・**常時FAIL** | なし |

**命名規則：**

- rule名・分類名は検出対象文字列を直接含めない
- 固定部分一致や大文字小文字非区別でも衝突しない名称とする
- 新しい検出語彙を追加する際は、既存rule名・分類名との衝突を確認する
- 語彙変更時は衝突確認testを追加または更新する

**今回の衝突確認（現行スクリプトの固定一致に対して）：**

- 上記仮称は、現行の部分一致語のいずれにも**文字列として一致しない**ことを目視確認した
- `hard-placeholder-triple-x` は大文字3連続パターンと一致しない（小文字ハイフン区切り）
- `task-reminder-term` は大文字のタスク残リマインダ語と一致しない

### 0-3. 今回の対象外（保留表記検品設計の範囲外）

次は**今回の保留表記検品設計の対象外**とする。必要なら別設計ゲートで扱う。

```text
- 読点検出
- AI語検出
- ブランド色検出
- その他のWARNカテゴリにおけるindex／working tree非対称
```

読点カテゴリは検品ルール設計の対象外である。本メモ内の改行直前読点の整形は、**新規文書としての通常の文章推敲**であり、読点検出ルールの設計変更ではない。

また、`normalize_rel_path`がリポジトリ外ファイルでbasenameへ縮退する挙動は、検査対象をリポジトリ内成果物に限定するv0.1運用では実害がないため、**今回の実装対象外**とする。将来リポジトリ外ファイルを検査対象にする場合は見直し条件とする。

---

## 1. 目的

意図的に残す `soft-uncertainty-term` 該当表記を、黙認ではなく**監査可能な狭い例外**として管理し、次を同時に満たす検品ルールを設計する。

- 凍結文書（`status: frozen`）に未登録の該当表記が残ることを防ぐ
- draft文書では意図的保留をWARNとして可視化する
- 次の回避経路を塞ぐ（v0.1が保証する範囲）
  - 台帳登録行の文言変更
  - 同件数の内容すり替え
  - 既知の検出語彙による回避
- 台帳自体の陳腐化・重複・不正を**FAIL**として検出する
- 検品ルールを説明する文書（自己参照）を恒久的な黙認にしない

語彙外の同義表現を完全検出できない点は、§9の**v0.1で受容済みの既知の限界**として維持する（目的文と矛盾させない）。

---

## 2. 対象範囲

### 含む

- `scripts/pre-delivery-check.sh` の保留表記検出・status切替・台帳整合
- `scripts/pre-delivery-intentional-uncertainty.tsv` の識別単位・分類・ライフサイクル
- `.githooks/pre-commit`／`scripts/stop-hook-check.sh` の走査モード
- `scripts/test-pre-delivery-check.sh` の回帰ケース拡張設計
- 検出語彙の管理方針
- 文書全体statusと層別status（例：validator設計メモ）の関係

### 含まない

- pre-delivery-check本体の実装変更（本書では行わない）
- 例外台帳への行追加・削除（本書では行わない）
- organization-diagnosis validatorの例外・finding設計
- DECISION確定・文書凍結
- §0-3に列挙した対象外カテゴリ

---

## 3. 現状仕様（実物ベース）

正本コード：`scripts/pre-delivery-check.sh`  
正本台帳：`scripts/pre-delivery-intentional-uncertainty.tsv`  
呼び出し：`.githooks/pre-commit` → `--staged`、`scripts/stop-hook-check.sh` → 変更＋未追跡ファイル列挙

**fixtureは未作成。** 現時点の検出文字列の正本はスクリプト本体のみ。

### 3-1. 検出対象（現状＝説明は分類名）

| 区分 | 分類名（仮称） | 照合 | 単位 | 台帳 | status連動 |
|---|---|---|---|---|---|
| A | `soft-uncertainty-term` | 固定部分一致 | **行単位** | **あり** | draft/reviewed→WARN、それ以外→FAIL（未登録時） |
| B | `review-required-marker`／`task-reminder-term`／`temporary-placeholder-term` | **固定文字列による部分一致** | **ファイル単位** | なし | draft/reviewed→WARN、それ以外→FAIL |
| C | `hard-placeholder-symbol-pair`／`hard-placeholder-triple-x` | **固定文字列による部分一致** | **ファイル単位** | なし | **常にFAIL** |

#### B群・C群の照合方式（現状の正確な記述）

```text
固定文字列による部分一致
フィルタ後テキスト全体をファイル単位で検査
各検出語につき1ファイル1判定
```

- 実装は `grep -qF`（固定文字列）である。正規表現ではない。
- 行全体またはファイル全体との**完全一致でもない**。
- フィルタ後テキストが検出語を**包含していれば検出される**（前後に別文字列があってもヒットする）。

#### fence除外の適用範囲（現状）

```text
現行:
  A群、B群、C群のすべてでfenced code block内が検出対象外
  （行スキャン／PROSE_TEXT生成の双方でfence除去後を検査）

v0.1推奨:
  通常成果物ではA群、B群、C群のすべてについてfenceを原則走査
```

- 現行回帰test #3の期待値は「fence内のA群検出語 → exit 0」。
- 実装後は**期待値の反転**が必要（fence内A群 → 検出／frozenならFAIL）。
- push済みの全`docs`および`DECISIONS.md`について、現行fence内の検出語該当は**0行**だった（実測）。fence原則走査への移行により、現時点で既存文書の台帳件数が増える事例は確認されていない。ただし原理上、登録済み`exact_line`と同じ行がfence内にも存在する文書では実件数が増加しうるため、実装前の台帳事前監査で確認する。

#### 「記録形式」節除外（現状）

```text
現行:
  DECISIONS.md限定ではない
  すべての走査対象ファイルで「## 記録形式」から次のH2までを除外

抜け穴:
  一般文書で同名節を作るだけで、該当節内の検出を回避できる

v0.1推奨:
  「記録形式」節の除外はDECISIONS.mdだけに限定する
  その他の文書では通常どおり検出する
```

その他の補足（現状挙動）：

- 正規表現ではない（公開禁止パターン等の別チェックを除く）。
- 大文字小文字・全角半角の正規化は行わない。
- Markdown表・見出し・箇条書き・YAML frontmatter本文行も、フェンス外なら検出する。
- HTML comment・blockquote・inline codeは専用除外なし。

**注意：** コードコメントと実装が不一致（draft未登録をFAILと書いたコメントがあるが、実装はWARN）。

### 3-2. statusによる判定（現状）

`get_doc_status` は frontmatter 先頭の `status:` **1行だけ**を読む。層別statusは非認識。

| frontmatter `status` | 未登録のA/B | 登録済みA | C（hard） |
|---|---|---|---|
| `draft` / `reviewed` | WARN | WARN（台帳） | FAIL |
| `frozen` その他・空・statusなし | FAIL | WARN（台帳） | FAIL |

### 3-3. 例外台帳の識別単位（現状）

```text
path<TAB>expected_count<TAB>classification<TAB>exact_line
```

`reason`列は**現行にない**。v0.1推奨では必須化し、列順を§7のとおりとする。

現行台帳の実測：

```text
現行登録:
  27行

内訳:
  history 8 / data_state 1 / deferred_v0.2 16 / implementation_detail 1 / meta_check 1

TABを含むexact_line:
  0件

現時点の移行実害:
  なし
```

### 3-4. 台帳整合検査（現状→推奨への差分）

| 事象 | 現状 | v0.1推奨 |
|---|---|---|
| 台帳ファイル自体が不在 | FAIL（読込時） | **FAIL**（維持） |
| 登録先ファイル不在 | 黙殺 | **FAIL** |
| 完全一致行が0件 | WARN | **FAIL**（台帳陳腐化） |
| 実件数 ＜ expected | 未検知 | **FAIL** |
| 実件数 ＞ expected | FAIL | **FAIL**（維持） |
| 同一登録重複 | FAIL | **FAIL**（維持） |
| 不正classification | FAIL | **FAIL**（維持） |
| expected_count ≤ 0 | FAIL | **FAIL**（維持） |
| expected_countが非数値 | FAIL | **FAIL**（維持） |
| reasonなし／空白 | （列なし） | **FAIL**（新） |
| exact_lineにhard検出語 | （未検査） | **台帳読込FAIL**（新） |

陳腐化をWARNのまま残す案は**不採用**。件数減少が本文改善であっても、台帳が古いこと自体を検品不整合とみなす。

### 3-5. 走査モードと内容ソース（現状と推奨）

#### 現状の`--staged`

```text
現行:
  stagedファイル名を収集（git diff --cached --diff-filter=ACM）
  working tree本文を検査（ファイルパスを直接読む）
  frontmatter statusもworking treeから読む
  例外台帳もworking tree上の既定パス（または明示指定パス）から読む

問題:
  staged内容とunstaged内容が異なる場合は
  commit対象と検品対象が一致しない
```

リネームについて（現状）：

```text
- 追加A、コピーC、修正Mは走査対象
- リネームRは走査対象外
- リネームと編集を同時にstageしGitがR判定すると
  編集内容が本文検査から漏れる可能性がある
```

台帳登録済みファイルは旧path消失を台帳整合で検出できる場合があるが、**未登録のfrozen文書には効かない**ため、本文走査側で閉じる必要がある。

本文検査対象0件時（現状）：

```text
TARGETSが0件のとき、台帳整合（check_stale）前に正常終了する
```

#### v0.1推奨：同一snapshot整合＋台帳全体整合

```text
通常本文の検出:
  staged対象ファイルを走査

例外台帳の整合検査:
  台帳に登録された全path・全登録を毎回走査
  本文検査対象が0件でも、台帳読込と全登録整合検査は必ず実行する
```

```text
pre-commit:
  本文、frontmatter status、例外台帳をGit indexから読む
  （commitされるsnapshot全体を検品対象とする）

Stopフック・手動実行:
  本文、frontmatter status、例外台帳をworking treeから読む
```

**本文・status・例外台帳は、必ず同一の内容ソース（同一snapshot）から取得する。**

禁止する混在：

```text
本文・status: Git index版 / 例外台帳: working tree版
本文・status: working tree版 / 例外台帳: Git index版
本文: Git index版 / status: working tree版
```

理由：本文・status・台帳のstage状態が異なる場合に、WARN／FAILの判定がcommit対象とずれるため。

#### 例外台帳のindex読取の適用範囲

既定台帳を使用する場合：

```text
scripts/pre-delivery-intentional-uncertainty.tsv

pre-commit:
  本文 = Git index
  frontmatter status = Git index
  既定の例外台帳 = Git index
```

環境変数等で台帳パスが明示指定された場合：

```text
PRE_DELIVERY_UNCERTAINTY_REGISTRY=<path>

明示指定台帳:
  Git index版を要求しない
  指定パスの実ファイルを読む
```

理由：

```text
- 回帰testは一時ディレクトリ内の台帳を使用する
- それらの台帳はGit indexに存在しない
- 明示指定されたtest用台帳までindex読取へ強制すると
  現行test基盤と両立しない
```

したがってindex読取の対象は**既定のリポジトリ内台帳パス**に限定する。  
**本番pre-commitのsnapshot整合**と**test fixture用の明示指定台帳**を混同しない。

リネーム（v0.1推奨）：

```text
git diff --cached --diff-filter=ACMR
```

リネーム後の新pathと、Git index上の新しい本文を検査対象にする。削除`D`は本文が存在しないため本文検査対象にしないが、台帳登録済みファイルの削除は台帳全体整合で検知する設計を維持する。

これにより全リポジトリ本文走査を避けつつ、次を検知する。

- 登録先ファイル削除
- ファイル移動
- 完全一致行の変更
- 件数不足／超過
- 古い台帳登録の残存
- リネーム＋編集による未登録違反の混入

将来台帳が大規模化し負荷が問題になった場合は、CI等への分離を見直し条件とする。

### 3-6. 検出語彙の現状管理

| 項目 | 現状 |
|---|---|
| 管理場所 | `scripts/pre-delivery-check.sh` 内ハードコード |
| 承認 | コード変更の通常レビュー |
| 語彙変更時test | 一部あり。語彙リスト全体の契約テストはない |

候補語の拡充（検討中・要検討・TBD等）は、誤検知が大きいため**v0.1では追加しない**。

### 3-7. Office文書の責務境界（現状と推奨）

現状：

```text
A群:
  元のバイナリファイルを行走査している

B群・C群:
  ZIP内XMLから抽出したテキストを走査している

status:
  YAML frontmatterを取得できないため、draft/reviewedとして判定できない
```

v0.1推奨：

```text
A群の行単位検出とexact-line台帳:
  md、txt、html、htm等の安定したテキスト系ファイルを対象

pptx、docx、xlsx:
  exact-line例外台帳の対象外
```

Office文書でA/B/Cを共通化する場合は、**正規化テキスト仕様を別工程で設計する**。

#### 実装注記：Office文書のGit index読取

これは新しい設計判断ではなく、実装者向けの注記である。pre-commitでOffice文書のGit index版を検査する場合：

```text
Markdown等:
  git show ":<path>" の標準出力を直接テキスト処理できる

pptx / docx / xlsx:
  index上のバイナリを一時ファイルへ書き出したうえで
  unzip等の既存抽出処理へ渡す必要がある
```

実装イメージ：

```text
1. Git index上のOfficeバイナリを一時ファイルへ書き出す
2. 一時ファイルへ既存のZIP/XML抽出処理を適用する
3. 処理後に一時ファイルを確実に削除する
```

制約：

```text
- 一時ファイル名は衝突しない方法で生成する
- trap等で正常・異常終了時とも削除する
- working treeのOfficeファイルへフォールバックしない
```

Office文書はexact-line台帳の対象外という設計を維持する。この注記は、B/C等のOffice検出においても、commit対象と検品対象を一致させるための実装上の補足である。

### 3-8. 検出・台帳照合・件数計数の走査基盤（設計原則）

```text
同じ検出区分について
検出・台帳exact照合・expected_count計数は
常に同一の内容ソースと同一の文脈フィルタを使用する。
```

特にA群について、次の3処理を分離しない。

```text
1. 検出対象行の抽出
2. exact_lineとの一致確認
3. expected_countの実件数計数
```

- fence原則走査を有効にする場合は、これら3処理すべてでfence内を対象にする。
- 「記録形式」節の扱いを変更する場合も、3処理すべてへ同じ条件を適用する。
- 本文ソースについても同様（pre-commitは3処理すべてGit index版、Stop／手動はすべてworking tree版）。

禁止する不整合の例：

```text
検出: fence内を含む / 件数計数: fence内を除外
検出: Git index版 / exact照合: working tree版
```

---

## 4. 現状の問題

1. frozen化で未登録の `soft-uncertainty-term` が一括FAIL化し、commit不能になった実例
2. 文書全体をdraftへ戻すとWARNになり通過する（層別status非認識）
3. 語彙外の同趣旨表現へ変えると機械検出を回避できる（v0.1で受容済みの既知の限界）
4. 正当改訂でもexact台帳追随が必要
5. DECISIONS.mdの改行直前読点WARNは別カテゴリ負債（今回対象外）
6. fence除外がA/B/Cすべてで回避経路になる（現行）
7. 「記録形式」節除外が全ファイルに及び、同名節だけで回避できる
8. ファイル削除時の台帳黙殺、件数不足の未検知、本文0件時の台帳整合スキップ
9. stagedはファイル名のみindex、本文／status／台帳はworking tree（非対称）
10. リネームRがstaged走査から漏れる
11. 説明文書への検出文字列重複記載が自己参照ノイズ／hard FAILを生む
12. Office文書でA群とB/C群の走査基盤が不一致

---

## 5. 識別方式3案比較（要約）

| 案 | 結論 |
|---|---|
| A 完全一致行 | **v0.1採用**。すり替え耐性・レビュー容易性を優先 |
| B ファイル×分類×件数 | **不採用**。同件数すり替えが致命的 |
| C 安定識別子ハイブリッド | **v0.1非採用**（将来候補）。同義語回避が反復した場合に再検討 |

---

## 6. 二層ステータスとの関係

validator設計メモ（DEC-015）：文書全体draft／思想層frozen／パラメータ層implementation-time decision。

| 案 | v0.1 |
|---|---|
| 検品は文書全体statusのみ | **採用** |
| 層別statusをcheckerが解釈 | **不採用**（複雑化） |
| 思想層凍結はDECISION担保 | **採用** |

---

## 7. 台帳スキーマとライフサイクル（v0.1推奨）

### 7-1. 論理5列（reason → exact_line）

```text
path<TAB>expected_count<TAB>classification<TAB>reason<TAB>exact_line
```

論理構造：

```text
第1論理列: path
第2論理列: expected_count
第3論理列: classification
第4論理列: reason
第5論理列: exact_line
```

parserは**最初の4個のTABだけ**を列区切りとして解釈し、それ以降の文字列全体を`exact_line`として扱う。

```text
- pathにはTAB・改行を許可しない
- expected_countにはTAB・改行を許可しない
- classificationにはTAB・改行を許可しない
- reasonにはTAB・改行を許可しない（作成規約）
- reasonはtrim後に空ならFAIL
- exact_lineは空文字を許可しない
- exact_lineには本文の逐語性を保つためTABを許可する
- parserは最初の4個のTABだけを区切りとして扱う
- 4個未満のTABしかない行は列不足としてFAIL
```

通常の`NF=5`による物理フィールド数検証は**採用しない**。

理由：本文行にTABが含まれる場合でも、`exact_line`を逐語的に台帳登録できるようにするため。将来TAB入り本文行が現れても構造的に登録不能にならないよう、最終列方式を採用する。

#### reason内TABの既知特性

最終列方式では、作成者が`reason`内へTABを入力したつもりでも、parser上は次のように解釈される。

```text
reason:
  4個目のTABより前の文字列

exact_line:
  4個目のTABより後の文字列を先頭に含む、ずれた本文行
```

したがって「reasonにTABが含まれている」という意図を、**台帳構文だけから直接識別することはできない**。これは最終列方式の**既知特性**である。

間接的な検出経路：

```text
ずれたexact_lineが対象文書の本文行と一致しなくなる
→ 登録されたexact_lineの実件数が0
→ 台帳陳腐化FAIL
```

reason内TABを構文段階で直接拒否するには、escape規則・quote規則・TSV以外の構造化形式のいずれかが必要となる。これらは**v0.1では導入しない**。

v0.1の運用：

```text
reasonへTABを使用しないという作成規約
+
ずれたexact_lineを検出する台帳全体整合
```

将来、reasonへTABを含む任意文字列を安全に保存する必要が生じた場合は、**台帳形式そのものの見直し条件**とする。

### 7-2. classificationの意味（例外を残す理由の種類）

classificationはseverityやライフサイクルではなく、**例外を残す理由の種類**である。  
現行台帳27行の用途に沿った定義：

| classification | 意味 | 現行件数 |
|---|---|---|
| `history` | 過去の判断、改訂履歴、不採用案等を逐語的に保存する表記 | 8 |
| `data_state` | 現在のデータ状態として未確認・未取得であることを明示する表記 | 1 |
| `deferred_v0.2` | v0.1では扱わず、後続versionへ正式に送った事項 | 16 |
| `implementation_detail` | 設計原則は確定しているが、実装工程で決める具体パラメータ | 1 |
| `meta_check` | 設計・作業が soft-uncertainty-term 該当の保留を勝手に埋めていないこと等を確認する自己検品表記 | 1 |

現行台帳ヘッダの分類基準とも整合する。lifecycle（active／resolved／obsolete）はv0.1必須にしない。

### 7-3. 移行手順（実装前の先行手順）

現行 → 移行後：

```text
現行:
  path / expected_count / classification / exact_line

移行後:
  path / expected_count / classification / reason / exact_line
```

既存の`exact_line`の前に`reason`を挿入する。4列形式の暫定許容は行わない。

実装前の先行手順：

```text
1. 現行台帳を新5列schemaで事前監査
2. 全既存登録へreasonを付与
3. 登録先ファイル不在、0件、件数不足を確認
4. classificationの妥当性を全件再確認
5. parser、台帳、testを同一commitで切り替える
```

同一commitで切り替えるもの：

```text
- parser変更
- 現行台帳全行へのreason追記
- 台帳整合の事前監査
- 回帰test更新
```

### 7-4. hard検出語の台帳登録拒否（検査仕様）

方針ではなく**検査仕様**とする。

```text
例外台帳のexact_lineにhard検出語が含まれる場合:
  台帳読込FAIL

hard検出語:
  例外台帳の対象外
```

- 説明文書では実際の検出文字列を直接書かず、分類名（`hard-placeholder-symbol-pair`／`hard-placeholder-triple-x`）で参照する。
- この検査は、hard failureを台帳で黙認できないことを保証する。

### 7-5. meta_check先例と受容済み限界の将来登録

現行台帳の`meta_check`既存登録は、**設計上の自己確認行を台帳化した先例**である（schema設計メモのチェックリスト行）。

validator設計メモの受容済み限界を将来登録する場合は、次の2案を比較し、**人間判断として残す**。

```text
案1: meta_checkを使用する
案2: accepted_risk分類を追加する
```

### 7-6. 陳腐化はすべてFAIL

§3-4の表どおり。WARN据え置きは不採用。

owner、期限、review_trigger、lifecycle（active／resolved／obsolete）は**将来候補**。v0.1必須にはしない。

---

## 8. 判定モデル（推奨）

```text
検出結果 ≠ 登録状態 ≠ 文書状態 ≠ 台帳状態 ≠ 最終判定
```

| 条件 | 最終判定 |
|---|---|
| draft×未登録のA/B | WARN |
| draft×登録済みA | WARN |
| frozen×未登録のA/B | FAIL |
| frozen×登録済みA | WARN（PASSへ格上げしない） |
| hard（C） | 常にFAIL（例外台帳対象外） |
| exact_lineにhard検出語を含む台帳行 | 台帳読込FAIL |
| 台帳陳腐化・件数不一致・reason欠落等 | **FAIL** |

---

## 9. 語彙検出の限界（v0.1で受容済みの既知の限界）

v0.1は現行語彙方式を維持し、安定識別子を導入しない。

**v0.1で受容済みの既知の限界：**

検出語彙に含まれない表現で書かれた未確定事項は、機械検品だけでは捕捉できない。

補足：

- 語彙検出は、既知の危険表現を拾う探索網である
- 未確定事項の意味的な完全検出を保証しない
- frozen文書の意味確認は、人間レビューとDECISIONも担う
- 新しい回避表現を発見した場合は、検出語彙とtestを同一commitで追加する
- 同義語回避が反復する場合は、安定識別子方式への移行を再検討する

**確定内容：**

```text
- 語彙外表現の検出限界はv0.1で受容する
- 本メモ§9の当該2件のsoft WARNは
  受容済みの既知の限界を本文へ記載したWARNである
- 文書全体はdraftのため、現時点では例外台帳へ登録しない
- 設計判断の凍結はDECISIONで担保する
```

---

## 10. 文脈別検出と自己参照

### 10-1. fenced code block（v0.1推奨）

| 対象 | 扱い |
|---|---|
| 通常成果物 | **A/B/Cすべてについてfenceを含め原則走査**（一律除外は不採用） |
| 検出器の定義ファイル | 検出文字列の正本として保持 |
| 将来のtest fixture | 実際の検出文字列で検証 |
| 説明文書 | rule名／分類名で参照（検出文字列を書かない） |

理由：fenceへ移動するだけで検出を回避できる状態を残さないため。検出・exact照合・件数計数は同一フィルタでfence内を含む（§3-8）。

### 10-2. 採用しない自己参照回避

| 方法 | 不採用理由 |
|---|---|
| fenceへの退避 | 通常文書でfenceが検品回避経路となるため |
| hard failure語を例外台帳へ登録可能にする | hard failureの意味を弱め、本来禁止すべきplaceholderを黙認する経路となるため |
| 単なる文字分断・同義語置換 | 説明責務の整理を伴わない場合、検品通過だけを目的とした迂回になるため |

**採用：** 検出文字列の正本をコード（および将来の語彙定義／fixture）へ置き、説明文書では分類名で参照する。

### 10-3. 自己参照の二分類

| 種別 | 意味 | 扱い |
|---|---|---|
| A. 設計判断が未了の事項 | 設計としてまだ判断していない事項 | WARNとして残してよい |
| B. 説明的自己参照 | 検出ルール説明のため検出文字列を書いたもの | 分類名参照へ置換（正当なWARN減少） |
| （参考）受容済みの既知の限界の本文記載 | §9のとおり | draft中は台帳未登録のWARNとして許容 |

### 10-4. fixture配置方針（実装ゲート）

現行の`scripts/*`はpre-delivery-checkの走査除外対象である。実装ゲートで作るfixtureの配置候補：

```text
scripts/fixtures/pre-delivery-check/
```

理由：

```text
- 通常成果物の走査対象から分離できる
- 実際の検出文字列をtest入力として保持できる
- fence原則走査と自己参照問題を追加の例外なしで分離できる
```

fixtureは検出文字列の正本ではなく、**正本を検証するtest入力**であることを維持する。

---

## 11. 走査モード推奨（再掲）

**同一snapshot（本文・status・既定台帳）＋台帳全体整合**（§3-5）。

- pre-commitはGit index、Stop／手動はworking tree
- 明示指定台帳は指定パスの実ファイル（index非要求）
- 本文検査対象0件でも台帳読込と全登録整合は必ず実行
- リネームは`ACMR`
- 陳腐化・削除・移動・件数不一致の保証タイミング：毎回のpre-commitにおける台帳全体整合

---

## 12. test設計

実装ゲートで作成する。fixtureは現時点で未作成。

### 12-0. 契約原則

各**実行回帰test**は次を固定する。終了コードだけが一致し、別の理由でFAILした場合は**test成功としない**。

```text
期待exit code
期待する診断
含んではならない診断
```

「AまたはB」のどちらでも成功とする期待診断は残さない。  
数値のexit codeを持たないものは、実行testへ落とすか、静的契約確認／観測・mutation確認へ分離する。

### 12-1. 重複ケースの整理

| 旧組 | 判断 | 理由 |
|---|---|---|
| #14 / #16（語彙外同義） | **統合** | 実行モード・守る仕様が同一 |
| #12 / #25（移動・旧path残） | **統合** | いずれも台帳全体整合のパス追随 |
| #9 / #26（同件数すり替え） | **統合** | 案B不採用根拠と内容すり替えが同一仕様 |
| #27 / #31（分類名自己参照） | **統合** | 説明責務分離の検証として同一 |

### 12-2. 実行回帰test

| # | 入力概要 | 実行モード | 期待exit | 必須診断 | 含んではならない診断 | 守る仕様 |
|---|---|---|---|---|---|---|
| E01 | 検出表現なしdraft | 手動 | 0 | 保留表記のWARN/FAILなし | soft未登録FAIL | 正常系 |
| E02 | draft＋未登録 soft | 手動 | 0 | soft未登録WARN | soft未登録FAIL | draft可視化 |
| E03 | frozen＋未登録 soft | 手動 | 1 | soft未登録FAIL | 台帳陳腐化だけのFAIL | 凍結厳格 |
| E04 | frozen＋登録済みexact | 手動 | 0 | 登録済みWARN | 未登録FAIL | 意図的例外 |
| E05 | exact 1文字変更（新行あり・旧行消失） | 手動 | 1 | 新しい行の未登録FAIL **および** 旧登録行の台帳陳腐化FAIL | 片方のみでの成功扱い | すり替え |
| E06 | 実件数＞expected | 手動 | 1 | 件数超過FAIL | 列不足FAIL | 件数上限 |
| E07 | 実件数＜expected | 手動 | 1 | 件数不足FAIL | 件数超過FAIL | 件数下限 |
| E08 | 登録行削除（実件数0） | 台帳整合 | 1 | 台帳陳腐化FAIL | reason不正FAIL | 消失 |
| E09 | 同件数で別行へ入替 | 手動 | 1 | 新しい行の未登録FAIL **および** 旧登録行の台帳陳腐化FAIL | 件数超過FAILのみ | 内容すり替え |
| E10 | 台帳key重複 | 台帳読込 | 1 | 重複登録FAIL | 陳腐化FAIL | 重複 |
| E11 | 不正classification | 台帳読込 | 1 | classification不正FAIL | 列不足FAIL | 分類契約 |
| E12 | ファイル移動、旧path残存 | 台帳整合 | 1 | 登録先ファイル不在FAIL | soft未登録FAIL | 移動 |
| E13 | 語彙外同義表現（draft） | 手動 | 0 | 当該語彙では非検出 | soft検出WARN/FAIL | 受容済み限界 |
| E14 | 語彙追加後：frozen本文に新語 | 手動 | 1 | 新語による検出FAIL | 旧語のみのヒット | 語彙変更契約 |
| E15 | fence内A群・frozen | 手動 | 1 | soft未登録FAIL | exit 0（現行test#3反転） | fence原則走査 |
| E16 | fence内B群・draft | 手動 | 0 | B群WARN | fence除外による非検出 | fence原則走査 |
| E17 | fence内B群・frozen | 手動 | 1 | B群FAIL | B群WARN格下げ | fence原則走査 |
| E18 | fence内C群 | 手動 | 1 | hard FAIL | WARN格下げ | fence原則走査 |
| E19 | blockquote内soft・frozen | 手動 | 1 | soft未登録FAIL | 非検出 | 引用退避禁止 |
| E20 | inline code内soft・frozen | 手動 | 1 | soft未登録FAIL | 非検出 | インライン退避禁止 |
| E21 | frontmatter内soft・frozen | 手動 | 1 | soft未登録FAIL | 非検出 | FM対象 |
| E22 | HTML commentに安定ID（検出語なし） | 手動 | 0 | 非ヒット | soft/hard検出 | マーカー衝突回避 |
| E23 | 一般文書の「記録形式」節内soft・frozen | 手動 | 1 | soft未登録FAIL | 節除外による非検出 | 一般文書は除外しない |
| E24 | DECISIONS.mdの「記録形式」節内に検出対象語（他違反なし） | 手動 | 0 | 当該節内表記は検出対象外 | 記録形式節内の検出語に基づくWARN/FAIL | DECISIONS限定除外の陽性回帰 |
| E25 | 自己参照説明draft（分類名のみ・§9限界記載なし） | 手動 | 0 | 検出文字列自己参照なし | 説明文字列での誤検出 | 責務分離 |
| E26 | 台帳ファイル自体が存在しない | 台帳読込 | 1 | 台帳不在FAIL | 検査対象なしexit 0 | 台帳必須 |
| E27 | 区切りTABが4個未満 | 台帳読込 | 1 | 列不足FAIL | 陳腐化FAIL | 論理5列 |
| E28 | reasonが空または空白 | 台帳読込 | 1 | reason必須FAIL | 列不足FAIL | reason必須 |
| E29 | reasonあり・正常5列・違反なし本文 | 台帳読込＋手動 | 0 | 読込成功・保留表記FAILなし | 列不足FAIL | reason必須 |
| E30 | exact_lineにTABを含むfrozen登録済みfixture | 手動 | 0 | 登録済みWARN | 列数誤認FAIL | TAB許容 |
| E31 | reason内にTABを入力した台帳行（ずれたexactが本文に無し） | 台帳整合 | 1 | exact_line不一致による台帳陳腐化FAIL | reason列不正FAIL | 既知特性の間接検出 |
| E32 | exact_lineが空 | 台帳読込 | 1 | exact_line空FAIL | 陳腐化FAIL | exact必須 |
| E33 | hard語をexact_lineへ登録 | 台帳読込 | 1 | hard台帳登録拒否FAIL | 陳腐化FAIL | hard非例外化 |
| E34 | 登録先ファイル不在 | 台帳整合 | 1 | 登録先ファイル不在FAIL | 黙殺exit 0 | 削除検知 |
| E35 | expected_count = 0 | 台帳読込 | 1 | expected_count不正FAIL | 陳腐化FAIL | 件数契約（現行test復元） |
| E36 | expected_countが非数値 | 台帳読込 | 1 | expected_count不正FAIL | 列不足FAILのみ | 件数契約 |
| E37 | expected_countが負数 | 台帳読込 | 1 | expected_count不正FAIL | 列不足FAILのみ | 件数契約 |
| E38 | 空白を含むパスのfrozen＋未登録soft（手動） | 手動 | 1 | soft未登録FAIL | path切断による別診断 | path耐性 |
| E39 | 空白を含むパスのfrozen＋未登録soft（Stopフック経由） | Stop | 1 | soft未登録FAIL | 引数分割・glob展開による誤診 | Stop quoted展開 |
| E40 | fixture内の検出文字列を含む内容を一時成果物パスのfrozen文書へコピー | 手動 | 1 | soft未登録FAIL | fixture配置先の除外による非検出 | fixtureはtest入力 |
| E41 | staged版は正常／working tree版は違反 | `--staged` | 0 | index版で当該違反なし | WT版違反でのFAIL | index本文 |
| E42 | staged版は違反／working tree版は正常 | `--staged` | 1 | index版で違反FAIL | WT版正常でのexit 0 | index本文 |
| E43 | staged本文違反＋staged status frozen、WTは本文・status変更済み | `--staged` | 1 | index本文＋index statusによるsoft FAIL | WT statusのWARN格下げ | 同一snapshot |
| E44 | staged本文正常＋staged status frozen、WTだけdraft＋違反本文 | `--staged` | 0 | index本文＋index statusで当該違反なし | WT draft違反WARNの混入 | 同一snapshot |
| E45 | staged既定台帳は正常／WT既定台帳は不正 | `--staged` | 0 | index台帳で読込成功 | WT台帳不正でのFAIL | 既定台帳=index |
| E46 | staged既定台帳は不正／WT既定台帳は正常 | `--staged` | 1 | index台帳に基づく台帳読込FAIL | WT台帳正常でのexit 0 | 既定台帳=index |
| E47 | `PRE_DELIVERY_UNCERTAINTY_REGISTRY`で一時台帳（不正classification）を指定 | 手動 | 1 | classification不正FAIL | 台帳のindex不在を理由とするFAIL | 明示指定=実ファイル |
| E48 | リネームのみ（違反なし文書） | `--staged` | 0 | 新pathを走査し違反なし | 旧pathのみ検査 | ACMR |
| E49 | リネーム＋違反内容の編集 | `--staged` | 1 | 新pathのindex本文で違反FAIL | リネーム漏れによるexit 0 | ACMR |
| E50 | 未登録frozenをリネーム＋編集 | `--staged` | 1 | 本文検査でsoft FAIL | 台帳整合依存だけの成功 | 本文側で閉じる |
| E51 | 登録対象ファイルだけ削除（本文対象0件） | `--staged` | 1 | 登録先ファイル不在FAIL | 「検査対象なし」exit 0 | 0件でも整合 |
| E52 | 台帳ファイルだけをstage（不整合fixture） | `--staged` | 1 | 台帳不整合FAIL | 本文0件スキップ | 0件でも整合 |
| E53 | staged対象がすべて除外対象（台帳不整合fixture） | `--staged` | 1 | 台帳不整合FAIL | 除外だけを理由に整合スキップ | 0件でも整合 |
| E54 | 登録済みexactがfence外1・fence内1、expected_count=2 | 手動 | 0 | 登録済みWARN（実件数2） | 件数超過FAIL | fence内も計数 |
| E55 | 同条件でexpected_count=1 | 手動 | 1 | 件数超過FAIL | 陳腐化FAILのみ | fence内も計数 |

E23とE24は**対になる契約**である（一般文書は検出し、DECISIONS.mdは除外する）。

E36とE37は同一parser経路のパラメータ群として実装してよい。いずれも期待診断は`expected_count不正FAIL`で一意とする。

### 12-3. 静的契約確認

実行時のexit codeを持たず、実装・命名・文書契約の静的確認とする。

| # | 確認内容 | 合格条件 | 守る仕様 |
|---|---|---|---|
| S01 | 設計上の仮称と検出パターンの衝突 | 現行仮称が検出語に文字列一致しない | 命名規約 |
| S02 | rule名は検出文字列を直接含めない | 命名規則§0-2を満たす | 命名規約 |
| S03 | fixtureは検出文字列の正本ではない | fixtureはtest入力としてのみ扱う | fixture役割 |
| S04 | 本番snapshot整合と明示指定台帳を混同しない | 既定台帳のみindex、明示指定は実ファイル | §3-5適用範囲 |
| S05 | classificationは例外理由の種類 | 表§7-2どおり（severityではない） | 分類意味 |
| S06 | draft→frozen昇格はE02とE03の対で担保 | 同一本文でWARN→FAILへ変わることを両ケースで確認 | 昇格 |

### 12-4. 観測・mutation確認

| # | 確認内容 | 合格条件 | 区分 |
|---|---|---|---|
| M01 | Office文書の現状限界 | Aはバイナリ行走査、B/CはZIPテキスト、status判定不能を実装観測で確認。exact-line台帳対象外を維持 | 観測 |
| M02 | 検出側だけfenceを含み件数側が除外する実装 | 当該mutationを入れた場合、E54/E55が失敗すること | mutation |
| M03 | 本文・status・台帳を別ソースから読む実装 | 当該mutationを入れた場合、E43–E46が失敗すること | mutation |

### 12-5. 集計

```text
実行回帰test数: 55
静的契約確認数: 6
観測・mutation確認数: 3
総確認項目数: 64
```

現行 `scripts/test-pre-delivery-check.sh` は13ケース。差分は実装ゲートで追加・置換する（現行#3のfence除外期待はE15へ反転吸収。現行`expected_count=0`はE35として維持）。

---

## 13. 推奨案（確定反映）

### 13-1. 必須10問

| # | 問い | 推奨 | 残す人間判断 |
|---|---|---|---|
| 1 | 語彙検出は正本か | **はい（v0.1）** | 語追加は抑制。追加時はtest同一commit |
| 2 | 安定識別子 | **v0.1非採用** | 移行開始条件 |
| 3 | 併用 | 将来形。v0.1は語彙＋exact＋reason | 開始ゲート |
| 4 | fence／引用／例示 | **通常成果物はA/B/Cともfence原則走査**。説明は分類名 | — |
| 5 | 自己参照 | 責務分離。恒久例外にしない。§9限界の本文WARNはdraft中台帳未登録で許容（確定済み） | — |
| 6 | pre-commit範囲 | **indexの本文・status・既定台帳＋台帳全体整合（ACMR）** | CI必須化 |
| 7 | 陳腐化保証 | 台帳全体整合で**FAIL**（本文0件でも実行） | — |
| 8 | validator WARN 17件 | 文書全体draftのまま。**今は台帳登録しない** | frozen移行時：meta_check vs accepted_risk |
| 9 | DECISIONS WARN | 台帳済みsoftは維持。読点は別カテゴリ負債（対象外） | 読点修正ゲート |
| 10 | マーカー衝突 | v0.1未採用。採用時は命名規則§0-2 | 正式マーカー名 |

### 13-2. 採用

- v0.1は完全一致行方式を継続（A群台帳）
- 論理5列（reason → exact_line、exact_lineは残り全部）
- reason必須（trim後空はFAIL）。reason内TABは構文直接拒否せず、作成規約＋陳腐化で運用
- hard検出語をexact_lineへ含む登録は台帳読込FAIL
- 台帳の不足・消失・移動等の陳腐化はFAIL
- pre-commitはGit indexの本文・status・既定例外台帳を同一snapshotから読む
- 明示指定台帳は指定パスの実ファイルを読む（index非要求）
- Stop／手動はworking treeの本文・status・例外台帳を同一snapshotから読む
- staged収集は`ACMR`
- 本文検査対象0件でも台帳全体整合を実行
- 検出・exact照合・件数計数は同一ソース・同一文脈フィルタ
- 通常成果物のfenceはA/B/Cとも原則走査
- 「記録形式」節除外はDECISIONS.md限定
- Office（pptx/docx/xlsx）はexact-line台帳の対象外
- 説明文書はrule名・分類名で参照
- fixtureは`scripts/fixtures/pre-delivery-check/`候補
- 語彙外表現の検出限界はv0.1で受容済みの既知の限界
- 層別statusはcheckerへ実装しない
- validator設計メモのWARNは現在台帳登録しない

### 13-3. 不採用

- ファイル×分類×件数だけで管理する方式（案B）
- v0.1での安定識別子導入
- fenceへの退避による自己参照回避
- hard failure対象を例外台帳へ登録可能にする方式
- reason内TABのescape／quote／非TSV化（v0.1）
- 4列形式の暫定許容
- 単なる文字分断や同義語置換
- 台帳陳腐化をWARNのまま許容する方式
- 層別statusのchecker実装
- Officeへのexact-line台帳適用（正規化仕様なしのまま）

### 13-4. 変更範囲（実装ゲート候補）

1. 台帳schemaを論理5列（reason→exact_line）へ切替（parser・台帳・test同一commit）
2. 陳腐化・件数不足・ファイル不在をFAIL化。本文0件でも台帳整合
3. hard語の台帳登録拒否
4. 通常成果物のfence原則走査（検出・exact・件数を同時に）
5. 「記録形式」節除外をDECISIONS.md限定
6. pre-commitのindex本文＋index status＋既定台帳（index）、ACMR
7. Officeとexact-line台帳の責務分離。Officeのindexバイナリは一時ファイル化（§3-7注記）
8. `scripts/stop-hook-check.sh`からpre-delivery-checkへ変更ファイルを渡す際、ファイルパスを安全にquoted展開する（空白分割・glob展開を防ぐ）。実装候補：NUL区切り、配列への安全な格納、mapfile等による1パス1要素の保持。E39と範囲を一致させる
9. 実行回帰test 55件＋静的6＋mutation/観測3へ段階拡張（診断理由検証付き）
10. 誤コメント修正

**やらない：** 層別statusパーサ、語彙大幅追加、validator共通台帳、本メモの例外登録、読点／AI語／ブランド色のindex非対称解消

---

## 14. 人間判断が必要な事項

### 14-1. 確定済み（人間判断一覧から外す）

```text
- 語彙外表現の検出限界はv0.1で受容する
- 本メモ§9の当該2件は受容済みの既知の限界を本文へ記載したWARN
- 文書全体はdraftのため、現時点では例外台帳へ登録しない
- 設計判断の凍結はDECISIONで担保する
```

### 14-2. なお残る人間判断

1. 安定識別子をいつ導入するか
2. validator設計メモの受容済み限界をfrozen時に台帳化するか。するなら`meta_check`か`accepted_risk`追加か
3. DECISIONSの改行直前読点を修正する別ゲートを立てるか（今回対象外）
4. CIでの全体本文走査を必須化するか
5. 検出文字列の正式な唯一の正本を、スクリプト本体とするか、独立語彙定義ファイルとするか
6. lifecycle／owner列をいつ必須化するか
7. reasonへ任意文字列（TAB含む）を必要とする段階で、台帳形式を見直すか

---

## 15. 見直し条件

- 語彙外表現による検品漏れが実際に発生した場合
- 同義語追加が反復し、語彙保守が不安定になった場合
- 台帳規模増大でpre-commitの台帳全体整合が重くなった場合（CI分離を検討）
- exact台帳追随コストが実害になった場合（案C再検討）
- reasonへTABを含む任意文字列を安全に保存する必要が生じた場合（形式見直し）
- リポジトリ外ファイルを検査対象にする場合（`normalize_rel_path`見直し）
- Office文書でA/B/Cを共通化する必要が生じた場合（正規化テキスト仕様）
- 実案件検証で工程区分や検品粒度が異なると判明した場合

---

## 16. 停止点

本設計メモの凍結前最終清書をもって、同一設計ゲート内の清書を停止する。

次に進んではならないもの：

- pre-delivery-check実装
- 例外台帳変更
- test／fixture作成
- DECISION追加
- git add／commit／push

再開条件（DEC-014）：人間が本メモを確認し、次ゲート（DECISION凍結または実装）を明示承認したとき。

---

*本ファイルは pre-delivery-check 例外台帳の設計draftです。実装・台帳正本・DECISIONの代替ではありません。*
