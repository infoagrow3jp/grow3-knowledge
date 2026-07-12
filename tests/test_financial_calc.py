# -*- coding: utf-8 -*-
"""
financial_calc.py の回帰テスト（残タスク②）

tests/fixtures/ の期待値（本体3期ケース・境界値ミニケース12件・
営業CF層選択の安全動作ケース2件）に対して financial_calc.py の出力が
全件一致することを検証する。

fixtureは tests/build_financial_fixture.py ／
tests/build_boundary_fixtures.py という、financial_calc.py とは別の
独立したスクリプトで生成している（期待値生成ロジックと実装ロジックを
共有しないことで、同じ誤りを両方に持ち込むリスクを下げる設計）。

使い方：python tests/test_financial_calc.py
標準ライブラリのunittestのみを使用する（pytest等の追加依存を持たない）。
"""
import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import financial_calc as fc

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_json(name):
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class TestMainCaseThreePeriods(unittest.TestCase):
    """本体：架空製造業3期分のfixtureと analyze_period() の出力を突き合わせる。"""

    @classmethod
    def setUpClass(cls):
        cls.data = load_json("financial_analysis_case_manufacturing_3fy.json")

    def test_all_periods_match_expected_indicators(self):
        for period in self.data["periods"]:
            with self.subTest(period=period["name"]):
                actual = fc.analyze_period(
                    pl=period["pl"], cf=period["cf"],
                    opening_bs=period["opening_bs"], ending_bs=period["ending_bs"],
                )
                expected = period["indicators"]
                for key, expected_value in expected.items():
                    actual_value = actual.get(key)
                    if isinstance(expected_value, float):
                        self.assertAlmostEqual(
                            actual_value, expected_value, places=4,
                            msg=f"{period['name']} / {key}: expected={expected_value} actual={actual_value}",
                        )
                    else:
                        self.assertEqual(
                            actual_value, expected_value,
                            msg=f"{period['name']} / {key}: expected={expected_value!r} actual={actual_value!r}",
                        )


class TestBoundaryCases(unittest.TestCase):
    """境界値ミニケース12件（CF自走性5・EBITDA型3・現預金月商倍率4）。"""

    @classmethod
    def setUpClass(cls):
        cls.data = load_json("financial_analysis_boundary_cases.json")

    def test_cf_self_sufficiency_boundaries(self):
        cases = self.data["cf_self_sufficiency_boundary_cases"]
        self.assertEqual(len(cases), 5)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                inputs = case["inputs"]
                result = fc.calc_cf_self_sufficiency(
                    annual_principal_repayment_scheduled=inputs["annual_principal_repayment_scheduled"],
                    actual_operating_cf=inputs["operating_cf_input"],
                    capex_maintenance_actual=inputs["maintenance_investment"],
                )
                self.assertAlmostEqual(result.fcf, case["expected"]["fcf"], places=6)
                self.assertAlmostEqual(
                    result.cf_self_sufficiency, case["expected"]["cf_self_sufficiency"], places=6,
                )
                self.assertEqual(result.zone, case["expected"]["zone"])

    def test_debt_payback_ebitda_boundaries(self):
        cases = self.data["debt_payback_ebitda_boundary_cases"]
        self.assertEqual(len(cases), 3)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                inputs = case["inputs"]
                net_debt = inputs["borrowings"] - inputs["cash"]
                ebitda, years, zone = fc.calc_debt_payback_years_ebitda(
                    net_debt, inputs["operating_profit"], inputs["depreciation_total"],
                )
                self.assertAlmostEqual(ebitda, case["expected"]["ebitda"], places=6)
                self.assertAlmostEqual(
                    net_debt, case["expected"]["net_interest_bearing_debt"], places=6,
                )
                self.assertAlmostEqual(years, case["expected"]["debt_payback_years_ebitda"], places=6)
                self.assertEqual(zone, case["expected"]["zone"])

    def test_cash_months_boundaries(self):
        cases = self.data["cash_months_boundary_cases"]
        self.assertEqual(len(cases), 4)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                inputs = case["inputs"]
                ratio, zone = fc.calc_cash_to_monthly_sales(inputs["cash"], inputs["monthly_sales"])
                self.assertAlmostEqual(ratio, case["expected"]["cash_to_monthly_sales_ratio"], places=6)
                self.assertEqual(zone, case["expected"]["zone"])
                surplus_cash = fc.calc_surplus_cash(
                    inputs["cash"], inputs["normal_working_capital"], inputs["monthly_sales"],
                )
                self.assertAlmostEqual(surplus_cash, case["expected"]["surplus_cash"], places=6)


class TestOcfSourceSafetyCases(unittest.TestCase):
    """営業CF層選択の安全動作（簡易層しか無い場合は判定をブロックする）。"""

    @classmethod
    def setUpClass(cls):
        cls.data = load_json("financial_analysis_boundary_cases.json")
        cls.cases = {c["case_id"]: c for c in cls.data["ocf_source_safety_cases"]}

    def test_simplified_only_input_blocks_judgment_with_warning(self):
        case = self.cases["ocf_source_simplified_only_no_prior_bs"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            annual_principal_repayment_scheduled=inputs["annual_principal_repayment_scheduled"],
            ordinary_profit=inputs["ordinary_profit"],
            depreciation_total=inputs["depreciation_total"],
            tax=inputs["tax"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertTrue(result.judgment_blocked)
        self.assertEqual(result.judgment_blocked, expected["judgment_blocked"])
        self.assertIsNone(result.cf_self_sufficiency)
        self.assertIsNone(result.zone)
        self.assertIsNone(result.judgment)
        self.assertEqual(result.judgment_status, "screening_only")
        self.assertEqual(
            result.warning_code,
            fc.WARNING_CODE_SIMPLIFIED_OCF_NOT_ELIGIBLE_FOR_FORMAL_JUDGMENT,
        )
        self.assertEqual(result.warning, expected["warning"])
        self.assertEqual(result.confidence_grade, expected["confidence_grade"])

        simple_ocf = fc.calc_simple_operating_cf(
            inputs["ordinary_profit"], inputs["depreciation_total"], inputs["tax"],
        )
        self.assertAlmostEqual(simple_ocf, expected["simple_operating_cf"], places=6)

    def test_estimated_input_available_allows_judgment(self):
        case = self.cases["ocf_source_estimated_available_with_prior_bs"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            annual_principal_repayment_scheduled=inputs["annual_principal_repayment_scheduled"],
            net_income=inputs["net_income"],
            depreciation_total=inputs["depreciation_total"],
            delta_ar=inputs["delta_ar"],
            delta_inv=inputs["delta_inv"],
            delta_ap=inputs["delta_ap"],
            capex_maintenance_actual=inputs["maintenance_investment"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertFalse(result.judgment_blocked)
        self.assertEqual(result.judgment_blocked, expected["judgment_blocked"])
        self.assertAlmostEqual(result.fcf, expected["fcf"], places=6)
        self.assertAlmostEqual(result.cf_self_sufficiency, expected["cf_self_sufficiency"], places=6)
        self.assertEqual(result.zone, expected["cf_self_sufficiency_zone"])
        self.assertEqual(result.judgment, expected["cf_self_sufficiency_zone"])
        self.assertEqual(result.judgment_status, "formal")
        self.assertEqual(result.repayment_source, "scheduled")
        self.assertIsNone(result.warning_code)
        self.assertIsNone(result.warning)

    def test_actual_takes_priority_over_estimated_when_both_available(self):
        """3層ロジック専用テスト①：実績と推計可能データが両方ある→実績を優先。"""
        case = self.cases["ocf_source_actual_takes_priority_over_estimated"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            annual_principal_repayment_scheduled=inputs["annual_principal_repayment_scheduled"],
            actual_operating_cf=inputs["actual_operating_cf"],
            net_income=inputs["net_income"],
            depreciation_total=inputs["depreciation_total"],
            delta_ar=inputs["delta_ar"],
            delta_inv=inputs["delta_inv"],
            delta_ap=inputs["delta_ap"],
            capex_maintenance_actual=inputs["maintenance_investment"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertEqual(result.confidence_grade, expected["confidence_grade"])
        # 実績値(50,000)が採用され、推計すれば得られたはずの値(46,000)ではないことを確認
        self.assertAlmostEqual(
            result.fcf + inputs["maintenance_investment"],
            expected["operating_cf_value_used"], places=6,
        )
        self.assertNotAlmostEqual(
            result.fcf + inputs["maintenance_investment"],
            expected["estimated_operating_cf_if_computed_instead"], places=6,
        )
        self.assertAlmostEqual(result.fcf, expected["fcf"], places=6)
        self.assertAlmostEqual(result.cf_self_sufficiency, expected["cf_self_sufficiency"], places=6)
        self.assertEqual(result.zone, expected["cf_self_sufficiency_zone"])
        self.assertFalse(result.judgment_blocked)
        self.assertIsNone(result.warning)

    def test_capex_source_depreciation_proxy_when_actual_missing(self):
        """3層ロジック専用テスト④：維持投資実額なし→capex_source=depreciation_proxy。"""
        case = self.cases["capex_source_depreciation_proxy_when_capex_actual_missing"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            annual_principal_repayment_scheduled=inputs["annual_principal_repayment_scheduled"],
            actual_operating_cf=inputs["actual_operating_cf"],
            depreciation_total=inputs["depreciation_total"],
            # capex_maintenance_actual を渡さない＝維持投資の実額が欠落している状況
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertEqual(result.capex_source, expected["capex_source"])
        self.assertAlmostEqual(result.fcf, expected["fcf"], places=6)
        self.assertAlmostEqual(result.cf_self_sufficiency, expected["cf_self_sufficiency"], places=6)
        self.assertEqual(result.zone, expected["cf_self_sufficiency_zone"])

    def test_zero_delta_ar_is_not_treated_as_missing(self):
        """欠落とゼロの区別（zero側）：Δ売掛金が明示的な0.0でも推計営業CFを算出できる。"""
        case = self.cases["zero_vs_missing_delta_ar_explicit_zero_estimated_succeeds"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            annual_principal_repayment_scheduled=inputs["annual_principal_repayment_scheduled"],
            net_income=inputs["net_income"],
            depreciation_total=inputs["depreciation_total"],
            delta_ar=inputs["delta_ar"],  # 明示的な0.0（欠落ではない）
            delta_inv=inputs["delta_inv"],
            delta_ap=inputs["delta_ap"],
            capex_maintenance_actual=inputs["maintenance_investment"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertFalse(result.judgment_blocked)
        self.assertAlmostEqual(result.fcf, expected["fcf"], places=6)
        self.assertAlmostEqual(result.cf_self_sufficiency, expected["cf_self_sufficiency"], places=6)
        self.assertEqual(result.zone, expected["cf_self_sufficiency_zone"])
        self.assertIsNone(result.warning)

    def test_missing_delta_ar_falls_back_to_simplified(self):
        """欠落とゼロの区別（missing側）：Δ売掛金のフィールド自体が欠落していると簡易層にフォールバックする。

        zero側テスト（test_zero_delta_ar_is_not_treated_as_missing）と
        delta_inv・delta_apは同じ0.0を使い、delta_arの有無だけを変えている。
        両テストの結果が異なることが、欠落とゼロを区別できている証拠になる。
        """
        case = self.cases["zero_vs_missing_delta_ar_missing_falls_back_to_simplified"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            annual_principal_repayment_scheduled=inputs["annual_principal_repayment_scheduled"],
            net_income=inputs["net_income"],
            depreciation_total=inputs["depreciation_total"],
            # delta_ar を渡さない（=None・欠落）。delta_inv・delta_apは0.0で渡す。
            delta_inv=inputs["delta_inv"],
            delta_ap=inputs["delta_ap"],
            ordinary_profit=inputs["ordinary_profit"],
            tax=inputs["tax"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertTrue(result.judgment_blocked)
        self.assertIsNone(result.cf_self_sufficiency)
        self.assertIsNone(result.zone)
        self.assertEqual(result.warning, expected["warning"])

    def test_missing_annual_principal_repayment_blocks_formal_judgment(self):
        """2026-07-12追加（Eタスクeval E-3で発見した不具合の回帰テスト）。

        営業CFの層（推計層）は正常に解決できても、CF自走性の分母
        （年間元本返済予定額）自体が欠落している場合、judgment_status="formal"
        を誤って返してはならない（旧実装は無警告でformalを返していた）。
        """
        case = self.cases["annual_principal_repayment_missing_blocks_formal_judgment"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            # scheduled／actual_proxy／manual_estimateのいずれも渡さない＝欠落
            net_income=inputs["net_income"],
            depreciation_total=inputs["depreciation_total"],
            delta_ar=inputs["delta_ar"],
            delta_inv=inputs["delta_inv"],
            delta_ap=inputs["delta_ap"],
            capex_maintenance_actual=inputs["maintenance_investment"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertEqual(result.capex_source, expected["capex_source"])
        self.assertAlmostEqual(result.fcf, expected["fcf"], places=6)
        self.assertIsNone(result.cf_self_sufficiency)
        self.assertIsNone(result.zone)
        self.assertIsNone(result.judgment)
        self.assertEqual(result.judgment_status, expected["judgment_status"])
        self.assertTrue(result.judgment_blocked)
        self.assertEqual(result.repayment_source, "missing")
        self.assertEqual(result.warning_code, expected["warning_code"])
        self.assertEqual(result.warning_code, fc.WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_MISSING)
        self.assertIsNotNone(result.warning)

    def test_actual_proxy_repayment_blocks_formal_judgment_but_returns_reference_ratio(self):
        """追加仕様・検品要件①②の回帰テスト：実績返済額の代用値はformalにしてはならない。

        比率自体は参考計算値として返すが、judgment・zoneはNoneのまま、
        judgment_status=screening_only・専用warning_codeを返すことを確認する。
        """
        case = self.cases["annual_principal_repayment_actual_proxy_blocks_formal_judgment"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            annual_principal_repayment_actual_proxy=inputs["annual_principal_repayment_actual_proxy"],
            net_income=inputs["net_income"],
            depreciation_total=inputs["depreciation_total"],
            delta_ar=inputs["delta_ar"],
            delta_inv=inputs["delta_inv"],
            delta_ap=inputs["delta_ap"],
            capex_maintenance_actual=inputs["maintenance_investment"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertEqual(result.capex_source, expected["capex_source"])
        self.assertAlmostEqual(result.fcf, expected["fcf"], places=6)
        self.assertAlmostEqual(result.cf_self_sufficiency, expected["cf_self_sufficiency"], places=6)
        self.assertIsNone(result.zone)
        self.assertIsNone(result.judgment)
        self.assertEqual(result.judgment_status, "screening_only")
        self.assertTrue(result.judgment_blocked)
        self.assertEqual(result.repayment_source, "actual_proxy")
        self.assertEqual(result.warning_code, fc.WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_ACTUAL_PROXY_USED)
        self.assertIsNotNone(result.warning)

    def test_manual_estimate_repayment_blocks_formal_judgment_but_returns_reference_ratio(self):
        """追加仕様・検品要件①②の回帰テスト（manual_estimate側）。"""
        case = self.cases["annual_principal_repayment_manual_estimate_blocks_formal_judgment"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            annual_principal_repayment_manual_estimate=inputs["annual_principal_repayment_manual_estimate"],
            net_income=inputs["net_income"],
            depreciation_total=inputs["depreciation_total"],
            delta_ar=inputs["delta_ar"],
            delta_inv=inputs["delta_inv"],
            delta_ap=inputs["delta_ap"],
            capex_maintenance_actual=inputs["maintenance_investment"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertEqual(result.capex_source, expected["capex_source"])
        self.assertAlmostEqual(result.fcf, expected["fcf"], places=6)
        self.assertAlmostEqual(result.cf_self_sufficiency, expected["cf_self_sufficiency"], places=6)
        self.assertIsNone(result.zone)
        self.assertIsNone(result.judgment)
        self.assertEqual(result.judgment_status, "screening_only")
        self.assertTrue(result.judgment_blocked)
        self.assertEqual(result.repayment_source, "manual_estimate")
        self.assertEqual(result.warning_code, fc.WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_MANUAL_ESTIMATE_USED)
        self.assertIsNotNone(result.warning)

    def test_multiple_repayment_sources_given_simultaneously_raises(self):
        """由来の混在（scheduledとactual_proxyを同時指定等）はValueErrorとする。"""
        with self.assertRaises(ValueError):
            fc.calc_cf_self_sufficiency(
                annual_principal_repayment_scheduled=20000.0,
                annual_principal_repayment_actual_proxy=18000.0,
                net_income=26000.0, depreciation_total=20000.0,
                delta_ar=0.0, delta_inv=0.0, delta_ap=0.0,
                capex_maintenance_actual=20000.0,
            )

    def test_total_capex_proxy_conservative_scenario_does_not_override_formal(self):
        """追加仕様・検品要件③の回帰テスト：total_capex_proxyは基本計算・formal判定を上書きしない。"""
        case = self.cases["total_capex_proxy_conservative_scenario_does_not_override_formal"]
        inputs = case["inputs"]
        expected = case["expected"]
        result = fc.calc_cf_self_sufficiency(
            annual_principal_repayment_scheduled=inputs["annual_principal_repayment_scheduled"],
            net_income=inputs["net_income"],
            depreciation_total=inputs["depreciation_total"],
            delta_ar=inputs["delta_ar"],
            delta_inv=inputs["delta_inv"],
            delta_ap=inputs["delta_ap"],
            capex_maintenance_actual=inputs["maintenance_investment"],
            total_capex_proxy=inputs["total_capex_proxy"],
        )
        # 基本結果（total_capex_proxyの影響を一切受けない）
        self.assertEqual(result.capex_source, expected["capex_source"])
        self.assertAlmostEqual(result.fcf, expected["fcf"], places=6)
        self.assertAlmostEqual(result.cf_self_sufficiency, expected["cf_self_sufficiency"], places=6)
        self.assertEqual(result.zone, expected["cf_self_sufficiency_zone"])
        self.assertEqual(result.judgment, expected["cf_self_sufficiency_zone"])
        self.assertEqual(result.judgment_status, "formal")
        self.assertFalse(result.judgment_blocked)
        self.assertIsNone(result.warning_code)
        # 保守シナリオ（基本結果と分離。judgment・judgment_statusを持たない）
        self.assertIsNotNone(result.conservative_scenario)
        self.assertAlmostEqual(
            result.conservative_scenario.total_capex_proxy, expected["conservative_total_capex_proxy"], places=6,
        )
        self.assertAlmostEqual(
            result.conservative_scenario.fcf_conservative, expected["conservative_fcf"], places=6,
        )
        self.assertAlmostEqual(
            result.conservative_scenario.cf_self_sufficiency_conservative,
            expected["conservative_cf_self_sufficiency"], places=6,
        )
        self.assertFalse(hasattr(result.conservative_scenario, "judgment"))
        self.assertFalse(hasattr(result.conservative_scenario, "judgment_status"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
