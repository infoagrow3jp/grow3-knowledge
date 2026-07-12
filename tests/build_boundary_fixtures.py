# -*- coding: utf-8 -*-
"""
financial-analysis テストケース設計用（残タスク③・境界値ミニケース）

目的：確定済みの閾値境界（債務償還年数EBITDA倍率型／余剰現預金月商倍率／
CF自走性）を、B/S全体の整合を要さない最小構成のミニケースとして生成する。
本体3期ケース（financial_analysis_case_manufacturing_3fy.json）を補完する。

数値・企業名はすべて架空。単位は千円。
"""
import json
from pathlib import Path


def build_cf_self_sufficiency_cases():
    """
    CF自走性＝FCF÷年間返済元金。境界値：0.95／1.00／1.19／1.20／1.50
    年間返済元金を10,000千円に固定し、FCFを逆算する。
    FCF＝実績営業CF−維持投資（≒減価償却費）。減価償却費は5,000千円に固定し、
    実績営業CF＝FCF＋減価償却費で逆算する。
    """
    annual_principal = 10000.0
    depreciation = 5000.0
    targets = [0.95, 1.00, 1.19, 1.20, 1.50]
    cases = []
    for ratio in targets:
        fcf = ratio * annual_principal
        actual_operating_cf = fcf + depreciation
        computed_ratio = fcf / annual_principal
        if computed_ratio < 1.0:
            zone = "要改善（自走していない。最優先論点）"
        elif computed_ratio < 1.2:
            zone = "ぎりぎり（自走はしているが、突発的な支出へのショック耐性がない）"
        elif computed_ratio < 1.5:
            zone = "標準（銀行の融資目安圏）"
        else:
            zone = "余裕（銀行評価良好圏）"
        cases.append({
            "case_id": f"cf_self_sufficiency_{ratio}",
            "target_ratio": ratio,
            "inputs": {
                "actual_operating_cf": actual_operating_cf,
                "maintenance_capex_proxy_depreciation": depreciation,
                "annual_principal_repayment_next12m": annual_principal,
            },
            "expected": {
                "fcf": fcf,
                "cf_self_sufficiency": computed_ratio,
                "zone": zone,
            },
            "formula": "CF自走性 = FCF ÷ 年間返済元金、FCF = 実績営業CF − 維持投資（≒減価償却費）",
        })
    return cases


def build_debt_payback_ebitda_cases():
    """
    債務償還年数（EBITDA倍率型）＝（有利子負債−現預金）÷（営業利益＋減価償却費）。
    境界値：9.9／10.0／13.1年
    EBITDA（営業利益＋減価償却費）＝10,000千円に固定（営業利益8,000＋減価償却費2,000）。
    現預金＝20,000千円に固定し、有利子負債＝年数×EBITDA＋現預金 で逆算する。
    """
    operating_profit = 8000.0
    depreciation = 2000.0
    ebitda = operating_profit + depreciation
    cash = 20000.0
    targets = [9.9, 10.0, 13.1]
    cases = []
    for years in targets:
        net_debt = years * ebitda
        borrowings = net_debt + cash
        computed_years = (borrowings - cash) / ebitda
        if computed_years < 7:
            zone = "良好（追加調達余力あり）"
        elif computed_years < 10:
            zone = "標準（公的制度基準10年/10倍以内）"
        elif computed_years <= 13:
            zone = "注意（中小企業平均圏内だが制度基準外）"
        else:
            zone = "要改善（改善論点として必ず提示）"
        cases.append({
            "case_id": f"debt_payback_ebitda_{years}",
            "target_years": years,
            "inputs": {
                "operating_profit": operating_profit,
                "depreciation_total": depreciation,
                "cash": cash,
                "borrowings": borrowings,
            },
            "expected": {
                "ebitda": ebitda,
                "net_interest_bearing_debt": net_debt,
                "debt_payback_years_ebitda": computed_years,
                "zone": zone,
            },
            "formula": "債務償還年数（EBITDA倍率型） = （有利子負債 − 現預金） ÷ （営業利益 ＋ 減価償却費）",
        })
    return cases


def build_cash_months_cases():
    """
    余剰現預金ゾーン判定＝現預金÷月商。境界値：0.9／1.0／2.9／3.0か月
    月商＝10,000千円（年間売上高120,000千円）に固定し、現預金＝倍率×月商で逆算する。
    余剰現預金＝現預金−（正常運転資金＋月商×3）も参考として算出する
    （正常運転資金は15,000千円に固定）。
    """
    monthly_sales = 10000.0
    normal_working_capital = 15000.0
    targets = [0.9, 1.0, 2.9, 3.0]
    cases = []
    for months in targets:
        cash = months * monthly_sales
        computed_months = cash / monthly_sales
        if computed_months < 1.0:
            zone = "危険水域（資金繰りリスク・最優先論点）"
        elif computed_months < 2.0:
            zone = "最低確保ゾーン（世間目安の下限圏。増強を推奨）"
        elif computed_months < 3.0:
            zone = "標準ゾーン（通常運転として許容）"
        else:
            zone = "安全〜戦略判断ゾーン（余剰現預金を算出し戦略論点化）"
        surplus_cash = cash - (normal_working_capital + monthly_sales * 3)
        cases.append({
            "case_id": f"cash_months_{months}",
            "target_months": months,
            "inputs": {
                "cash": cash,
                "monthly_sales": monthly_sales,
                "normal_working_capital": normal_working_capital,
            },
            "expected": {
                "cash_to_monthly_sales_ratio": computed_months,
                "zone": zone,
                "surplus_cash": surplus_cash,
            },
            "formula": (
                "ゾーン判定 = 現預金 ÷ 月商。"
                "余剰現預金 = 現預金 − （正常運転資金 ＋ 月商 × 3）"
            ),
        })
    return cases


def main():
    out = {
        "_disclaimer": "本fixtureの数値はすべて架空である。実在の企業・決算データではない。",
        "_purpose": (
            "docs/financial-analysis_指標定義書_v0.2.md で確定済みの閾値境界を"
            "単体で検証するためのミニケース群。本体3期ケース"
            "（financial_analysis_case_manufacturing_3fy.json）を補完する。"
            "B/S全体の整合は要さず、各指標の計算に必要な項目のみで構成する。"
        ),
        "unit": "千円",
        "cf_self_sufficiency_boundary_cases": build_cf_self_sufficiency_cases(),
        "debt_payback_ebitda_boundary_cases": build_debt_payback_ebitda_cases(),
        "cash_months_boundary_cases": build_cash_months_cases(),
    }

    out_path = Path(__file__).parent / "fixtures" / "financial_analysis_boundary_cases.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
