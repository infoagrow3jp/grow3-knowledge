#!/usr/bin/env python3
"""through-line の問い（一本線の、つながっている所・切れている所・次の問い）

line_check.py と同じ検査を回し、結果を合否ではなく「問い」として出す。
検査の中身は line_check.py のものをそのまま使う（ここでは何も足さない・変えない）。
違いは3つだけ:
  1. register が揃っていなくてよい。無い register は空として扱う（どの段から入ってもよい）
  2. 外れた項目を、「次の問い」「根拠の欠落・不一致」「形式の直し」に分けて出す
     - 根拠の欠落・不一致（参照先が無い、案件が違う、など）は、AI が直さない。
       まだ渡されていないだけかもしれない。検査に通すために参照や根拠を消さない
     - 形式の直しは、原資料と照らして一意に直せるものだけを AI が直す
  3. 合否を出さない。終了コードは、読めたら 0

線を確定させるとき（モノサシを業務の基準や評価に使う前など）は、line_check.py を使う。

使い方:
  python3 -I tools/line_questions.py <case_dir>
  python3 -I tools/line_questions.py --schemas <dir> <case_dir>
<case_dir> には、ある register だけを置く（evidence.json だけでもよい）。
出力は、AI が小林さんへ返す前の材料。ID や記号は、そのまま見せるためのものではない。
終了コード: 0=読めた / 2=読めない（register の形が崩れている、schema が取れない、など）
"""
import importlib.util, json, pathlib, re, shutil, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("line_check", HERE / "line_check.py")
lc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lc)

REGISTER_TYPES = {"evidence.json": "evidence", "patterns.json": "patterns", "hypotheses.json": "hypotheses",
                  "causal.json": "causal", "verification_actions.json": "verification_actions"}

# 外れた項目 → 問い。上から順に、記号と、文中の言葉で引く。None は「形式の直し」。
# ただし、文中に MISSING の言葉があるものは、記号によらず「根拠の欠落・不一致」に回す（AI は直さない）。
MISSING = ("存在しない", "見つからない", "case_id", "棄却した証拠", "重複")
QUESTIONS = [
    ("schema", "", None), ("参照", "", None), ("L1", "", None), ("L8", "", None), ("M1", "", None), ("M6", "", None),
    ("L2", "財務の数字だけ", "その数字の変化が起きている場面を、流れの測定か現場の出来事で示せるか。"),
    ("L2", "1件も無い", "この因果は、何を見てそう考えたか。"),
    ("L2", "", None),
    ("L3", "流れの測定", "その工程の完了件数・滞留・待ちを、どの記録から測れるか。"),
    ("L3", "現場の証拠", "その工程で、誰が・どの場面で止まっているかを、見るか聞くかできるか。"),
    ("L3", "ほかの工程", "ほかの工程が全体を縛っている可能性は無いか。無いと言える材料は何か。"),
    ("L3", "確かめる測定", "何を測れば、この見立てが強まるか。何が出たら弱まるか。"),
    ("L3", "強まり", "何が出たら、この見立てが強まるか。何が出たら弱まるか。"),
    ("L3", "資源", "縛っているのは、その工程の何か（人・設備・判断）。"),
    ("L3", "", None),
    ("L4", "", "比べる相手の工程を1つ、同じ期間で測れるか（制約は、工程どうしの比較でしか言えない）。"),
    ("L5", "", "その工程が詰まると、どの数字（Q・P・V・F）がどう動くか。その途中に何が起きているか。"),
    ("L6", "", "いま全体を縛っているのは、どちらか（制約は1つに絞る）。"),
    ("L7", "", "その制約のところで、誰のどの判断が効いているか。聞き取るなら、どの場面か。"),
    ("L9", "書かれていない", "この制約がほどけたら、次に詰まるのはどこか。"),
    ("L9", "", "次に詰まるとした工程そのものの流れを、測っているか。"),
    ("L10", "待っていた時間", "待った時間ではなく、制約になっている資源を使った時間を測れるか。"),
    ("L10", "", None),
    ("L11", "裏づけが無い仮定", "裏づけの無い仮定のうち、先に確かめるならどれか。何を測れば確かめられるか。"),
    ("L11", "上限が置かれていない", "改善後に流せる件数の上限（上流の工程、需要）を、何で置くか。測定か、仮定か。"),
    ("L11", "", None),
    ("L12", "測られていない", "制約とした資源の、使える量と使った量を測れるか（使用率が低ければ、そこは制約ではない）。"),
    ("L12", "", None),
    ("M2", "見つからない", None),
    ("M2", "", "このモノサシは、制約につながる場面の聞き取りから出たものか。"),
    ("M3", "", "責任者は、これを会社の基準として認定したか。"),
    ("M4", "", "評価に使う前の確認（責任者の認定、相談線なら線の4基準、本人の情報と権限、人事制度設計OS）のうち、どれが済んでいないか。"),
    ("M5", "", "認定前のものを育成に使うなら、暫定であることを本人に伝えているか。"),
]
STAGE_OF = {"L2": "4 因果", "L3": "5 制約", "L4": "2 流れ", "L5": "4 因果", "L6": "5 制約", "L7": "6 判断", "L9": "5 制約",
            "L10": "戻し", "L11": "戻し", "L12": "5 制約", "M2": "6 判断", "M3": "7 人", "M4": "7 人", "M5": "7 人"}


def classify(msg):
    m = re.match(r"\[([^\]]+)\]\s*(.*)", msg)
    code, body = (m.group(1), m.group(2)) if m else ("?", msg)
    if any(w in body for w in MISSING):
        return code, body, False
    for c, word, q in QUESTIONS:
        if c == code and word in body:
            return code, body, q
    return code, body, ""  # 表に無いもの：文だけ出す


def stage_in(case):
    """無い register を空で補った一時フォルダを作る。"""
    have = [f for f in REGISTER_TYPES if (case / f).exists()]
    if not have:
        raise lc.CheckError(f"{case}: register が1つも無い（evidence.json から始める）")
    head = lc.load_json(case / have[0])
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="through-line-q-"))
    try:  # 写しには顧客の記録が入る。途中で失敗しても、一時フォルダを残さない
        for f, rtype in REGISTER_TYPES.items():
            if f in have:
                shutil.copy(case / f, tmp / f)
            else:
                stub = {"schema_version": head.get("schema_version"), "case_id": head.get("case_id"), "register_type": rtype,
                        "last_updated_at": head.get("last_updated_at"), "items": []}
                (tmp / f).write_text(json.dumps(stub, ensure_ascii=False), encoding="utf-8")
        if (case / "monosashi.json").exists():
            shutil.copy(case / "monosashi.json", tmp / "monosashi.json")
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return tmp, [f for f in REGISTER_TYPES if f not in have]


def explain_schema(case, schemas):
    """schema 違反の中身を、直せる粒度で出す。
    evidence は種類ごとの分岐（oneOf）なので、line_check.py の文だけでは、どの欄が違うのか分からない。
    いちばん違反の少ない分岐を選び、その中の違反だけを出す。"""
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    mschema = next((lc.load_json(p) for p in lc.MONOSASHI_SCHEMAS if p.exists()), None)
    allschemas = list(schemas.values()) + ([mschema] if mschema else [])
    reg = Registry().with_resources([(x["$id"], Resource.from_contents(x)) for x in allschemas])
    fc, out = lc.make_format_checker(), []

    def leaves(e):
        if not e.context:
            return [e]
        branches = {}
        for c in e.context:
            branches.setdefault(c.relative_schema_path[0], []).append(c)
        best = min(branches.values(), key=lambda cs: sum(len(leaves(c)) for c in cs))
        return [l for c in best for l in leaves(c)]

    targets = [(f, schemas[n]) for f, n in lc.REGISTERS.items()]
    if mschema and (case / "monosashi.json").exists():
        targets.append(("monosashi.json", mschema))
    for fname, schema in targets:
        v = Draft202012Validator(schema, registry=reg, format_checker=fc)
        for e in v.iter_errors(lc.load_json(case / fname)):
            for l in leaves(e):
                line = f"{fname}: {'/'.join(map(str, l.absolute_path)) or '(root)'}: {l.message[:160]}"
                if line not in out:
                    out.append(line)
    return out


def overview(data, mono):
    """7段のそれぞれに、いま何があるか。"""
    tl = lc.tl
    ev = [e for e in data["evidence.json"]["items"] if e.get("review_status") != "rejected"]
    by = {l: [e for e in ev if tl(e).get("layer") == l] for l in lc.LAYERS}
    flow_stages = sorted({tl(e).get("stage") for e in by["flow"]} - {None})
    edges = [c for c in data["causal.json"]["items"]
             if c.get("causal_type") == "causal_hypothesis" and c.get("status") not in lc.DEAD_EDGE]
    hyps = data["hypotheses.json"]["items"]
    cons = [h for h in hyps if tl(h).get("kind") == "constraint_candidate" and h.get("status") in lc.ACTIVE_HYP]
    acts = data["verification_actions.json"]["items"]
    kinds = [tl(a).get("kind") for a in acts]
    rows, gaps = [], []

    rows.append(("1 数字", f"証拠 {len(by['finance'])}" if by["finance"] else "まだ無い"))
    if not by["finance"]:
        gaps.append(("1 数字", "気になっている数字はどれか。決算書か試算表があれば、financial_calc.py で出す。"))
    rows.append(("2 流れ", f"測定 {len(by['flow'])}（工程: {' / '.join(flow_stages)}）" if by["flow"] else "まだ無い"))
    if not by["flow"]:
        gaps.append(("2 流れ", "工程ごとの完了件数・滞留・待ちを、どの記録から取れるか。"))
    rows.append(("3 現場", f"証拠 {len(by['field'])}" if by["field"] else "まだ無い"))
    if not by["field"]:
        gaps.append(("3 現場", "誰に、どの場面を聞くか。どこを見に行くか。"))
    rows.append(("4 因果", f"矢印 {len(edges)}" if edges else "まだ無い"))
    if not edges and sum(bool(v) for v in by.values()) >= 2:
        gaps.append(("4 因果", "数字の変化を、どの流れ・どの現場の出来事が生んでいると見ているか。"))
    if cons:
        label = {"TO_CONFIRM": "確認中", "SUPPORTED": "支持", "WEAKENED": "弱まった"}
        rows.append(("5 制約", " ／ ".join(
            f"{h['hypothesis_id']} {tl(h).get('stage')}・{tl(h).get('resource') or '資源未記入'}（{label.get(h['status'], h['status'])}）"
            for h in cons)))
    else:
        rows.append(("5 制約", "仮説はまだ無い"))
        if by["flow"] or by["field"]:
            gaps.append(("5 制約", "全体の流れを縛っているのは、どこだと見ているか。それ以外の工程の可能性は。"))
    n_int = kinds.count("monosashi_interview")
    if mono is not None:
        items = mono["items"]
        rows.append(("6 判断", f"聞き取りの指定 {n_int} ／ モノサシ {len(items)}（認定 {sum(m['state'] == 'certified' for m in items)}・"
                               f"候補 {sum(m['state'] == 'candidate' for m in items)}・保留 {sum(m['state'] == 'on_hold' for m in items)}）"))
        rows.append(("7 人", f"育成に使用 {sum(m['uses']['development'] == 'in_use' for m in items)} ／ "
                             f"業務の基準 {sum(m['uses']['work_standard'] == 'adopted' for m in items)} ／ "
                             f"評価へ {sum(m['uses']['evaluation'] in ('proposed_to_hr_os', 'adopted') for m in items)}"))
    else:
        rows.append(("6 判断", f"聞き取りの指定 {n_int} ／ モノサシの台帳はまだ無い"))
        rows.append(("7 人", "まだ無い"))
        if cons and n_int:
            gaps.append(("6 判断", "指定した場面の聞き取りは済んだか。済んだら、本人と責任者の見えの違いを記録する。"))
    has_rank = any(isinstance(tl(a).get("ranking"), list) and tl(a)["ranking"] for a in acts)
    has_sc = any(isinstance(tl(a).get("scenario"), dict) for a in acts)
    rows.append(("戻し", f"制約資源あたりMQ の順位表 {'あり' if has_rank else 'まだ無い'} ／ 改善シナリオ {'あり' if has_sc else 'まだ無い'}"))
    if cons and not has_rank:
        gaps.append(("戻し", "制約になっている資源を、案件の種類ごとに1件あたりどれだけ使うかを測れるか（制約資源あたりMQ を出すため）。"))
    return rows, gaps


def main(argv):
    schemas_dir = None
    if "--schemas" in argv:
        i = argv.index("--schemas")
        if i + 1 >= len(argv):
            print("through-line の問い: 読めない\n  - --schemas にパスが無い")
            return 2
        schemas_dir, argv = argv[i + 1], argv[:i] + argv[i + 2:]
    if len(argv) != 1:
        print("through-line の問い: 読めない\n  - 案件のフォルダを1つ渡す")
        return 2
    case, tmp = pathlib.Path(argv[0]), None
    try:
        tmp, missing = stage_in(case)
        schemas, src = lc.load_schemas(schemas_dir)
        data, mono, errs = lc.check_schema(tmp, schemas)
        if errs:
            print("through-line の問い: 読めない（register の形が schema に合っていない。形だけを直す。値・参照・根拠を消して通さない）")
            for e in (explain_schema(tmp, schemas) or errs)[:40]:
                print(f"  - {e}")
            return 2
        stages, stage_src = lc.stage_vocabulary()
        fails, warns, _ = lc.check_line(data, mono, stages, lc.known_lens_ids())
        rows, gaps = overview(data, mono)
    except (lc.CheckError, OSError) as e:
        print(f"through-line の問い: 読めない\n  - {e}")
        return 2
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)

    print("through-line の問い（合否ではない。線を確定させるときは line_check.py）")
    print(f"schema: {src} / 工程の語彙: {stage_src}")
    if missing:
        print(f"まだ無い register（空として扱った）: {', '.join(missing)}")
    print("\n[いま、あるもの]")
    for name, state in rows:
        print(f"  {name}: {state}")

    asks, fixes, lost = [], [], []
    for msg in fails + warns:
        code, body, q = classify(msg)
        (lost if q is False else fixes if q is None else asks).append((code, body, q))
    print("\n[切れているところと、次の問い]")
    if not asks and not gaps:
        print("  （検査で外れたところは無い。線がつながっていることと、見立てが正しいことは別）")
    # 読みやすいように、段の順（1 数字 から）に並べる。どの問いを選ぶかは、材料のある段と相談の目的で決める（SKILL.md）
    order = ["1 数字", "2 流れ", "3 現場", "4 因果", "5 制約", "6 判断", "7 人", "戻し"]
    rows_q = [(name, "まだ材料が無い", q) for name, q in gaps]
    rows_q += [(STAGE_OF.get(code, code), body, q) for code, body, q in asks]
    rows_q.sort(key=lambda r: order.index(r[0]) if r[0] in order else len(order))
    for name, body, q in rows_q:
        print(f"  - （{name}）{body}")
        if q:
            print(f"      問い: {q}")
    if lost:
        print("\n[根拠の欠落・不一致（AI は直さない。参照や根拠を消して合わせない）]")
        if "evidence.json" in missing:
            print("  ※ evidence.json がまだ無い。参照先が見つからないのは、渡されていないだけの可能性が高い")
        for code, body, _ in lost:
            print(f"  - [{code}] {body}")
        print("      確かめること: 元の材料に当たる。まだ渡されていない材料なら、そう伝えて受け取る。見当たらなければ、小林さんに聞く。")
    if fixes:
        print("\n[形式の直し（原資料と照らして一意に直せるものだけ、AI が直す。直せなければ聞く）]")
        for code, body, _ in fixes:
            print(f"  - [{code}] {body}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
