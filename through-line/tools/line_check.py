#!/usr/bin/env python3
"""through-line gate（一本線の検査）

数字 → 流れ → 現場 → 因果 → 制約 → 判断 の一本線が、organization-diagnosis の
register（evidence / patterns / hypotheses / causal / verification_actions）の上で
つながっているかを検査する。register の形そのものは organization-diagnosis の schema が
決める。ここでは、その上に載せた「一本線の約束」だけを見る。

検査は2層:
  A. schema 適合（Draft 2020-12 + 日時・日付の形式）と、register 間の参照整合
  B. 一本線の約束（framework/line_map.md「検査」の L1〜L12）
  C. モノサシ台帳（monosashi.json。あれば）の約束（同 M1〜M6）

schema の探し方（上から順）:
  1. --schemas <dir>
  2. リポジトリ内の schemas/organization-diagnosis/（grow3-knowledge の中で実行したとき）
  3. GitHub の正本を一時フォルダに取得（リポジトリ内には何も書かない・消さない）
取得できない、参照が解決できない、ファイルが読めない、はすべて FAIL（検査不能）。

使い方:
  python3 -I tools/line_check.py <case_dir>
  python3 -I tools/line_check.py --schemas <dir> <case_dir>
<case_dir> には evidence.json / patterns.json / hypotheses.json / causal.json /
verification_actions.json を置く（5つとも必須）。monosashi.json は、6段の聞き取りが済んでから置く（任意）。
終了コード: 0=PASS（WARN があっても 0）/ 1=FAIL または検査不能
"""
import datetime, json, pathlib, re, sys, tempfile, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
LOCAL_SCHEMAS = REPO / "schemas" / "organization-diagnosis"
LENS_SCHEMA = REPO / "schemas" / "practice-lens" / "card.schema.json"
MONOSASHI_SCHEMAS = [REPO / "schemas" / "through-line" / "monosashi.schema.json", ROOT / "schemas" / "monosashi.schema.json"]
LENS_FILES = [REPO / "practice-lens" / "library" / "candidates" / "lens_candidates.json",
              REPO / "practice-lens" / "library" / "lens_library.json"]
RAW = "https://raw.githubusercontent.com/infoagrow3jp/grow3-knowledge/main/schemas/organization-diagnosis/"
ID_BASE = "https://grow3.jp/schemas/organization-diagnosis/v0.1/"
REGISTERS = {  # ファイル名 -> schema名
    "evidence.json": "evidence", "patterns.json": "pattern", "hypotheses.json": "hypothesis",
    "causal.json": "causal", "verification_actions.json": "verification_action"}
# 工程の語彙。正本は practice-lens の card.schema.json（valueChainStage）。読めないときだけこの写しを使う。
STAGES_FALLBACK = ["intake", "survey", "design", "production", "handoff", "install", "close", "after", "support"]
LAYERS = ("finance", "flow", "field")
ACTIVE_HYP = ("TO_CONFIRM", "SUPPORTED", "WEAKENED")
DEAD_EDGE = ("REJECTED", "SUPERSEDED")
KEY = "through_line"


class CheckError(Exception):
    pass


def load_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise CheckError(f"{path}: 読めない（{e}）")


_DT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
_D = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def make_format_checker():
    from jsonschema import FormatChecker
    fc = FormatChecker(formats=())

    @fc.checks("date-time", raises=ValueError)
    def _dt(v):
        if isinstance(v, str):
            if not _DT.match(v):
                raise ValueError(v)
            datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True

    @fc.checks("date", raises=ValueError)
    def _d(v):
        if isinstance(v, str):
            if not _D.match(v):
                raise ValueError(v)
            datetime.date.fromisoformat(v)
        return True

    return fc


def load_schemas(schemas_dir=None):
    names = ["common"] + sorted(set(REGISTERS.values()))
    if schemas_dir:
        d, src = pathlib.Path(schemas_dir), str(schemas_dir)
        out = {n: load_json(d / f"{n}.schema.json") for n in names}
    elif LOCAL_SCHEMAS.exists():
        src = LOCAL_SCHEMAS.relative_to(REPO).as_posix()
        out = {n: load_json(LOCAL_SCHEMAS / f"{n}.schema.json") for n in names}
    else:
        src, out = "GitHub正本（一時取得）", {}
        try:
            with tempfile.TemporaryDirectory() as tmp:
                for n in names:
                    dst = pathlib.Path(tmp) / f"{n}.schema.json"
                    with urllib.request.urlopen(RAW + f"{n}.schema.json", timeout=30) as r:
                        dst.write_bytes(r.read())
                    out[n] = load_json(dst)
        except CheckError:
            raise
        except Exception as e:
            raise CheckError(f"schema を取得できない（{e}）。--schemas で渡す")
    for n, s in out.items():
        if s.get("$id") != ID_BASE + f"{n}.schema.json":
            raise CheckError(f"{n}.schema.json の $id が想定と違う: {s.get('$id')!r}")
    return out, src


def stage_vocabulary():
    if LENS_SCHEMA.exists():
        return load_json(LENS_SCHEMA)["$defs"]["valueChainStage"]["enum"], "practice-lens の card.schema.json"
    return STAGES_FALLBACK, "写し（practice-lens の schema が見つからない）"


def known_lens_ids():
    ids, found = set(), False
    for p in LENS_FILES:
        if p.exists():
            found = True
            ids |= {c["card_id"] for c in load_json(p)["items"]}
    return ids if found else None


def load_calc_functions():
    """シナリオの再計算に使う関数を読む。提案（proposals/）を先に、無ければ正本の financial_calc.py を見る。"""
    import importlib.util
    for path in (ROOT / "proposals" / "constraint_calc.py", REPO / "financial_calc.py"):
        if path.exists():
            spec = importlib.util.spec_from_file_location("tl_calc_" + path.stem, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                raise CheckError(f"{path.name} を読めない（{e}）")
            if all(hasattr(mod, f) for f in ("calc_weighted_average", "calc_throughput_scenario", "calc_mq_delta_scenario")):
                return mod
    raise CheckError("シナリオの再計算に使う関数（calc_throughput_scenario など）が見つからない")


def tl(item):
    """extensions.through_line を返す（無ければ空の辞書）。"""
    ext = item.get("extensions") or {}
    v = ext.get(KEY)
    return v if isinstance(v, dict) else {}


def check_schema(case, schemas):
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError:
        raise CheckError("jsonschema / referencing が無い（pip install jsonschema referencing）")
    mschema = next((load_json(p) for p in MONOSASHI_SCHEMAS if p.exists()), None)
    allschemas = list(schemas.values()) + ([mschema] if mschema else [])
    reg = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in allschemas])
    fc, errs, data = make_format_checker(), [], {}
    for fname, sname in REGISTERS.items():
        d = load_json(case / fname)
        data[fname] = d
        try:
            v = Draft202012Validator(schemas[sname], registry=reg, format_checker=fc)
            errs += [f"[schema] {fname}: {'/'.join(map(str, e.path)) or '(root)'}: {e.message[:150]}"
                     for e in v.iter_errors(d)]
        except Exception as e:
            raise CheckError(f"{fname}: 検証できない（{type(e).__name__}: {e}）")
    mono = None
    if (case / "monosashi.json").exists():
        if mschema is None:
            raise CheckError("monosashi.json があるのに、monosashi.schema.json が見つからない")
        mono = load_json(case / "monosashi.json")
        try:
            v = Draft202012Validator(mschema, registry=reg, format_checker=fc)
            errs += [f"[schema] monosashi.json: {'/'.join(map(str, e.path)) or '(root)'}: {e.message[:150]}"
                     for e in v.iter_errors(mono)]
        except Exception as e:
            raise CheckError(f"monosashi.json: 検証できない（{type(e).__name__}: {e}）")
    return data, mono, errs


def check_line(data, mono, stages, lens_ids):
    F, W = [], []  # FAIL, WARN
    ev = {e["evidence_id"]: e for e in data["evidence.json"]["items"]}
    pats = {p["pattern_id"]: p for p in data["patterns.json"]["items"]}
    hyps = {h["hypothesis_id"]: h for h in data["hypotheses.json"]["items"]}
    causal = data["causal.json"]["items"]
    edges = {c["edge_id"]: c for c in causal if c["causal_type"] == "causal_hypothesis"}
    acts = data["verification_actions.json"]["items"]

    # ---- A. 参照整合（register をまたぐ ID が実在するか、案件が同じか、棄却した証拠を使っていないか）
    cases = {f: d["case_id"] for f, d in data.items()}
    if len(set(cases.values())) != 1:
        F.append(f"[参照] case_id が register 間で違う: {cases}")
    for label, seq, key in (("evidence", data["evidence.json"]["items"], "evidence_id"),
                            ("patterns", data["patterns.json"]["items"], "pattern_id"),
                            ("hypotheses", data["hypotheses.json"]["items"], "hypothesis_id"),
                            ("actions", acts, "action_id")):
        ids = [x[key] for x in seq]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            F.append(f"[参照] {label} の ID が重複: {', '.join(dup)}")

    def need_ev(owner, ids):
        for i in ids:
            if i not in ev:
                F.append(f"[参照] {owner}: 存在しない証拠 {i}")
            elif ev[i]["review_status"] == "rejected":
                F.append(f"[参照] {owner}: 棄却した証拠 {i} を根拠にしている")

    for p in pats.values():
        need_ev(p["pattern_id"], p["supporting_evidence_ids"])
    for h in hyps.values():
        need_ev(h["hypothesis_id"], h["supporting_evidence_ids"])
        for i in h["primary_supporting_evidence_ids"]:
            if i not in h["supporting_evidence_ids"]:
                F.append(f"[参照] {h['hypothesis_id']}: 主要な証拠 {i} が supporting に入っていない")
        for i in h["supporting_pattern_ids"]:
            if i not in pats:
                F.append(f"[参照] {h['hypothesis_id']}: 存在しないパターン {i}")
    for e in edges.values():
        need_ev(e["edge_id"], e["supporting_evidence_ids"])
        for i in e["supporting_hypothesis_ids"]:
            if i not in hyps:
                F.append(f"[参照] {e['edge_id']}: 存在しない仮説 {i}")
    for c in causal:
        if c["causal_type"] != "causal_hypothesis":
            for i in c.get("edge_ids", []):
                if i not in edges:
                    F.append(f"[参照] {c['causal_type']}: 存在しない矢印 {i}")
    for a in acts:
        for i in a["target_hypothesis_ids"]:
            if i not in hyps:
                F.append(f"[参照] {a['action_id']}: 存在しない仮説 {i}")

    # ---- L1 証拠の層と工程
    for e in ev.values():
        t, eid = tl(e), e["evidence_id"]
        layer, stage = t.get("layer"), t.get("stage")
        if layer not in LAYERS:
            F.append(f"[L1] {eid}: 層（finance / flow / field）が付いていない")
            continue
        if layer in ("finance", "flow") and e["evidence_type"] != "MEASURED":
            F.append(f"[L1] {eid}: {layer} の層なのに測定（MEASURED）ではない")
        if layer == "field" and e["evidence_type"] == "MEASURED":
            F.append(f"[L1] {eid}: field の層なのに測定（MEASURED）になっている")
        if layer != "finance" and stage not in stages:
            F.append(f"[L1] {eid}: 工程 {stage!r} が語彙に無い")
        if layer == "finance" and stage is not None and stage not in stages:
            F.append(f"[L1] {eid}: 工程 {stage!r} が語彙に無い")
        if lens_ids is not None:
            for lid in t.get("lens_ids", []):
                if lid not in lens_ids:
                    W.append(f"[L8] {eid}: Lens {lid} が practice-lens に無い")

    def layers_of(ids):
        return [tl(ev[i]).get("layer") for i in ids if i in ev]

    # ---- L2 数字から因果へ直接飛ばない
    live = {k: e for k, e in edges.items() if e["status"] not in DEAD_EDGE}
    for e in live.values():
        ls = layers_of(e["supporting_evidence_ids"])
        if not ls:
            F.append(f"[L2] {e['edge_id']}: 根拠の証拠が1件も無い矢印")
        elif not any(l in ("flow", "field") for l in ls):
            F.append(f"[L2] {e['edge_id']}: 財務の数字だけを根拠にしている（流れの測定か現場の証拠が要る）")
        t = tl(e)
        for side in ("from", "to"):
            s = t.get(side) or {}
            if s.get("layer") not in LAYERS:
                F.append(f"[L2] {e['edge_id']}: {side} 側の変数に層が付いていない")
            elif s["layer"] != "finance" and s.get("stage") not in stages:
                F.append(f"[L2] {e['edge_id']}: {side} 側の工程 {s.get('stage')!r} が語彙に無い")

    # ---- L3〜L7 制約の仮説
    cons = [h for h in hyps.values() if tl(h).get("kind") == "constraint_candidate"]
    flow_stages = {tl(e).get("stage") for e in ev.values()
                   if tl(e).get("layer") == "flow" and e["review_status"] != "rejected"}
    for h in cons:
        hid, t = h["hypothesis_id"], tl(h)
        if h["status"] not in ACTIVE_HYP:
            continue
        stage = t.get("stage")
        if h["layer"] != "structure":
            F.append(f"[L3] {hid}: 制約の仮説は構造（structure）の層に置く")
        if stage not in stages:
            F.append(f"[L3] {hid}: 制約の工程 {stage!r} が語彙に無い")
        if not t.get("resource"):
            F.append(f"[L3] {hid}: 制約になっている資源（人・設備・判断）が書かれていない")
        sup = [ev[i] for i in h["supporting_evidence_ids"] if i in ev]
        if not any(tl(e).get("layer") == "flow" and tl(e).get("stage") == stage for e in sup):
            F.append(f"[L3] {hid}: 制約とした工程（{stage}）の流れの測定が、根拠に1件も無い")
        if not any(tl(e).get("layer") == "field" for e in sup):
            F.append(f"[L3] {hid}: 現場の証拠（発言・観察・文書）が、根拠に1件も無い")
        if h["alternative_hypothesis_review"]["status"] == "not_reviewed":
            F.append(f"[L3] {hid}: ほかの工程が制約である可能性を検討していない")
        mine = [a for a in acts if hid in a["target_hypothesis_ids"]]
        meas = [a for a in mine if tl(a).get("kind") == "constraint_measurement"]
        if not meas:
            F.append(f"[L3] {hid}: 制約を確かめる測定（constraint_measurement）が決まっていない")
        for a in meas:
            if not a["support_signal"].strip() or not a["weaken_signal"].strip():
                F.append(f"[L3] {a['action_id']}: 何が出たら強まり／弱まるかが空")
        # L4 比較
        if len(flow_stages - {None}) < 2:
            F.append(f"[L4] {hid}: 流れの測定が1工程分しか無い（制約は工程どうしの比較でしか言えない）")
        # L5 数字までの道
        start = set()  # 制約の工程に属する変数（財務の変数は除く）
        for e in live.values():
            for side, var in (("from", e["from_variable"]), ("to", e["to_variable"])):
                s = tl(e).get(side)
                if isinstance(s, dict) and s.get("stage") == stage and s.get("layer") != "finance":
                    start.add(var)
        fin = {e["to_variable"] for e in live.values()
               if isinstance(tl(e).get("to"), dict) and tl(e)["to"].get("layer") == "finance"}
        seen, todo = set(start), list(start)
        while todo:
            v = todo.pop()
            for e in live.values():
                if e["from_variable"] == v and e["to_variable"] not in seen:
                    seen.add(e["to_variable"])
                    todo.append(e["to_variable"])
        if not (seen & fin):
            F.append(f"[L5] {hid}: 制約の工程（{stage}）から財務の変数まで、矢印がつながっていない")
        # L7 判断への受け渡し
        if not any(tl(a).get("kind") == "monosashi_interview" and str(tl(a).get("judgment_scene", "")).strip()
                   for a in mine):
            msg = f"{hid}: モノサシ化の聞き取り対象（判断の場面）が指定されていない"
            (F if h["status"] == "SUPPORTED" else W).append(f"[L7] {msg}")
        # L9 制約が動いたあと
        nxt = t.get("next_constraint")
        if not (isinstance(nxt, dict) and nxt.get("stage") in stages):
            W.append(f"[L9] {hid}: この制約をほどいたとき、次に縛る工程が書かれていない")
        else:
            basis = nxt.get("basis_evidence_ids") or []
            if not basis:
                F.append(f"[L9] {hid}: 次に縛る工程の根拠（流れの測定）が書かれていない")
            for i in basis:
                if i not in ev:
                    F.append(f"[L9] {hid}: 次に縛る工程の根拠に、存在しない証拠 {i}")
                elif tl(ev[i]).get("layer") != "flow":
                    F.append(f"[L9] {hid}: 次に縛る工程の根拠 {i} が、流れの測定ではない")
            if basis and not any(i in ev and tl(ev[i]).get("layer") == "flow" and tl(ev[i]).get("stage") == nxt["stage"]
                                 for i in basis):
                F.append(f"[L9] {hid}: 次に縛る工程（{nxt['stage']}）の流れの測定が、根拠に1件も無い")
        # L12 制約資源の使える量と使った量
        used, avail = ev.get(t.get("used_evidence_id")), ev.get(t.get("available_evidence_id"))
        if not (used and avail and tl(used).get("measure") == "constraint_used"
                and tl(avail).get("measure") == "constraint_available"):
            W.append(f"[L12] {hid}: 制約資源の使える量と使った量が測られていない（使用率が分からない）")
        elif used.get("unit") != avail.get("unit") or used.get("population") != avail.get("population"):
            F.append(f"[L12] {hid}: 制約資源の使える量と使った量で、単位か期間が揃っていない")
    # ---- L10 制約資源あたりMQ の順位表、L11 改善シナリオ
    def close(a, b):
        return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))

    for a in acts:
        t, aid = tl(a), a["action_id"]
        for row in t.get("ranking", []) if isinstance(t.get("ranking"), list) else []:
            name = f"{aid}（{row.get('item_type')}）"
            me, ce = ev.get(row.get("m_evidence_id")), ev.get(row.get("constraint_evidence_id"))
            if me is None or ce is None:
                F.append(f"[L10] {name}: 分子か分母の証拠が存在しない")
                continue
            if tl(me).get("layer") != "finance" or tl(me).get("measure") != "unit_margin":
                F.append(f"[L10] {name}: 分子が、1件あたりM の測定ではない")
            if tl(ce).get("measure") == "wait":
                F.append(f"[L10] {name}: 待っていた時間を分母にしている（分母は、制約資源を占有した量）")
            elif tl(ce).get("layer") != "flow" or tl(ce).get("measure") != "constraint_per_item":
                F.append(f"[L10] {name}: 分母が、制約資源の占有量の測定ではない")
            if tl(me).get("item_type") != row.get("item_type") or tl(ce).get("item_type") != row.get("item_type"):
                F.append(f"[L10] {name}: 分子・分母の案件の種類が、行と合っていない")
            if me.get("population") != ce.get("population"):
                F.append(f"[L10] {name}: 分子と分母で、測った期間・対象が揃っていない")
            cu = t.get("constraint_unit")
            if me.get("unit") != "円/件":
                F.append(f"[L10] {name}: 分子の単位が 円/件 ではない（{me.get('unit')}）")
            if not cu or ce.get("unit") != f"{cu}/件":
                F.append(f"[L10] {name}: 分母の単位が {cu}/件 ではない（{ce.get('unit')}）")
            if not (close(me.get("value", 0), row.get("m_unit_margin", -1))
                    and close(ce.get("value", 0), row.get("constraint_units_per_item", -1))):
                F.append(f"[L10] {name}: 行の数値が、元の測定と合っていない")
            elif not (isinstance(ce.get("value"), (int, float)) and ce["value"] > 0):
                F.append(f"[L10] {name}: 分母の占有量が0以下（{ce.get('value')}）。制約資源あたりMQ は算定不能")
            elif not close(row.get("mq_per_constraint_unit", -1), me["value"] / ce["value"]):
                F.append(f"[L10] {name}: 制約資源あたりMQ が、分子÷分母と合っていない")
        sc = t.get("scenario")
        if isinstance(sc, dict):
            if sc.get("label") != "scenario":
                F.append(f"[L11] {aid}: シナリオであることが明示されていない（label: scenario）")
            assumptions = {x.get("id"): x for x in sc.get("assumptions", [])}
            caps = sc.get("caps", [])
            if not any(c.get("kind") == "demand" for c in caps):
                F.append(f"[L11] {aid}: 需要の上限が置かれていない（測定が無ければ、仮定として明示する）")
            if not any(c.get("kind") == "upstream" for c in caps):
                F.append(f"[L11] {aid}: 上流の工程の上限が置かれていない")
            for c in caps:
                if "basis_evidence_id" in c:
                    e = ev.get(c["basis_evidence_id"])
                    if e is None:
                        F.append(f"[L11] {aid}: 上限 {c.get('name')} の根拠の証拠が存在しない")
                    elif not close(e.get("value", -1), c.get("value", -2)):
                        F.append(f"[L11] {aid}: 上限 {c.get('name')} の値が、元の測定と合っていない")
                elif c.get("assumption_id") not in assumptions:
                    F.append(f"[L11] {aid}: 上限 {c.get('name')} に、測定も仮定も紐づいていない")
            after = sc.get("after", {})
            limits = [c.get("value") for c in caps if isinstance(c.get("value"), (int, float))]
            if isinstance(after.get("by_constraint"), (int, float)):
                limits.append(after["by_constraint"])
            thr = after.get("throughput")
            if not isinstance(thr, (int, float)) or not limits:
                F.append(f"[L11] {aid}: 改善後の件数、または上限が書かれていない")
            elif thr > min(limits) + 1e-9:
                F.append(f"[L11] {aid}: 改善後の件数（{thr}）が、いちばん小さい上限（{min(limits)}）を超えている")
            # 再計算：元の測定と計算関数から、シナリオの数値を出し直して照らす
            try:
                calc = load_calc_functions()

                def vals(key, measure, layer):
                    out = {}
                    for k, i in (sc.get(key) or {}).items():
                        e = ev.get(i)
                        if e is None or tl(e).get("measure") != measure or tl(e).get("layer") != layer or tl(e).get("item_type") != k:
                            raise KeyError(f"{key} の {k}")
                        out[k] = e["value"]
                    if not out:
                        raise KeyError(key)
                    return out

                per, mix = vals("constraint_per_item_evidence_ids", "constraint_per_item", "flow"), vals("mix_evidence_ids", "mix_count", "flow")
                um = vals("unit_margin_evidence_ids", "unit_margin", "finance")
                av = ev.get(sc.get("constraint_available_evidence_id"))
                if av is None or tl(av).get("measure") != "constraint_available":
                    raise KeyError("constraint_available_evidence_id")
                before = sc.get("before", {})
                be = ev.get(before.get("throughput_evidence_id"))
                # 単位と期間：計算に使う測定どうしが、同じ単位・同じ期間のものか
                cu, period = sc.get("constraint_unit"), sc.get("period")
                if not cu or not period:
                    F.append(f"[L11] {aid}: 制約資源の単位（constraint_unit）か、期間（period）が書かれていない")
                else:
                    used = [("使える量", av, f"{cu}/{period}")]
                    used += [(f"占有量（{k}）", ev[i], f"{cu}/件") for k, i in sc["constraint_per_item_evidence_ids"].items()]
                    used += [(f"1件あたりM（{k}）", ev[i], "円/件") for k, i in sc["unit_margin_evidence_ids"].items()]
                    if be is not None:
                        used.append(("改善前の件数", be, f"件/{period}"))
                    used += [(f"上限 {c.get('name')}", ev[c["basis_evidence_id"]], f"件/{period}")
                             for c in caps if c.get("basis_evidence_id") in ev]
                    for label, e, want in used:
                        if e.get("unit") != want:
                            F.append(f"[L11] {aid}: {label} の単位が {want} ではない（{e.get('unit')}）")
                    mixes = [ev[i] for i in sc["mix_evidence_ids"].values()]
                    munits = {e.get("unit") for e in mixes}
                    if len(munits) != 1 or not str(next(iter(munits))).startswith("件/"):
                        F.append(f"[L11] {aid}: 種類ごとの件数の単位が揃っていない、または 件/… ではない（{sorted(map(str, munits))}）")
                    pops = {e.get("population") for _, e, _ in used} | {e.get("population") for e in mixes}
                    if len(pops) != 1:
                        F.append(f"[L11] {aid}: 計算に使う測定の期間・対象が揃っていない（{len(pops)} 通りある）")
                if be is None or tl(be).get("measure") != "throughput" or not close(be["value"], before.get("throughput", -1)):
                    F.append(f"[L11] {aid}: 改善前の件数が、元の測定と合っていない")
                r_before = calc.calc_weighted_average(per, mix, "占有量", non_negative=True)
                r_after = calc.calc_weighted_average(after.get("constraint_units_per_item_by_type") or {}, mix, "占有量", non_negative=True)
                r_m = calc.calc_weighted_average(um, mix, "1件あたりM")
                if None in (r_before["average"], r_after["average"], r_m["average"]):
                    F.append(f"[L11] {aid}: 加重平均を出し直せない（種類か件数が揃っていない、または占有量に負の値がある）")
                else:
                    if not close(r_before["average"], before.get("constraint_units_per_item_avg", -1)):
                        F.append(f"[L11] {aid}: 改善前の1件あたり占有量が、元の測定からの計算と合っていない")
                    if not close(r_after["average"], after.get("constraint_units_per_item_avg", -1)):
                        F.append(f"[L11] {aid}: 改善後の1件あたり占有量が、仮定からの計算と合っていない")
                    r_t = calc.calc_throughput_scenario(av["value"], r_after["average"],
                                                        {c.get("name"): c.get("value") for c in caps}, sc.get("period", ""))
                    if r_t["throughput"] is None:
                        F.append(f"[L11] {aid}: 改善後の件数を出し直せない（{r_t['reason']}）")
                    else:
                        if not close(r_t["by_constraint"], after.get("by_constraint", -1)):
                            F.append(f"[L11] {aid}: 制約資源から見た上限が、使える量÷改善後の占有量（{r_t['by_constraint']:.4g}）と合っていない")
                        if not close(r_t["throughput"], after.get("throughput", -1)):
                            F.append(f"[L11] {aid}: 改善後の件数が、上限の最小値（{r_t['throughput']:.4g}）と合っていない")
                        if sorted(after.get("binding") or []) != r_t["binding"]:
                            F.append(f"[L11] {aid}: 上限を決めているもの（binding）が、計算と合っていない")
                        eff = sc.get("mq_effect", {})
                        m_added = eff.get("m_unit_margin_for_added")
                        if eff.get("m_basis") == "weighted_average_current_mix" and not close(r_m["average"], m_added if m_added is not None else -1):
                            F.append(f"[L11] {aid}: 増える案件の1件あたりM が、今の構成の加重平均と合っていない")
                        if isinstance(m_added, (int, float)) and isinstance(before.get("throughput"), (int, float)):
                            r_d = calc.calc_mq_delta_scenario(before["throughput"], r_t["throughput"], m_added, sc.get("period", ""))
                            if r_d["mq_delta"] is None or not close(r_d["delta_q"], eff.get("delta_q", -1)) \
                                    or not close(r_d["mq_delta"], eff.get("mq_delta_per_period", -1)):
                                F.append(f"[L11] {aid}: 増える件数・増えるMQ が、（改善後−改善前）×1件あたりM と合っていない")
                        else:
                            F.append(f"[L11] {aid}: 増える案件の1件あたりM が書かれていない")
            except KeyError as e:
                F.append(f"[L11] {aid}: 再計算に要る測定が紐づいていない、または種類が合っていない（{e.args[0]}）")
            for x in assumptions.values():
                for i in x.get("basis_evidence_ids", []):
                    if i not in ev:
                        F.append(f"[L11] {aid}: 仮定 {x.get('id')} の根拠に、存在しない証拠 {i}")
            n_bare = sum(1 for x in assumptions.values() if x.get("basis") != "evidence")
            if n_bare:
                W.append(f"[L11] {aid}: 測定の裏づけが無い仮定が {n_bare} 件ある（シナリオであり、見込みではない）")
    # L6 制約は1つ
    sup_cons = [h["hypothesis_id"] for h in cons if h["status"] == "SUPPORTED"]
    if len(sup_cons) > 1:
        F.append(f"[L6] 支持された制約の仮説が2つ以上ある: {', '.join(sup_cons)}（制約は1つに絞る）")
    for a in acts:
        if lens_ids is not None:
            for lid in tl(a).get("lens_ids", []):
                if lid not in lens_ids:
                    W.append(f"[L8] {a['action_id']}: Lens {lid} が practice-lens に無い")
    # ---- C. モノサシ台帳
    n_mono = "なし"
    if mono is not None:
        items = mono["items"]
        n_mono = (f"{len(items)}（認定 {sum(m['state'] == 'certified' for m in items)} / "
                  f"候補 {sum(m['state'] == 'candidate' for m in items)} / 保留 {sum(m['state'] == 'on_hold' for m in items)}）")
        if mono["case_id"] != data["evidence.json"]["case_id"]:
            F.append("[参照] monosashi.json の case_id が register と違う")
        actmap = {a["action_id"]: a for a in acts}
        con_ids = {h["hypothesis_id"] for h in cons}
        for m in items:
            mid, uses = m["monosashi_id"], m["uses"]
            wants_eval = uses["evaluation"] in ("proposed_to_hr_os", "adopted")
            # M1 元の証拠
            for i in m["source_evidence_ids"]:
                if i not in ev:
                    F.append(f"[M1] {mid}: 存在しない証拠 {i}")
                elif ev[i]["review_status"] == "rejected":
                    F.append(f"[M1] {mid}: 棄却した証拠 {i} を元にしている")
                elif tl(ev[i]).get("layer") != "field":
                    F.append(f"[M1] {mid}: 元の証拠 {i} が現場の証拠（field）ではない")
            # M2 聞き取りと、制約へのつながり
            a = actmap.get(m["source_action_id"])
            if a is None or tl(a).get("kind") != "monosashi_interview":
                F.append(f"[M2] {mid}: 元の聞き取り（monosashi_interview）が見つからない")
            elif not (set(a["target_hypothesis_ids"]) & con_ids):
                (F if wants_eval else W).append(f"[M2] {mid}: 制約の仮説につながる聞き取りから出たものではない")
            # M3 業務の基準
            if uses["work_standard"] == "adopted" and m["state"] != "certified":
                F.append(f"[M3] {mid}: 認定されていないのに、業務の基準として採用している")
            # M4 評価
            if wants_eval:
                if m["state"] != "certified":
                    F.append(f"[M4] {mid}: 認定されていないのに、評価へ出している")
                if m["kind"] == "consultation_line" and m["line_check_status"] != "passed":
                    F.append(f"[M4] {mid}: 相談線なのに、線の4基準の検証を通していない")
                if not m["info_and_authority_confirmed"]:
                    F.append(f"[M4] {mid}: 本人が情報と権限を持っているかを確かめていない")
                if m["source_case_count"] < 2 and uses["evaluation"] == "proposed_to_hr_os":
                    W.append(f"[M4] {mid}: 実案件が2件に満たないものを評価へ出している（人事制度設計OS の判断へ渡す）")
            if uses["evaluation"] == "adopted":
                if m["hr_os_review_status"] != "reviewed_ok":
                    F.append(f"[M4] {mid}: 人事制度設計OS の確認が済んでいないのに、評価項目として採用している")
                if m["source_case_count"] < 2 and "evaluation_exception" not in uses:
                    F.append(f"[M4] {mid}: 実案件が2件に満たないのに評価項目に採用している。例外とするなら、認めた人と理由を書く")
            # M6 件数の根拠：元の証拠に付いている出来事の、異なるものの数と合っているか
            occs = {ev[i].get("occurrence_key") for i in m["source_evidence_ids"] if i in ev}
            occs = {o for o in occs if o and "UNKNOWN" not in o}
            if m["source_case_count"] != len(occs):
                F.append(f"[M6] {mid}: source_case_count={m['source_case_count']} だが、元の証拠にある異なる出来事は {len(occs)} 件")
            # M5 認定前のものを育成に使うなら、暫定と明示する
            if m["state"] != "certified" and uses["development"] == "in_use" and not m["provisional"]:
                F.append(f"[M5] {mid}: 認定前のものを育成に使うなら、暫定（provisional）と明示する")
    summary = (f"証拠 {len(ev)}（finance {sum(tl(e).get('layer') == 'finance' for e in ev.values())} / "
               f"flow {sum(tl(e).get('layer') == 'flow' for e in ev.values())} / "
               f"field {sum(tl(e).get('layer') == 'field' for e in ev.values())}） / パターン {len(pats)} / "
               f"仮説 {len(hyps)}（うち制約 {len(cons)}） / 矢印 {len(edges)} / 検証 {len(acts)} / モノサシ {n_mono}")
    return F, W, summary


def main(argv):
    schemas_dir = None
    if "--schemas" in argv:
        i = argv.index("--schemas")
        if i + 1 >= len(argv):
            print("through-line: FAIL（検査不能）\n  - --schemas にパスが無い")
            return 1
        schemas_dir, argv = argv[i + 1], argv[:i] + argv[i + 2:]
    if len(argv) != 1:
        print("through-line: FAIL（検査不能）\n  - 案件のフォルダを1つ渡す")
        return 1
    case = pathlib.Path(argv[0])
    try:
        schemas, src = load_schemas(schemas_dir)
        data, mono, errs = check_schema(case, schemas)
        if errs:
            print(f"schema: {src}")
            print(f"through-line: FAIL（schema違反 {len(errs)} 件。一本線の検査はしていない）")
            for e in errs[:40]:
                print(f"  - {e}")
            return 1
        stages, stage_src = stage_vocabulary()
        fails, warns, summary = check_line(data, mono, stages, known_lens_ids())
    except CheckError as e:
        print(f"through-line: FAIL（検査不能）\n  - {e}")
        return 1
    print(f"schema: {src} / 工程の語彙: {stage_src}")
    print(summary)
    for w in warns:
        print(f"  WARN {w}")
    if fails:
        print(f"through-line: FAIL ({len(fails)})")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("through-line: PASS" + (f"（WARN {len(warns)}）" if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
