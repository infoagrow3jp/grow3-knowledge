#!/usr/bin/env python3
"""schema gate（構造ゲート）

カード（候補・正式Library）と promotion record が schema に適合するかを検査する。
参照する common.schema.json は organization-diagnosis の正本で、`$id` で解決する
（`$id` は論理的な識別URI。実ファイルを v0.1/ フォルダに置く必要はない）。

common.schema.json の探し方（上から順）:
  1. --common <path> で渡されたファイル
  2. このリポジトリの schemas/organization-diagnosis/common.schema.json（grow3-knowledge 内で実行したとき）
  3. GitHub の正本を一時フォルダに取得（リポジトリ内には何も書かない・消さない）
取得できない、`$id` が想定と違う、参照が解決できない、のいずれも FAIL。

日時（date-time）と日付（date）の形式も検査する（正本の schema gate と同じく Draft 2020-12 + format）。
追加ライブラリに頼らず、このファイル内で判定する。

使い方:
  python3 -I tools/schema_check.py                       # カードだけ
  python3 -I tools/schema_check.py <promotion.json> ...   # カード＋promotion record
  python3 -I tools/schema_check.py --common <path> ...
終了コード: 0=全件適合 / 1=不適合または検査不能
"""
import datetime, json, pathlib, re, sys, tempfile, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent  # schemas/ だけはリポジトリ直下（practice-lens/ の1つ上）にある
SCHEMAS = REPO / "schemas" / "practice-lens"
CARD_FILES = [
    ROOT / "library" / "candidates" / "lens_candidates.json",  # 候補
    ROOT / "library" / "lens_library.json",                    # 正式Library（最初の採用時に作る）
]
COMMON_ID = "https://grow3.jp/schemas/organization-diagnosis/v0.1/common.schema.json"
COMMON_LOCAL = REPO / "schemas" / "organization-diagnosis" / "common.schema.json"
COMMON_URL = ("https://raw.githubusercontent.com/infoagrow3jp/grow3-knowledge/main/"
              "schemas/organization-diagnosis/common.schema.json")


class CheckError(Exception):
    pass


_DT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
_D = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def make_format_checker():
    """date-time（RFC3339・タイムゾーン必須）と date（YYYY-MM-DD）だけを検査する。"""
    from jsonschema import FormatChecker
    fc = FormatChecker(formats=())

    @fc.checks("date-time", raises=ValueError)
    def _dt(v):
        if not isinstance(v, str):
            return True
        if not _DT.match(v):
            raise ValueError(v)
        datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True

    @fc.checks("date", raises=ValueError)
    def _d(v):
        if not isinstance(v, str):
            return True
        if not _D.match(v):
            raise ValueError(v)
        datetime.date.fromisoformat(v)
        return True

    return fc


def load_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise CheckError(f"{path}: 読めない（{e}）")


def load_common(common_path=None):
    if common_path:
        common, src = load_json(common_path), str(common_path)
    elif COMMON_LOCAL.exists():
        common, src = load_json(COMMON_LOCAL), COMMON_LOCAL.relative_to(REPO).as_posix()
    else:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                dst = pathlib.Path(tmp) / "common.schema.json"
                with urllib.request.urlopen(COMMON_URL, timeout=30) as r:
                    dst.write_bytes(r.read())
                common, src = load_json(dst), "GitHub正本（一時取得）"
        except CheckError:
            raise
        except Exception as e:
            raise CheckError(f"common.schema.json を取得できない（{e}）。--common で渡す")
    if common.get("$id") != COMMON_ID:
        raise CheckError(f"common.schema.json の $id が想定と違う: {common.get('$id')!r}")
    return common, src


def build_validators(common_path=None):
    """(card用validator, promotion用validator, commonの出どころ) を返す。失敗は CheckError。"""
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError:
        raise CheckError("jsonschema / referencing が無い（pip install jsonschema referencing）")
    common, src = load_common(common_path)
    card = load_json(SCHEMAS / "card.schema.json")
    prom = load_json(SCHEMAS / "promotion.schema.json")
    for s in (card, prom):
        Draft202012Validator.check_schema(s)
    reg = Registry().with_resources(
        [(s["$id"], Resource.from_contents(s)) for s in (common, card, prom)])
    fc = make_format_checker()
    return (Draft202012Validator(card, registry=reg, format_checker=fc),
            Draft202012Validator(prom, registry=reg, format_checker=fc), src)


def errors_of(validator, data, label):
    """schema違反を文字列のリストで返す。参照が解決できない場合は CheckError。"""
    try:
        return [f"{label}: {'/'.join(map(str, e.path)) or '(root)'}: {e.message[:140]}"
                for e in validator.iter_errors(data)]
    except Exception as e:  # 参照解決の失敗など
        raise CheckError(f"{label}: 検証できない（{type(e).__name__}: {e}）")


def existing_card_files():
    return [p for p in CARD_FILES if p.exists()]


def main(argv):
    common_path = None
    if "--common" in argv:
        i = argv.index("--common")
        if i + 1 >= len(argv):
            print("schema: FAIL\n  - --common にパスが無い")
            return 1
        common_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    errs = []
    try:
        vc, vp, src = build_validators(common_path)
        files = existing_card_files()
        if not files:
            raise CheckError("カードのファイルが1つも無い")
        ids = []
        for p in files:
            data = load_json(p)
            errs += errors_of(vc, data, str(p.relative_to(ROOT)))
            ids += [c.get("card_id") for c in data.get("items", []) if isinstance(c, dict)]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            errs.append(f"card_id の重複: {', '.join(map(str, dup))}")
        for a in argv:
            errs += errors_of(vp, load_json(a), pathlib.Path(a).name)
    except CheckError as e:
        print(f"schema: FAIL（検査不能）\n  - {e}")
        return 1
    print(f"common: {src} / card files: {len(files)} / cards: {len(ids)} / promotion files: {len(argv)}")
    if not errs:
        print("schema: PASS")
        return 0
    print(f"schema: FAIL ({len(errs)})")
    for e in errs[:40]:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
