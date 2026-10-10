#!/usr/bin/env python3
"""provenance gate（出典ゲート）

カード（候補と、あれば正式Library）の sources[] に書かれた資料名が、framework/sources.md の台帳に
「名前があり」「URLまたはローカル正本があり」「確認日が入っている」かを検査する。

Critic は内容（rubric）しか見ない。ここは根拠の所在だけを見る。
candidates → library 昇格時に必須。Editor は並行して走ってよい。

使い方:
  python3 -I tools/provenance_check.py                 # 候補全件
  python3 -I tools/provenance_check.py LENS-009 LENS-008  # 指定カードだけ
終了コード: 0=全件通過 / 1=未台帳・未確認あり、または指定したカードが無い
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "framework" / "sources.md"
CARD_FILES = [
    ROOT / "library" / "candidates" / "lens_candidates.json",  # 候補
    ROOT / "library" / "lens_library.json",                    # 正式Library（あれば）
]


def norm(s: str) -> str:
    # 全角括弧・空白のゆれを吸収して突き合わせる
    s = s.strip()
    s = s.replace("（", "(").replace("）", ")").replace("　", " ")
    return re.sub(r"\s+", "", s)


def load_ledger():
    """台帳の表行を {名前: {url, checked, local}} にする"""
    rows = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0] in ("ソース", "") or set(cells[0]) <= {"-"}:
            continue
        name, url, _trust, _what, checked = cells[:5]
        note = cells[5] if len(cells) > 5 else ""
        rows[norm(name)] = {
            "name": name,
            "url": url,
            "checked": checked,
            "local": "ローカル" in note or "手元" in note,
        }
    return rows


def main(argv):
    ledger = load_ledger()
    data = {"items": []}
    for path in CARD_FILES:
        if path.exists():
            data["items"] += json.loads(path.read_text(encoding="utf-8"))["items"]
    only = set(argv)
    unknown = sorted(only - {c["card_id"] for c in data["items"]})
    if unknown or not data["items"]:
        print("provenance: FAIL（検査不能）")
        print(f"  - 指定したカードが無い: {', '.join(unknown)}" if unknown else "  - カードが1枚も無い")
        return 1
    fails = {}   # source名 -> [card_id]
    reasons = {}
    for card in data["items"]:
        cid = card["card_id"]
        if only and cid not in only:
            continue
        for src in card["sources"]:
            row = ledger.get(norm(src))
            if row is None:
                r = "台帳に無い"
            elif not row["url"] and not row["local"]:
                r = "URLもローカル正本も無い"
            elif not row["checked"]:
                r = "未確認（確認日が空）"
            else:
                continue
            fails.setdefault(src, []).append(cid)
            reasons[src] = r

    n_cards = len([c for c in data["items"] if not only or c["card_id"] in only])
    n_src = len({s for c in data["items"] if not only or c["card_id"] in only for s in c["sources"]})
    print(f"cards: {n_cards} / distinct sources: {n_src} / 台帳行: {len(ledger)}")
    if not fails:
        print("provenance: PASS")
        return 0
    print(f"provenance: FAIL ({len(fails)} sources)")
    for src, cids in sorted(fails.items(), key=lambda x: -len(x[1])):
        print(f"  - [{reasons[src]}] {src}  ← {', '.join(cids)}")
    blocked = sorted({c for cids in fails.values() for c in cids})
    print(f"昇格できないカード: {len(blocked)} 枚 ({', '.join(blocked)})")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
