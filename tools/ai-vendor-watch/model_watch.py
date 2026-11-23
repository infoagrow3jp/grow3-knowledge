# -*- coding: utf-8 -*-
"""使っているモデルの廃止・互換性の変更だけを見張る（sources.yaml の mode: watch_models の提供元）。

- 使っているモデルの名前は、このPCの設定ファイル（Hermes・Codex など）から毎回読み直す。
  読み方は ~/.ai-vendor-watch/config.json の "model_watch"（公開しない）。
- 公式の廃止予定の表（deprecations.md）と、Codex のモデルのページの廃止の節、API の変更履歴を見る。
- 見つけたものは失敗として返し、観測ハブの即時通知（失敗の通知と同じ経路）に載せる。
  同じものは1回だけ知らせ、廃止日の remind_days 日前にもう一度だけ知らせる（控えは model-watch.json）。
- スキル（gpt-usage）は書き換えない。
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
COMPAT = re.compile(r"deprecat|retir|shut ?down|sunset|breaking|no longer|removed|remov(e|ing) support|"
                    r"will stop|end of life|migrat", re.I)


def in_use(spec: list[dict]) -> tuple[list[dict], list[str]]:
    """config.json の model_watch から、使っているモデルを読む。
    1件：{"name": 呼び出し元, "file": パス, "pattern": 正規表現（value という名前の組）, "default": 見つからないときの扱い}"""
    out, notes = [], []
    for s in spec:
        if s.get("glob"):            # 実行記録から読むとき：いちばん新しいファイル（例：Codex の会話の記録）
            files = sorted(Path(os.path.expandvars(s["root"])).glob(s["glob"]), key=lambda p: p.stat().st_mtime)
            path = files[-1] if files else Path("__none__")
        else:
            path = Path(os.path.expandvars(s["file"]))
        if not path.exists():
            notes.append(f"モデルの見張り：設定ファイルが無い（{s['name']}）")
            continue
        m = re.search(s["pattern"], path.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            out.append({"name": s["name"], "model": m.group("value").strip().strip("\"'")})
        else:
            notes.append(f"モデルの見張り：{s['name']} はモデルを指定していない（{s.get('default', '提供元の推奨モデル')}）")
    return out, notes


def _date(s: str) -> str | None:
    m = re.search(r"([A-Z][a-z]{2})[a-z]*\.? (\d{1,2}),? (20\d\d)", s)
    if not m or m[1].lower() not in MONTHS:
        return None
    return f"{m[3]}-{MONTHS[m[1].lower()]:02d}-{int(m[2]):02d}"


def deprecation_rows(md: str) -> list[dict]:
    """パイプ表の行のうち、先頭の列に日付があるものを取り出す（廃止日・対象の列・代替先）。"""
    rows, header = [], []
    for line in md.splitlines():
        if not line.startswith("|"):
            header = [] if not line.strip() else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if not header and not _date(cells[0]):
            header = [c.lower() for c in cells]
            continue
        day = _date(cells[0])
        if not day:
            continue
        rep = ""
        for i, h in enumerate(header):
            if "replacement" in h and i < len(cells):
                rep = cells[i]
        rows.append({"shutdown": day, "affected": cells[1] if len(cells) > 1 else "", "replacement": rep,
                     "raw": line.strip()})
    return rows


def _names(cell: str) -> set[str]:
    return {n.strip().lower() for n in re.findall(r"`([^`]+)`", cell)} or {cell.strip().lower()}


def check(cfg_vendor: dict, models: list[dict], get, today: str, sent: dict) -> tuple[list[str], list[str]]:
    """知らせること（failures）と記録（notes）を返す。sent は控え（書き換える）。"""
    alerts, notes = [], []
    remind = int(cfg_vendor.get("remind_days", 30))
    t = dt.date.fromisoformat(today)
    names = {m["model"].lower(): m for m in models}

    # 1) 廃止予定の表
    try:
        rows = deprecation_rows(get(cfg_vendor["deprecations"]))
        if not rows:
            raise RuntimeError("表の行が1つも読めない（ページの形が変わった可能性）")
    except Exception as e:
        return [f"モデルの見張り：廃止予定のページを読めなかった（{e}）"[:300]], notes
    for r in rows:
        hit = names.keys() & _names(r["affected"])
        for n in hit:
            m = names[n]
            key = f"dep|{n}|{r['shutdown']}"
            left = (dt.date.fromisoformat(r["shutdown"]) - t).days
            msg = (f"【モデルの廃止】{m['name']} が使っている {m['model']} は {r['shutdown']} に廃止予定"
                   f"（あと{left}日）。代替先：{r['replacement'] or '記載なし'}。呼び出しの設定を切り替える")
            if key not in sent:
                sent[key] = today
                alerts.append(msg)
            elif left <= remind and f"{key}|remind" not in sent:
                sent[f"{key}|remind"] = today
                alerts.append(msg)
    # 2) Codex のモデルのページの廃止の節
    try:
        page = get(cfg_vendor["codex_models"])
        sec = re.search(r"^#+ .*deprecat.*$(.*?)(?=^#{1,2} |\Z)", page, re.I | re.M | re.S)
        text = (sec[1] if sec else "").lower()
        for n, m in names.items():
            if n in text:
                key = f"codex|{n}"
                if key not in sent:
                    sent[key] = today
                    alerts.append(f"【モデルの廃止】{m['name']} が使っている {m['model']} が、Codex のモデルのページの"
                                  "廃止の節に出ている。ページで日付と代替先を確かめる")
    except Exception as e:
        notes.append(f"モデルの見張り：Codex のモデルのページを読めなかった（{e}）"[:200])
    # 3) API の変更履歴：使っているモデルの名前と、廃止・互換性の語が同じ段落にあるもの
    #    そのモデルを初めて見張る日は、すでに載っている記述を控えるだけで知らせない。
    try:
        log = get(cfg_vendor["changelog"])
        for n, m in names.items():
            first = f"chg-init|{n}" not in sent
            for para in re.split(r"\n\s*\n", log):
                if n in para.lower() and COMPAT.search(para):
                    key = f"chg|{n}|" + hashlib.sha1(" ".join(para.split()).encode()).hexdigest()[:12]
                    if key in sent:
                        continue
                    sent[key] = "baseline" if first else today
                    if not first:
                        alerts.append(f"【互換性の変更】{m['name']} が使っている {m['model']} について、API の変更履歴に"
                                      f"廃止・互換性の記述がある：{' '.join(para.split())[:160]}")
            sent[f"chg-init|{n}"] = sent.get(f"chg-init|{n}", today)
    except Exception as e:
        notes.append(f"モデルの見張り：API の変更履歴を読めなかった（{e}）"[:200])
    return alerts, notes


def load_sent(home: Path) -> dict:
    p = home / "model-watch.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_sent(home: Path, sent: dict) -> None:
    (home / "model-watch.json").write_text(json.dumps(sent, ensure_ascii=False, indent=1), encoding="utf-8")
