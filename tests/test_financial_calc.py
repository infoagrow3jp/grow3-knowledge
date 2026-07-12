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
                    inputs["annual_principal_repayment_next12m"],
                    actual_operating_cf=inputs["operating_cf_input"],
                    capex_actual=inputs["maintenance_investment"],
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
            inputs["annual_principal_repayment_next12m"],
            ordinary_profit=inputs["ordinary_profit"],
            depreciation_total=inputs["depreciation_total"],
            tax=inputs["tax"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertTrue(result.judgment_blocked)
        self.assertEqual(result.judgment_blocked, expected["judgment_blocked"])
        self.assertIsNone(result.cf_self_sufficiency)
        self.assertIsNone(result.zone)
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
            inputs["annual_principal_repayment_next12m"],
            net_income=inputs["net_income"],
            depreciation_total=inputs["depreciation_total"],
            delta_ar=inputs["delta_ar"],
            delta_inv=inputs["delta_inv"],
            delta_ap=inputs["delta_ap"],
            capex_actual=inputs["maintenance_investment"],
        )
        self.assertEqual(result.ocf_source, expected["ocf_source"])
        self.assertFalse(result.judgment_blocked)
        self.assertEqual(result.judgment_blocked, expected["judgment_blocked"])
        self.assertAlmostEqual(result.fcf, expected["fcf"], places=6)
        self.assertAlmostEqual(result.cf_self_sufficiency, expected["cf_self_sufficiency"], places=6)
        self.assertEqual(result.zone, expected["cf_self_sufficiency_zone"])
        self.assertIsNone(result.warning)


if __name__ == "__main__":
    unittest.main(verbosity=2)
