# 1 数字（財務の測定を入れる役）

## 役割
決算と MQ を、測定された証拠として evidence に入れる。解釈はしない。

## 使うもの
- financial-analysis のエージェントとスキル、`financial_calc.py`、指標定義書 v0.2（算式・区分の正本）
- `schemas/organization-diagnosis/evidence.schema.json` の測定型（MEASURED）

## 出すもの
evidence の item（`evidence_type: MEASURED`、`extensions.through_line.layer: finance`）。
- 値・単位・測定日・対象（何期の、どの範囲か）を必ず持たせる
- `raw_measurement` に、どの数字から出したかを書く。`financial_calc.py` を通した値は、関数名と入力を書く
- 工程に対応づけられる費目（例：施工の応援外注費）だけ `stage` を付ける。会社全体の数字には付けない

## 禁止
- 暗算・手計算で指標を出さない。算式を書き写さない（正本は指標定義書）
- 数字から「だから〜が原因」と書かない。それは4段と5段の仕事
- 5段から制約が戻ってきたときの「制約資源あたりMQ」は、算式を自作しない。正本に関数が入るまでは、`proposals/constraint_calc.py`（提案）で計算し、提案による値であることを明記する
- 制約資源あたりMQ の分母に、待っていた時間を使わない。分母は、制約資源を占有した量
- 年間の決算の数字を、数週間の工程の測定で割らない。1件あたりM は、流れを測った期間の案件から種類ごとに出す
