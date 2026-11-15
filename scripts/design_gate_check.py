# -*- coding: utf-8 -*-
"""設計の関門：着手票・照合の機械チェック（2026-11-15）

研修・商品・提案の設計の仕事を始めるとき・納品するときに、作業フォルダへ置く
「着手票」と「照合」を機械で確かめる。見るのは次の3点だけ（判断の良し悪しは見ない）。
  1. 票があるか（着手票*.md）
  2. 3点（今回の仕事／適用する既存判断／今回の判断基準）が埋まっているか
  3. 引用元のファイルが実在するか

特定のAIに依存しない。Python 3 の標準ライブラリだけで動く。

使い方（どのAI・人からも同じ）:
  python scripts/design_gate_check.py --init <作業フォルダ>     # 着手票の型を書き出す
  python scripts/design_gate_check.py <作業フォルダ>            # 着手票を検査（着手時）
  python scripts/design_gate_check.py --delivery <作業フォルダ> # 着手票＋照合を検査（納品時）
  python scripts/design_gate_check.py --hook                    # 対象フォルダを一括検査
  python scripts/design_gate_check.py --pretooluse              # 書き込み前フック用
                                                                # （stdinのJSONからfile_pathを読む）
検査対象の設定は scripts/design-gate-active.txt（scan:／except:。git管理・公開）と
scripts/design-gate-local.txt（extra:。git管理しない。--init が自動登録する）の2つ。
scan: の直下のサブフォルダは登録不要で自動検出する。
終了コード: 0=合格 / 1=FAILあり（--pretooluseのみ 2=書き込みを止める）
Dropbox等リポジトリ外の作業フォルダも、絶対パスを渡せばそのまま検査できる。
"""
import glob
import io
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG = os.path.join(SCRIPT_DIR, "design-gate-active.txt")
# extra: の置き場所。作業フォルダの絶対パスを公開リポジトリに載せないため、
# git管理しないローカルファイルに分ける（.gitignore 登録済み）。
CONFIG_LOCAL = os.path.join(SCRIPT_DIR, "design-gate-local.txt")

CONFIG_LOCAL_HEADER = """# 設計の関門：このPCだけの検査対象（git管理しない。design_gate_check.py が読む）
# extra: scan配下以外で検査対象に足すフォルダ（絶対パス）。--init が自動で追記する。
# 誤検出で止まるときは該当の extra: 行を外して先へ進み、小林さんへ一行で報告する。
"""

TEMPLATE = """# 着手票：（仕事の名前）（YYYY-MM-DD）

## 1. 今回の仕事
- 作るもの：
- 主な対象：商品／研修／ゲームと問い（いずれかを残す）
- 保存先：

## 2. 適用する既存判断（出どころのファイル名と、原文の引用。要約しない）
- [判断1] 出どころ：
  > （原文の引用をここに。要約しない）

## 3. 今回の判断基準
- 具体化すること：
- 足さない・変えないこと：
"""

FAIL = []
OK = []


def report(level, path, msg):
    (OK if level == "OK" else FAIL).append("[%s] %s : %s" % (level, path, msg))


def read_text(path):
    with io.open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def load_config():
    """scan/except/extra の設定を読む（公開のactiveとローカルの両方から）。"""
    scans, excepts, extras = [], set(), []
    for config in (CONFIG, CONFIG_LOCAL):
        if not os.path.isfile(config):
            continue
        with io.open(config, "r", encoding="utf-8-sig", errors="replace") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("scan:"):
                    scans.append(os.path.abspath(line[5:].strip()))
                elif line.startswith("except:"):
                    excepts.add(line[7:].strip())
                elif line.startswith("extra:"):
                    p = line[6:].strip()
                    extras.append(os.path.abspath(p if os.path.isabs(p)
                                                  else os.path.join(REPO_ROOT, p)))
    return scans, excepts, extras


def target_folders():
    """検査対象フォルダの一覧（scan直下のサブフォルダ−except、＋extra）。"""
    scans, excepts, extras = load_config()
    targets = []
    for root in scans:
        if not os.path.isdir(root):
            report("FAIL", root, "scan対象の親フォルダが見つかりません（design-gate-active.txt を直す）")
            continue
        for name in sorted(os.listdir(root)):
            p = os.path.join(root, name)
            if not os.path.isdir(p) or name in excepts or name.startswith((".", "_tmp_", "__")):
                continue
            targets.append(p)
    for p in extras:
        if not os.path.isdir(p):
            report("FAIL", p, "extra登録の設計作業フォルダが見つかりません（design-gate-local.txt を直す）")
            continue
        targets.append(p)
    return targets


def folder_has_content(folder):
    """票・照合以外のファイルが1つでもあるか（空フォルダは検査しない）。"""
    for cur, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith((".", "__"))]
        for f in files:
            if f.startswith(("着手票", "照合", ".")):
                continue
            return True
    return False


def split_sections(text):
    """見出し（## を含む行）でおおまかに区切り、キーワードで3節を取り出す。"""
    sections = {"仕事": "", "判断": "", "基準": ""}
    current = None
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s", line):
            if "今回の仕事" in line:
                current = "仕事"
                continue
            if "適用する既存判断" in line:
                current = "判断"
                continue
            if "今回の判断基準" in line:
                current = "基準"
                continue
            current = None
            continue
        if current:
            sections[current] += line + "\n"
    return sections


def field_value(body, label):
    """「- ラベル：値」の値を返す（なければNone）。"""
    m = re.search(r"%s[ \t]*[:：][ \t]*(.*)" % re.escape(label), body)
    return m.group(1).strip() if m else None


def resolve_source(raw, ticket_dir):
    """出どころ欄のパスを実ファイルに解決する。見つかれば実パス、なければNone。"""
    s = raw.strip().strip("`").strip()
    s = re.sub(r"[（(][^（）()]*[)）]\s*$", "", s).strip()  # 末尾の（注記）を外す
    if not s:
        return None
    for base in (None, ticket_dir, REPO_ROOT):
        p = s if base is None else os.path.join(base, s)
        if os.path.isfile(p):
            return p
    return None


def check_ticket(path):
    """着手票1枚を検査。通ればTrue。"""
    text = read_text(path)
    sec = split_sections(text)
    ok = True

    # --- 1. 今回の仕事 ---
    if not sec["仕事"].strip():
        report("FAIL", path, "「今回の仕事」の節がない、または空です")
        ok = False
    else:
        making = field_value(sec["仕事"], "作るもの")
        target = field_value(sec["仕事"], "主な対象")
        if not making:
            report("FAIL", path, "「作るもの」が空です")
            ok = False
        if not target or "いずれかを残す" in (target or ""):
            report("FAIL", path, "「主な対象」が未選択です（商品／研修／ゲームと問い）")
            ok = False
        elif not any(w in target for w in ("商品", "研修", "ゲームと問い")):
            report("FAIL", path, "「主な対象」に 商品／研修／ゲームと問い のいずれも含まれていません")
            ok = False

    # --- 2. 適用する既存判断 ---
    body = sec["判断"]
    entries = re.split(r"(?=^- \[判断)", body, flags=re.M)
    entries = [e for e in entries if e.strip().startswith("- [判断")]
    if not entries:
        report("FAIL", path, "「適用する既存判断」に [判断N] の項目が1つもありません")
        ok = False
    for e in entries:
        label_m = re.match(r"- \[(判断[^\]]*)\]", e.strip())
        label = label_m.group(1) if label_m else "判断?"
        src_m = re.search(r"出どころ(（ファイル外）)?[ \t]*[:：][ \t]*(\S.*)", e)
        if not src_m:
            report("FAIL", path, "%s に「出どころ：」がありません" % label)
            ok = False
        elif src_m.group(1):  # 出どころ（ファイル外）：実在確認はしない
            if not src_m.group(2).strip():
                report("FAIL", path, "%s の出どころ（ファイル外）が空です" % label)
                ok = False
        else:
            resolved = resolve_source(src_m.group(2), os.path.dirname(path))
            if not resolved:
                report("FAIL", path, "%s の出どころのファイルが見つかりません：%s"
                       % (label, src_m.group(2).strip()))
                ok = False
        quotes = re.findall(r"^\s*>\s*(\S.*)$", e, flags=re.M)
        quoted = [q for q in quotes if len(q.strip()) >= 8 and "ここに" not in q]
        if not quoted:
            report("FAIL", path, "%s に原文の引用（> で始まる8文字以上の行）がありません" % label)
            ok = False

    # --- 3. 今回の判断基準 ---
    if not sec["基準"].strip():
        report("FAIL", path, "「今回の判断基準」の節がない、または空です")
        ok = False
    else:
        conc = field_value(sec["基準"], "具体化すること")
        keep = field_value(sec["基準"], "足さない・変えないこと")
        if not conc:
            report("FAIL", path, "「具体化すること」が空です")
            ok = False
        if not keep:
            report("FAIL", path, "「足さない・変えないこと」が空です")
            ok = False

    if ok:
        report("OK", path, "着手票：3点が埋まり、引用元の実在を確認（%d件の判断）" % len(entries))
    return ok, [re.match(r"- \[(判断[^\]]*)\]", e.strip()).group(1) for e in entries
                if re.match(r"- \[(判断[^\]]*)\]", e.strip())]


def check_folder(folder, delivery=False, skip_empty=False):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        report("FAIL", folder, "作業フォルダが存在しません")
        return False
    if skip_empty and not folder_has_content(folder):
        return True
    tickets = sorted(glob.glob(os.path.join(folder, "着手票*.md")))
    if not tickets:
        report("FAIL", folder, "着手票がありません（着手票*.md）。設計の仕事は票を書いてから始める")
        return False
    ok = True
    all_labels = []
    for t in tickets:
        t_ok, labels = check_ticket(t)
        ok = ok and t_ok
        all_labels.extend(labels)

    if delivery:
        matches = sorted(glob.glob(os.path.join(folder, "照合*.md")))
        if not matches:
            report("FAIL", folder, "照合がありません（照合*.md）。納品前に、各判断を成果物のどこで使ったかを書く")
            ok = False
        else:
            mtext = "".join(read_text(m) for m in matches)
            for label in all_labels:
                m = re.search(r"\[%s\](.*?)(?=\[判断|\Z)" % re.escape(label), mtext, flags=re.S)
                if not m:
                    report("FAIL", matches[0], "照合に [%s] の項目がありません" % label)
                    ok = False
                elif len(re.sub(r"\s", "", m.group(1))) < 8:
                    report("FAIL", matches[0], "[%s] の使った場所の記述が短すぎます" % label)
                    ok = False
            if ok:
                report("OK", matches[0], "照合：着手票の全判断（%d件）の使用箇所を確認" % len(all_labels))
    return ok


def run_hook():
    """対象フォルダ（scan直下−except、＋extra）を一括検査。空フォルダは飛ばす。"""
    ok = True
    for p in target_folders():
        ok = check_folder(p, skip_empty=True) and ok
    return ok and not FAIL


def gate_applies_to(path):
    """このパスへの書き込みに関門がかかるか。かかるなら対象フォルダを返す。"""
    path = os.path.abspath(path)
    scans, excepts, extras = load_config()
    for root in scans:
        if not path.lower().startswith((root + os.sep).lower()):
            continue
        rel = path[len(root) + 1:]
        parts = rel.split(os.sep)
        if len(parts) < 2:  # drafts直下の単独ファイルはフォルダ単位の票を置けないため対象外
            return None
        if parts[0] in excepts or parts[0].startswith((".", "_tmp_", "__")):
            return None
        return os.path.join(root, parts[0])
    for p in extras:
        if path.lower().startswith((p + os.sep).lower()):
            return p
    return None


def run_pretooluse():
    """書き込み前フック：stdinのJSONからfile_pathを読み、対象フォルダに
    有効な着手票が無ければ exit 2 で書き込みを止める。票・照合自体の書き込みは通す。"""
    try:
        # Windowsのコンソール既定（cp932）に依存せず、常にUTF-8のJSONとして読む
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except Exception:
        return 0  # 読めない入力でセッションを壊さない
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("path") or ""
    if not path:
        return 0
    folder = gate_applies_to(path)
    if not folder:
        return 0
    base = os.path.basename(path)
    if base.startswith(("着手票", "照合")):
        return 0  # 票と照合は書けないと関門が始まらない
    tickets = sorted(glob.glob(os.path.join(folder, "着手票*.md")))
    if not tickets:
        sys.stderr.write(
            "設計の関門：%s には着手票がありません。先に着手票を書いてください"
            "（python scripts/design_gate_check.py --init \"%s\"）。\n" % (folder, folder))
        return 2
    ok = True
    for t in tickets:
        t_ok, _ = check_ticket(t)
        ok = ok and t_ok
    if not ok:
        for line in FAIL:
            sys.stderr.write(line + "\n")
        sys.stderr.write("設計の関門：着手票が未完成です。3点を埋めてから成果物を書いてください。\n")
        return 2
    return 0


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--pretooluse":
        return run_pretooluse()
    if argv[0] == "--init":
        folder = os.path.abspath(argv[1])
        os.makedirs(folder, exist_ok=True)
        import datetime
        name = "着手票_%s.md" % datetime.date.today().strftime("%Y%m%d")
        dest = os.path.join(folder, name)
        if os.path.exists(dest):
            print("[FAIL] %s : 既に存在します（別名で書くか、既存の票を使う）" % dest)
            return 1
        with io.open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(TEMPLATE)
        print("[OK] 着手票の型を書き出しました：%s" % dest)
        if gate_applies_to(os.path.join(folder, "x")) is None:
            # scan対象の外なら extra: として自動登録する（手での追記忘れを防ぐ）。
            # 登録先は git管理しないローカルファイル（公開側に絶対パスを書かない）。
            new_local = not os.path.isfile(CONFIG_LOCAL)
            with io.open(CONFIG_LOCAL, "a", encoding="utf-8", newline="\n") as f:
                if new_local:
                    f.write(CONFIG_LOCAL_HEADER)
                f.write("extra: %s\n" % folder)
            print("[OK] design-gate-local.txt（git管理外）に extra: として登録しました")
        return 0
    if argv[0] == "--hook":
        ok = run_hook()
    elif argv[0] == "--delivery":
        ok = check_folder(argv[1], delivery=True)
    else:
        ok = check_folder(argv[0])
    for line in OK + FAIL:
        print(line)
    print("-" * 40)
    print("設計の関門: FAIL %d件" % len(FAIL))
    print("判定: %s" % ("合格" if ok and not FAIL else "不合格（着手票・照合を直してから進む）"))
    return 0 if ok and not FAIL else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
