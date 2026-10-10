#!/usr/bin/env python3
"""cases_count gate（現場件数ゲート）

カードの field_validation.cases_count と review_status が、
非公開の promotion record と食い違っていないかを検査する。

cases_count ＝ そのLensを問いとして実際に使い、有効性を確認した「異なる案件」の数。
  - 数えるのは record_kind=field_use の記録だけ。origin（Lensを生んだ案件）は数えない
  - 同一案件で何度使っても1件（case_id の重複を除く）
  - 使ったが効かなかった記録は promotion に入れない（顧客側のEvidenceに残す）

数える前に、渡された promotion record を promotion.schema.json で検証する。
schema違反・検証不能があれば、件数は数えずに FAIL にする。
対象カードは、候補（library/candidates/lens_candidates.json）と
正式Library（library/lens_library.json、あれば）の両方。

promotion record は非公開領域にあるので、パスは引数で渡す。
渡し忘れと「まだ記録が無い」を区別するため、記録が無いときは --no-records を明示する。

使い方:
  python3 -I tools/cases_count_check.py <promotion.json> [<promotion.json> ...]
  python3 -I tools/cases_count_check.py --no-records      # 記録がまだ1件も無いとき
  （--common <path> は schema_check.py と同じ）
終了コード: 0=一致 / 1=不一致または検査不能
"""
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # -I では自動で入らない
import schema_check as sc  # noqa: E402


def main(argv):
    common_path = None
    if "--common" in argv:
        i = argv.index("--common")
        if i + 1 >= len(argv):
            print("cases_count: FAIL\n  - --common にパスが無い")
            return 1
        common_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    no_records = "--no-records" in argv
    files = [a for a in argv if a != "--no-records"]
    if no_records == bool(files):
        print("cases_count: FAIL（検査不能）")
        print("  - promotion record のパスを渡すか、記録が無いなら --no-records を明示する（どちらか一方）")
        return 1

    try:
        vc, vp, _src = sc.build_validators(common_path)
        card_files = sc.existing_card_files()
        if not card_files:
            raise sc.CheckError("カードのファイルが1つも無い")
        schema_errs, cards, records = [], [], []
        for p in card_files:
            data = sc.load_json(p)
            schema_errs += sc.errors_of(vc, data, str(p.relative_to(sc.ROOT)))
            cards += data.get("items", []) if isinstance(data, dict) else []
        for a in files:
            data = sc.load_json(a)
            schema_errs += sc.errors_of(vp, data, pathlib.Path(a).name)
            records += data.get("items", []) if isinstance(data, dict) else []
    except sc.CheckError as e:
        print(f"cases_count: FAIL（検査不能）\n  - {e}")
        return 1
    if schema_errs:
        print(f"cases_count: FAIL（schema違反 {len(schema_errs)} 件。件数は数えていない）")
        for e in schema_errs[:40]:
            print(f"  - {e}")
        return 1

    used = {}  # lens_id -> set(case_id)
    for rec in records:
        if rec["record_kind"] == "field_use":
            used.setdefault(rec["lens_id"], set()).add(rec["case_id"])

    errors = []
    ids = {c["card_id"] for c in cards}
    for lens_id in sorted({r["lens_id"] for r in records} - ids):
        errors.append(f"{lens_id}: promotion record があるが、カードが無い")
    for c in cards:
        cid, rs = c["card_id"], c["review_status"]
        n, backed = c["field_validation"]["cases_count"], len(used.get(cid, ()))
        if n != backed:
            errors.append(f"{cid}: cases_count={n} だが field_use の異なる案件は {backed} 件")
        if rs == "unreviewed" and n != 0:
            errors.append(f"{cid}: unreviewed なのに cases_count={n}")
        if rs == "spot_checked" and n < 1:
            errors.append(f"{cid}: spot_checked なのに cases_count={n}")
        if rs == "verified" and n < 2:
            errors.append(f"{cid}: verified なのに cases_count={n}")

    print(f"card files: {len(card_files)} / cards: {len(cards)} / promotion files: {len(files)}"
          f"{'（--no-records）' if no_records else ''} / records: {len(records)} / field_use のあるLens: {len(used)}")
    if not errors:
        print("cases_count: PASS")
        return 0
    print(f"cases_count: FAIL ({len(errors)})")
    for e in errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
