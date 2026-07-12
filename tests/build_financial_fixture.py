# -*- coding: utf-8 -*-
"""
financial-analysis テストケース設計用モデルビルダー（残タスク③）

目的：
- docs/financial-analysis_指標定義書_v0.2.md の全指標について、
  架空製造業3期分の決算数値からの期待値を「暗算せず」コード実行で算出する。
- 出力は tests/fixtures/ 配下のJSONに書き出し、後続の financial_calc.py
  実装がそのまま参照できるようにする。

このスクリプト自体は納品物ではなく、fixtures生成・検算用のツールである。
数値・企業名はすべて架空。単位はすべて千円（数量のみ「個」）。
"""
import json
from pathlib import Path

TAX_RATE = 0.35
DAYS_IN_YEAR = 365.0
SURPLUS_CASH_SAFETY_MONTHS = 3  # §17: N=3（v0.2固定）
CASH_BUFFER_FOR_RECONFIGURED_DEBT = 0.0  # §18 分配可能原資の「現預金積増計画」（本fixtureでは0固定）

# ============================================================
# 期首（Period0・第1期開始前）B/S
# ============================================================
# 作り方：他の項目を先に決め、貸借一致となるよう現金預金を逆算する
# （実務の決算書の作り方としては不自然だが、テストfixtureとして
#  貸借一致を絶対要件にするための構成手順。以降は複式簿記の恒等式
#  （期末現金＝期首現金＋営業CF＋投資CF＋財務CF）で機械的に前進させる
#  ため、Period1以降は自動的に貸借一致する）。

opening = {
    "accounts_receivable": 98630.0,   # 45日分（対応年間売上高800,000千円ベース）
    "inventory": 78904.0,             # 60日分（対応変動費480,000千円ベース）
    "ppe_net": 200000.0,
    "accounts_payable": 39452.0,      # 30日分（対応変動費480,000千円ベース）
    "borrowings": 500000.0,           # 過去の設備投資・コロナ融資等で借入依存度が高い前提
    "capital_stock": 50000.0,
    "retained_earnings": -10000.0,    # 過去の累積損失が薄く残る前提（直近3期は黒字化途上）
}
opening["cash"] = (
    opening["accounts_payable"] + opening["borrowings"]
    + opening["capital_stock"] + opening["retained_earnings"]
    - opening["accounts_receivable"] - opening["inventory"] - opening["ppe_net"]
)

# ============================================================
# 各期のP/L前提（すべて千円。数量のみ「個」）
# ============================================================
# MQ会計：単一製品に単純化。P（単価）・V（単位変動費）・Q（数量）を明示し、
# 売上高＝P×Q、変動費＝V×Qとなるよう整合させる。
periods_input = [
    {
        "name": "第1期（安定期）",
        "units_q": 10000.0,        # Q（年間販売数量・個）
        "unit_price_p": 80.0,      # P（単価・千円/個）
        "unit_variable_cost_v": 48.0,  # V（単位変動費・千円/個）
        # 変動費のうち外部労働費（人的役務相当）の割合。製造の外注加工費のうち
        # 人的役務部分（§3 外部労働費）を示すための内訳（P/L合計は変えないメモ値）。
        "variable_cost_outsourced_labor_ratio": 0.05,
        "fixed_costs": {
            "labor_cogs": 120000.0,       # 労務費（原価）
            "rent_cogs": 40000.0,         # 賃借料（原価）
            "depreciation_cogs": 16000.0, # 減価償却費（原価）
            "personnel_sga": 55000.0,     # 人件費（販管費）
            "rent_sga": 10000.0,          # 賃借料（販管費）
            "depreciation_sga": 4000.0,   # 減価償却費（販管費）
            "tax_dues_sga": 5000.0,       # 租税公課（販管費）
            "skill_dev_sga": 1000.0,      # 能力開発費（販管費・特掲）
            "other_fixed_sga": 19000.0,   # その他固定費（販管費）
        },
        "ar_days": 45, "inv_days": 60, "ap_days": 30,
        "capex": 20000.0,               # 維持投資（＝減価償却費と一致させる。§18前提）
        "debt_repayment": 20000.0,      # 当期元本返済額（予定通り＝年間返済元金）
        "debt_new_borrowing": 0.0,
        "interest_rate": 0.02,          # 期首借入金残高に対して
    },
    {
        "name": "第2期（急成長期・必須シナリオ）",
        "units_q": 12500.0,         # 前期比+25%
        "unit_price_p": 80.0,
        "unit_variable_cost_v": 48.0,
        "variable_cost_outsourced_labor_ratio": 0.05,
        "fixed_costs": {
            "labor_cogs": 132000.0,
            "rent_cogs": 40000.0,
            "depreciation_cogs": 16000.0,
            "personnel_sga": 58000.0,
            "rent_sga": 10000.0,
            "depreciation_sga": 4000.0,
            "tax_dues_sga": 5500.0,
            "skill_dev_sga": 1000.0,
            "other_fixed_sga": 19500.0,
        },
        # 急拡大により回収・在庫が悪化（売掛金・棚卸資産の滞留日数が伸びる）。
        # これが「黒字なのにCF自走性<1.0」を発生させる主因（本ケースの核）。
        "ar_days": 55, "inv_days": 75, "ap_days": 30,
        "capex": 20000.0,
        "debt_repayment": 20000.0,
        "debt_new_borrowing": 0.0,
        "interest_rate": 0.02,
    },
    {
        "name": "第3期（回復・安定化期）",
        "units_q": 13125.0,         # 前期比+5%（成長は鈍化・回収サイト正常化）
        "unit_price_p": 80.0,
        "unit_variable_cost_v": 48.0,
        "variable_cost_outsourced_labor_ratio": 0.05,
        "fixed_costs": {
            "labor_cogs": 133000.0,
            "rent_cogs": 40000.0,
            "depreciation_cogs": 16000.0,
            "personnel_sga": 58500.0,
            "rent_sga": 10000.0,
            "depreciation_sga": 4000.0,
            "tax_dues_sga": 5600.0,
            "skill_dev_sga": 1000.0,
            "other_fixed_sga": 19600.0,
        },
        # 回収サイト・在庫日数が正常水準に戻る（急成長期の反動でCFが急回復する）
        "ar_days": 45, "inv_days": 60, "ap_days": 30,
        "capex": 20000.0,
        "debt_repayment": 20000.0,
        "debt_new_borrowing": 0.0,
        "interest_rate": 0.02,
    },
]


def zone_cf_self_sufficiency(x):
    if x is None:
        return "算定不能（年間返済元金ゼロ）"
    if x < 1.0:
        return "要改善（自走していない。最優先論点）"
    if x < 1.2:
        return "ぎりぎり（自走はしているが、突発的な支出へのショック耐性がない）"
    if x < 1.5:
        return "標準（銀行の融資目安圏）"
    return "余裕（銀行評価良好圏）"


def zone_debt_payback_ebitda(years):
    if years is None:
        return "算定不能（EBITDAがゼロ以下）"
    if years < 0:
        return "実質無借金相当（ネット有利子負債がマイナス）"
    if years < 7:
        return "良好（追加調達余力あり）"
    if years < 10:
        return "標準（公的制度基準10年/10倍以内）"
    if years <= 13:
        return "注意（中小企業平均圏内だが制度基準外）"
    return "要改善（改善論点として必ず提示）"


def zone_cash_months(months):
    if months is None:
        return "算定不能（月商ゼロ）"
    if months < 1.0:
        return "危険水域（資金繰りリスク・最優先論点）"
    if months < 2.0:
        return "最低確保ゾーン（世間目安の下限圏。増強を推奨）"
    if months < 3.0:
        return "標準ゾーン（通常運転として許容）"
    return "安全〜戦略判断ゾーン（余剰現預金を算出し戦略論点化）"


def compute_period(prev_bs, p):
    sales = p["units_q"] * p["unit_price_p"]
    variable_cost = p["units_q"] * p["unit_variable_cost_v"]
    m_unit = p["unit_price_p"] - p["unit_variable_cost_v"]
    mq = m_unit * p["units_q"]
    assert abs(mq - (sales - variable_cost)) < 1e-6, "MQ整合チェック失敗"

    outsourced_labor_cost = variable_cost * p["variable_cost_outsourced_labor_ratio"]

    fc = p["fixed_costs"]
    fixed_total = sum(fc.values())
    operating_profit = mq - fixed_total  # G（MQ会計のG＝MQ−F。会計上の営業利益と一致）

    opening_borrowings = prev_bs["borrowings"]
    interest_expense = opening_borrowings * p["interest_rate"]
    ordinary_profit = operating_profit - interest_expense

    tax = max(ordinary_profit, 0.0) * TAX_RATE
    net_income = ordinary_profit - tax

    # B/S期末残高（回転日数ベース）
    ar_end = sales / DAYS_IN_YEAR * p["ar_days"]
    inv_end = variable_cost / DAYS_IN_YEAR * p["inv_days"]
    ap_end = variable_cost / DAYS_IN_YEAR * p["ap_days"]

    depreciation_total = fc["depreciation_cogs"] + fc["depreciation_sga"]
    ppe_end = prev_bs["ppe_net"] + p["capex"] - depreciation_total

    borrowings_end = opening_borrowings - p["debt_repayment"] + p["debt_new_borrowing"]
    capital_stock_end = prev_bs["capital_stock"]  # 増減なし
    retained_earnings_end = prev_bs["retained_earnings"] + net_income  # 配当なし

    # --- 推計営業CF（2026-07-12訂正：本fixtureにはCF計算書が無いため、
    #     P/L＋2期分B/Sから運転資本増減を反映して間接法準拠で推計する。
    #     以前「実績営業CF」と呼んでいたが、起点がP/L・B/Sであり実績値では
    #     ないため誤りだった。ocf_source=estimated として扱う ---
    delta_ar = ar_end - prev_bs["accounts_receivable"]
    delta_inv = inv_end - prev_bs["inventory"]
    delta_ap = ap_end - prev_bs["accounts_payable"]
    estimated_operating_cf = net_income + depreciation_total - delta_ar - delta_inv + delta_ap

    investing_cf = -p["capex"]
    financing_cf = p["debt_new_borrowing"] - p["debt_repayment"]

    cash_end = prev_bs["cash"] + estimated_operating_cf + investing_cf + financing_cf

    bs_end = {
        "cash": cash_end,
        "accounts_receivable": ar_end,
        "inventory": inv_end,
        "ppe_net": ppe_end,
        "accounts_payable": ap_end,
        "borrowings": borrowings_end,
        "capital_stock": capital_stock_end,
        "retained_earnings": retained_earnings_end,
    }

    total_assets = bs_end["cash"] + bs_end["accounts_receivable"] + bs_end["inventory"] + bs_end["ppe_net"]
    total_liab_equity = (bs_end["accounts_payable"] + bs_end["borrowings"]
                          + bs_end["capital_stock"] + bs_end["retained_earnings"])
    balance_check = total_assets - total_liab_equity

    employment_labor_cost = fc["labor_cogs"] + fc["personnel_sga"]
    total_human_cost = employment_labor_cost + outsourced_labor_cost  # §3 総人的コスト

    pl = {
        "units_q": p["units_q"],
        "unit_price_p": p["unit_price_p"],
        "unit_variable_cost_v": p["unit_variable_cost_v"],
        "unit_margin_m": m_unit,
        "sales": sales,
        "variable_cost": variable_cost,
        "outsourced_labor_cost": outsourced_labor_cost,
        "mq": mq,
        "margin_ratio": mq / sales,
        "fixed_costs": fc,
        "fixed_costs_total": fixed_total,
        "operating_profit": operating_profit,  # ＝G
        "interest_expense": interest_expense,
        "ordinary_profit": ordinary_profit,
        "tax": tax,
        "net_income": net_income,
        "depreciation_total": depreciation_total,
        "employment_labor_cost": employment_labor_cost,
        "total_human_cost": total_human_cost,
    }

    cf = {
        "net_income": net_income,
        "depreciation_total": depreciation_total,
        "delta_ar": delta_ar,
        "delta_inv": delta_inv,
        "delta_ap": delta_ap,
        "estimated_operating_cf": estimated_operating_cf,  # ＝推計営業CF（CF計算書なし。ocf_source=estimated）
        "investing_cf": investing_cf,
        "financing_cf": financing_cf,
        "capex": p["capex"],                   # 実額の維持投資（本fixtureでは減価償却費と一致するよう設計。capex_source=actual）
        "debt_repayment": p["debt_repayment"],
        "debt_new_borrowing": p["debt_new_borrowing"],
    }

    return pl, cf, bs_end, balance_check, total_assets, total_liab_equity


def compute_indicators(pl, cf, bs_end, prev_bs):
    result = {}
    fc = pl["fixed_costs"]

    # ============================================================
    # §1 キャッシュフロー系指標（4定義）
    # ============================================================
    # 本fixtureにはCF計算書が無いため、営業CFの実体は「推計営業CF」
    # （ocf_source=estimated）である。§18の3層優先順位のうち第2層。
    estimated_operating_cf = cf["estimated_operating_cf"]
    simple_operating_cf = pl["ordinary_profit"] + pl["depreciation_total"] - pl["tax"]  # 簡易営業CF（補正なし＝補正後と同値。速報・一次スクリーニング専用）
    broad_fcf = estimated_operating_cf + cf["investing_cf"]  # 広義FCF（投資CFは負数のまま加算）
    # 維持投資：実額（capex）が取得できるため実額を使用する（capex_source=actual）。
    # 減価償却費への代理は行わない（実額があるのに代理値を使うのは禁止のため）。
    maintenance_investment_actual = cf["capex"]
    capex_source = "actual"
    # 返済原資CF＝補正後簡易営業CF−維持投資−事業外資金流出（本fixtureでは調整項目・事業外流出=0）
    repayment_source_cf = simple_operating_cf - maintenance_investment_actual - 0.0
    result["estimated_operating_cf"] = estimated_operating_cf
    result["ocf_source"] = "estimated"
    result["simple_operating_cf"] = simple_operating_cf
    result["broad_fcf"] = broad_fcf
    result["repayment_source_cf_calculated"] = repayment_source_cf
    result["repayment_source_cf_adjustment_items"] = 0.0
    result["repayment_source_cf_adjustment_reason"] = "本fixtureでは実態修正・事業外資金流出なし（調整なしの計算値のみ）"

    # ============================================================
    # §2 債務償還年数と返済負担
    # ============================================================
    gross_interest_bearing_debt = bs_end["borrowings"]  # ①総有利子負債
    net_interest_bearing_debt = bs_end["borrowings"] - bs_end["cash"]  # ②ネット有利子負債
    normal_working_capital = bs_end["accounts_receivable"] + bs_end["inventory"] - bs_end["accounts_payable"]
    monthly_sales = pl["sales"] / 12.0
    surplus_cash = bs_end["cash"] - (normal_working_capital + monthly_sales * SURPLUS_CASH_SAFETY_MONTHS)
    # ④Grow3調整後要返済債務＝有利子負債−正常運転資金−余剰現預金（余剰現預金がマイナスなら控除なし＝0扱い）
    surplus_cash_for_deduction = max(surplus_cash, 0.0)
    grow3_adjusted_debt = gross_interest_bearing_debt - normal_working_capital - surplus_cash_for_deduction

    debt_payback_years_screening = (
        gross_interest_bearing_debt / simple_operating_cf if simple_operating_cf else None
    )  # 一次スクリーニング：①÷簡易営業CF
    debt_payback_years_detailed = (
        grow3_adjusted_debt / simple_operating_cf if simple_operating_cf else None
    )  # 精査時：④÷簡易営業CF

    annual_principal_next12m = cf["debt_repayment"]  # 今後12か月の元本返済予定額（本fixtureでは当期実績＝翌期予定と仮定）
    principal_repayment_burden_ratio = (
        annual_principal_next12m / repayment_source_cf if repayment_source_cf else None
    )

    result["gross_interest_bearing_debt"] = gross_interest_bearing_debt
    result["net_interest_bearing_debt"] = net_interest_bearing_debt
    result["normal_working_capital"] = normal_working_capital
    result["grow3_adjusted_debt"] = grow3_adjusted_debt
    result["debt_payback_years_screening_def1_over_simple_ocf"] = debt_payback_years_screening
    result["debt_payback_years_detailed_def4_over_simple_ocf"] = debt_payback_years_detailed
    result["annual_principal_repayment_next12m"] = annual_principal_next12m
    result["principal_repayment_burden_ratio"] = principal_repayment_burden_ratio

    # ============================================================
    # §3 人件費の定義（3層構造）
    # ============================================================
    result["employment_labor_cost"] = pl["employment_labor_cost"]
    result["outsourced_labor_cost"] = pl["outsourced_labor_cost"]
    result["total_human_cost"] = pl["total_human_cost"]

    # ============================================================
    # §4 労働分配率系指標
    # ============================================================
    value_added = (
        fc["labor_cogs"] + fc["rent_cogs"] + fc["depreciation_cogs"]
        + fc["personnel_sga"] + fc["rent_sga"] + fc["depreciation_sga"] + fc["tax_dues_sga"]
        + pl["interest_expense"] + pl["ordinary_profit"] + fc["skill_dev_sga"]
    )
    labor_cost_stat = fc["labor_cogs"] + fc["personnel_sga"]
    labor_share_stat = labor_cost_stat / value_added * 100 if value_added else None
    labor_share_bast = pl["employment_labor_cost"] / pl["mq"] * 100  # ＝MQ雇用人件費比率
    mq_total_human_cost_ratio = pl["total_human_cost"] / pl["mq"] * 100

    result["value_added"] = value_added
    result["labor_share_stat_pct"] = labor_share_stat
    result["labor_share_bast_pct"] = labor_share_bast
    result["mq_employment_labor_ratio_pct"] = labor_share_bast
    result["mq_total_human_cost_ratio_pct"] = mq_total_human_cost_ratio

    # ============================================================
    # §5 MQ会計
    # ============================================================
    result["mq_p_unit_price"] = pl["unit_price_p"]
    result["mq_v_unit_variable_cost"] = pl["unit_variable_cost_v"]
    result["mq_q_units"] = pl["units_q"]
    result["mq_m_unit_margin"] = pl["unit_margin_m"]
    result["mq_mq_total"] = pl["mq"]
    result["mq_f_fixed_total"] = pl["fixed_costs_total"]
    result["mq_g_operating_profit"] = pl["operating_profit"]

    # ============================================================
    # §14/§15 中核指標：限界利益率・債務償還年数（EBITDA倍率型）
    # ============================================================
    result["margin_ratio_pct"] = pl["margin_ratio"] * 100
    ebitda = pl["operating_profit"] + pl["depreciation_total"]
    debt_payback_years_ebitda = net_interest_bearing_debt / ebitda if ebitda else None
    result["ebitda"] = ebitda
    result["debt_payback_years_ebitda"] = debt_payback_years_ebitda
    result["debt_payback_years_ebitda_zone"] = zone_debt_payback_ebitda(debt_payback_years_ebitda)

    # ============================================================
    # §17 余剰現預金
    # ============================================================
    cash_to_monthly_sales_ratio = bs_end["cash"] / monthly_sales if monthly_sales else None
    result["monthly_sales"] = monthly_sales
    result["cash_to_monthly_sales_ratio"] = cash_to_monthly_sales_ratio
    result["cash_to_monthly_sales_zone"] = zone_cash_months(cash_to_monthly_sales_ratio)
    result["surplus_cash"] = surplus_cash

    # ============================================================
    # §18 CF自走性（第0指標）
    # 2026-07-12訂正：営業CFは3層優先順位の第2層「推計営業CF」
    # （ocf_source=estimated）を使用。維持投資は実額capexを使用
    # （capex_source=actual。減価償却費への代理は実額がある本fixtureでは
    #  行わない＝実額があるのに代理値を使うことは禁止のルールに従う）。
    # ============================================================
    fcf = estimated_operating_cf - maintenance_investment_actual
    cf_self_sufficiency = fcf / annual_principal_next12m if annual_principal_next12m else None
    distributable_resource = fcf - annual_principal_next12m - CASH_BUFFER_FOR_RECONFIGURED_DEBT
    result["fcf"] = fcf
    result["capex_source"] = capex_source
    result["cf_self_sufficiency"] = cf_self_sufficiency
    result["cf_self_sufficiency_zone"] = zone_cf_self_sufficiency(cf_self_sufficiency)
    result["distributable_resource_for_executive_comp"] = distributable_resource

    # ============================================================
    # 参考欄：自己資本比率・ROE（B/S系・合否判定には使わない）
    # ============================================================
    total_assets = bs_end["cash"] + bs_end["accounts_receivable"] + bs_end["inventory"] + bs_end["ppe_net"]
    equity = bs_end["capital_stock"] + bs_end["retained_earnings"]
    equity_ratio = equity / total_assets * 100
    prev_equity = prev_bs["capital_stock"] + prev_bs["retained_earnings"]
    avg_equity = (equity + prev_equity) / 2
    roe = pl["net_income"] / avg_equity * 100 if avg_equity else None
    result["total_assets"] = total_assets
    result["equity"] = equity
    result["equity_ratio_pct"] = equity_ratio
    result["roe_pct"] = roe

    return result


def main():
    prev_bs = dict(opening)
    all_periods = []
    for p in periods_input:
        pl, cf, bs_end, balance_check, total_assets, total_liab_equity = compute_period(prev_bs, p)
        indicators = compute_indicators(pl, cf, bs_end, prev_bs)
        all_periods.append({
            "name": p["name"],
            "input_assumptions": p,
            "opening_bs": dict(prev_bs),
            "pl": pl,
            "cf": cf,
            "ending_bs": bs_end,
            "balance_check": {
                "total_assets": total_assets,
                "total_liabilities_equity": total_liab_equity,
                "diff": balance_check,
            },
            "indicators": indicators,
        })
        prev_bs = bs_end

    out = {
        "_disclaimer": "本fixtureの数値・企業名はすべて架空である。実在の企業・決算データではない。",
        "unit": "千円（数量のみ「個」）",
        "opening_bs_period0": opening,
        "periods": all_periods,
    }

    out_path = Path(__file__).parent / "fixtures" / "financial_analysis_case_manufacturing_3fy.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- サマリー表示（検証用） ----
    print("=== 期首B/S ===")
    print(json.dumps(opening, ensure_ascii=False, indent=2))
    keys_to_print = [
        "ocf_source", "capex_source",
        "cf_self_sufficiency", "cf_self_sufficiency_zone",
        "debt_payback_years_ebitda", "debt_payback_years_ebitda_zone",
        "margin_ratio_pct", "labor_share_stat_pct", "labor_share_bast_pct",
        "mq_total_human_cost_ratio_pct",
        "cash_to_monthly_sales_ratio", "cash_to_monthly_sales_zone", "surplus_cash",
        "debt_payback_years_screening_def1_over_simple_ocf",
        "debt_payback_years_detailed_def4_over_simple_ocf",
        "principal_repayment_burden_ratio",
        "distributable_resource_for_executive_comp",
        "equity_ratio_pct", "roe_pct",
    ]
    for period in all_periods:
        print(f"\n=== {period['name']} ===")
        print("balance_check.diff (should be ~0):", period["balance_check"]["diff"])
        print("net_income:", period["pl"]["net_income"])
        print("estimated_operating_cf:", period["indicators"]["estimated_operating_cf"])
        print("simple_operating_cf:", period["indicators"]["simple_operating_cf"])
        print("fcf:", period["indicators"]["fcf"])
        for k in keys_to_print:
            print(f"{k}:", period["indicators"][k])


if __name__ == "__main__":
    main()
