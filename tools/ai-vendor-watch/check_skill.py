#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使い方スキル（claude-usage / gpt-usage / gemini-usage）の機械検査。全スキル共通。

検査する5点:
  1. SKILL.md が60行以内
  2. SKILL.md と details.md に、出典IDのない規則行がない
  3. 出典IDが、ログ（state/items.json）か references/sources.md に存在する
  4. SKILL.md に URL・「以前は」・「最近の変更」の節がない
  5. superseded.md へ移した行に日付がある

使い方:
  py -3 -X utf8 check_skill.py                 # 3つとも検査
  py -3 -X utf8 check_skill.py claude-usage    # 1つだけ
終了コード: 0=合格 / 1=不合格
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SKILLS = ["claude-usage", "gpt-usage", "gemini-usage"]
MAX_LINES = 60
ID_RE = re.compile(r"\b([AOG]-\d{4}-\d{2}-\d{2}-\d+|D-[a-z0-9][a-z0-9-]*)")
CITE_RE = re.compile(r"［([^］]+)］")
POINTER = "詳細は references/details.md"


def body_lines(text: str):
    """(行番号, 行) のうち、規則行として検査する行だけを返す。"""
    out, in_fm, in_code = [], False, False
    lines = text.splitlines()
    for no, line in enumerate(lines, 1):
        s = line.strip()
        if no == 1 and s == "---":
            in_fm = True
            continue
        if in_fm:
            if s == "---":
                in_fm = False
            continue
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not s or s.startswith("#"):
            continue
        if re.fullmatch(r"\|?[\s:|-]+\|?", s):          # 表の区切り行
            continue
        if s.endswith(("：", ":")) and not s.startswith("|"):  # 導入行（下の行に出典IDが付く）
            continue
        if s.startswith(POINTER):
            continue
        out.append((no, line))
    return out


def cited_ids(line: str) -> list[str]:
    ids = []
    for grp in CITE_RE.findall(line):
        ids += ID_RE.findall(grp)
    return ids


def known_ids(skill_dir: Path) -> set[str]:
    ids = set()
    src = skill_dir / "references" / "sources.md"
    if src.exists():
        ids |= set(re.findall(r"\bD-[a-z0-9][a-z0-9-]*", src.read_text(encoding="utf-8")))
    state = HERE / "state" / "items.json"
    if state.exists():
        ids |= set(json.loads(state.read_text(encoding="utf-8")).get("items", {}))
    return ids


def check(skill: str) -> list[str]:
    d = REPO / ".claude" / "skills" / skill
    errs = []
    skill_md = d / "SKILL.md"
    details = d / "references" / "details.md"
    superseded = d / "references" / "superseded.md"
    for p in (skill_md, details, superseded, d / "references" / "sources.md"):
        if not p.exists():
            errs.append(f"ファイルがない: {p.relative_to(REPO)}")
    if errs:
        return errs
    known = known_ids(d)

    text = skill_md.read_text(encoding="utf-8")
    n = len(text.splitlines())
    if n > MAX_LINES:
        errs.append(f"[1] SKILL.md が{n}行（上限{MAX_LINES}行）")
    if POINTER not in text.strip().splitlines()[-1]:
        errs.append("[1] SKILL.md の最後の行が「詳細は references/details.md、…」になっていない")

    for name, path in (("SKILL.md", skill_md), ("details.md", details)):
        for no, line in body_lines(path.read_text(encoding="utf-8")):
            ids = cited_ids(line)
            if not ids:
                errs.append(f"[2] {name}:{no} 出典IDがない: {line.strip()[:60]}")
            for i in ids:
                if i not in known:
                    errs.append(f"[3] {name}:{no} 出典ID {i} がログにも sources.md にもない")

    for no, line in enumerate(text.splitlines(), 1):
        if re.search(r"https?://", line):
            errs.append(f"[4] SKILL.md:{no} URLがある")
        if "以前は" in line:
            errs.append(f"[4] SKILL.md:{no} 「以前は」がある")
        if line.lstrip().startswith("#") and "最近の変更" in line:
            errs.append(f"[4] SKILL.md:{no} 「最近の変更」の節がある")

    in_code = False
    for no, line in enumerate(superseded.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
        if in_code or not s.startswith(("|", "-")) or re.fullmatch(r"\|?[\s:|-]+\|?", s):
            continue
        if s.startswith("|") and "置き換わった日" in s:   # 表の見出し行
            continue
        if not re.search(r"20\d\d-\d\d-\d\d", s):
            errs.append(f"[5] superseded.md:{no} 置き換わった日がない: {s[:60]}")
    return errs


def main() -> int:
    targets = sys.argv[1:] or SKILLS
    bad = False
    for skill in targets:
        errs = check(skill)
        if errs:
            bad = True
            print(f"不合格 {skill}（{len(errs)}件）")
            for e in errs:
                print("  " + e)
        else:
            print(f"合格 {skill}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
