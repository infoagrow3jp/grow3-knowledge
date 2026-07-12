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
    FCF＝営業CF−維持投資。維持投資は5,000千円に固定し、
    営業CF＝FCF＋維持投資で逆算する。

    注：本ケース群は§18のFCF÷年間返済元金の算式とゾーン境界のみを検証する
    ものであり、営業CFがどの層（実績／推計／簡易）から得られたかは問わない
    （層の選択ロジック自体は`ocf_source_safety_cases`で別途検証する）。
    そのため入力キーは層を示唆しない`operating_cf_input`とする。
    """
    annual_principal = 10000.0
    maintenance_investment = 5000.0
    targets = [0.95, 1.00, 1.19, 1.20, 1.50]
    cases = []
    for ratio in targets:
        fcf = ratio * annual_principal
        operating_cf_input = fcf + maintenance_investment
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
                "operating_cf_input": operating_cf_input,
                "maintenance_investment": maintenance_investment,
                "annual_principal_repayment_next12m": annual_principal,
            },
            "expected": {
                "fcf": fcf,
                "cf_self_sufficiency": computed_ratio,
                "zone": zone,
            },
            "formula": "CF自走性 = FCF ÷ 年間返済元金、FCF = 営業CF − 維持投資（層・出典はこのケースでは不問。ocf_source_safety_casesで別途検証）",
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


def build_ocf_source_safety_cases():
    """
    2026-07-12追加（①の指示に基づく②実装向け安全動作ケース）：
    営業CFの3層優先順位（実績＞推計＞簡易）のうち、簡易営業CFしか
    算出できない入力（CF計算書なし・2期分B/Sなし＝前期末B/Sが無い）で
    CF自走性の正式判定を求めた場合、判定値を出さず警告を返すことを
    検証するための最小ケース。B/S全体の整合は不要（前期末B/Sが
    無いことそのものがテストの前提条件）。
    """
    cases = [
        {
            "case_id": "ocf_source_simplified_only_no_prior_bs",
            "description": "前期末B/S・CF計算書のいずれも無く、当期P/Lのみで簡易営業CFしか算出できない入力",
            "inputs": {
                "has_cash_flow_statement": False,
                "has_prior_period_bs": False,
                "ordinary_profit": 48000.0,
                "depreciation_total": 20000.0,
                "tax": 16800.0,
                "annual_principal_repayment_next12m": 20000.0,
            },
            "expected": {
                "ocf_source": "simplified",
                "simple_operating_cf": 51200.0,
                "cf_self_sufficiency": None,
                "cf_self_sufficiency_zone": None,
                "judgment_blocked": True,
                "warning": "運転資本変動を確認できないため正式判定不可。2期分のB/SまたはCF計算書が必要",
                "confidence_grade": "C",
            },
            "formula": (
                "簡易営業CF = 経常利益 + 減価償却費 − 法人税等 = 48,000 + 20,000 − 16,800 = 51,200。"
                "ただし簡易営業CFは速報・一次スクリーニング専用のため、CF自走性の正式判定には使用せず、"
                "judgment_blocked=True・warning付きで返す（判定値・ゾーンは出さない）。"
            ),
        },
        {
            "case_id": "ocf_source_estimated_available_with_prior_bs",
            "description": "CF計算書は無いが前期末B/Sがあり、推計営業CFが算出できる入力（対照ケース：判定は実行される）",
            "inputs": {
                "has_cash_flow_statement": False,
                "has_prior_period_bs": True,
                "net_income": 26000.0,
                "depreciation_total": 20000.0,
                "delta_ar": 0.0,
                "delta_inv": 0.0,
                "delta_ap": 0.0,
                "maintenance_investment": 20000.0,
                "annual_principal_repayment_next12m": 20000.0,
            },
            "expected": {
                "ocf_source": "estimated",
                "estimated_operating_cf": 46000.0,
                "fcf": 26000.0,
                "cf_self_sufficiency": 1.3,
                "cf_self_sufficiency_zone": "標準（銀行の融資目安圏）",
                "judgment_blocked": False,
                "warning": None,
            },
            "formula": (
                "推計営業CF = 当期純利益 + 減価償却費 − Δ売掛金 − Δ棚卸資産 + Δ買掛金 "
                "= 26,000 + 20,000 − 0 − 0 + 0 = 46,000。"
                "FCF = 46,000 − 20,000(維持投資) = 26,000。CF自走性 = 26,000 ÷ 20,000 = 1.3倍。"
            ),
        },
        {
            # ①の完了条件④相当ケース：実績と推計可能データが両方ある場合、
            # 実績を優先すること（推計値とは異なる値を意図的に設定し、
            # 返り値が実績値の方であることを検証できるようにする）。
            "case_id": "ocf_source_actual_takes_priority_over_estimated",
            "description": (
                "CF計算書の実績値（actual_operating_cf）と、推計に必要な"
                "P/L＋2期分B/S項目の両方が入力された場合、実績を優先する"
                "（推計すれば46,000になるが、実績値50,000が採用されることを確認する）"
            ),
            "inputs": {
                "has_cash_flow_statement": True,
                "has_prior_period_bs": True,
                "actual_operating_cf": 50000.0,
                "net_income": 26000.0,
                "depreciation_total": 20000.0,
                "delta_ar": 0.0,
                "delta_inv": 0.0,
                "delta_ap": 0.0,
                "maintenance_investment": 20000.0,
                "annual_principal_repayment_next12m": 20000.0,
            },
            "expected": {
                "ocf_source": "actual",
                "operating_cf_value_used": 50000.0,
                "estimated_operating_cf_if_computed_instead": 46000.0,
                "fcf": 30000.0,
                "cf_self_sufficiency": 1.5,
                "cf_self_sufficiency_zone": "余裕（銀行評価良好圏）",
                "judgment_blocked": False,
                "warning": None,
                "confidence_grade": "A",
            },
            "formula": (
                "実績営業CF（CF計算書） = 50,000（推計すれば46,000になるが、実績値が"
                "優先されるため50,000が使用される）。"
                "FCF = 50,000 − 20,000(維持投資) = 30,000。CF自走性 = 30,000 ÷ 20,000 = 1.5倍。"
            ),
        },
        {
            # ①の完了条件④：維持投資の実額（capex_actual）が入力されない場合、
            # 減価償却費を代理値として使用し capex_source=depreciation_proxy を
            # メタデータとして明示すること。
            "case_id": "capex_source_depreciation_proxy_when_capex_actual_missing",
            "description": "維持投資の実額が入力されず、減価償却費を代理値として使用するケース",
            "inputs": {
                "has_cash_flow_statement": True,
                "actual_operating_cf": 50000.0,
                "depreciation_total": 15000.0,
                # maintenance_investment（capex実額）キー自体を与えない＝欠落
                "annual_principal_repayment_next12m": 20000.0,
            },
            "expected": {
                "ocf_source": "actual",
                "capex_source": "depreciation_proxy",
                "maintenance_investment_value_used": 15000.0,
                "fcf": 35000.0,
                "cf_self_sufficiency": 1.75,
                "cf_self_sufficiency_zone": "余裕（銀行評価良好圏）",
            },
            "formula": (
                "維持投資の実額が未入力のため、減価償却費(15,000)を代理値として使用"
                "（capex_source=depreciation_proxy）。"
                "FCF = 50,000 − 15,000 = 35,000。CF自走性 = 35,000 ÷ 20,000 = 1.75倍。"
            ),
        },
        {
            # 欠落とゼロの区別（①の指示3・4／②の完了条件(c)）：
            # Δ売掛金が明示的な0.0（有効な入力値）の場合は推計営業CFを算出できる
            # ことを確認するペアケースの片方（zero側）。
            "case_id": "zero_vs_missing_delta_ar_explicit_zero_estimated_succeeds",
            "description": (
                "Δ売掛金・Δ棚卸資産・Δ買掛金がすべて明示的な数値0.0（実際に"
                "変動が無かった有効な入力値）の場合、欠落と誤判定せず推計営業CFを"
                "算出できることを確認する"
            ),
            "inputs": {
                "net_income": 30000.0,
                "depreciation_total": 10000.0,
                "delta_ar": 0.0,
                "delta_inv": 0.0,
                "delta_ap": 0.0,
                "maintenance_investment": 10000.0,
                "annual_principal_repayment_next12m": 15000.0,
            },
            "expected": {
                "ocf_source": "estimated",
                "estimated_operating_cf": 40000.0,
                "fcf": 30000.0,
                "cf_self_sufficiency": 2.0,
                "cf_self_sufficiency_zone": "余裕（銀行評価良好圏）",
                "judgment_blocked": False,
                "warning": None,
            },
            "formula": (
                "推計営業CF = 30,000 + 10,000 − 0 − 0 + 0 = 40,000（Δ項目が明示的な"
                "0.0であり欠落ではないため、推計営業CFとして正常に算出される）。"
                "FCF = 40,000 − 10,000 = 30,000。CF自走性 = 30,000 ÷ 15,000 = 2.0倍。"
            ),
        },
        {
            # 欠落とゼロの区別のペアケース（missing側）：Δ売掛金の項目自体が
            # 入力されない（欠落）場合は推計層を構成できず、簡易層へ
            # フォールバックし正式判定をブロックすることを確認する。
            # delta_inv・delta_apは同じ0.0を与えており、delta_arの有無だけが
            # 挙動を変える唯一の差分であることに注意（zero側ケースとの対比）。
            "case_id": "zero_vs_missing_delta_ar_missing_falls_back_to_simplified",
            "description": (
                "Δ売掛金のフィールド自体が欠落している場合（他のΔ項目は0.0で"
                "存在）、推計層を構成できず簡易層にフォールバックし正式判定を"
                "ブロックすることを確認する"
            ),
            "inputs": {
                "net_income": 30000.0,
                "depreciation_total": 10000.0,
                # delta_ar キー自体を与えない＝欠落（delta_inv・delta_apは0.0で存在）
                "delta_inv": 0.0,
                "delta_ap": 0.0,
                "ordinary_profit": 40000.0,
                "tax": 14000.0,
                "annual_principal_repayment_next12m": 15000.0,
            },
            "expected": {
                "ocf_source": "simplified",
                "simple_operating_cf": 36000.0,
                "cf_self_sufficiency": None,
                "cf_self_sufficiency_zone": None,
                "judgment_blocked": True,
                "warning": "運転資本変動を確認できないため正式判定不可。2期分のB/SまたはCF計算書が必要",
            },
            "formula": (
                "Δ売掛金が欠落（フィールドなし）のため推計層を構成できず、"
                "簡易営業CF = 40,000 + 10,000 − 14,000 = 36,000 にフォールバック。"
                "簡易営業CFは正式判定に使用しないため judgment_blocked=True。"
            ),
        },
        {
            # 2026-07-12追加（financial-analysis Eタスクeval E-3で発見した不具合の
            # 回帰テスト用ケース）：営業CFの層（推計層）は正常に解決できても、
            # CF自走性の分母（年間元本返済予定額）自体が欠落している場合、
            # judgment_status="formal"を誤って返してはならない
            # （欠落=annual_principal_repayment_next12mキー自体を与えない）。
            "case_id": "annual_principal_repayment_missing_blocks_formal_judgment",
            "description": (
                "推計営業CFは正常に算出できる入力だが、CF自走性の分母である"
                "年間元本返済予定額のフィールド自体が欠落している場合、"
                "judgment_status=formalを返さず、judgment=None・screening_only・"
                "専用warning_codeで判定不可を明示することを確認する"
            ),
            "inputs": {
                "net_income": 26000.0,
                "depreciation_total": 20000.0,
                "delta_ar": 0.0,
                "delta_inv": 0.0,
                "delta_ap": 0.0,
                "maintenance_investment": 20000.0,
                # annual_principal_repayment_next12m キー自体を与えない＝欠落
            },
            "expected": {
                "ocf_source": "estimated",
                "capex_source": "actual",
                "estimated_operating_cf": 46000.0,
                "fcf": 26000.0,
                "cf_self_sufficiency": None,
                "cf_self_sufficiency_zone": None,
                "judgment_blocked": True,
                "judgment_status": "screening_only",
                "warning_code": "ANNUAL_PRINCIPAL_REPAYMENT_MISSING",
            },
            "formula": (
                "推計営業CF = 26,000 + 20,000 − 0 − 0 + 0 = 46,000。"
                "FCF = 46,000 − 20,000(維持投資) = 26,000。"
                "年間元本返済予定額が欠落しているため、CF自走性 = 26,000 ÷ (欠落) は"
                "算定不能。judgment_status=formalを返さず、screening_only・"
                "warning_code=ANNUAL_PRINCIPAL_REPAYMENT_MISSINGで判定不可を明示する。"
            ),
        },
    ]
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
        "ocf_source_safety_cases": build_ocf_source_safety_cases(),
    }

    out_path = Path(__file__).parent / "fixtures" / "financial_analysis_boundary_cases.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
