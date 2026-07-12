# -*- coding: utf-8 -*-
"""
financial-analysisスキル（.claude/skills/financial-analysis/SKILL.md）の
スモークテスト。

スキルのStep0〜4の手順に従って financial_calc.py を呼び出した場合の結果が、
financial_calc.pyの直接実行結果（＝tests/test_financial_calc.pyが検証している
期待値）と一致することを確認する。

ケース①：本体fixture第2期（推計営業CFを使用するケース）
ケース②：簡易営業CFのみで judgment_status=screening_only となるケース

使い方：python tests/smoke_test_financial_analysis_skill.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import financial_calc as fc

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_json(name):
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


REQUIRED_METADATA_KEYS_FOR_CF_SELF_SUFFICIENCY = [
    "ocf_source",
    "capex_source",
    "judgment_status",
    "warning",
    "warning_code",
    "calculation_trace",
]


def run_case_1_estimated_ocf_period2():
    """
    ケース①：本体fixture第2期（推計営業CFを使用）。

    Step0（実行前チェック）：本fixtureにはCF計算書が無い（has_cash_flow_statement
    に相当する情報はfixtureに含まれないが、cfブロックに actual_operating_cf が
    無いことで確認できる）。前期末B/S（opening_bs）はある。維持投資の実額
    （cf["capex"]）はある。→ 営業CFは推計層、維持投資は実額を使う想定。
    """
    data = load_json("financial_analysis_case_manufacturing_3fy.json")
    period2 = data["periods"][1]
    assert period2["name"] in ("第2期", "期2") or "2" in period2["name"], (
        f"想定と異なる期名: {period2['name']}"
    )

    # Step0：実行前チェック（本fixtureの入力に前期末B/S・当期末B/S・P/L・CF明細が
    # 揃っていることを確認。CF計算書そのものは無いことを確認）
    assert "opening_bs" in period2 and "ending_bs" in period2 and "pl" in period2 and "cf" in period2
    assert "actual_operating_cf" not in period2["cf"], (
        "本ケースはCF計算書が無い前提（推計層想定）のはずが actual_operating_cf が入力に存在する"
    )

    # Step1（入力整形）は不要（fixtureが既にanalyze_period()の入力形状）。
    # Step2：financial_calc.pyの実行
    actual = fc.analyze_period(
        pl=period2["pl"], cf=period2["cf"],
        opening_bs=period2["opening_bs"], ending_bs=period2["ending_bs"],
    )

    # Step3：出力メタデータの検証（スキルSKILL.md Step3）
    for key in ["ocf_source", "capex_source"]:
        assert key in actual and actual[key] is not None, f"必須メタデータ欠落: {key}"
    for key in [
        "cf_self_sufficiency_judgment_status",
        "cf_self_sufficiency_warning",
        "cf_self_sufficiency_warning_code",
        "cf_self_sufficiency_calculation_trace",
    ]:
        assert key in actual, f"必須メタデータ欠落: {key}"
    assert actual["cf_self_sufficiency_calculation_trace"], "calculation_traceが空"

    # Step4：judgment_statusに応じた表示分岐の確認（本ケースは formal のはず）
    assert actual["cf_self_sufficiency_judgment_status"] == "formal"
    assert actual["ocf_source"] == "estimated"
    assert actual["capex_source"] == "actual"

    # financial_calc.pyの直接実行結果（＝test_financial_calc.pyが使う期待値）との一致確認
    expected = period2["indicators"]
    mismatches = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if isinstance(expected_value, float):
            if actual_value is None or abs(actual_value - expected_value) > 1e-4:
                mismatches.append((key, expected_value, actual_value))
        elif actual_value != expected_value:
            mismatches.append((key, expected_value, actual_value))
    assert not mismatches, f"スキル経由の結果が直接実行の期待値と不一致: {mismatches}"

    return actual


def run_case_2_simplified_only_screening():
    """
    ケース②：簡易営業CFのみで judgment_status=screening_only となるケース。

    Step0（実行前チェック）：CF計算書なし・前期末B/Sなし（本ケースの前提）→
    推計層を構成できないため簡易層にフォールバックする想定。
    """
    data = load_json("financial_analysis_boundary_cases.json")
    case = {c["case_id"]: c for c in data["ocf_source_safety_cases"]}[
        "ocf_source_simplified_only_no_prior_bs"
    ]
    inputs = case["inputs"]
    expected = case["expected"]

    # Step0：前期末B/S・CF計算書のいずれも無いことがfixtureのdescriptionで
    # 明示されている（has_cash_flow_statement=False・has_prior_period_bs=False）。
    assert inputs["has_cash_flow_statement"] is False
    assert inputs["has_prior_period_bs"] is False

    # Step1（入力整形）：欠落（actual_operating_cf・net_income等）と有効値を区別する。
    # 本ケースは経常利益・減価償却費・法人税等のみが有効値として存在する。
    # Step2：financial_calc.pyの実行（直接financial_calc.py関数を呼ぶ＝スキルの手順）
    result = fc.calc_cf_self_sufficiency(
        inputs["annual_principal_repayment_next12m"],
        ordinary_profit=inputs["ordinary_profit"],
        depreciation_total=inputs["depreciation_total"],
        tax=inputs["tax"],
    )

    # Step3：出力メタデータの検証
    for attr in REQUIRED_METADATA_KEYS_FOR_CF_SELF_SUFFICIENCY:
        assert hasattr(result, attr), f"必須メタデータ欠落: {attr}"
    assert result.calculation_trace, "calculation_traceが空"

    # Step4：judgment_status=screening_onlyのレポート表示分岐の確認
    assert result.judgment_status == "screening_only"
    assert result.judgment is None, "screening_only時にjudgment（正式区分）が表示されてはならない"
    assert result.zone is None
    assert result.cf_self_sufficiency is None
    assert result.warning_code == fc.WARNING_CODE_SIMPLIFIED_OCF_NOT_ELIGIBLE_FOR_FORMAL_JUDGMENT
    assert result.warning == expected["warning"]

    # レポート表示文の組み立て（SKILL.md Step4のルールをシミュレート）
    if result.judgment_status == "screening_only":
        report_line = (
            f"CF自走性：正式判定不可（judgment_status=screening_only）。"
            f"参考値のみ：簡易営業CFベースの計算過程＝{result.calculation_trace}"
            f"／警告コード={result.warning_code}／理由={result.warning}"
        )
        assert "標準" not in report_line and "余裕" not in report_line and "要改善" not in report_line and "ぎりぎり" not in report_line, (
            "screening_only表示に正式区分語が混入している"
        )

    # financial_calc.pyの直接実行結果（fixtureの期待値）との一致確認
    assert result.ocf_source == expected["ocf_source"]
    assert result.judgment_blocked == expected["judgment_blocked"]
    assert result.confidence_grade == expected["confidence_grade"]
    simple_ocf = fc.calc_simple_operating_cf(
        inputs["ordinary_profit"], inputs["depreciation_total"], inputs["tax"],
    )
    assert abs(simple_ocf - expected["simple_operating_cf"]) < 1e-6

    return result, report_line


def main():
    print("=== ケース①：本体fixture第2期（推計営業CF使用） ===")
    actual1 = run_case_1_estimated_ocf_period2()
    print(f"ocf_source={actual1['ocf_source']} / capex_source={actual1['capex_source']} / "
          f"judgment_status={actual1['cf_self_sufficiency_judgment_status']} / "
          f"cf_self_sufficiency={actual1['cf_self_sufficiency']:.4f} / "
          f"zone={actual1['cf_self_sufficiency_zone']}")
    print("→ スキル経由の結果が直接実行（fixture期待値）と全件一致：OK")
    print()

    print("=== ケース②：簡易営業CFのみ・judgment_status=screening_only ===")
    result2, report_line = run_case_2_simplified_only_screening()
    print(f"ocf_source={result2.ocf_source} / judgment_status={result2.judgment_status} / "
          f"judgment={result2.judgment} / warning_code={result2.warning_code}")
    print(f"レポート表示文（Step4シミュレーション）：{report_line}")
    print("→ スキル経由の結果が直接実行（fixture期待値）と全件一致：OK")
    print()

    print("2ケースとも成功。")


if __name__ == "__main__":
    main()
