#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公式の更新情報を集めて、スキルごとの日付順ログと state/items.json に追記する。

LLMは使わない。提供元ごとの違いは sources.yaml に寄せる。
書くのは公式の見出し・バージョン・日付・出典まで（要約は run.py が判定結果から付ける）。

使い方:
  py -3 -X utf8 collect.py                # 全ソースを取得して追記
  py -3 -X utf8 collect.py --only gemini-api --dry-run
  py -3 -X utf8 collect.py --save-fixtures DIR   # 取得データを保存
  py -3 -X utf8 collect.py --fixtures DIR        # 保存した取得データで動かす（通信しない）
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
STATE_PATH = HERE / "state" / "items.json"
SOURCES_PATH = HERE / "sources.yaml"
PRIVATE_DIR = Path(os.environ.get("AI_VENDOR_WATCH_HOME", Path.home() / ".ai-vendor-watch"))
UA = "Mozilla/5.0 (compatible; ai-vendor-watch/1.0)"

ST_JUDGE = "判定待ち"
ST_APPLY = "反映待ち"
ST_DONE = "反映済み"
ST_SKIP = "対象外"
ST_HOLD = "確認保留"

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS["sept"] = 9


# ---------- 取得 ----------

class Fetcher:
    def __init__(self, fixtures: Path | None, save: Path | None):
        self.fixtures, self.save = fixtures, save
        self.cache: dict[str, str] = {}

    @staticmethod
    def _name(url: str) -> str:
        return hashlib.sha1(url.encode()).hexdigest()[:16] + ".txt"

    def get(self, url: str) -> str:
        if url in self.cache:
            return self.cache[url]
        if self.fixtures:
            p = self.fixtures / self._name(url)
            if not p.exists():
                raise RuntimeError(f"保存データなし: {url}")
            text = p.read_text(encoding="utf-8")
        else:
            text = self._http(url)
            if self.save:
                self.save.mkdir(parents=True, exist_ok=True)
                (self.save / self._name(url)).write_text(text, encoding="utf-8")
        self.cache[url] = text
        return text

    @staticmethod
    def _http(url: str) -> str:
        last = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    return r.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as e:
                last = e
                if e.code in (401, 403, 404, 410):
                    break
            except Exception as e:  # 通信エラーは少し待って再試行
                last = e
            time.sleep(3 * (attempt + 1))
        raise RuntimeError(f"取得失敗: {url} ({last})")


# ---------- 小道具 ----------

def strip_html(s: str) -> str:
    s = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", s, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def strip_md(s: str) -> str:
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\{%.*?%\}", "", s)
    s = re.sub(r"[*_`]+", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def cut(s: str, n: int = 90) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def parse_date(text: str, year: int | None = None) -> str | None:
    """日付の文字列をYYYY-MM-DDにする。読み取れなければNone（推測しない）。"""
    t = text.strip()
    m = re.search(r"(20\d\d)[-./](\d{1,2})[-./](\d{1,2})", t)
    if m:
        return _ymd(int(m[1]), int(m[2]), int(m[3]))
    m = re.search(r"([A-Za-z]{3,9})\.? (\d{1,2})(?:st|nd|rd|th)?,? (20\d\d)", t)
    if m and m[1].lower() in MONTHS:
        return _ymd(int(m[3]), MONTHS[m[1].lower()], int(m[2]))
    m = re.search(r"([A-Za-z]{3,9})\.? (\d{1,2})\b", t)
    if m and m[1].lower() in MONTHS and year:
        return _ymd(year, MONTHS[m[1].lower()], int(m[2]))
    return None


def _ymd(y: int, m: int, d: int) -> str | None:
    try:
        return dt.date(y, m, d).isoformat()
    except ValueError:
        return None


def rfc_date(s: str) -> str | None:
    try:
        return parsedate_to_datetime(s.strip()).date().isoformat()
    except Exception:
        return parse_date(s)


# リポジトリの出荷前検品が止める語（検品の対象は tools 配下）。公式の原文に含まれていても
# 状態ファイルに残らないよう、保存前に字面だけ崩す。
_STOP = [("TO" + "DO", "todo"), ("XX" + "X", "xxx"), ("★" + "★", "★ ★"), ("未" + "確定", "未 確定"),
         ("【要" + "確認】", "〔要 確認〕"), ("仮" + "置き", "仮 置き")]


def safe(s: str) -> str:
    for a, b in _STOP:
        s = s.replace(a, b)
    return s


def mk(title, published, url, key=None, excerpt=""):
    return {"title": safe(cut(re.sub(r"[｜|]", "/", title), 100)), "published": published,
            "url": url, "key": key, "excerpt": safe(excerpt[:2500])}


# ---------- 解析（ソースの種類ごと） ----------

def p_md_dated(src, f):
    """日付の見出しの下に項目が並ぶMarkdown。item: bullets / bold / entry / subheads"""
    text = f.get(src["url"])
    page = src.get("page_url", src["url"])
    head_re = re.compile(src["heading"])
    year_re = re.compile(src["year_heading"]) if src.get("year_heading") else None
    mode = src.get("item", "bullets")
    out, year, cur, buf = [], None, None, []

    def flush():
        if cur is None:
            return
        date, anchor = cur
        url = page + (("#" + anchor) if anchor else "")
        body = "\n".join(buf).strip()
        if mode == "entry":
            paras = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
            tags = strip_md(paras[0]) if paras else ""
            main = strip_md(paras[1]) if len(paras) > 1 else tags
            out.append(mk(main, date, url, excerpt=strip_md(body)))
            return
        if mode == "bold":
            parts = re.split(r"^\*\*(.+?)\*\*\s*$", body, flags=re.M)
            if len(parts) >= 3:
                for i in range(1, len(parts), 2):
                    out.append(mk(strip_md(parts[i]), date, url,
                                  excerpt=strip_md(parts[i] + ". " + parts[i + 1])))
                return
        if mode == "subheads":
            parts = re.split(r"^#{3,4} (.+)$", body, flags=re.M)
            for i in range(1, len(parts), 2):
                out.append(mk(strip_md(parts[i]), date, url, excerpt=strip_md(parts[i + 1])))
            return
        items = re.split(r"^[-*] ", body, flags=re.M)
        if len(items) > 1:
            for it in items[1:]:
                t = strip_md(it)
                if t:
                    out.append(mk(t, date, url, excerpt=t))
        elif strip_md(body):
            out.append(mk(strip_md(body), date, url, excerpt=strip_md(body)))

    for line in text.splitlines():
        if year_re:
            ym = year_re.match(line)
            if ym:
                flush(); cur, buf = None, []
                year = int(ym.group("year"))
                continue
        hm = head_re.match(line)
        if hm:
            flush(); buf = []
            gd = hm.groupdict()
            date = parse_date(gd["date"], year) if gd.get("date") else None
            cur = (date, gd.get("anchor"))
            if gd.get("period"):
                cur = (None, None)
                buf.append("")  # 週単位の見出しは公開日を決めない
                src.setdefault("_period", {})[len(out)] = strip_md(gd["period"])
            continue
        if cur is not None:
            buf.append(line)
    flush()
    return out


def p_md_weekly(src, f):
    """週単位の見出し（例: November 9–13, 2026）の下に ### 項目 が並ぶ。公開日は決めない。"""
    text = f.get(src["url"])
    out, period, end, link = [], None, None, None
    for line in text.splitlines():
        m = re.match(r"^## \[?([^\]\n]+?)\]?(?:\((\S+?)\))?\s*$", line)
        if m:
            period, link = m[1].strip(), m[2]
            dm = re.search(r"([A-Za-z]+) (\d{1,2})(?:\s*[–-]\s*(?:([A-Za-z]+) )?(\d{1,2}))?, (20\d\d)", period)
            end = None
            if dm:
                mon = (dm[3] or dm[1]).lower()
                end = _ymd(int(dm[5]), MONTHS.get(mon, 0) or 1, int(dm[4] or dm[2])) if mon in MONTHS else None
            continue
        m = re.match(r"^### \[?([^\]\n]+?)\]?(?:\((\S+?)\))?\s*$", line)
        if m and period:
            it = mk(f"{strip_md(m[1])}〔週: {period}〕", None, m[2] or link or src["url"],
                    key=f"{period}|{strip_md(m[1])}")
            it["_filter_date"] = end
            out.append(it)
    return out


def p_claude_code(src, f):
    text = f.get(src["url"])
    times = {}
    try:
        times = json.loads(f.get(src["npm"])).get("time", {})
    except Exception as e:
        src["_warn"] = f"npmの公開日を取得できず（公開日は不明扱い）: {e}"
    out = []
    parts = re.split(r"^## (\d+\.\d+\.\d+\S*)\s*$", text, flags=re.M)
    for i in range(1, len(parts), 2):
        ver, body = parts[i], parts[i + 1]
        date = times[ver][:10] if ver in times else None
        out.append(mk(f"{src['product']} {ver}", date, src.get("page_url", src["url"]),
                      key=ver, excerpt=strip_md(body)))
    return out


def p_codex_html(src, f):
    text = f.get(src["url"])
    marks = list(re.finditer(r'<li[^>]*\bid="((?:github-release|codex)-[^"]+)"[^>]*>', text))
    out = []
    for i, m in enumerate(marks):
        seg = text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else m.end() + 200000]
        tm = re.search(r"<time[^>]*>([^<]*)</time>", seg)
        hm = re.search(r"<h3[^>]*>(.*?)</h3>", seg, re.S)
        if not hm:
            continue
        date = parse_date(tm[1]) if tm else None
        out.append(mk(strip_html(hm[1]), date, f"{src['url']}#{m[1]}", key=m[1],
                      excerpt=strip_html(seg[seg.find('</h3>'):][:6000])))
    if not out:
        raise RuntimeError("項目を1件も読み取れない（ページの構造が変わった可能性）")
    return out


def p_html_dated(src, f):
    """HTMLの一覧。pattern は date / title / href（任意）の名前付きグループを持つ正規表現。"""
    text = f.get(src["url"])
    base = src.get("base", "")
    out, seen = [], set()
    for m in re.finditer(src["pattern"], text, re.S):
        gd = m.groupdict()
        title = strip_html(gd["title"])
        href = html.unescape(gd.get("href") or "")
        url = (base + href) if href.startswith("/") else (href or src["url"])
        if not title or (title, url) in seen:
            continue
        seen.add((title, url))
        out.append(mk(title, parse_date(strip_html(gd["date"])), url,
                      key=url if href else None, excerpt=title))
    if not out:
        raise RuntimeError("項目を1件も読み取れない（ページの構造が変わった可能性）")
    return out


def p_html_cards(src, f):
    """日付の見出し（card_date）ごとに、小見出し（card_title）が並ぶHTML。"""
    text = f.get(src["url"])
    marks = list(re.finditer(src["card_date"], text, re.S))
    out = []
    for i, m in enumerate(marks):
        date = parse_date(strip_html(m.group("date")))
        seg = text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        tms = list(re.finditer(src["card_title"], seg, re.S))
        for j, t in enumerate(tms):
            body = seg[t.end(): tms[j + 1].start() if j + 1 < len(tms) else len(seg)]
            out.append(mk(strip_html(t.group("title")), date, src["url"],
                          excerpt=strip_html(t.group("title") + ". " + body[:4000])))
    if not out:
        raise RuntimeError("項目を1件も読み取れない（ページの構造が変わった可能性）")
    return out


def p_rss(src, f):
    text = f.get(src["url"])
    out = []
    for m in re.finditer(r"<item\b.*?</item>|<entry\b.*?</entry>", text, re.S):
        blk = m.group(0)

        def tag(name):
            t = re.search(rf"<{name}\b[^>]*>(.*?)</{name}>", blk, re.S)
            return re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", t[1], flags=re.S).strip() if t else ""
        link = tag("link") or (re.search(r'<link[^>]*href="([^"]+)"', blk) or [None, ""])[1]
        raw = tag("pubDate") or tag("published") or tag("updated")
        title = strip_html(tag("title"))
        if title:
            out.append(mk(title, rfc_date(raw) if raw else None, link or src["url"],
                          key=link or None, excerpt=strip_html(tag("description"))[:600]))
    if not out:
        raise RuntimeError("項目を1件も読み取れない")
    return out


def p_github_releases(src, f):
    out, since = [], src["_since"]
    skip = re.compile(src.get("skip_tag", r"nightly|preview"), re.I)
    for page in range(1, 11):
        rels = json.loads(f.get(f"https://api.github.com/repos/{src['repo']}/releases?per_page=100&page={page}"))
        if not rels:
            break
        for r in rels:
            if r.get("prerelease") or r.get("draft") or skip.search(r.get("tag_name", "")):
                continue
            date = (r.get("published_at") or "")[:10] or None
            out.append(mk(f"{src['product']} {r['tag_name']}", date, r["html_url"],
                          key=r["tag_name"], excerpt=strip_md(r.get("body") or "")))
        last = (rels[-1].get("published_at") or "")[:10]
        if last and last < since:
            break
    return out


PARSERS = {
    "md_dated": p_md_dated, "md_weekly": p_md_weekly, "claude_code_changelog": p_claude_code,
    "codex_html": p_codex_html, "html_dated": p_html_dated, "html_cards": p_html_cards,
    "rss": p_rss, "github_releases": p_github_releases,
}


# ---------- 状態とログ ----------

def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"version": 1, "sources_seen": {}, "skipped_keys": [], "docs": {}, "focus": {}, "items": {}}


def save_state(state: dict) -> None:
    """1項目1行で書く（差分を読みやすくするため）。"""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    d = lambda o: json.dumps(o, ensure_ascii=False, sort_keys=True)
    lines = ["{", f' "version": {state.get("version", 1)},',
             f' "sources_seen": {d(state.get("sources_seen", {}))},',
             f' "skipped_keys": {d(sorted(state.get("skipped_keys", [])))},', ' "docs": {']
    docs = state.get("docs", {})
    lines += [f'  {d(k)}: {d(docs[k])}' + ("," if i < len(docs) - 1 else "")
              for i, k in enumerate(sorted(docs))]
    lines += [" },", f' "focus": {d(state.get("focus", {}))},', ' "items": {']
    items = state.get("items", {})
    keys = sorted(items, key=id_sort_key, reverse=True)
    lines += [f'  {d(k)}: {d(items[k])}' + ("," if i < len(keys) - 1 else "")
              for i, k in enumerate(keys)]
    lines += [" }", "}"]
    STATE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def id_sort_key(item_id: str):
    m = re.match(r"([A-Z])-(\d{4}-\d{2}-\d{2})-(\d+)$", item_id)
    return (m[2], m[1], int(m[3])) if m else ("", "", 0)


def next_id(state: dict, prefix: str, date: str, counters: dict) -> str:
    k = (prefix, date)
    if k not in counters:
        counters[k] = max([int(i.rsplit("-", 1)[1]) for i in state["items"]
                           if i.startswith(f"{prefix}-{date}-")] or [0])
    counters[k] += 1
    return f"{prefix}-{date}-{counters[k]}"


def provisional(src: dict, cfg: dict, title: str, excerpt: str) -> tuple[str, str]:
    """仮判定。決めきれないものは対象外にせず判定待ちにする。"""
    text = f"{title} {excerpt}"
    core = re.search(cfg["judge"]["core"], text, re.I)
    if src.get("default", ST_JUDGE) == ST_SKIP:
        return (ST_JUDGE, "") if core else (ST_SKIP, "仮判定：呼び方に関わる語を含まない")
    if not core and re.search(cfg["judge"]["exclude"], text, re.I):
        return ST_SKIP, "仮判定：料金・地域展開・管理機能だけの更新"
    return ST_JUDGE, ""


def entry_text(item_id: str, it: dict, label: str) -> str:
    date = it["published"] or it["detected"]
    pub = it["published"] or "不明"
    return (f"### {date}｜{label}｜{it['title']}\n- ID：{item_id}\n"
            f"- 公開日：{pub}／検知日：{it['detected']}\n- 出典：{it['url']}\n")


def log_path(skill: str, month: str) -> Path:
    return REPO / ".claude" / "skills" / skill / "references" / "changelog" / f"{month}.md"


def read_log(path: Path) -> tuple[str, dict[str, str]]:
    if not path.exists():
        return "", {}
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^(?=### )", text)
    entries = {}
    for blk in parts[1:]:
        m = re.search(r"^- ID：(\S+)", blk, re.M)
        if m:
            entries[m[1]] = blk.rstrip() + "\n"
    return parts[0], entries


def write_log(path: Path, skill: str, month: str, entries: dict[str, str]) -> None:
    head = f"# {skill} 変更ログ {month}\n\n公式の更新を新しい順に記録する（自動追記）。\n\n"
    order = sorted(entries, key=id_sort_key, reverse=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head + "\n".join(entries[i] for i in order), encoding="utf-8", newline="\n")


def append_logs(new: dict[str, dict], cfg: dict) -> None:
    by_file: dict[tuple[str, str], dict[str, str]] = {}
    labels = {s["id"]: s["label"] for s in cfg["sources"]}
    for item_id, it in new.items():
        skill = cfg["vendors"][it["vendor"]]["skill"]
        month = id_sort_key(item_id)[0][:7]
        by_file.setdefault((skill, month), {})[item_id] = entry_text(
            item_id, it, labels.get(it["source"], it["source"]))
    for (skill, month), ents in by_file.items():
        path = log_path(skill, month)
        _, cur = read_log(path)
        for k, v in ents.items():
            cur.setdefault(k, v)  # 同じIDは二重に書かない
        write_log(path, skill, month, cur)


def set_summary(item_id: str, skill: str, summary: str) -> bool:
    """ログの該当項目に要約の行を付ける（すでにあれば置き換える）。"""
    path = log_path(skill, id_sort_key(item_id)[0][:7])
    _, cur = read_log(path)
    if item_id not in cur:
        return False
    blk = re.sub(r"(?m)^- 要約：.*\n?", "", cur[item_id]).rstrip() + "\n"
    cur[item_id] = blk + f"- 要約：{' '.join(summary.split())}\n"
    write_log(path, skill, id_sort_key(item_id)[0][:7], cur)
    return True


# ---------- ドキュメント（ページ一覧と重点ページ） ----------

def focus_pages(cfg) -> list[dict]:
    """重点ページの一覧。正は各スキルの references/sources.md の表（根拠ID｜ページ｜URL｜確認日）。
    sources.yaml の focus_pages に書いたものも足す。"""
    pages = list(cfg.get("focus_pages") or [])
    seen = {p["id"] for p in pages}
    for vendor, v in cfg["vendors"].items():
        path = REPO / ".claude" / "skills" / v["skill"] / "references" / "sources.md"
        if not path.exists():
            continue
        for m in re.finditer(r"(?m)^\|\s*(D-[a-z0-9][a-z0-9-]*)\s*\|\s*([^|]+?)\s*\|\s*(https?://\S+?)\s*\|",
                             path.read_text(encoding="utf-8")):
            if m[1] not in seen:
                seen.add(m[1])
                pages.append({"id": m[1], "vendor": vendor, "label": m[2], "url": m[3]})
    return pages


def active(cfg, vendor: str) -> bool:
    """sources.yaml の vendors.<提供元>.mode が active（既定）のときだけ、定期の収集と自動更新をする。"""
    return cfg["vendors"][vendor].get("mode", "active") == "active"


def collect_docs(cfg, state, f, today, add, failures):
    for idx in cfg.get("doc_indexes", []):
        if not active(cfg, idx["vendor"]):
            continue
        try:
            urls = set()
            for u in idx["urls"]:
                urls |= set(re.findall(r"\]\((https?://[^)\s]+)\)", f.get(u)))
            if len(urls) < idx.get("min_pages", 5):
                raise RuntimeError(f"ページ一覧が少なすぎる（{len(urls)}件）")
        except Exception as e:
            failures.append({"source": idx["id"], "error": str(e)})
            continue
        prev = state["docs"].get(idx["id"])
        if prev is not None:
            old = set(prev)
            for u in sorted(urls - old):
                add(idx, mk(f"ページの新規：{u.split('/', 3)[-1]}", None, u, key="add|" + u, excerpt=u))
            for u in sorted(old - urls):
                add(idx, mk(f"ページの削除：{u.split('/', 3)[-1]}", None, u, key=f"del|{today}|{u}", excerpt=u))
        state["docs"][idx["id"]] = sorted(urls)

    cache = PRIVATE_DIR / "cache" / "focus"
    for pg in focus_pages(cfg):
        if not active(cfg, pg["vendor"]):
            continue
        try:
            text = "\n".join(l.rstrip() for l in f.get(pg["url"]).splitlines()).strip()
            if len(text) < 200:
                raise RuntimeError("本文が短すぎる")
        except Exception as e:
            failures.append({"source": pg["id"], "error": str(e)})
            continue
        digest = hashlib.sha256(text.encode()).hexdigest()[:16]
        prev = state["focus"].get(pg["id"])
        cpath = cache / (pg["id"] + ".md")
        if prev and prev["hash"] != digest:
            diff = ""
            if cpath.exists():
                old = cpath.read_text(encoding="utf-8").splitlines()
                diff = "\n".join(l for l in difflib.unified_diff(old, text.splitlines(), lineterm="", n=1)
                                 if l[:1] in "+-" and l[:3] not in ("+++", "---"))
            src = dict(pg, label="重点ページ", default=ST_JUDGE, _focus=True)
            add(src, mk(f"本文の変更：{pg['label']}（根拠ID {pg['id']}）", None, pg["url"],
                        key=f"focus|{pg['id']}|{digest}", excerpt=diff or "（差分の控えなし。出典を読んで判定する）"))
        if not prev or prev["hash"] != digest:
            state["focus"][pg["id"]] = {"hash": digest, "checked": today}
        try:
            cache.mkdir(parents=True, exist_ok=True)
            cpath.write_text(text, encoding="utf-8")
        except OSError:
            pass


# ---------- 本体 ----------

def run(args) -> dict:
    cfg = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8"))
    state = load_state()
    today = args.today or dt.date.today().isoformat()
    since = cfg["since"]
    f = Fetcher(Path(args.fixtures) if args.fixtures else None,
                Path(args.save_fixtures) if args.save_fixtures else None)
    known = {v["key"] for v in state["items"].values()} | set(state.setdefault("skipped_keys", []))
    counters, new, failures, counts = {}, {}, [], {}

    def keyof(src, it):
        return hashlib.sha1(f"{src['id']}|{it['key'] or (str(it['published']) + '|' + it['title'])}"
                            .encode()).hexdigest()[:16]

    def add(src, it, baseline=False):
        key = keyof(src, it)
        if key in known:
            return
        known.add(key)
        vendor = src["vendor"]
        item_id = next_id(state, cfg["vendors"][vendor]["prefix"], it["published"] or today, counters)
        if baseline:
            st, reason = ST_SKIP, "初回取り込み"
        else:
            st, reason = provisional(src, cfg, it["title"], it["excerpt"])
        rec = {"key": key, "vendor": vendor, "source": src["id"], "title": it["title"],
               "published": it["published"], "detected": today, "url": it["url"], "state": st}
        if reason:
            rec["reason"] = reason
        if st == ST_JUDGE and it["excerpt"]:
            rec["excerpt"] = it["excerpt"]
        state["items"][item_id] = rec
        new[item_id] = rec
        counts[src["id"]] = counts.get(src["id"], 0) + 1

    for src in cfg["sources"]:
        if args.only and src["id"] not in args.only:
            continue
        if not active(cfg, src["vendor"]):      # 休止中・モデルの見張りだけの提供元は定期の収集をしない
            continue
        src["_since"] = since
        try:
            items = PARSERS[src["type"]](src, f)
        except Exception as e:
            failures.append({"source": src["id"], "error": str(e)})
            continue
        if src.get("_warn"):
            failures.append({"source": src["id"], "error": src["_warn"], "partial": True})
        first = src["id"] not in state["sources_seen"]
        # 古い順に採番する（同じ日の中で、先に出たものが小さい番号になる）
        for it in reversed(items):
            fdate = it.pop("_filter_date", None) or it["published"]
            if fdate and fdate < since:
                continue
            if fdate is None and first:
                # 初回で日付のない項目は、いつのものか分からないので取り込まない（次回以降に新着と数えないよう控える）
                k = keyof(src, it)
                if k not in known:
                    known.add(k)
                    state["skipped_keys"].append(k)
                continue
            if fdate and fdate > today:
                it["published"] = it["published"] if it["published"] and it["published"] <= today else None
            add(src, it, baseline=first)
        state["sources_seen"].setdefault(src["id"], today)

    if not args.only:
        collect_docs(cfg, state, f, today, add, failures)

    result = {"today": today, "new": len(new), "by_source": counts, "failures": failures,
              "pending": sum(1 for v in state["items"].values() if v["state"] in (ST_JUDGE, ST_APPLY))}
    if not args.dry_run:
        append_logs(new, cfg)
        save_state(state)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fixtures")
    ap.add_argument("--save-fixtures")
    ap.add_argument("--today")
    args = ap.parse_args()
    res = run(args)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
