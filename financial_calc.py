# -*- coding: utf-8 -*-
"""
financial-analysis 計算モジュール（残タスク②：financial_calc.py実装）

docs/financial-analysis_指標定義書_v0.2.md の全指標を実装する。
検算必須原則（§0-1・暗算禁止）に従い、主要な判定関数は計算過程
（使用した項目・式）を `calculation_trace` として結果に含める。

設計方針：
- 各関数は最小限の入力のみを受け取る独立した純粋関数とする（境界値
  ミニケースが最小入力で構成されているため、実装側もそれに対応する）。
- ゾーン名称・区分名称は指標定義書（DEC-004確定版）の文言を一字一句
  そのまま使用する。文言そのものを表現の裁量とみなして言い換えない。
- CF自走性の算定に使う営業CFは §18（2026-07-12訂正）の3層優先順位
  （実績＞推計＞簡易）で決定し、どの層を使用したかを `ocf_source`
  （actual|estimated|simplified）として結果に必ず含める。
- 簡易営業CFしか算出できない場合、CF自走性の参考計算値・計算過程は
  出力するが、正式な判定区分は出力しない（`judgment=None`・
  `judgment_status="screening_only"`・警告コード
  `WARNING_CODE_SIMPLIFIED_OCF_NOT_ELIGIBLE_FOR_FORMAL_JUDGMENT`
  ＝`"SIMPLIFIED_OCF_NOT_ELIGIBLE_FOR_FORMAL_JUDGMENT"`と理由文を付す。
  後工程のレポート生成がこのコードで機械的に判定要否を分岐できるように
  するため、自由文の`warning`だけに依存しない）。
- 維持投資は、維持・更新投資として確認済みの実額を優先し、実額が無い
  場合のみ減価償却費を代理値として使用し `capex_source`
  （maintenance_actual|depreciation_proxy）として明示する（2026-07-12
  再訂正：`actual`は「維持・更新投資として確認済みか」を示さないため
  廃止）。確認済みの実額があるのに代理値を使うことはしない。成長投資が
  混在する疑いのある総capexは`total_capex_proxy`（保守シナリオ専用。
  基本計算・正式判定を上書きしない）として別扱いする。
- 年間元本返済予定額は、返済予定表に基づく正式値（scheduled）・実績
  代用値（actual_proxy）・手動見積額（manual_estimate）を入力項目として
  分離する（2026-07-12再訂正）。CF自走性のformal判定はscheduledが
  入力された場合に限り、actual_proxy・manual_estimateはscreening_only
  （由来別の警告コード付き）として扱う。
- 本モジュールは tests/build_financial_fixture.py・
  tests/build_boundary_fixtures.py（期待値の生成に使ったスクリプト）
  から独立して実装している。両者が同じ誤りを共有しないようにするため、
  ロジックを共有・import しない（tests/test_financial_calc.py で
  出力を突き合わせて検証する）。
"""
from dataclasses import dataclass
from typing import Optional


# ============================================================
# ゾーン・区分の名称（指標定義書 DEC-004確定版。文言は変更しないこと）
# ============================================================

def zone_cf_self_sufficiency(ratio: Optional[float]) -> Optional[str]:
    """§18 CF自走性のゾーン区分。"""
    if ratio is None:
        return None
    if ratio < 1.0:
        return "要改善（自走していない。最優先論点）"
    if ratio < 1.2:
        return "ぎりぎり（自走はしているが、突発的な支出へのショック耐性がない）"
    if ratio < 1.5:
        return "標準（銀行の融資目安圏）"
    return "余裕（銀行評価良好圏）"


def zone_debt_payback_ebitda(years: Optional[float]) -> str:
    """§15 債務償還年数（EBITDA倍率型）のゾーン区分。"""
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


def zone_cash_months(months: Optional[float]) -> str:
    """§17 余剰現預金（月商倍率）のゾーン区分。"""
    if months is None:
        return "算定不能（月商ゼロ）"
    if months < 1.0:
        return "危険水域（資金繰りリスク・最優先論点）"
    if months < 2.0:
        return "最低確保ゾーン（世間目安の下限圏。増強を推奨）"
    if months < 3.0:
        return "標準ゾーン（通常運転として許容）"
    return "安全〜戦略判断ゾーン（余剰現預金を算出し戦略論点化）"


# ============================================================
# §18 営業CFの3層優先順位（実績＞推計＞簡易）・維持投資の実額／代理値
# ============================================================

@dataclass
class OperatingCFResult:
    value: Optional[float]
    ocf_source: str  # actual | estimated | simplified
    confidence_grade: str  # A | B | C（§0-4）
    judgment_blocked: bool = False
    warning: Optional[str] = None
    calculation_trace: str = ""


_OCF_CONFIDENCE_GRADE = {"actual": "A", "estimated": "B", "simplified": "C"}


def resolve_operating_cf(
    actual_operating_cf: Optional[float] = None,
    *,
    net_income: Optional[float] = None,
    depreciation_total: Optional[float] = None,
    delta_ar: Optional[float] = None,
    delta_inv: Optional[float] = None,
    delta_ap: Optional[float] = None,
    ordinary_profit: Optional[float] = None,
    tax: Optional[float] = None,
    for_formal_judgment: bool = True,
) -> OperatingCFResult:
    """
    v0.2 §18の3層優先順位で営業CFを決定する。

    層1（実績・ocf_source=actual）：`actual_operating_cf` が与えられていれば
        最優先で使用する（CF計算書の実績値）。
    層2（推計・ocf_source=estimated）：CF計算書が無い場合、`net_income` ・
        `depreciation_total` ・`delta_ar` ・`delta_inv` ・`delta_ap`
        （当期純利益・非資金項目・運転資本増減）がすべて与えられていれば、
        間接法準拠で推計する。
    層3（簡易・ocf_source=simplified）：`ordinary_profit` ・
        `depreciation_total` ・`tax` のみが与えられている場合。
        `for_formal_judgment=True`（デフォルト）の場合は正式判定を
        ブロックし、判定値を返さず警告する（速報・一次スクリーニング
        専用のため）。
    """
    if actual_operating_cf is not None:
        return OperatingCFResult(
            value=actual_operating_cf,
            ocf_source="actual",
            confidence_grade=_OCF_CONFIDENCE_GRADE["actual"],
            calculation_trace=f"実績営業CF（CF計算書） = {actual_operating_cf}",
        )

    have_estimated_inputs = None not in (net_income, depreciation_total, delta_ar, delta_inv, delta_ap)
    if have_estimated_inputs:
        estimated = net_income + depreciation_total - delta_ar - delta_inv + delta_ap
        trace = (
            f"推計営業CF = 当期純利益({net_income}) + 減価償却費({depreciation_total}) "
            f"− Δ売掛金({delta_ar}) − Δ棚卸資産({delta_inv}) + Δ買掛金({delta_ap}) = {estimated}"
        )
        return OperatingCFResult(
            value=estimated, ocf_source="estimated",
            confidence_grade=_OCF_CONFIDENCE_GRADE["estimated"],
            calculation_trace=trace,
        )

    have_simplified_inputs = None not in (ordinary_profit, depreciation_total, tax)
    if have_simplified_inputs:
        simplified = ordinary_profit + depreciation_total - tax
        trace = (
            f"簡易営業CF = 経常利益({ordinary_profit}) + 減価償却費({depreciation_total}) "
            f"− 法人税等({tax}) = {simplified}"
        )
        if for_formal_judgment:
            return OperatingCFResult(
                value=None,
                ocf_source="simplified",
                confidence_grade=_OCF_CONFIDENCE_GRADE["simplified"],
                judgment_blocked=True,
                warning="運転資本変動を確認できないため正式判定不可。2期分のB/SまたはCF計算書が必要",
                calculation_trace=trace + "（速報・一次スクリーニング専用。運転資本変動が大きい期の正式判定には使用しない）",
            )
        return OperatingCFResult(
            value=simplified, ocf_source="simplified",
            confidence_grade=_OCF_CONFIDENCE_GRADE["simplified"],
            calculation_trace=trace,
        )

    raise ValueError("営業CFを算定するための入力が不足している（実績・推計・簡易のいずれの層も構成できない）")


@dataclass
class MaintenanceInvestmentResult:
    value: float
    capex_source: str  # maintenance_actual | depreciation_proxy
    calculation_trace: str


def resolve_maintenance_investment(
    capex_maintenance_actual: Optional[float] = None,
    *,
    depreciation_total: Optional[float] = None,
) -> MaintenanceInvestmentResult:
    """
    維持投資は、維持・更新投資であることが確認済みの実額
    （capex_maintenance_actual）が取得できる場合はその値を使用する
    （capex_source=maintenance_actual）。2026-07-12再訂正：以前は
    capex_source="actual"としていたが、この名称は「実額かどうか」しか
    示さず「維持・更新投資として確認済みか（≠新規出店等の成長投資が
    混在していないか）」を区別できなかった。名称そのものに確認済みで
    あることを明記し、成長投資が疑われる実額（未分離のCIP振替等を含む
    大型投資等）は本関数に渡さず、`total_capex_proxy`（保守シナリオ専用。
    calc_cf_self_sufficiency参照）側で扱うこと。

    維持・更新投資として確認済みの実額が取得できない場合に限り、
    減価償却費を代理値として使用し capex_source=depreciation_proxy と
    して明示する。
    """
    if capex_maintenance_actual is not None:
        return MaintenanceInvestmentResult(
            value=capex_maintenance_actual,
            capex_source="maintenance_actual",
            calculation_trace=f"維持投資（維持・更新投資として確認済みの実額） = {capex_maintenance_actual}",
        )
    if depreciation_total is not None:
        return MaintenanceInvestmentResult(
            value=depreciation_total,
            capex_source="depreciation_proxy",
            calculation_trace=f"維持投資（維持・更新投資として確認済みの実額が無いため減価償却費を代理値として使用） = {depreciation_total}",
        )
    raise ValueError("維持投資を算定するための入力（維持・更新投資として確認済みの実額capex_maintenance_actual、または減価償却費）が不足している")


#: 簡易営業CFしか算出できず正式判定をブロックした場合の警告コード
#: （2026-07-12再訂正：レポート生成側がこのコードで判定要否を機械的に
#:  分岐できるようにする。自由文の`warning`だけでは誤って区分表示される
#:  リスクがあるため、コードと理由文の両方を持つ）。
WARNING_CODE_SIMPLIFIED_OCF_NOT_ELIGIBLE_FOR_FORMAL_JUDGMENT = (
    "SIMPLIFIED_OCF_NOT_ELIGIBLE_FOR_FORMAL_JUDGMENT"
)

#: 2026-07-12追加（Eタスクeval E-3で発見）：営業CFの層は解決できても、
#: CF自走性の分母（年間元本返済予定額）自体が欠落している場合の警告コード。
#: 分母が無ければ比率は定義できないため、judgment_status="formal"を
#: 返してはならない（従来はこの分岐が無く、judgment=None・warning=None
#: のまま誤ってjudgment_status="formal"を返していた）。
WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_MISSING = (
    "ANNUAL_PRINCIPAL_REPAYMENT_MISSING"
)

#: 2026-07-12再訂正：年間元本返済予定額に、正式な返済予定表に基づく値
#: （scheduled）ではなく、当期の実績返済額を代用値として使用した場合の
#: 警告コード。実績返済額は「今後12か月の予定」を保証しないため、
#: judgment_status="formal"を返さない（screening_onlyに固定する）。
WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_ACTUAL_PROXY_USED = (
    "ANNUAL_PRINCIPAL_REPAYMENT_ACTUAL_PROXY_USED"
)

#: 2026-07-12再訂正：年間元本返済予定額に、正式な返済予定表に基づく値
#: （scheduled）ではなく、手動見積額を使用した場合の警告コード。
#: judgment_status="formal"を返さない（screening_onlyに固定する）。
WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_MANUAL_ESTIMATE_USED = (
    "ANNUAL_PRINCIPAL_REPAYMENT_MANUAL_ESTIMATE_USED"
)


@dataclass
class AnnualPrincipalRepaymentResult:
    value: Optional[float]
    source: str  # scheduled | actual_proxy | manual_estimate | missing
    eligible_for_formal: bool
    warning: Optional[str]
    warning_code: Optional[str]
    calculation_trace: str


def resolve_annual_principal_repayment(
    *,
    scheduled: Optional[float] = None,
    actual_proxy: Optional[float] = None,
    manual_estimate: Optional[float] = None,
) -> AnnualPrincipalRepaymentResult:
    """
    2026-07-12再訂正：年間元本返済予定額（CF自走性の分母）は、由来を
    区別しない単一の`annual_principal_repayment_next12m`に代入しては
    ならない。正式な返済予定表に基づく値（scheduled）と、実績返済額の
    代用値（actual_proxy）・手動見積額（manual_estimate）は入力項目を
    分離し、formal判定は正式な返済予定額（scheduled）が入力された場合に
    限る。由来ごとに警告コードを分ける：

    - scheduled：formal判定、警告なし
    - actual_proxy：screening_only、
      WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_ACTUAL_PROXY_USED
    - manual_estimate：screening_only、
      WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_MANUAL_ESTIMATE_USED
    - missing（いずれも未指定）：screening_only、
      WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_MISSING

    3つの由来を同時に指定することは呼び出し側の設計ミスであるため、
    複数指定はValueErrorとする（由来の混在・優先順位のあいまいさを
    暗黙に許さない）。
    """
    provided = [
        name for name, val in (
            ("scheduled", scheduled),
            ("actual_proxy", actual_proxy),
            ("manual_estimate", manual_estimate),
        )
        if val is not None
    ]
    if len(provided) > 1:
        raise ValueError(
            "年間元本返済予定額は scheduled／actual_proxy／manual_estimate の"
            f"いずれか1つのみを指定すること（由来の混在は禁止・指定された由来: {provided}）"
        )

    if scheduled is not None:
        return AnnualPrincipalRepaymentResult(
            value=scheduled, source="scheduled", eligible_for_formal=True,
            warning=None, warning_code=None,
            calculation_trace=f"年間元本返済予定額（返済予定表に基づく正式値） = {scheduled}",
        )
    if actual_proxy is not None:
        return AnnualPrincipalRepaymentResult(
            value=actual_proxy, source="actual_proxy", eligible_for_formal=False,
            warning=(
                "正式な返済予定表ではなく、当期の実績返済額を代用値として使用しているため、"
                "CF自走性を正式判定できません（参考値として表示）。"
            ),
            warning_code=WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_ACTUAL_PROXY_USED,
            calculation_trace=f"年間元本返済予定額（当期実績返済額の代用値） = {actual_proxy}",
        )
    if manual_estimate is not None:
        return AnnualPrincipalRepaymentResult(
            value=manual_estimate, source="manual_estimate", eligible_for_formal=False,
            warning=(
                "正式な返済予定表ではなく、手動見積額を使用しているため、"
                "CF自走性を正式判定できません（参考値として表示）。"
            ),
            warning_code=WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_MANUAL_ESTIMATE_USED,
            calculation_trace=f"年間元本返済予定額（手動見積額） = {manual_estimate}",
        )
    return AnnualPrincipalRepaymentResult(
        value=None, source="missing", eligible_for_formal=False,
        warning=(
            "年間元本返済予定額（返済予定表に基づく正式値・実績代用値・手動見積額の"
            "いずれも）が指定されていないため、CF自走性を判定できません。"
        ),
        warning_code=WARNING_CODE_ANNUAL_PRINCIPAL_REPAYMENT_MISSING,
        calculation_trace="年間元本返済予定額 = 欠落",
    )


@dataclass
class ConservativeCapexScenarioResult:
    """
    2026-07-12再訂正：`total_capex_proxy`（維持・更新投資として確認済み
    とは言えない、成長投資混在の疑いがある総capex等）を使った保守的な
    参考シナリオ。基本計算（CFSelfSufficiencyResult本体）とは常に分離し、
    judgment・judgment_statusを一切持たない（参考専用であり、いかなる
    場合も正式判定を上書きしない）。
    """
    total_capex_proxy: float
    fcf_conservative: float
    cf_self_sufficiency_conservative: Optional[float]
    calculation_trace: str


@dataclass
class CFSelfSufficiencyResult:
    fcf: Optional[float]
    ocf_source: str
    capex_source: Optional[str]
    confidence_grade: str
    cf_self_sufficiency: Optional[float]
    zone: Optional[str]
    judgment: Optional[str]  # 正式判定区分（zoneと同値）。screening_only時はNone
    judgment_status: str  # "formal" | "screening_only"
    judgment_blocked: bool
    repayment_source: Optional[str]  # scheduled | actual_proxy | manual_estimate | missing
    warning: Optional[str]
    warning_code: Optional[str]
    calculation_trace: str
    conservative_scenario: Optional[ConservativeCapexScenarioResult] = None


def calc_cf_self_sufficiency(
    *,
    annual_principal_repayment_scheduled: Optional[float] = None,
    annual_principal_repayment_actual_proxy: Optional[float] = None,
    annual_principal_repayment_manual_estimate: Optional[float] = None,
    actual_operating_cf: Optional[float] = None,
    net_income: Optional[float] = None,
    depreciation_total: Optional[float] = None,
    delta_ar: Optional[float] = None,
    delta_inv: Optional[float] = None,
    delta_ap: Optional[float] = None,
    ordinary_profit: Optional[float] = None,
    tax: Optional[float] = None,
    capex_maintenance_actual: Optional[float] = None,
    total_capex_proxy: Optional[float] = None,
) -> CFSelfSufficiencyResult:
    """§18 CF自走性（第0指標）＝FCF÷年間返済元金。営業CFは3層優先順位で解決する。

    2026-07-12再訂正：
    - 年間元本返済予定額は`annual_principal_repayment_scheduled`
      （返済予定表に基づく正式値）・`annual_principal_repayment_actual_proxy`
      （実績代用値）・`annual_principal_repayment_manual_estimate`
      （手動見積額）に分離した（旧`annual_principal_repayment_next12m`は
      廃止）。formal判定はscheduledが入力された場合に限る。
    - 維持投資の実額は、維持・更新投資として確認済みの場合のみ
      `capex_maintenance_actual`に渡す（capex_source=maintenance_actual）。
    - `total_capex_proxy`（成長投資混在の疑いがある総capex等）を渡した
      場合、基本計算・正式判定とは分離した保守的な参考シナリオ
      （`conservative_scenario`）を追加で返す。基本結果を上書きしない。
    """
    ocf = resolve_operating_cf(
        actual_operating_cf,
        net_income=net_income, depreciation_total=depreciation_total,
        delta_ar=delta_ar, delta_inv=delta_inv, delta_ap=delta_ap,
        ordinary_profit=ordinary_profit, tax=tax,
        for_formal_judgment=True,
    )
    if ocf.judgment_blocked:
        return CFSelfSufficiencyResult(
            fcf=None, ocf_source=ocf.ocf_source, capex_source=None,
            confidence_grade=ocf.confidence_grade,
            cf_self_sufficiency=None, zone=None,
            judgment=None, judgment_status="screening_only",
            judgment_blocked=True, repayment_source=None, warning=ocf.warning,
            warning_code=WARNING_CODE_SIMPLIFIED_OCF_NOT_ELIGIBLE_FOR_FORMAL_JUDGMENT,
            calculation_trace=ocf.calculation_trace,
            conservative_scenario=None,
        )

    maint = resolve_maintenance_investment(capex_maintenance_actual, depreciation_total=depreciation_total)
    fcf = ocf.value - maint.value

    repay = resolve_annual_principal_repayment(
        scheduled=annual_principal_repayment_scheduled,
        actual_proxy=annual_principal_repayment_actual_proxy,
        manual_estimate=annual_principal_repayment_manual_estimate,
    )

    conservative_scenario = None
    if total_capex_proxy is not None:
        fcf_conservative = ocf.value - total_capex_proxy
        ratio_conservative = (
            fcf_conservative / repay.value if repay.value else None
        )
        conservative_scenario = ConservativeCapexScenarioResult(
            total_capex_proxy=total_capex_proxy,
            fcf_conservative=fcf_conservative,
            cf_self_sufficiency_conservative=ratio_conservative,
            calculation_trace=(
                f"[保守シナリオ・参考専用・正式判定を上書きしない] "
                f"FCF(保守) = 営業CF({ocf.value}) − 総capex参考値({total_capex_proxy}) = {fcf_conservative}／"
                f"CF自走性(保守・参考) = FCF(保守)({fcf_conservative}) ÷ "
                f"年間返済元金({repay.value}) = {ratio_conservative}"
            ),
        )

    if repay.value is None:
        # 営業CFの層は解決できているが、CF自走性の分母（年間返済元金）が
        # いずれの由来（scheduled/actual_proxy/manual_estimate）でも
        # 指定されていないため比率そのものが定義できない（ゼロと欠落は区別する。
        # 明示的な0.0が渡された場合はこの分岐に入らず、通常どおり算式を評価する）。
        trace = (
            f"{ocf.calculation_trace}／{maint.calculation_trace}／"
            f"FCF = 営業CF({ocf.value}) − 維持投資({maint.value}) = {fcf}／{repay.calculation_trace}／"
            f"CF自走性 = FCF({fcf}) ÷ 年間返済元金（欠落） = 算定不能"
        )
        return CFSelfSufficiencyResult(
            fcf=fcf, ocf_source=ocf.ocf_source, capex_source=maint.capex_source,
            confidence_grade=ocf.confidence_grade,
            cf_self_sufficiency=None, zone=None,
            judgment=None, judgment_status="screening_only",
            judgment_blocked=True, repayment_source=repay.source,
            warning=repay.warning, warning_code=repay.warning_code,
            calculation_trace=trace,
            conservative_scenario=conservative_scenario,
        )

    # ここに到達した時点でrepay.valueはNoneではないと確定している（上のNone分岐で処理済み）。
    # 明示的な0.0は既存どおりratio=Noneのフォールバックに残す（ゼロ除算回避。
    # 本修正の対象はNone欠落の誤ったformal判定のみで、0.0の扱いは変更しない）。
    ratio = fcf / repay.value if repay.value else None
    trace = (
        f"{ocf.calculation_trace}／{maint.calculation_trace}／"
        f"FCF = 営業CF({ocf.value}) − 維持投資({maint.value}) = {fcf}／{repay.calculation_trace}／"
        f"CF自走性 = FCF({fcf}) ÷ 年間返済元金({repay.value}) = {ratio}"
    )

    if repay.eligible_for_formal:
        zone = zone_cf_self_sufficiency(ratio)
        return CFSelfSufficiencyResult(
            fcf=fcf, ocf_source=ocf.ocf_source, capex_source=maint.capex_source,
            confidence_grade=ocf.confidence_grade,
            cf_self_sufficiency=ratio, zone=zone,
            judgment=zone, judgment_status="formal",
            judgment_blocked=False, repayment_source=repay.source,
            warning=None, warning_code=None,
            calculation_trace=trace,
            conservative_scenario=conservative_scenario,
        )

    # actual_proxy・manual_estimate：比率（参考計算値）は返すが、
    # 正式な判定区分（zone・judgment）は表示しない（screening_only）。
    return CFSelfSufficiencyResult(
        fcf=fcf, ocf_source=ocf.ocf_source, capex_source=maint.capex_source,
        confidence_grade=ocf.confidence_grade,
        cf_self_sufficiency=ratio, zone=None,
        judgment=None, judgment_status="screening_only",
        judgment_blocked=True, repayment_source=repay.source,
        warning=repay.warning, warning_code=repay.warning_code,
        calculation_trace=trace,
        conservative_scenario=conservative_scenario,
    )


def calc_distributable_resource(fcf: float, annual_principal_repayment: float,
                                  cash_buffer_for_reconfigured_debt: float = 0.0) -> float:
    """§18 分配可能原資（役員報酬適正性判定の参考値）＝FCF−年間返済元金−現預金積増計画。

    2026-07-12改名：引数名を`annual_principal_repayment_next12m`から
    `annual_principal_repayment`へ変更（廃止した引数名との混同を避けるため）。
    本関数は正式／代用の区別を持たない単純な算式のみで、呼び出し側が
    どの由来の返済額を渡したかに応じて結果の扱い（formal可否）を判断する。
    """
    return fcf - annual_principal_repayment - cash_buffer_for_reconfigured_debt


# ============================================================
# §1 キャッシュフロー系指標（実績営業CF・推計営業CF・簡易営業CF・広義FCF・返済原資CF）
# 実績／推計営業CFの3層優先順位ロジックは resolve_operating_cf() に実装している
# ============================================================

def calc_simple_operating_cf(ordinary_profit: float, depreciation_total: float, tax: float) -> float:
    """簡易営業CF＝経常利益＋減価償却費−法人税等（速報・一次スクリーニング専用。FCFと呼ばない）。"""
    return ordinary_profit + depreciation_total - tax


def calc_broad_fcf(operating_cf: float, investing_cf: float) -> float:
    """広義FCF＝営業CF＋投資CF（投資CFは負数のまま加算）。単に「FCF」と呼ばない。"""
    return operating_cf + investing_cf


@dataclass
class RepaymentSourceCFResult:
    calculated: float
    adjustment_items: float
    adjustment_reason: str


def calc_repayment_source_cf(
    simple_operating_cf: float,
    maintenance_investment: float,
    off_pl_cash_outflow: float = 0.0,
    adjustment_reason: str = "調整項目なし",
) -> RepaymentSourceCFResult:
    """
    返済原資CF＝補正後簡易営業CF−維持更新に必要な設備投資−P/Lに反映されていない
    事業外資金流出。計算値＋調整項目＋調整理由の3列で扱い、自動確定しない。
    役員報酬の過大過小はここで再控除しない（二重控除禁止）。
    """
    calculated = simple_operating_cf - maintenance_investment - off_pl_cash_outflow
    return RepaymentSourceCFResult(
        calculated=calculated,
        adjustment_items=off_pl_cash_outflow,
        adjustment_reason=adjustment_reason,
    )


# ============================================================
# §2 債務償還年数と返済負担
# ============================================================

def calc_normal_working_capital(accounts_receivable: float, inventory: float, accounts_payable: float) -> float:
    return accounts_receivable + inventory - accounts_payable


def calc_surplus_cash(cash: float, normal_working_capital: float, monthly_sales: float,
                       safety_months: float = 3.0) -> float:
    """余剰現預金＝現預金−（正常運転資金＋月商×安全余裕月数）。v0.2固定でN=3。"""
    return cash - (normal_working_capital + monthly_sales * safety_months)


def calc_grow3_adjusted_debt(gross_interest_bearing_debt: float, normal_working_capital: float,
                              surplus_cash: float) -> float:
    """④Grow3調整後要返済債務＝有利子負債−正常運転資金−余剰現預金（余剰現預金が負なら控除0）。"""
    surplus_cash_for_deduction = max(surplus_cash, 0.0)
    return gross_interest_bearing_debt - normal_working_capital - surplus_cash_for_deduction


def calc_debt_payback_years_screening(gross_interest_bearing_debt: float,
                                       simple_operating_cf: float) -> Optional[float]:
    """一次スクリーニング：①総有利子負債÷簡易営業CF。"""
    return gross_interest_bearing_debt / simple_operating_cf if simple_operating_cf else None


def calc_debt_payback_years_detailed(grow3_adjusted_debt: float, simple_operating_cf: float) -> Optional[float]:
    """精査時：④Grow3調整後要返済債務÷簡易営業CF。"""
    return grow3_adjusted_debt / simple_operating_cf if simple_operating_cf else None


def calc_principal_repayment_burden_ratio(annual_principal_repayment: float,
                                           repayment_source_cf: float) -> Optional[float]:
    """
    2026-07-12改名：引数名を`annual_principal_repayment_next12m`から
    `annual_principal_repayment`へ変更（廃止した引数名との混同を避けるため）。
    本指標は§2の速報・一次スクリーニング専用の簡便指標であり、
    calc_cf_self_sufficiency()のformal判定とは無関係（由来の区別を持たない）。
    """
    return annual_principal_repayment / repayment_source_cf if repayment_source_cf else None


# ============================================================
# §3 人件費の定義（3層構造）
# ============================================================

def calc_human_cost_layers(labor_cogs: float, personnel_sga: float, outsourced_labor_cost: float) -> dict:
    employment_labor_cost = labor_cogs + personnel_sga
    total_human_cost = employment_labor_cost + outsourced_labor_cost
    return {
        "employment_labor_cost": employment_labor_cost,
        "outsourced_labor_cost": outsourced_labor_cost,
        "total_human_cost": total_human_cost,
    }


# ============================================================
# §4 労働分配率系指標（統計定義・BAST定義・MQ総人的コスト比率）
# ============================================================

def calc_value_added_stat_definition(labor_cogs: float, rent_cogs: float, depreciation_cogs: float,
                                      personnel_sga: float, rent_sga: float, depreciation_sga: float,
                                      tax_dues_sga: float, interest_expense: float,
                                      ordinary_profit: float, skill_dev_sga: float) -> float:
    """実態基本調査方式の付加価値額（§4・§16）。"""
    return (labor_cogs + rent_cogs + depreciation_cogs + personnel_sga + rent_sga
            + depreciation_sga + tax_dues_sga + interest_expense + ordinary_profit + skill_dev_sga)


def calc_labor_share_stat(labor_cogs: float, personnel_sga: float, value_added: float) -> Optional[float]:
    labor_cost_stat = labor_cogs + personnel_sga
    return labor_cost_stat / value_added * 100 if value_added else None


def calc_labor_share_bast(employment_labor_cost: float, mq: float) -> float:
    """労働分配率（BAST定義）＝MQ雇用人件費比率＝雇用人件費÷MQ×100。"""
    return employment_labor_cost / mq * 100


def calc_mq_total_human_cost_ratio(total_human_cost: float, mq: float) -> float:
    return total_human_cost / mq * 100


# ============================================================
# §5 MQ会計（P・V・Q・M・MQ・F・G）
# ============================================================

@dataclass
class MQResult:
    p_unit_price: float
    v_unit_variable_cost: float
    q_units: float
    m_unit_margin: float
    mq_total: float
    f_fixed_total: float
    g_operating_profit: float
    margin_ratio: float


def calc_mq(unit_price_p: float, unit_variable_cost_v: float, units_q: float, fixed_costs_total: float) -> MQResult:
    m_unit = unit_price_p - unit_variable_cost_v
    mq_total = m_unit * units_q
    sales = unit_price_p * units_q
    g = mq_total - fixed_costs_total
    margin_ratio = mq_total / sales if sales else None
    return MQResult(
        p_unit_price=unit_price_p, v_unit_variable_cost=unit_variable_cost_v, q_units=units_q,
        m_unit_margin=m_unit, mq_total=mq_total, f_fixed_total=fixed_costs_total,
        g_operating_profit=g, margin_ratio=margin_ratio,
    )


# ============================================================
# §15 債務償還年数（EBITDA倍率型）
# ============================================================

def calc_debt_payback_years_ebitda(net_interest_bearing_debt: float, operating_profit: float,
                                    depreciation_total: float) -> tuple:
    """
    債務償還年数（EBITDA倍率型） = （有利子負債 − 現預金） ÷ （営業利益 ＋ 減価償却費）
    戻り値：(ebitda, years, zone)
    """
    ebitda = operating_profit + depreciation_total
    years = net_interest_bearing_debt / ebitda if ebitda else None
    zone = zone_debt_payback_ebitda(years)
    return ebitda, years, zone


# ============================================================
# §17 余剰現預金の月商倍率
# ============================================================

def calc_cash_to_monthly_sales(cash: float, monthly_sales: float) -> tuple:
    """戻り値：(ratio, zone)"""
    ratio = cash / monthly_sales if monthly_sales else None
    zone = zone_cash_months(ratio)
    return ratio, zone


# ============================================================
# 参考欄：自己資本比率・ROE（B/S系・合否判定には使わない）
# ============================================================

def calc_equity_ratio(equity: float, total_assets: float) -> float:
    return equity / total_assets * 100


def calc_roe(net_income: float, equity_end: float, equity_begin: float) -> Optional[float]:
    avg_equity = (equity_end + equity_begin) / 2
    return net_income / avg_equity * 100 if avg_equity else None


# ============================================================
# 統合：1期分のP/L・B/S・CF一式から全指標を算出する
# （tests/fixtures/financial_analysis_case_manufacturing_3fy.json の
#  各期 pl・cf・opening_bs・ending_bs と同一の入力形状を想定）
# ============================================================

def analyze_period(pl: dict, cf: dict, opening_bs: dict, ending_bs: dict,
                    surplus_cash_safety_months: float = 3.0,
                    cash_buffer_for_reconfigured_debt: float = 0.0) -> dict:
    """
    1期分の完全なP/L・B/S・CFデータから、v0.2の全指標を算出して
    indicatorsキーの辞書として返す。営業CFはCF計算書が無い前提
    （ocf_source=estimated）・維持投資はcf['capex']の実額を使用する
    （2026-07-12再訂正：capex_source=maintenance_actual。cf['capex']は
    維持・更新投資として確認済みであることが前提。本関数を成長投資が
    混在する疑いのある実データに適用する場合は、cf['capex']へ渡す前に
    呼び出し側で維持投資分のみへ切り分けること）。年間元本返済予定額は
    cf['debt_repayment']を返済予定表に基づく正式値（scheduled）として
    扱う。CF計算書がある場合や、返済額が実績代用値・手動見積である場合は
    calc_cf_self_sufficiency() を個別に呼び直すこと（本関数は
    「CF計算書なし・返済予定額はscheduled」の標準ケース専用）。
    """
    result = {}
    fc = pl["fixed_costs"]

    # ---- §1・§18：営業CF（推計層）とFCF・CF自走性を一度に解決する ----
    # 広義FCFには維持投資を引く前の営業CFの生値が必要なため、まず
    # resolve_operating_cf() で生値を取得し、その後calc_cf_self_sufficiency()
    # で同じ入力から改めてFCF・CF自走性まで解決する（内部でresolve_operating_cf
    # を再度呼ぶが、入力は同一のため結果は一致する）。
    ocf_raw = resolve_operating_cf(
        net_income=pl["net_income"], depreciation_total=pl["depreciation_total"],
        delta_ar=cf["delta_ar"], delta_inv=cf["delta_inv"], delta_ap=cf["delta_ap"],
    )
    simple_ocf = calc_simple_operating_cf(pl["ordinary_profit"], pl["depreciation_total"], pl["tax"])
    broad_fcf = calc_broad_fcf(ocf_raw.value, cf["investing_cf"])
    repayment_source = calc_repayment_source_cf(
        simple_ocf, cf["capex"], 0.0,
        "本fixtureでは実態修正・事業外資金流出なし（調整なしの計算値のみ）",
    )
    cf_result = calc_cf_self_sufficiency(
        annual_principal_repayment_scheduled=cf["debt_repayment"],
        net_income=pl["net_income"], depreciation_total=pl["depreciation_total"],
        delta_ar=cf["delta_ar"], delta_inv=cf["delta_inv"], delta_ap=cf["delta_ap"],
        capex_maintenance_actual=cf["capex"],
    )
    result["estimated_operating_cf"] = ocf_raw.value
    result["ocf_source"] = ocf_raw.ocf_source
    result["simple_operating_cf"] = simple_ocf
    result["broad_fcf"] = broad_fcf
    result["repayment_source_cf_calculated"] = repayment_source.calculated
    result["repayment_source_cf_adjustment_items"] = repayment_source.adjustment_items
    result["repayment_source_cf_adjustment_reason"] = repayment_source.adjustment_reason

    # ---- §2 ----
    gross_debt = ending_bs["borrowings"]
    net_debt = ending_bs["borrowings"] - ending_bs["cash"]
    normal_wc = calc_normal_working_capital(ending_bs["accounts_receivable"], ending_bs["inventory"],
                                             ending_bs["accounts_payable"])
    monthly_sales = pl["sales"] / 12.0
    surplus_cash = calc_surplus_cash(ending_bs["cash"], normal_wc, monthly_sales, surplus_cash_safety_months)
    grow3_adjusted_debt = calc_grow3_adjusted_debt(gross_debt, normal_wc, surplus_cash)
    screening_years = calc_debt_payback_years_screening(gross_debt, simple_ocf)
    detailed_years = calc_debt_payback_years_detailed(grow3_adjusted_debt, simple_ocf)
    annual_principal = cf["debt_repayment"]
    burden_ratio = calc_principal_repayment_burden_ratio(annual_principal, repayment_source.calculated)

    result["gross_interest_bearing_debt"] = gross_debt
    result["net_interest_bearing_debt"] = net_debt
    result["normal_working_capital"] = normal_wc
    result["grow3_adjusted_debt"] = grow3_adjusted_debt
    result["debt_payback_years_screening_def1_over_simple_ocf"] = screening_years
    result["debt_payback_years_detailed_def4_over_simple_ocf"] = detailed_years
    result["annual_principal_repayment_next12m"] = annual_principal
    result["principal_repayment_burden_ratio"] = burden_ratio

    # ---- §3 ----
    human_cost = calc_human_cost_layers(fc["labor_cogs"], fc["personnel_sga"], pl["outsourced_labor_cost"])
    result.update(human_cost)

    # ---- §4 ----
    value_added = calc_value_added_stat_definition(
        fc["labor_cogs"], fc["rent_cogs"], fc["depreciation_cogs"],
        fc["personnel_sga"], fc["rent_sga"], fc["depreciation_sga"], fc["tax_dues_sga"],
        pl["interest_expense"], pl["ordinary_profit"], fc["skill_dev_sga"],
    )
    labor_share_stat = calc_labor_share_stat(fc["labor_cogs"], fc["personnel_sga"], value_added)
    labor_share_bast = calc_labor_share_bast(human_cost["employment_labor_cost"], pl["mq"])
    mq_total_human_cost_ratio = calc_mq_total_human_cost_ratio(human_cost["total_human_cost"], pl["mq"])

    result["value_added"] = value_added
    result["labor_share_stat_pct"] = labor_share_stat
    result["labor_share_bast_pct"] = labor_share_bast
    result["mq_employment_labor_ratio_pct"] = labor_share_bast
    result["mq_total_human_cost_ratio_pct"] = mq_total_human_cost_ratio

    # ---- §5 ----
    mq = calc_mq(pl["unit_price_p"], pl["unit_variable_cost_v"], pl["units_q"], pl["fixed_costs_total"])
    result["mq_p_unit_price"] = mq.p_unit_price
    result["mq_v_unit_variable_cost"] = mq.v_unit_variable_cost
    result["mq_q_units"] = mq.q_units
    result["mq_m_unit_margin"] = mq.m_unit_margin
    result["mq_mq_total"] = mq.mq_total
    result["mq_f_fixed_total"] = mq.f_fixed_total
    result["mq_g_operating_profit"] = mq.g_operating_profit

    # ---- §14/§15 ----
    result["margin_ratio_pct"] = pl["margin_ratio"] * 100
    ebitda, debt_payback_ebitda_years, debt_payback_ebitda_zone = calc_debt_payback_years_ebitda(
        net_debt, pl["operating_profit"], pl["depreciation_total"],
    )
    result["ebitda"] = ebitda
    result["debt_payback_years_ebitda"] = debt_payback_ebitda_years
    result["debt_payback_years_ebitda_zone"] = debt_payback_ebitda_zone

    # ---- §17 ----
    cash_months_ratio, cash_months_zone = calc_cash_to_monthly_sales(ending_bs["cash"], monthly_sales)
    result["monthly_sales"] = monthly_sales
    result["cash_to_monthly_sales_ratio"] = cash_months_ratio
    result["cash_to_monthly_sales_zone"] = cash_months_zone
    result["surplus_cash"] = surplus_cash

    # ---- §18 ----
    result["fcf"] = cf_result.fcf
    result["capex_source"] = cf_result.capex_source
    result["cf_self_sufficiency"] = cf_result.cf_self_sufficiency
    result["cf_self_sufficiency_zone"] = cf_result.zone
    result["cf_self_sufficiency_judgment"] = cf_result.judgment
    result["cf_self_sufficiency_judgment_status"] = cf_result.judgment_status
    result["cf_self_sufficiency_repayment_source"] = cf_result.repayment_source
    result["cf_self_sufficiency_warning"] = cf_result.warning
    result["cf_self_sufficiency_warning_code"] = cf_result.warning_code
    result["cf_self_sufficiency_calculation_trace"] = cf_result.calculation_trace
    result["distributable_resource_for_executive_comp"] = calc_distributable_resource(
        cf_result.fcf, annual_principal, cash_buffer_for_reconfigured_debt,
    )

    # ---- 参考欄 ----
    total_assets = (ending_bs["cash"] + ending_bs["accounts_receivable"]
                    + ending_bs["inventory"] + ending_bs["ppe_net"])
    equity_end = ending_bs["capital_stock"] + ending_bs["retained_earnings"]
    equity_begin = opening_bs["capital_stock"] + opening_bs["retained_earnings"]
    result["total_assets"] = total_assets
    result["equity"] = equity_end
    result["equity_ratio_pct"] = calc_equity_ratio(equity_end, total_assets)
    result["roe_pct"] = calc_roe(pl["net_income"], equity_end, equity_begin)

    return result
