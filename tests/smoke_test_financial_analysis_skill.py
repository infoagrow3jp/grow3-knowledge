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

    # Step3：出力メタデータの検証（スキルSKILL.md Step3・6項目）
    for key in ["ocf_source", "capex_source"]:
        assert key in actual and actual[key] is not None, f"必須メタデータ欠落: {key}"
    for key in [
        "cf_self_sufficiency_judgment_status",
        "cf_self_sufficiency_warning",
        "cf_self_sufficiency_warning_code",
        "cf_self_sufficiency_calculation_trace",
    ]:
        assert key in actual, f"必須メタデータ欠落: {key}"
    trace = actual["cf_self_sufficiency_calculation_trace"]
    assert trace, "calculation_traceが空"
    # 「使用した費目と算式」チェック：抽象的な記述ではなく、具体的な数値・
    # 項目名（推計営業CF・維持投資・CF自走性の各算式）が含まれていることを確認
    for must_contain in ["推計営業CF", "維持投資", "CF自走性"]:
        assert must_contain in trace, f"calculation_traceに必須の費目・算式名が欠落: {must_contain}"

    # Step4：judgment_statusに応じた表示分岐の確認（本ケースは formal のはず）
    assert actual["cf_self_sufficiency_judgment_status"] == "formal"
    assert actual["ocf_source"] == "estimated", "使用されたocf_sourceが期待（estimated）と不一致"
    assert actual["capex_source"] == "maintenance_actual", "使用されたcapex_sourceが期待（maintenance_actual）と不一致"
    assert actual["cf_self_sufficiency_repayment_source"] == "scheduled", "使用されたrepayment_sourceが期待（scheduled）と不一致"
    assert actual["cf_self_sufficiency_warning_code"] is None, "formal判定なのに警告コードが設定されている"

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
        annual_principal_repayment_scheduled=inputs["annual_principal_repayment_scheduled"],
        ordinary_profit=inputs["ordinary_profit"],
        depreciation_total=inputs["depreciation_total"],
        tax=inputs["tax"],
    )

    # Step3：出力メタデータの検証（6項目：ocf_source・capex_source・
    # judgment_status・警告/警告コード・計算過程・使用した費目と算式）
    for attr in REQUIRED_METADATA_KEYS_FOR_CF_SELF_SUFFICIENCY:
        assert hasattr(result, attr), f"必須メタデータ欠落: {attr}"
    assert result.calculation_trace, "calculation_traceが空"
    for must_contain in ["経常利益", "減価償却費", "法人税等", "簡易営業CF"]:
        assert must_contain in result.calculation_trace, (
            f"calculation_traceに必須の費目・算式名が欠落: {must_contain}"
        )

    # Step4：judgment_status=screening_onlyのレポート表示分岐の確認
    assert result.judgment_status == "screening_only", "judgment_statusが期待（screening_only）と不一致"
    assert result.judgment is None, "screening_only時にjudgment（正式区分）が表示されてはならない"
    assert result.zone is None
    assert result.cf_self_sufficiency is None
    assert result.warning_code == fc.WARNING_CODE_SIMPLIFIED_OCF_NOT_ELIGIBLE_FOR_FORMAL_JUDGMENT, (
        "警告コードが期待値と不一致"
    )
    assert result.warning == expected["warning"]
    assert result.ocf_source == expected["ocf_source"], "使用されたocf_sourceが期待（simplified）と不一致"

    # レポート表示文の組み立て（SKILL.md Step4・screening_only時の5点構成をシミュレート）
    simple_ocf = fc.calc_simple_operating_cf(
        inputs["ordinary_profit"], inputs["depreciation_total"], inputs["tax"],
    )
    report_lines = {
        "1_参考計算値": f"簡易営業CF（参考値） = {simple_ocf:,.1f}千円",
        "2_スクリーニング値である旨": (
            "本値は速報・一次スクリーニング専用の簡易営業CFに基づく参考値であり、"
            "運転資本変動を反映していない"
        ),
        "3_正式判定を行っていない理由": result.warning,
        "4_警告コードおよび警告内容": f"{result.warning_code}：{result.warning}",
        "5_正式判定に追加で必要な資料": "2期分のB/SまたはCF計算書",
    }
    full_report_text = "／".join(report_lines.values())
    for forbidden_zone_word in ["要改善（自走していない", "ぎりぎり（自走はしている", "標準（銀行の融資目安圏）", "余裕（銀行評価良好圏）"]:
        assert forbidden_zone_word not in full_report_text, (
            f"screening_only表示に正式区分語が混入している: {forbidden_zone_word}"
        )
    assert result.zone not in (report_lines.values()), "zone（正式区分）がレポート文に紛れ込んでいる"

    # financial_calc.pyの直接実行結果（fixtureの期待値）との一致確認
    assert result.judgment_blocked == expected["judgment_blocked"]
    assert result.confidence_grade == expected["confidence_grade"]
    assert abs(simple_ocf - expected["simple_operating_cf"]) < 1e-6

    return result, report_lines


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
    result2, report_lines = run_case_2_simplified_only_screening()
    print(f"ocf_source={result2.ocf_source} / judgment_status={result2.judgment_status} / "
          f"judgment={result2.judgment} / warning_code={result2.warning_code}")
    print("レポート表示文（Step4・screening_only時の5点構成）：")
    for label, text in report_lines.items():
        print(f"  {label}：{text}")
    print("→ 正式な判定区分（zone）は表示されていないことを確認済み")
    print("→ スキル経由の結果が直接実行（fixture期待値）と全件一致：OK")
    print()

    print("2ケースとも成功。")


if __name__ == "__main__":
    main()
