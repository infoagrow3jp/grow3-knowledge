#!/usr/bin/env python3
"""架空の1社（看板製作・施工）の通しデータを作る。

実在の会社・人物とは無関係。数値はすべて架空の設定。
MQ・G は自分で計算せず、正本の financial_calc.py（calc_mq）に通した結果を使う。
制約資源あたりMQ とシナリオは、proposals/constraint_calc.py（財務側へ入れる提案。正本ではない）で計算する。

使い方（grow3-knowledge の中で）:
  python3 -I through-line/tools/build_fixture.py
  python3 -I through-line/tools/build_fixture.py --calc <financial_calc.py のパス>
出力: through-line/fixtures/fictional-signage/ の5ファイル
"""
import importlib.util, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUT = ROOT / "fixtures" / "fictional-signage"
CASE = "CASE-ORG-901"
NOW = "2026-11-16T10:00:00+09:00"
M1, M2, M3 = "MTG-20261101-001", "MTG-20261108-001", "MTG-20261115-001"  # 決算受領／聞き取り／実測の回収
M4 = "MTG-20261122-001"  # モノサシ化の聞き取り（言語化シート＋すり合わせシート）


def load_calc(argv):
    path = pathlib.Path(argv[argv.index("--calc") + 1]) if "--calc" in argv else REPO / "financial_calc.py"
    if not path.exists():
        sys.exit(f"financial_calc.py が見つからない: {path}（--calc で渡す）")
    spec = importlib.util.spec_from_file_location("financial_calc", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["financial_calc"] = mod
    spec.loader.exec_module(mod)
    return mod


def load_proposal():
    path = ROOT / "proposals" / "constraint_calc.py"
    spec = importlib.util.spec_from_file_location("constraint_calc", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ext(**kw):
    return {"through_line": kw}


def measured(n, mtg, date, statement, instrument, field, raw, population, value, unit, layer, stage, src, **tags):
    return {
        "evidence_id": f"EVD-{mtg[4:12]}-{n:03d}", "evidence_type": "MEASURED", "mtg_session_id": mtg,
        "source_file": src, "source_date": date,
        "source_pointer": {"type": "measurement", "instrument": instrument, "field": field},
        "normalized_statement": statement, "source_form": "measured_raw", "review_status": "spot_checked",
        "sensitivity": "internal", "notes": "架空の設定値。",
        "raw_measurement": raw, "instrument_name": instrument, "instrument_version": "fixture-1",
        "measurement_date": date, "population": population, "value": value, "unit": unit,
        "extensions": ext(layer=layer, stage=stage, **tags)}


def reported(n, statement, excerpt, role, context, occ, occ_date, stage, lens, para):
    e = {
        "evidence_id": f"EVD-{M2[4:12]}-{n:03d}", "evidence_type": "REPORTED", "mtg_session_id": M2,
        "source_file": "mtg/20261108_minutes.md", "source_date": "2026-11-08",
        "source_pointer": {"type": "minutes", "section": "価値の流れとこだわり", "paragraph": para, "line": 1},
        "normalized_statement": statement, "source_form": "summary_minutes", "review_status": "spot_checked",
        "sensitivity": "internal", "notes": "", "occurrence_key_applicability": "applicable",
        "occurrence_key": occ, "occurrence_date": occ_date,
        "verbatim_excerpt": excerpt, "speaker_category": "client_manager" if role in ("社長", "施工班長") else "client_member",
        "speaker_role_label": role, "speaker_attribution_status": "verified", "elicitation_context": context,
        "extensions": ext(layer="field", stage=stage, **({"lens_ids": lens} if lens else {}))}
    return e


def main(argv):
    calc = load_calc(argv)
    cc = load_proposal()
    # ---- 段1 数字：分析単位＝案件、期間＝直近1期。P・V・Q・F は架空の設定。MQ と G は calc_mq の出力。
    P, V, Q, FX = 450000.0, 180000.0, 420.0, 105000000.0
    mq = calc.calc_mq(P, V, Q, FX)
    fin = "finance/fy2026_pl.xlsx"
    ev = [
        measured(1, M1, "2026-11-01", "直近期の完了案件数（Q）は420件。", "決算書・案件台帳", "完了案件数",
                 "完了案件数 420", "直近1期の全案件", Q, "件", "finance", None, fin),
        measured(2, M1, "2026-11-01", f"直近期のMQ総額は{mq.mq_total:,.0f}円（financial_calc.calc_mq の出力）。",
                 "financial_calc.calc_mq", "mq_total", f"P={P:.0f} V={V:.0f} Q={Q:.0f} → mq_total={mq.mq_total:.0f}",
                 "直近1期の全案件", mq.mq_total, "円", "finance", None, fin),
        measured(3, M1, "2026-11-01", f"直近期のGは{mq.g_operating_profit:,.0f}円（financial_calc.calc_mq の出力）。",
                 "financial_calc.calc_mq", "g_operating_profit", f"mq_total={mq.mq_total:.0f} F={FX:.0f} → g={mq.g_operating_profit:.0f}",
                 "直近1期の全案件", mq.g_operating_profit, "円", "finance", None, fin),
        measured(4, M1, "2026-11-01", "直近期の施工応援の外注費は960万円（V候補・区分要確認）。", "総勘定元帳", "外注費（施工応援）",
                 "外注費（施工応援）9,600,000", "直近1期", 9600000.0, "円", "finance", "install", "finance/fy2026_ledger.xlsx"),
    ]
    # ---- 段2 流れ：4週間の実測（工程ごとの完了件数・滞留・待ち）
    flow = "flow/4weeks_log.xlsx"
    rows = [
        (1, "設計・見積の完了は週平均9.0件。", "工程記録表", "設計完了件数", 9.0, "件/週", "design"),
        (2, "製作の完了は週平均10.0件。", "工程記録表", "製作完了件数", 10.0, "件/週", "production"),
        (3, "製作完了から施工着手までの滞留は平均6.5日。", "工程記録表", "製作完了→施工着手の日数", 6.5, "日", "handoff"),
        (4, "施工班から設計・製作への確認の連絡は週平均14.0件。", "連絡記録", "施工前後の確認連絡件数", 14.0, "件/週", "handoff"),
        (5, "施工の完了は週平均7.0件。", "工程記録表", "施工完了件数", 7.0, "件/週", "install"),
        (6, "施工班長の判断を待つ時間は1案件あたり平均2.1時間。", "施工日報", "班長の判断待ち時間", 2.1, "時間/件", "install"),
        (7, "施工後の再訪問（手直し）は4週間で5件。", "施工日報", "再訪問件数", 5.0, "件/4週", "install"),
    ]
    PERIOD = "2026-10-19〜11-13の全案件"
    MEASURE = {1: "throughput", 2: "throughput", 5: "throughput", 6: "wait"}
    for n, st, inst, field, val, unit, stage in rows:
        tags = {"measure": MEASURE[n]} if n in MEASURE else {}
        ev.append(measured(n, M3, "2026-11-15", st, inst, field, f"{field} {val}", PERIOD, val, unit, "flow", stage, flow, **tags))
    # ---- 段3 現場：Lens で引き出した発言と、立ち会いの観察
    ev += [
        reported(1, "施工班長は、図面に無い現場条件を施工当日に電話で確認している。",
                 "図面には書いてないことが多いんで、現場に着いてから毎回電話して聞いてます。", "施工班長", "open_question",
                 "OCC-20261020-001", "2026-10-20", "install", ["LENS-009"], 3),
        reported(2, "製作担当は、依頼主の営業時間などの現場条件を施工班に渡していない。",
                 "できたら渡して終わりです。お店が何時に閉まるかまでは、こっちは聞いてないです。", "製作担当", "open_question",
                 "OCC-20261027-001", "2026-10-27", "handoff", ["LENS-008"], 5),
        reported(3, "施工班員は、班長に確認するまで作業を止めて待っている。",
                 "班長に聞かないと決められないので、電話がつながるまで待っています。", "施工班員", "spontaneous",
                 "OCC-20261029-001", "2026-10-29", "install", None, 7),
        reported(4, "社長は、施工が間に合わないときに応援を外注している。",
                 "施工が詰まったら応援を呼ぶしかない。高くつくのは分かっているんですが。", "社長", "spontaneous",
                 "OCC-UNKNOWN-001", None, "install", None, 9),
        {
            "evidence_id": f"EVD-{M3[4:12]}-008", "evidence_type": "OBSERVED", "mtg_session_id": M3,
            "source_file": "field/20261112_site_note.md", "source_date": "2026-11-12",
            "source_pointer": {"type": "note", "section": "施工立ち会い"},
            "normalized_statement": "施工当日、班員2名が班長の電話が終わるまで約40分作業を止めていた。",
            "source_form": "observer_note", "review_status": "spot_checked", "sensitivity": "internal", "notes": "",
            "occurrence_key_applicability": "applicable", "occurrence_key": "OCC-20261112-001", "occurrence_date": "2026-11-12",
            "observation_record": "10:20〜11:00、取付位置の判断待ちで班員2名が待機。班長は別現場と電話中。",
            "observer_category": "consultant", "observed_at": "2026-11-12T10:20:00+09:00",
            "extensions": ext(layer="field", stage="install")},
    ]
    # ---- 段2の続き：制約資源（班長の判断対応の時間）の、使える量・使った量・案件の種類ごとの占有量
    # 「待っていた時間」（上の n=6）とは別に測る。分母にするのは占有した時間。
    TYPES = {"standard": "袖・壁面（標準）", "large": "自立・大型", "illuminated": "電飾・改修"}
    HOURS = {"standard": 1.0, "large": 3.0, "illuminated": 2.0}       # 班長の判断対応 時間/件
    COUNTS = {"standard": 16, "large": 4, "illuminated": 8}           # 4週間の完了件数
    PV = {"standard": (380000.0, 150000.0), "large": (700000.0, 300000.0), "illuminated": (480000.0, 190000.0)}
    log = "flow/leader_time_log.xlsx"
    cap = [
        measured(9, M3, "2026-11-15", "班長が判断対応に使える時間は週12.0時間（残りは自分の施工作業）。", "班長の勤務配分表", "判断対応に使える時間",
                 "判断対応に使える時間 12.0", PERIOD, 12.0, "時間/週", "flow", "install", log, measure="constraint_available"),
        measured(10, M3, "2026-11-15", "班長が判断対応に使った時間は週平均11.0時間。", "班長の対応記録", "判断対応に使った時間",
                 "判断対応に使った時間 11.0", PERIOD, 11.0, "時間/週", "flow", "install", log, measure="constraint_used"),
    ]
    n = 11
    for k in TYPES:
        cap.append(measured(n, M3, "2026-11-15", f"{TYPES[k]}の案件で、班長が判断対応に使った時間は1件あたり{HOURS[k]}時間。", "班長の対応記録",
                            f"判断対応の時間（{TYPES[k]}）", f"{TYPES[k]} {HOURS[k]}", PERIOD, HOURS[k], "時間/件", "flow", "install", log,
                            measure="constraint_per_item", item_type=k))
        n += 1
    for k in TYPES:
        cap.append(measured(n, M3, "2026-11-15", f"{TYPES[k]}の完了は4週間で{COUNTS[k]}件。", "工程記録表", f"完了件数（{TYPES[k]}）",
                            f"{TYPES[k]} {COUNTS[k]}", PERIOD, float(COUNTS[k]), "件/4週", "flow", "install", flow, measure="mix_count", item_type=k))
        n += 1
    UNIT_M = {}
    for k in TYPES:  # 1件あたりのM は calc_mq の出力（F は種類別に配賦しないので 0 を渡し、m_unit_margin だけ使う）
        r = calc.calc_mq(PV[k][0], PV[k][1], float(COUNTS[k]), 0.0)
        UNIT_M[k] = r.m_unit_margin
        cap.append(measured(n, M3, "2026-11-15", f"{TYPES[k]}の1件あたりMは{r.m_unit_margin:,.0f}円（financial_calc.calc_mq の出力）。",
                            "financial_calc.calc_mq", "m_unit_margin", f"P={PV[k][0]:.0f} V={PV[k][1]:.0f} → m_unit_margin={r.m_unit_margin:.0f}",
                            PERIOD, r.m_unit_margin, "円/件", "finance", None, "finance/job_cost_ledger.xlsx", measure="unit_margin", item_type=k))
        n += 1
    ev[11:11] = cap  # 流れの測定のすぐ後ろに入れる（現場の証拠より前）
    CE = {e["extensions"]["through_line"]["measure"] + (":" + e["extensions"]["through_line"]["item_type"] if "item_type" in e["extensions"]["through_line"] else ""): e["evidence_id"] for e in cap}

    E = {k: e["evidence_id"] for k, e in zip(
        ["q", "mq", "g", "outsourcing", "f_design", "f_prod", "f_wait_days", "f_contacts", "f_install", "f_judge_wait", "f_revisit",
         "r_leader", "r_maker", "r_member", "r_ceo", "o_site"], [e for e in ev if e not in cap])}

    patterns = [{
        "pattern_id": "PAT-001", "pattern_type": "occurrence_pattern",
        "claim": "施工の現場で、図面に無い条件を班長に確認するために作業が止まる。",
        "supporting_evidence_ids": [E["r_leader"], E["r_member"], E["o_site"]],
        "supporting_occurrence_keys": ["OCC-20261020-001", "OCC-20261029-001", "OCC-20261112-001"],
        "occurrence_count": 3, "time_span": "2026-10-20〜2026-11-12", "scope": "施工工程", "status": "ACTIVE",
        "sensitivity": "internal", "notes": ""}]

    def hyp(n, layer, claim, sup, prim, pats, counter, alt, status, questions, tl):
        h = {"hypothesis_id": f"HYP-{n:03d}", "layer": layer, "claim": claim, "supporting_evidence_ids": sup,
             "primary_supporting_evidence_ids": prim, "supporting_pattern_ids": pats,
             "counter_evidence_review": counter, "alternative_hypothesis_review": alt, "status": status,
             "sensitivity": "internal", "confirmation_questions": questions,
             "next_review_trigger": "4週間の実測（ACT-001）の回収後", "created_at": NOW, "last_reviewed_at": NOW}
        if tl:
            h["extensions"] = ext(**tl)
        return h

    hypotheses = [
        hyp(1, "structure", "会社全体の完了件数を縛っているのは、施工工程のうち班長の判断を待つ時間である。",
            [E["f_install"], E["f_judge_wait"], E["f_prod"], E["f_design"], E["f_wait_days"], E["r_member"], E["o_site"],
             CE["constraint_used"], CE["constraint_available"]],
            [E["f_install"], E["f_judge_wait"], E["o_site"]], ["PAT-001"],
            {"status": "none_found_in_reviewed_sources", "reviewed_sources": [E["f_design"], E["f_prod"], "mtg/20261108_minutes.md"],
             "note": "設計・製作の完了件数は施工を上回っており、施工より上流が詰まっている証拠は見つからなかった。"},
            {"status": "considered", "alternatives": ["製作の処理能力が制約である", "設計・見積の着手待ちが制約である", "受注（案件数）そのものが制約である"],
             "note": "製作10件/週・設計9件/週に対し施工7件/週。受注が制約なら製作完了後の滞留は生じないはずだが、平均6.5日ある。"},
            "TO_CONFIRM", ["班長の判断待ちは、どの種類の案件で長いか。", "班長が不在の日の施工完了件数はどうなるか。"],
            {"kind": "constraint_candidate", "stage": "install", "resource": "班長が判断対応に使える時間",
             "constraint_unit": "時間", "used_evidence_id": CE["constraint_used"], "available_evidence_id": CE["constraint_available"],
             "next_constraint": {"stage": "design", "basis_evidence_ids": [E["f_design"], E["f_prod"]],
                                 "note": "施工が上がっても、上流は設計9件/週・製作10件/週。次に縛るのは設計の見込み。"}}),
        hyp(2, "structure", "製作から施工へ渡る情報に、図面に載らない現場条件（営業時間・電源の位置など）が含まれていない。",
            [E["r_leader"], E["r_maker"], E["f_contacts"]], [E["r_leader"], E["r_maker"]], [],
            {"status": "not_reviewed", "reviewed_sources": [], "note": ""},
            {"status": "considered", "alternatives": ["現場条件は渡っているが、施工側が読んでいない"], "note": ""},
            "TO_CONFIRM", ["受け渡しの書類に、現場条件を書く欄はあるか。"], {"kind": "structure"}),
        hyp(3, "mental_model", "現場の判断は班長がするもの、という前提が班員の側にある。",
            [E["r_member"]], [], [],
            {"status": "not_reviewed", "reviewed_sources": [], "note": ""},
            {"status": "not_reviewed"}, "DRAFT", ["班員は、どこまでなら自分で決めてよいと思っているか。"], None),
    ]

    def edge(n, frm, to, pol, delay, sup, hyps_, fl, fs, tl_, ts, notes=""):
        return {"causal_type": "causal_hypothesis", "edge_id": f"CED-{n:03d}", "from_variable": frm, "to_variable": to,
                "polarity": pol, "delay": delay, "supporting_evidence_ids": sup, "supporting_hypothesis_ids": hyps_,
                "status": "TO_CONFIRM", "sensitivity": "internal", "notes": notes,
                "extensions": ext(**{"from": {"layer": fl, "stage": fs}, "to": {"layer": tl_, "stage": ts}})}

    causal = [
        edge(1, "受け渡し時に渡る現場条件の量", "施工時の班長への確認件数", "negative", "none",
             [E["r_leader"], E["r_maker"], E["f_contacts"]], ["HYP-002"], "field", "handoff", "flow", "install"),
        edge(2, "施工時の班長への確認件数", "班長の判断を待つ時間", "positive", "none",
             [E["f_judge_wait"], E["r_member"], E["o_site"]], ["HYP-001"], "flow", "install", "flow", "install"),
        edge(3, "班長の判断を待つ時間", "施工の週あたり完了件数", "negative", "none",
             [E["f_judge_wait"], E["f_install"], E["o_site"]], ["HYP-001"], "flow", "install", "flow", "install"),
        edge(4, "施工の週あたり完了件数", "年間の完了案件数（Q）", "positive", "possible",
             [E["f_install"], E["f_wait_days"], E["q"]], ["HYP-001"], "flow", "install", "finance", None,
             "Q から MQ・G への関係は MQ会計の定義（指標定義書 §5）であり、因果の矢印にはしない。"),
        edge(5, "施工の週あたり完了件数", "施工応援の外注費（V候補）", "negative", "possible",
             [E["r_ceo"], E["outsourcing"]], [], "flow", "install", "finance", "install"),
        {"causal_type": "chain", "edge_ids": ["CED-001", "CED-002", "CED-003", "CED-004"],
         "sequence_note": "受け渡し → 確認件数 → 判断待ち → 施工完了件数 → Q。閉じていないのでループにはしない。",
         "sensitivity": "internal", "notes": ""},
    ]

    def act(n, kind_, typ, desc, targets, sup, weak, mtg, tl):
        return {"action_id": f"ACT-{n:03d}", "action_type": typ, "action_description": desc, "target_hypothesis_ids": targets,
                "support_signal": sup, "weaken_signal": weak, "next_review_trigger": "次回の打合せ", "sensitivity": "internal",
                "created_at": NOW, "mtg_session_id": mtg, "extensions": ext(kind=kind_, **tl)}

    actions = [
        act(1, "constraint_measurement", "data_collection",
            "さらに4週間、設計・製作・施工の完了件数、製作完了後の滞留日数、班長の判断待ち時間を日次で記録する。",
            ["HYP-001"], "施工の完了件数が設計・製作を一貫して下回り、製作完了後の滞留が減らない。",
            "製作または設計の完了件数が施工を下回る週が半分以上ある。", M3, {}),
        act(2, "monosashi_interview", "additional_interview",
            "施工班員1名に、判断のズレが起きた実案件1件について「判断の見え方・線のすり合わせシート」で聞き取り、班長の見えと比べる。",
            ["HYP-001", "HYP-003"], "班長だけが見ている手がかりが複数あり、班員は自分で決めてよい範囲を班長より狭く置いている。",
            "班員も同じ手がかりを見ており、止まる理由が見え方でも相談の線でもない。", M3,
            {"judgment_scene": "施工当日、図面に無い現場条件に気づいたとき、自分で決めて進めるか、班長に聞くか。",
             "case_selection": "この場面で、班長が途中で口を出した、または手直しになった実案件を1件。",
             "person": "施工班員", "responsible": "施工班長", "lens_ids": ["LENS-009", "LENS-008"],
             "instrument": "判断の見え方・線のすり合わせシート v0.2"}),
        act(3, "structure_experiment", "small_experiment",
            "2週間、受け渡しのときに現場条件3点（営業時間・電源の位置・搬入経路）を紙で渡す。",
            ["HYP-002"], "施工班からの確認連絡が週14件から目に見えて減る。", "確認連絡の件数が変わらない。", M3, {}),
        act(5, "monosashi_selfreport", "additional_interview",
            "聞き取りの前に、施工班長に「モノサシ言語化シート」を書いてもらう。任せたい仕事は、施工当日の現場判断。",
            ["HYP-001", "HYP-003"], "班長のモノサシのうち、班員にまだ渡せていないものが複数ある。",
            "班長のモノサシはすでに渡せており、班員が待つ理由が別にある。", M3,
            {"responsible": "施工班長", "instrument": "モノサシ言語化シート"}),
        act(4, "finance_recalc", "data_collection",
            "制約が確定したら、案件の種類ごとに「制約資源あたりMQ」（指標定義書 §6-1）を財務側で算定する。",
            ["HYP-001"], "班長の判断時間あたりのMQに、案件の種類による差がある。", "案件の種類による差がほとんど無い。", M3,
            {"constraint_unit": "時間"}),
    ]

    # ============ 1段への戻し：制約資源あたりMQ（提案中の関数で計算）============
    util = cc.calc_constraint_utilization(11.0, 12.0)
    ranking = []
    for k in TYPES:
        r = cc.calc_mq_per_constraint_unit(UNIT_M[k], HOURS[k], "時間")
        ranking.append({"item_type": k, "label": TYPES[k], "m_unit_margin": UNIT_M[k], "m_evidence_id": CE[f"unit_margin:{k}"],
                        "constraint_units_per_item": HOURS[k], "constraint_evidence_id": CE[f"constraint_per_item:{k}"],
                        "mq_per_constraint_unit": r["mq_per_constraint_unit"], "calculation_trace": r["calculation_trace"]})
    ranking.sort(key=lambda x: -x["mq_per_constraint_unit"])
    a4 = next(a for a in actions if a["action_id"] == "ACT-004")
    a4["action_description"] = "案件の種類ごとに「制約資源あたりMQ」（指標定義書 §6-1）を算定する。分母は、班長が判断対応に使った時間。"
    a4["extensions"]["through_line"].update({
        "computed_by": "proposals/constraint_calc.py（提案中。正本の financial_calc.py には未実装）",
        "utilization": {"value": util["utilization"], "used_evidence_id": CE["constraint_used"],
                        "available_evidence_id": CE["constraint_available"], "calculation_trace": util["calculation_trace"]},
        "ranking": ranking})

    # ============ 改善シナリオ（見込みではない。仮定を明示する）============
    AFTER = {"standard": 0.6, "large": 2.4, "illuminated": 1.4}  # 仮定：モノサシを渡したあとの、班長の判断対応 時間/件
    per_before = cc.calc_weighted_average(HOURS, COUNTS, "占有時間", non_negative=True)
    per_after = cc.calc_weighted_average(AFTER, COUNTS, "占有時間", non_negative=True)
    m_avg = cc.calc_weighted_average(UNIT_M, COUNTS, "1件あたりM")
    DEMAND = 10.0  # 仮定：需要は週10件ある
    sc = cc.calc_throughput_scenario(12.0, per_after["average"], {"design": 9.0, "production": 10.0, "demand": DEMAND}, "週")
    dq = cc.calc_mq_delta_scenario(7.0, sc["throughput"], m_avg["average"], "週")
    scenario = {
        "label": "scenario", "period": "週", "constraint_unit": "時間", "computed_by": "proposals/constraint_calc.py（提案中）",
        "constraint_available_evidence_id": CE["constraint_available"],
        "constraint_per_item_evidence_ids": {k: CE[f"constraint_per_item:{k}"] for k in TYPES},
        "mix_evidence_ids": {k: CE[f"mix_count:{k}"] for k in TYPES},
        "unit_margin_evidence_ids": {k: CE[f"unit_margin:{k}"] for k in TYPES},
        "assumptions": [
            {"id": "A1", "statement": "モノサシを渡すと、班長の判断対応は 標準1.0→0.6／大型3.0→2.4／電飾2.0→1.4 時間/件に減る。", "basis": "assumption", "basis_evidence_ids": []},
            {"id": "A2", "statement": "案件の構成は今と同じ（標準16：大型4：電飾8）。", "basis": "assumption",
             "basis_evidence_ids": [CE[f"mix_count:{k}"] for k in TYPES]},
            {"id": "A3", "statement": "需要は週10件ある。", "basis": "assumption", "basis_evidence_ids": [E["f_wait_days"]]},
            {"id": "A4", "statement": "設計・製作の処理量は、現状の完了実績（設計9・製作10 件/週）を超えない。完了実績は測定あり。処理できる最大の量（能力の上限）は測っていない。", "basis": "assumption", "basis_evidence_ids": [E["f_design"], E["f_prod"]]},
            {"id": "A5", "statement": "増える案件の1件あたりMは、今の構成の加重平均と同じ。", "basis": "assumption", "basis_evidence_ids": []},
        ],
        "before": {"throughput": 7.0, "throughput_evidence_id": E["f_install"], "constraint_units_per_item_avg": per_before["average"]},
        "after": {"constraint_units_per_item_by_type": AFTER, "constraint_units_per_item_avg": per_after["average"],
                  "by_constraint": sc["by_constraint"], "throughput": sc["throughput"], "binding": sc["binding"]},
        "caps": [
            {"kind": "upstream", "name": "design", "stage": "design", "value": 9.0, "value_kind": "actual_completed", "basis_evidence_id": E["f_design"], "assumption_id": "A4"},
            {"kind": "upstream", "name": "production", "stage": "production", "value": 10.0, "value_kind": "actual_completed", "basis_evidence_id": E["f_prod"], "assumption_id": "A4"},
            {"kind": "demand", "name": "demand", "value": DEMAND, "assumption_id": "A3"},
        ],
        "mq_effect": {"delta_q": dq["delta_q"], "m_unit_margin_for_added": m_avg["average"], "m_basis": "weighted_average_current_mix",
                      "mq_delta_per_period": dq["mq_delta"]},
        "next_constraint": [b for b in sc["binding"] if b != "constraint_resource"],
        "calculation_traces": {"per_before": per_before["calculation_trace"], "per_after": per_after["calculation_trace"],
                               "m_avg": m_avg["calculation_trace"], "throughput": sc["calculation_trace"], "mq_delta": dq["calculation_trace"]},
    }

    # ============ 6段：モノサシ化の聞き取り（架空の結果）============
    def said(n, statement, excerpt, role, context, section, para, occ=None, occ_date=None):
        e = {"evidence_id": f"EVD-{M4[4:12]}-{n:03d}", "evidence_type": "REPORTED", "mtg_session_id": M4,
             "source_file": "monosashi/20261122_suriawase_note.md", "source_date": "2026-11-22",
             "source_pointer": {"type": "minutes", "section": section, "paragraph": para, "line": 1},
             "normalized_statement": statement, "source_form": "summary_minutes", "review_status": "spot_checked",
             "sensitivity": "internal", "notes": "架空の聞き取り結果。",
             "verbatim_excerpt": excerpt, "speaker_category": "client_manager" if role == "施工班長" else "client_member",
             "speaker_role_label": role, "speaker_attribution_status": "verified", "elicitation_context": context,
             "extensions": ext(layer="field", stage="install", sheet=section)}
        if occ:
            e.update({"occurrence_key_applicability": "applicable", "occurrence_key": occ, "occurrence_date": occ_date})
        return e

    occ = ("OCC-20261118-001", "2026-11-18")  # 袖看板の取付で、配線が届かず翌日に手直しになった案件
    m4 = [
        {"evidence_id": f"EVD-{M4[4:12]}-001", "evidence_type": "DOCUMENTED", "mtg_session_id": M4,
         "source_file": "monosashi/20261122_gengoka_sheet.pdf", "source_date": "2026-11-22",
         "source_pointer": {"type": "document", "page": 1, "item": "普段使っているモノサシ／ペアシェア"},
         "normalized_statement": "班長は施工当日の現場判断について5つのモノサシを書き、うち3つ（電源の位置を最初に見る／下地が図面と違えば止める／迷ったら通りからの見え方を優先する）は班員に渡せていないとした。",
         "source_form": "original_document", "review_status": "spot_checked", "sensitivity": "internal", "notes": "架空の記入内容。",
         "verbatim_excerpt": "①着いたらまず電源の位置を見る ②営業時間中は音の出る作業をしない ③下地が図面と違えば止める ④迷ったら通りからの見え方を優先 ⑤完了は依頼主の立会いまで。渡せているのは②⑤。",
         "document_type": "モノサシ言語化シート", "document_issuer": "施工班長",
         "extensions": ext(layer="field", stage="install", sheet="言語化シート")},
        said(2, "班員は、取付位置が図面どおりかどうかを確かめようとしていた。", "図面どおりの位置に付いているか、そこだけ見ていました。",
             "施工班員", "open_question", "②再現（視点・着目点）", 1, *occ),
        said(3, "班員は、図面どおりなら問題は起きないと考え、班長に聞くほどではないと判断して取付を進めた。",
             "寸法は合っていたので、わざわざ班長に聞くことでもないかなと思って、そのまま付けました。",
             "施工班員", "open_question", "②再現（解釈・先読み・判断）", 2, *occ),
        said(4, "取付後、電源の位置が図面と違っていて配線が届かず、翌日に再訪問して手直しした。", "配線が届かなくて、次の日にもう一回行きました。",
             "施工班員", "open_question", "③結果", 1, *occ),
        said(5, "班長は、現場に着いたら最初に電源の位置を見る。図面と違うことがよくあるため。", "私は着いたらまず電源を見ます。図面と違うことがよくあるので。",
             "施工班長", "open_question", "④責任者の見え", 1),
        said(6, "班長は、取付位置を図面から変える必要が出たら、依頼主に見え方を確かめるので先に連絡がほしいと考えている。",
             "位置を変えるなら、お客さんに見え方を確認しないといけない。だから、やる前に電話してほしい。",
             "施工班長", "open_question", "④責任者の見え", 2),
    ]
    ev += m4
    E.update({"m_sheet": m4[0]["evidence_id"], "m_view": m4[1]["evidence_id"], "m_judge": m4[2]["evidence_id"],
              "m_result": m4[3]["evidence_id"], "m_leader_see": m4[4]["evidence_id"], "m_leader_line": m4[5]["evidence_id"]})

    # 聞き取りの結果を仮説に戻す：「判断は班長がするもの」という前提は弱まり、別の構造の仮説が立つ
    h3 = hypotheses[2]
    h3.update({"status": "WEAKENED", "primary_supporting_evidence_ids": [E["r_member"]], "last_reviewed_at": "2026-11-22T17:00:00+09:00",
               "counter_evidence_review": {"status": "found", "reviewed_sources": [E["m_judge"]],
                                           "note": "聞き取った案件では、班員は班長に聞かずに自分で判断して進めていた。"},
               "alternative_hypothesis_review": {"status": "considered", "alternatives": ["班員は判断しているが、見るところが班長と違う（HYP-004）"], "note": ""},
               "next_review_trigger": "次の聞き取り"})
    hypotheses.append(hyp(4, "structure", "班長が現場で見ているところ（電源の位置など）が班員に渡っていないため、班長は現場の判断を任せられず、確認が班長に集まる。",
                          [E["m_sheet"], E["m_view"], E["m_leader_see"], E["m_result"], E["r_leader"]], [E["m_sheet"], E["m_view"], E["m_leader_see"]], ["PAT-001"],
                          {"status": "not_reviewed", "reviewed_sources": [], "note": ""},
                          {"status": "considered", "alternatives": ["受け渡しの情報が足りないだけで、見るところは渡っている"], "note": "電源の位置は現場で見える情報で、受け渡しの不足だけでは説明できない。"},
                          "TO_CONFIRM", ["ほかの班員も、電源の位置を最初に見ていないか。"], {"kind": "structure"}))
    hypotheses[-1]["created_at"] = hypotheses[-1]["last_reviewed_at"] = "2026-11-22T17:00:00+09:00"
    hypotheses[-1]["next_review_trigger"] = "ACT-006 の確認場面のあと"

    T4 = "2026-11-22T17:00:00+09:00"
    mono_items = []

    def mono(n, kind, statement, src, state, cert, provisional, line, uses, hr="not_reviewed", info=False, cases=1):
        m = {"monosashi_id": f"MNS-{n:03d}", "kind": kind, "statement": statement, "job": "施工当日の現場判断",
             "judgment_scene": "施工当日、図面に無い現場条件に気づいたとき、自分で決めて進めるか、班長に聞くか。",
             "source_action_id": "ACT-002", "source_evidence_ids": src, "source_case_count": cases, "state": state,
             "provisional": provisional, "line_check_status": line, "info_and_authority_confirmed": info,
             "uses": uses, "hr_os_review_status": hr, "sensitivity": "internal", "created_at": T4, "updated_at": T4}
        if cert:
            m["certification"] = cert
        mono_items.append(m)

    mono(1, "observation_point", "取付の前に、電源の位置が図面と同じかを見る。",
         [E["m_view"], E["m_leader_see"], E["m_result"]], "certified",
         {"certified_by_role": "施工班長", "certified_at": "2026-11-22",
          "reason": "配線の手直しは再訪問になり、依頼主の営業を二度止めることになるから。"},
         False, "not_applicable",
         {"development": "in_use", "work_standard": "adopted", "evaluation": "on_hold",
          "evaluation_note": "1件の案件から出たもの。ほかの班員・ほかの案件で確かめておらず、等級別の役割との照らし合わせも済んでいない。"},
         info=True)
    mono(2, "consultation_line", "取付位置を図面から変えるときは、進める前に班長に連絡する。",
         [E["m_judge"], E["m_leader_line"]], "candidate", None, True, "not_checked",
         {"development": "in_use", "work_standard": "not_adopted", "evaluation": "not_proposed",
          "evaluation_note": "候補。線の4基準の検証をしていない。1on1の材料として使う。"})
    mono(3, "selection_rule", "工期と通りからの見え方がぶつかったら、見え方を優先する。",
         [E["m_sheet"]], "on_hold", None, False, "not_applicable",
         {"development": "not_used", "work_standard": "not_adopted", "evaluation": "not_proposed",
          "evaluation_note": "保留。班長の自己申告だけで、実案件での再現が無い。もう少し事例を見る。"}, cases=0)

    actions.append(act(6, "monosashi_trial", "observation",
                       "次の施工で、班員が現場に着いたら最初に電源の位置を見て、図面との違いを声に出す。班長はそれを聞いてから作業を始める。",
                       ["HYP-004"], "班員が自分から電源の位置を確かめ、班長への確認の連絡が減る。",
                       "班員が見ても違いに気づかない、または確認の連絡が減らない。", M4, {"monosashi_ids": ["MNS-001"]}))
    actions[-1]["next_review_trigger"] = "次回の袖看板の施工日"
    actions[-1]["created_at"] = T4
    actions.append(act(7, "improvement_scenario", "data_collection",
                       "モノサシを渡したあとの4週間、案件の種類ごとの班長の判断対応時間と、設計・製作・施工の完了件数を測り、シナリオと比べる。",
                       ["HYP-001", "HYP-004"], "班長の判断対応時間が仮定（A1）の水準まで下がり、施工の完了が週9件に近づき、製作完了後の滞留が減る。",
                       "判断対応時間が下がらない。または下がっても施工の完了件数が増えない（制約は別の場所にある）。", M4, {"scenario": scenario}))
    actions[-1]["next_review_trigger"] = "モノサシを渡してから4週間後"
    actions[-1]["created_at"] = T4

    rows_rank = "\n".join(f"| {i + 1} | {r['label']} | {r['m_unit_margin']:,.0f} | {r['constraint_units_per_item']} | {r['mq_per_constraint_unit']:,.0f} |"
                          for i, r in enumerate(ranking))
    smemo = f"""# 制約資源あたりMQ と、改善シナリオ（架空の例）

**架空の会社・架空の数値。** 計算は `proposals/constraint_calc.py`（財務側へ入れる提案。正本の `financial_calc.py` には未実装）。
**シナリオは見込みではない。** 仮定を変えれば結果は変わる。

## 分母を分ける

| 測ったもの | 値 | 分母にするか |
|---|---|---|
| 班員が班長の判断を待った時間 | 2.1 時間/件 | しない（待っていた時間） |
| 班長が判断対応に使った時間 | 標準1.0／大型3.0／電飾2.0 時間/件 | する（占有した時間） |
| 班長が判断対応に使える時間 | 12.0 時間/週 | 使える量 |
| 班長が判断対応に使った時間 | 11.0 時間/週 | 使った量 |

使用率は {util['utilization']:.1%}。班長の判断対応の時間は、ほぼ使い切っている。

## 制約資源あたりMQ（今の制約＝班長の判断対応の時間）

| 順位 | 案件の種類 | 1件あたりM（円） | 班長の時間（時間/件） | 制約資源あたりMQ（円/時間） |
|---|---|---|---|---|
{rows_rank}

1件あたりの M がいちばん大きいのは大型だが、班長の時間あたりでは標準がいちばん高い。
班長の時間が制約である間は、この順位が受注の優先順位の材料になる。

## 改善シナリオ

仮定：
- A1 モノサシを渡すと、班長の判断対応は 標準1.0→0.6／大型3.0→2.4／電飾2.0→1.4 時間/件に減る（**根拠の測定なし**）
- A2 案件の構成は今と同じ
- A3 需要は週{DEMAND:.0f}件ある（**根拠の測定なし**。製作完了後の滞留が平均6.5日あることは、需要があることの傍証にとどまる）
- A4 設計・製作の処理量は、現状の完了実績（設計9・製作10 件/週）を超えない（**完了実績は測定あり。「これが上限」は仮定**。処理できる最大の量は測っていない）
- A5 増える案件の1件あたりMは、今の構成の加重平均と同じ

| | 改善前 | 改善後（シナリオ） |
|---|---|---|
| 班長の時間（1件あたり・加重平均） | {per_before['average']:.2f} 時間 | {per_after['average']:.2f} 時間 |
| 班長の時間から見た上限 | — | {sc['by_constraint']:.1f} 件/週 |
| 全体で流せる件数 | 7.0 件/週 | {sc['throughput']:.1f} 件/週 |
| 上限を決めているもの | 班長の時間 | {'・'.join({'design': '設計', 'production': '製作', 'demand': '需要', 'constraint_resource': '班長の時間'}[b] for b in sc['binding'])} |

増える件数は週{dq['delta_q']:.1f}件。増えるMQ は週{dq['mq_delta']:,.0f}円（1件あたりM {m_avg['average']:,.0f}円 × {dq['delta_q']:.1f}件）。年換算はしていない。

## 読み方

- 班長の時間から見れば週{sc['by_constraint']:.1f}件まで流せるが、設計の完了実績が週9件なので、全体は9件で止まる。**A4 のもとでは、制約は設計へ動く。**
- 完了実績は、能力の上限ではない。設計が週9件しか完了していなくても、処理できる量は9件より多いかもしれない。「次の制約は設計」は、A4 が成り立つときの結果。設計の能力を測れば、結論は変わりうる
- 制約が動いたら、上の順位表は使えなくなる。分母を設計の時間に替えて、測り直してから出し直す
- 増えるMQ は、A1・A3・A4・A5 が成り立ったときの値。どれも、仮定の部分に測定の裏づけが無い。ACT-007 で、モノサシを渡したあとの4週間を測って比べる
"""

    memo = f"""# 7段：人への材料メモ（架空の例）

**架空の会社・架空の聞き取り結果・架空の認定。** 実際の現場検証や認定の実績ではない。
一本線が、数字から育成・評価の入口まで通るかを確かめるための例。

## 元になった線

数字（年{Q:.0f}件・MQ {mq.mq_total:,.0f}円）→ 流れ（設計9／製作10／施工7 件/週）→ 制約の仮説（施工班長の判断時間・確認中）
→ 聞き取り（施工班員1名・袖看板の取付で手直しになった案件1件）→ モノサシ3つ

聞き取りで分かったこと：班員は班長を待たずに自分で判断していた。ズレた場所は「情報はあったが、注意が向いていなかった」。
電源の位置は現場で見える。班長は最初にそこを見るが、班員は取付位置の寸法だけを見ていた。
このため「判断は班長がするもの、という前提がある」という仮説（HYP-003）は弱まり、
「班長が見ているところが班員に渡っていない」という仮説（HYP-004）を新しく立てた。

## 用途ごとの仕分け

| モノサシ | 状態 | 育成（1on1・振り返り） | 業務の基準（OJT） | 評価（等級別の期待行動） |
|---|---|---|---|---|
| MNS-001 観察ポイント：取付の前に、電源の位置が図面と同じかを見る | 認定（施工班長） | 使う | 採用 | **止める** |
| MNS-002 相談線：取付位置を図面から変えるときは、進める前に班長に連絡する | 候補 | 使う（暫定と明示） | 採用しない | 出さない |
| MNS-003 選択ルール：工期と見え方がぶつかったら、見え方を優先する | 保留 | 使わない | 採用しない | 出さない |

## 育成・OJT の計画（MNS-001）

1. 次の施工で、班員は現場に着いたら最初に電源の位置を見て、図面との違いを声に出す（ACT-006）
2. 班長は、自分ならどこで引っかかるかを一言返す。違ったところだけ話す
3. 3件続けて班員が自分から確かめられたら、班長の立会いなしで取付を始めてよい範囲を、班長が決める

MNS-002 は候補なので、1on1 では「班長はこう考えている」という材料として出す。守るべき決まりとしては伝えない。

## 等級別の期待行動の候補（人事制度設計OS へ渡す前の下書き）

- S職（一般職）：取付の前に、電源の位置が図面と同じかを確かめ、違いがあれば報告する
- L職（指導監督職）：班員が見落としやすい現場条件を、現場に入る前に伝える

**評価項目への採用は止めている。** 理由は3つ。

1. 1件の案件、1人の班員から出たもの。ほかの班員・ほかの案件で確かめていない
2. 人事制度設計OS の確認（等級別の役割・権限と合うか、観察できるか、公平に評価できるか、運用できるか）が済んでいない
3. 聞き取りのズレた場所は「注意が向いていなかった」で、本人の姿勢の問題とは言えない。見るところを渡していなかった会社の側の話でもある

## 一本線へ戻すもの

- ACT-006（次の施工で一つ試す）の結果は、現場の証拠として戻す。HYP-004 が強まるか弱まるかは、そこで決まる
- 班長への確認の連絡が減り、施工の完了件数が上がったら、流れを測り直す。次に縛るのは設計（9件/週）の見込みで、制約は動く
- 完了件数が増えても、MQ が同じだけ増えるとは限らない。案件の種類ごとの「制約資源あたりMQ」は、財務側で算定する（ACT-004）
"""

    def env(rtype, items):
        return {"schema_version": "0.1.0", "case_id": CASE, "register_type": rtype, "last_updated_at": NOW, "items": items}

    OUT.mkdir(parents=True, exist_ok=True)
    for name, rtype, items in (("evidence.json", "evidence", ev), ("patterns.json", "patterns", patterns),
                               ("hypotheses.json", "hypotheses", hypotheses), ("causal.json", "causal", causal),
                               ("verification_actions.json", "verification_actions", actions)):
        (OUT / name).write_text(json.dumps(env(rtype, items), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ledger = {"schema_version": "0.1.0", "record_type": "monosashi_ledger", "case_id": CASE, "last_updated_at": T4, "items": mono_items}
    (OUT / "monosashi.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "people_memo.md").write_text(memo, encoding="utf-8")
    (OUT / "scenario_memo.md").write_text(smemo, encoding="utf-8")
    print(f"wrote 5 registers + monosashi.json + 2 memos to {OUT} / MQ={mq.mq_total:.0f} G={mq.g_operating_profit:.0f}")


if __name__ == "__main__":
    main(sys.argv[1:])
