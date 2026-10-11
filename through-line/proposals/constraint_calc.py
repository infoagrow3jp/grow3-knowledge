# -*- coding: utf-8 -*-
"""制約資源あたりMQ と、改善シナリオの計算（financial_calc.py へ入れる提案）

**正本ではない。** 指標定義書 v0.2 §6-1 の「制約資源あたりMQ」には、まだ対応する関数が無い。
ここは、財務側に入れる前の提案と、その検算用。定義の案は同じフォルダの
「indicator-definition_6-1_addendum.md」。採用するときは、定義書と financial_calc.py の側で確定させる。

書き方は financial_calc.py に合わせた。
- 最小限の入力だけを受け取る、独立した関数
- 計算過程（入力値・使用式・丸め前の数値）を calculation_trace に残す（定義書 §0-1・§0-2）
- 算定できないときは 0 にせず、None と理由を返す（§0-4）
"""
from typing import Optional


def calc_mq_per_constraint_unit(m_unit_margin: float, constraint_units_per_item: Optional[float],
                                constraint_unit_label: str) -> dict:
    """制約資源あたりMQ ＝ 1件あたりのM ÷ その1件が占有する制約資源の量。

    分母は「制約資源を占有した量」（例：班長が判断対応に使った時間）。
    制約資源を待っていた時間は、分母にしない。
    """
    trace = {"formula": "m_unit_margin ÷ constraint_units_per_item",
             "m_unit_margin": m_unit_margin, "constraint_units_per_item": constraint_units_per_item,
             "constraint_unit": constraint_unit_label}
    if constraint_units_per_item is None or constraint_units_per_item <= 0:
        return {"mq_per_constraint_unit": None, "status": "not_computable",
                "reason": "制約資源の占有量が無い、または0以下のため算定不能", "calculation_trace": trace}
    value = m_unit_margin / constraint_units_per_item
    trace["unrounded"] = value
    return {"mq_per_constraint_unit": value, "status": "computed", "reason": "", "calculation_trace": trace}


def calc_constraint_utilization(constraint_units_used: float, constraint_units_available: Optional[float]) -> dict:
    """制約資源の使用率 ＝ 使った量 ÷ 使える量。同じ期間・同じ単位で測ったもの同士で計算する。"""
    trace = {"formula": "constraint_units_used ÷ constraint_units_available",
             "constraint_units_used": constraint_units_used, "constraint_units_available": constraint_units_available}
    if constraint_units_available is None or constraint_units_available <= 0 or constraint_units_used < 0:
        return {"utilization": None, "status": "not_computable",
                "reason": "制約資源の使える量が無い・0以下、または使った量が負のため算定不能", "calculation_trace": trace}
    value = constraint_units_used / constraint_units_available
    trace["unrounded"] = value
    return {"utilization": value, "status": "computed", "reason": "", "calculation_trace": trace}


def calc_weighted_average(values_by_type: dict, counts_by_type: dict, label: str, non_negative: bool = False) -> dict:
    """案件の種類ごとの値を、件数で加重平均する（1件あたりの占有量や、1件あたりのM）。

    占有量のように負になり得ない値は non_negative=True で渡す。負が混じっていれば算定不能にする。
    1件あたりM は負になり得る（P＜V）ので、既定では負を止めない。
    """
    total = sum(counts_by_type.values())
    trace = {"formula": f"Σ({label} × 件数) ÷ Σ件数", "values_by_type": values_by_type, "counts_by_type": counts_by_type}
    if total <= 0 or set(values_by_type) != set(counts_by_type) or any(c < 0 for c in counts_by_type.values()):
        return {"average": None, "status": "not_computable",
                "reason": "件数が0・負、または種類が揃っていないため算定不能", "calculation_trace": trace}
    if non_negative and any(v is None or v < 0 for v in values_by_type.values()):
        return {"average": None, "status": "not_computable",
                "reason": f"{label}に負の値があるため算定不能", "calculation_trace": trace}
    value = sum(values_by_type[k] * counts_by_type[k] for k in values_by_type) / total
    trace["unrounded"] = value
    return {"average": value, "status": "computed", "reason": "", "calculation_trace": trace}


def calc_throughput_scenario(constraint_units_available: float, constraint_units_per_item_after: float,
                             other_caps: dict, period_label: str) -> dict:
    """改善後に、期間あたり何件まで流せるかのシナリオ。

    制約資源から見た上限（使える量 ÷ 改善後の1件あたり占有量）と、ほかの上限（上流工程の完了件数、
    需要の仮定など）のうち、いちばん小さいものが全体の上限になる。どれが効いたかを binding（名前のリスト）に返す。
    見込みではなくシナリオ。需要を含め、仮定は呼び出し側で明示する（定義書 §6-1）。
    """
    trace = {"formula": "min(constraint_units_available ÷ constraint_units_per_item_after, ほかの上限…)",
             "constraint_units_available": constraint_units_available,
             "constraint_units_per_item_after": constraint_units_per_item_after, "other_caps": other_caps, "period": period_label}
    if (constraint_units_per_item_after <= 0 or constraint_units_available <= 0 or not other_caps
            or any(v is None or v < 0 for v in other_caps.values())):
        return {"throughput": None, "binding": None, "status": "not_computable",
                "reason": "占有量・使える量が0以下、ほかの上限が1つも無い、または上限に負の値があるため算定不能", "calculation_trace": trace}
    by_constraint = constraint_units_available / constraint_units_per_item_after
    caps = dict(other_caps)
    caps["constraint_resource"] = by_constraint
    lowest = min(caps.values())
    binding = sorted(k for k, v in caps.items() if v == lowest)  # 同じ値で並んだら、すべて返す
    trace.update({"by_constraint_unrounded": by_constraint, "caps": caps})
    return {"throughput": lowest, "binding": binding, "by_constraint": by_constraint,
            "status": "computed", "reason": "", "calculation_trace": trace}


def calc_mq_delta_scenario(throughput_before: float, throughput_after: float, m_unit_margin_for_added: float,
                           period_label: str) -> dict:
    """件数が増えた分のMQ ＝（改善後の件数 − 改善前の件数）× 増える案件の1件あたりM。期間あたり。

    増える案件のMは、呼び出し側が仮定として置く（今と同じ構成で増える、など）。年換算はしない。
    """
    if throughput_before < 0 or throughput_after < 0:
        return {"delta_q": None, "mq_delta": None, "status": "not_computable", "reason": "件数が負のため算定不能",
                "calculation_trace": {"formula": "(throughput_after − throughput_before) × m_unit_margin_for_added",
                                      "throughput_before": throughput_before, "throughput_after": throughput_after}}
    delta_q = throughput_after - throughput_before
    value = delta_q * m_unit_margin_for_added
    return {"delta_q": delta_q, "mq_delta": value, "status": "computed", "reason": "",
            "calculation_trace": {"formula": "(throughput_after − throughput_before) × m_unit_margin_for_added",
                                  "throughput_before": throughput_before, "throughput_after": throughput_after,
                                  "m_unit_margin_for_added": m_unit_margin_for_added, "period": period_label,
                                  "unrounded": value}}


if __name__ == "__main__":
    # 最小の数値例での検算（定義書 §0-7）。次元と、増減の向きを確かめる。
    r = calc_mq_per_constraint_unit(100.0, 2.0, "時間")
    assert r["mq_per_constraint_unit"] == 50.0                       # 円/件 ÷ 時間/件 ＝ 円/時間
    assert calc_mq_per_constraint_unit(100.0, 1.0, "時間")["mq_per_constraint_unit"] > r["mq_per_constraint_unit"]  # 占有が減ると上がる
    assert calc_mq_per_constraint_unit(100.0, 0.0, "時間")["status"] == "not_computable"
    assert calc_mq_per_constraint_unit(100.0, None, "時間")["mq_per_constraint_unit"] is None
    assert calc_constraint_utilization(9.0, 10.0)["utilization"] == 0.9
    assert calc_constraint_utilization(9.0, 0.0)["status"] == "not_computable"
    assert calc_weighted_average({"a": 1.0, "b": 3.0}, {"a": 3, "b": 1}, "x")["average"] == 1.5
    assert calc_weighted_average({"a": 1.0}, {"b": 1}, "x")["status"] == "not_computable"
    s = calc_throughput_scenario(10.0, 1.0, {"upstream": 8.0, "demand": 9.0}, "週")
    assert s["throughput"] == 8.0 and s["binding"] == ["upstream"] and s["by_constraint"] == 10.0   # 上流が先に効く
    s = calc_throughput_scenario(10.0, 2.0, {"upstream": 8.0}, "週")
    assert s["throughput"] == 5.0 and s["binding"] == ["constraint_resource"]                     # 制約資源が効く
    assert calc_throughput_scenario(10.0, 1.0, {"upstream": 8.0, "demand": 8.0}, "週")["binding"] == ["demand", "upstream"]
    assert calc_throughput_scenario(10.0, 1.0, {}, "週")["status"] == "not_computable"
    assert calc_throughput_scenario(10.0, 1.0, {"demand": -2.0}, "週")["throughput"] is None        # 負の上限は算定不能
    assert calc_constraint_utilization(-1.0, 10.0)["status"] == "not_computable"
    assert calc_weighted_average({"a": 1.0}, {"a": -1}, "x")["status"] == "not_computable"
    assert calc_weighted_average({"a": -1.0, "b": 3.0}, {"a": 1, "b": 1}, "占有量", non_negative=True)["status"] == "not_computable"
    assert calc_weighted_average({"a": -1.0, "b": 3.0}, {"a": 1, "b": 1}, "M")["average"] == 1.0   # M は負があり得るので止めない
    assert calc_mq_delta_scenario(-1.0, 9.0, 100.0, "週")["status"] == "not_computable"
    assert calc_mq_delta_scenario(7.0, 9.0, 100.0, "週")["mq_delta"] == 200.0
    assert calc_mq_delta_scenario(7.0, 7.0, 100.0, "週")["mq_delta"] == 0.0
    print("constraint_calc: 検算 OK")
