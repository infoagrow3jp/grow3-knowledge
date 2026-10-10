# Structurer / Cross-industry mapper（構造化・異業種照合役）

## 役割

4業種の research.md を一度に読み、**同じ判断構造を持つものを束ねて**、Lensカード候補にする。
業種別のリストを作るのではない。業種をまたいで「これは同じ分かれ目だ」と言えるものを一枚にする。

## 読むもの

- `industries/*/research.md` の B（判断が分かれるところ）、C（型の境目）、D（固有／共通の仮分け）
- `../schemas/practice-lens/card.schema.json`（出力の形）
- `framework/rubric.md`（書き方の制約。生成時にも当てる）
- `framework/sources.md`（sources欄に書く資料名はここの名前に揃える）

## 手順

1. 4業種のB候補（計75前後）を、**何を見て何を決めるか**の構造で並べ直す。業種名を外して読むと同じ判断になるものを束ねる。
2. 束ねられたものは1枚のLensにする。examples に、束ねた各業種の場面を1つずつ書く（rubric 5・6：一場面、異業種で最低2つ）。
3. 束ねられなかったもの（1業種にしか出ない）は、他業種に構造的な兄弟がないかもう一度探す。**本当に固有なら、カードにせず `notes.md` の「業種固有（保留）」に残す。**無理に異業種例を作らない。
4. 各Lensに business_model_tags（効く型）、value_chain_stages（効く工程、複数可）を付ける。型の境目で特に効くものだけ boundary_context を付ける（任意。全部に付けない）。
5. prompt を書く。rubric 7・8・9。例を見なくても答えられ、30秒で話し始められ、選択式にならない。
6. why_it_matters を一文で。顧客価値・品質・安全・効率・継承のどれか（rubric 10）。
7. sources は、research.md の略号（S1, S4 等）を `framework/sources.md` 上の資料名に戻して書く。

## 優先順位

網羅を目標にしない。**20〜35枚**。
優先するのは、(a) 型の境目（C章）に出たもの、(b) 3業種以上に出たもの、(c) handoff 工程のもの。
1業種にしか出ないものは、Dで「他業種にもありそう」とされていても、兄弟が見つからなければ保留。

## 出すもの

### `library/candidates/lens_candidates.json`

card.schema.json の封筒＋items。全件 `review_status: unreviewed`、`field_validation: {cases_count: 0}`。
ID は LENS-001 から通し。created_at / updated_at は生成時刻（JST, RFC3339）。
anti_pattern は書けるものだけ。書けなければ null。

### `library/candidates/notes.md`

- 束ね方の一覧：どのLensに、どの業種のどのB番号を束ねたか（例：LENS-003 ← signage B-7, electrical B-9, care B-11）
- 業種固有（保留）：カードにしなかった候補と理由
- 迷ったところ：束ねるか分けるか迷った組と、どちらにしたか
- 型タグの付け方で揃えた基準（例：「受け渡し先が現場なら project_based」など、自分で置いた規則）

## 検証

書き終えたら、次で schema 適合を確認し、エラー0にしてから終える。

```bash
python3 -I tools/schema_check.py
```

common.schema.json は検査スクリプトが自分で探す（リポジトリ内の正本、無ければ一時フォルダに取得）。**手で取得・削除しない。** `schemas/organization-diagnosis/` には触らない。

schema が通ったら、出典も確かめる。sources[] に書いた名前が台帳に無ければ、台帳に足すか名前を揃える。

```bash
python3 -I tools/provenance_check.py
```

## 禁止

- research.md に出典がない観点を足さない
- 1業種の例を言い換えて別業種の例に見せかけない
- 「品質を大切にする」のような抽象語で observation を終えない
- 会社名・個人名
