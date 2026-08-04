#!/usr/bin/env python3
"""grow3-knowledge build / check tool (Phase 1).

工程（実装仕様書 E）:
    本文hash確認 → metadata staleness確認 → 必要なら再生成 → INDEX再生成
    → リンク検査 → test

意図的に持たない機能（実装仕様書の却下事項）:
    - Summary本文の意味的変化量（semantic drift）の検知
    - embedding / LLMによる意味比較 / Vector DB / RAG
    - confidence分類やmulti-domain fallbackを持つ本格Router

外部依存を持たない（Python 3 標準ライブラリのみ）。frontmatterのYAMLは
汎用YAMLではなく、下記 parse_frontmatter が受理する厳格なサブセットのみを
扱う。サブセット外の記法は黙って解釈せずERRORにする。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "scripts" / "knowledge-structure-snapshot.json"
FRICTION_LOG_PATH = REPO_ROOT / "logs" / "search-friction.yaml"

SNAPSHOT_VERSION = "0.1"
HASH_PREFIX = "sha256:"
REGENERATION_WINDOW_DAYS = 30

# ---------------------------------------------------------------------------
# 対象範囲（2026-08-04 確定：正本OSファイル層のみ）
# ---------------------------------------------------------------------------

# frontmatter必須（実装仕様書 C が名指しした5本）。ここを善意で広げない。
MANAGED_FILES = (
    "grow3-frameworks.md",
    "grow3-training-design-os.md",
    "grow3-hr-system-design-os.md",
    "grow3-marketing-os.md",
    "grow3-blog-concept-map.md",
)

# INDEX生成とリンク検査の対象層。層 = (INDEX出力先, 見出し, 収集対象glob)
INDEX_LAYERS = (
    ("INDEX.md", "正本OS層（リポジトリ直下）", "*.md"),
    ("docs/INDEX.md", "設計メモ・定義書層（docs/）", "docs/*.md"),
)

# INDEXにも リンク検査にも載せないファイル
INDEX_EXCLUDE = {"INDEX.md", "docs/INDEX.md", "CLAUDE.md", "DECISIONS.md"}

ALLOWED_TYPES = {"os", "map"}
ALLOWED_STATUSES = {"draft", "canonical"}
ALLOWED_DOMAINS = {"frameworks", "training", "hr", "marketing", "blog"}

REQUIRED_FRONTMATTER_KEYS = ("id", "type", "status", "domain", "metadata_source_hash")
OPTIONAL_FRONTMATTER_KEYS = ("related",)

# search-friction ログの記録タイプ（当面この3種から増やさない）
ALLOWED_FRICTION_TYPES = {"canonical_not_found", "multi_domain", "fallback_used"}


class BuildError(Exception):
    """検査を続行できない構造的な誤り。"""


# ---------------------------------------------------------------------------
# frontmatter 抽出（DEC-012 の frontmatter抽出契約に準拠）
# ---------------------------------------------------------------------------

def split_frontmatter(text: str, *, where: str) -> tuple[str | None, str]:
    """(frontmatter本文, Markdown本文) を返す。frontmatterが無ければ (None, 全文)。

    DEC-012の抽出契約をそのまま適用する:
      - UTF-8テキストとして扱う
      - 1行目は単独の `---`
      - BOM・先頭空行・先頭コメントは許可しない
      - 次に現れる単独行の `---` を終了区切りとする
      - 終了区切り欠落はERROR
      - 本文中に後から現れる `---` はMarkdown本文として扱う
    """
    if text.startswith("﻿"):
        raise BuildError(f"{where}: BOMは許可しない")

    normalized = normalize_newlines(text)
    lines = normalized.split("\n")

    if not lines or lines[0] != "---":
        return None, normalized

    for idx in range(1, len(lines)):
        if lines[idx] == "---":
            fm = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1 :])
            if not fm.strip():
                raise BuildError(f"{where}: 空のfrontmatterはINVALID")
            return fm, body

    raise BuildError(f"{where}: frontmatterの終了区切り `---` がない")


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


# ---------------------------------------------------------------------------
# 最小YAMLサブセット parser
# ---------------------------------------------------------------------------

# docs/ の既存メモは日本語キーのfrontmatterを持つため、キーはunicode語字を許可する。
_KEY_RE = re.compile(r"^(\w+):(?:[ \t]+(.*))?$")


def parse_frontmatter(fm_text: str, *, where: str) -> dict[str, object]:
    """`key: scalar` と `key: [a, b]` だけを受理する厳格パーサ。

    ネスト・ブロックリスト・複数行文字列・アンカー等は受理せずERRORにする
    （汎用YAMLを黙って部分実装しない）。
    """
    result: dict[str, object] = {}
    for lineno, raw in enumerate(fm_text.split("\n"), start=1):
        if not raw.strip():
            continue
        if raw.lstrip().startswith("#"):
            continue
        if raw[:1] in (" ", "\t"):
            raise BuildError(
                f"{where}: frontmatter {lineno}行目 — インデントされた記法は非対応"
            )
        match = _KEY_RE.match(raw)
        if not match:
            raise BuildError(f"{where}: frontmatter {lineno}行目を解釈できない: {raw!r}")
        key, rawval = match.group(1), (match.group(2) or "").strip()
        if key in result:
            raise BuildError(f"{where}: frontmatterにキー重複: {key}")
        result[key] = _parse_value(rawval, where=where, lineno=lineno)
    return result


def _parse_value(rawval: str, *, where: str, lineno: int) -> object:
    if rawval == "":
        raise BuildError(f"{where}: frontmatter {lineno}行目 — 値が空")
    if rawval.startswith("[") and rawval.endswith("]"):
        inner = rawval[1:-1].strip()
        if not inner:
            return []
        return [_unquote(part.strip()) for part in inner.split(",")]
    return _unquote(rawval)


def _unquote(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
        return token[1:-1]
    return token


def dump_frontmatter(data: dict[str, object]) -> str:
    """parse_frontmatter が読み戻せる形式で出力する。"""
    ordered = list(REQUIRED_FRONTMATTER_KEYS) + list(OPTIONAL_FRONTMATTER_KEYS)
    keys = [k for k in ordered if k in data] + [k for k in data if k not in ordered]
    lines = []
    for key in keys:
        value = data[key]
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# hash / 構造シグネチャ
# ---------------------------------------------------------------------------

def body_hash(body: str) -> str:
    """本文hashの算法（本Phaseで確定・DEC-012の未確定を継承しない）。

    対象   : frontmatter終了区切り行の直後から末尾まで（Markdown本文のみ）
    正規化 : 改行をLFへ統一 → 末尾の空白文字を除去 → 末尾にLFを1つ付与
    符号化 : UTF-8
    算法   : SHA-256、小文字hex、`sha256:` を接頭辞として付ける
    """
    normalized = normalize_newlines(body).rstrip() + "\n"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{HASH_PREFIX}{digest}"


def extract_headings(body: str) -> list[str]:
    """主要見出し（H2）を出現順に返す。fenced code block内は無視する。"""
    headings: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in normalize_newlines(body).split("\n"):
        stripped = line.strip()
        if in_fence:
            if stripped.startswith(fence_marker):
                in_fence = False
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = True
            fence_marker = stripped[:3]
            continue
        if line.startswith("## ") and not line.startswith("###"):
            headings.append(line[3:].strip())
    return headings


def structural_signature(meta: dict[str, object], body: str) -> dict[str, object]:
    """STALE時に機械判定する構造的変化のみを取り出す（安価・決定的なものに限定）。"""
    domain = meta.get("domain", [])
    related = meta.get("related", [])
    return {
        "type": meta.get("type"),
        "status": meta.get("status"),
        "domain": sorted(domain if isinstance(domain, list) else [domain]),
        "related": sorted(related if isinstance(related, list) else [related]),
        "headings": extract_headings(body),
    }


def diff_signature(old: dict[str, object], new: dict[str, object]) -> list[str]:
    """変化した構造項目名を返す。空なら構造的変化なし。"""
    changed = []
    for field in ("type", "status", "domain", "related", "headings"):
        if old.get(field) != new.get(field):
            changed.append(field)
    return changed


# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------

def load_snapshot() -> dict:
    if not SNAPSHOT_PATH.exists():
        return {"snapshot_version": SNAPSHOT_VERSION, "files": {}}
    data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    data.setdefault("files", {})
    return data


def save_snapshot(snapshot: dict) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def prune_regenerations(dates: list[str], today: _dt.date) -> list[str]:
    """過去30日ぶんだけ残す（月次サンプル監査の候補選定に使う程度の用途）。"""
    cutoff = today - _dt.timedelta(days=REGENERATION_WINDOW_DAYS)
    kept = []
    for value in dates:
        try:
            parsed = _dt.date.fromisoformat(value)
        except ValueError:
            continue
        if parsed >= cutoff:
            kept.append(value)
    return sorted(kept)


# ---------------------------------------------------------------------------
# frontmatter 検証
# ---------------------------------------------------------------------------

def validate_frontmatter(meta: dict[str, object], *, rel: str, errors: list[str]) -> None:
    for key in REQUIRED_FRONTMATTER_KEYS:
        if key not in meta:
            errors.append(f"{rel}: frontmatterに必須項目 `{key}` がない")

    unknown = set(meta) - set(REQUIRED_FRONTMATTER_KEYS) - set(OPTIONAL_FRONTMATTER_KEYS)
    if unknown:
        errors.append(
            f"{rel}: 未定義のfrontmatter項目: {', '.join(sorted(unknown))}"
            "（最初から大量のタグを作らない方針）"
        )

    expected_id = rel.rsplit("/", 1)[-1][: -len(".md")]
    if meta.get("id") not in (None, expected_id):
        errors.append(f"{rel}: id は `{expected_id}` であるべき（実際: {meta.get('id')}）")

    if meta.get("type") not in ALLOWED_TYPES and "type" in meta:
        errors.append(f"{rel}: type `{meta['type']}` は許可されていない{sorted(ALLOWED_TYPES)}")

    if meta.get("status") not in ALLOWED_STATUSES and "status" in meta:
        errors.append(
            f"{rel}: status `{meta['status']}` は許可されていない{sorted(ALLOWED_STATUSES)}"
        )

    domain = meta.get("domain")
    if domain is not None:
        values = domain if isinstance(domain, list) else [domain]
        if not values:
            errors.append(f"{rel}: domain が空")
        for value in values:
            if value not in ALLOWED_DOMAINS:
                errors.append(
                    f"{rel}: domain `{value}` は許可されていない{sorted(ALLOWED_DOMAINS)}"
                )

    value = meta.get("metadata_source_hash")
    if isinstance(value, str) and not re.fullmatch(rf"{HASH_PREFIX}[0-9a-f]{{64}}", value):
        errors.append(f"{rel}: metadata_source_hash の形式が不正: {value}")


# ---------------------------------------------------------------------------
# 収集
# ---------------------------------------------------------------------------

def relpath(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def collect_layer_files(pattern: str) -> list[Path]:
    found = sorted(REPO_ROOT.glob(pattern), key=lambda p: relpath(p))
    return [
        p
        for p in found
        if p.is_file()
        and relpath(p) not in INDEX_EXCLUDE
        # `_*` は .gitignore 済みの一時作業ファイル（CLAUDE.md の命名規約）。
        # 成果物ではないのでINDEXにもリンク検査にも載せない。
        and not p.name.startswith("_")
    ]


def first_summary_line(body: str) -> str:
    """H1直後の最初の意味のある行を1行要約として使う。無ければ空文字。"""
    in_fence = False
    for line in normalize_newlines(body).split("\n"):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped or stripped.startswith("#"):
            continue
        stripped = stripped.lstrip("> ").strip()
        if not stripped or set(stripped) <= {"-", "*", "_", "="}:
            continue
        stripped = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
        return stripped if len(stripped) <= 80 else stripped[:79] + "…"
    return ""


def title_of(body: str, fallback: str) -> str:
    for line in normalize_newlines(body).split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


# ---------------------------------------------------------------------------
# リンク検査
# ---------------------------------------------------------------------------

_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def check_links(paths: list[Path]) -> list[str]:
    """相対リンクの参照先が存在するかだけを検査する。外部URLは検査しない。"""
    problems: list[str] = []
    for path in paths:
        text = normalize_newlines(path.read_text(encoding="utf-8"))
        _, body = split_frontmatter(text, where=relpath(path))
        in_fence = False
        for lineno, line in enumerate(body.split("\n"), start=1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for target in _LINK_RE.findall(line):
                target = target.split(" ")[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = target.split("#", 1)[0]
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    problems.append(f"{relpath(path)}:{lineno}: リンク切れ → {target}")
    return problems


# ---------------------------------------------------------------------------
# INDEX 生成
# ---------------------------------------------------------------------------

GENERATED_BANNER = (
    "<!-- このファイルは scripts/knowledge_build.py が生成する。手で編集しない。 -->"
)


def render_index(heading: str, rows: list[dict[str, str]], index_rel: str) -> str:
    lines = [
        GENERATED_BANNER,
        "",
        f"# {heading}",
        "",
        "| ファイル | 種別 | status | domain | 概要 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| [{title}]({href}) | {type} | {status} | {domain} | {summary} |".format(**row)
        )
    lines.append("")
    lines.append(
        f"生成元: `scripts/knowledge_build.py build`　対象: `{index_rel}` の層"
    )
    lines.append("")
    return "\n".join(lines)


def index_href(index_path: Path, target: Path) -> str:
    import os.path

    rel = os.path.relpath(target, index_path.parent)
    return Path(rel).as_posix()


# ---------------------------------------------------------------------------
# search-friction ログ検証
# ---------------------------------------------------------------------------

def check_friction_log() -> list[str]:
    """機械集計可能な形式を保っているかだけを検査する（内容の当否は見ない）。"""
    if not FRICTION_LOG_PATH.exists():
        return []
    problems: list[str] = []
    entries = _parse_friction_log(FRICTION_LOG_PATH.read_text(encoding="utf-8"), problems)
    for idx, entry in enumerate(entries, start=1):
        rel = f"{relpath(FRICTION_LOG_PATH)} エントリ{idx}"
        for key in ("date", "type", "query"):
            if key not in entry:
                problems.append(f"{rel}: 必須項目 `{key}` がない")
        entry_type = entry.get("type")
        if entry_type is not None and entry_type not in ALLOWED_FRICTION_TYPES:
            problems.append(
                f"{rel}: type `{entry_type}` は許可されていない"
                f"{sorted(ALLOWED_FRICTION_TYPES)}"
            )
        date_value = entry.get("date")
        if isinstance(date_value, str):
            try:
                _dt.date.fromisoformat(date_value)
            except ValueError:
                problems.append(f"{rel}: date `{date_value}` がISO日付でない")
    return problems


def _parse_friction_log(text: str, problems: list[str]) -> list[dict[str, object]]:
    """`- key: value` で始まる項目リストだけを受理する最小パーサ。"""
    entries: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for lineno, raw in enumerate(normalize_newlines(text).split("\n"), start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("- "):
            current = {}
            entries.append(current)
            payload = raw[2:]
        elif raw.startswith("  ") and current is not None:
            payload = raw[2:]
        else:
            problems.append(
                f"{relpath(FRICTION_LOG_PATH)}:{lineno}: 解釈できない行: {raw!r}"
            )
            continue
        match = _KEY_RE.match(payload.strip() if raw.startswith("- ") else payload)
        if not match:
            problems.append(
                f"{relpath(FRICTION_LOG_PATH)}:{lineno}: 解釈できない行: {raw!r}"
            )
            continue
        key, rawval = match.group(1), (match.group(2) or "").strip()
        try:
            current[key] = _parse_value(rawval, where=relpath(FRICTION_LOG_PATH), lineno=lineno)
        except BuildError as exc:
            problems.append(str(exc))
    return entries


# ---------------------------------------------------------------------------
# メイン工程
# ---------------------------------------------------------------------------

class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def emit(self) -> int:
        for note in self.notes:
            print(f"  {note}")
        for warning in self.warnings:
            print(f"WARN  {warning}")
        for error in self.errors:
            print(f"ERROR {error}")
        print()
        print(
            f"結果: ERROR {len(self.errors)}件 / WARN {len(self.warnings)}件"
        )
        if self.errors:
            return 1
        if self.warnings:
            return 2
        return 0


def run(*, write: bool, approve: list[str], today: _dt.date) -> int:
    report = Report()
    snapshot = load_snapshot()
    snapshot["snapshot_version"] = SNAPSHOT_VERSION
    files_state: dict = snapshot["files"]
    approve_set = set(approve)

    # ---- 1. 本文hash確認 / 2. staleness確認 / 3. 必要なら再生成 ----
    for name in MANAGED_FILES:
        path = REPO_ROOT / name
        if not path.exists():
            report.errors.append(f"{name}: 正本OSファイルが存在しない")
            continue

        text = path.read_text(encoding="utf-8")
        try:
            fm_text, body = split_frontmatter(text, where=name)
        except BuildError as exc:
            report.errors.append(str(exc))
            continue

        if fm_text is None:
            report.errors.append(
                f"{name}: frontmatterがない（`build --init` で初期付与する）"
            )
            continue

        try:
            meta = parse_frontmatter(fm_text, where=name)
        except BuildError as exc:
            report.errors.append(str(exc))
            continue

        validate_frontmatter(meta, rel=name, errors=report.errors)

        computed = body_hash(body)
        declared = meta.get("metadata_source_hash")
        state = files_state.setdefault(name, {})
        signature = structural_signature(meta, body)
        prior = state.get("structure")

        if declared == computed:
            state["metadata_source_hash"] = computed
            state["structure"] = signature
            state["regenerations"] = prune_regenerations(
                state.get("regenerations", []), today
            )
            report.notes.append(f"{name}: FRESH")
            continue

        # STALE
        changed = diff_signature(prior, signature) if prior is not None else []
        if prior is None:
            report.warnings.append(
                f"{name}: STALE（構造baselineが未記録のため構造判定は行わない）"
            )
            structural = False
        elif changed:
            structural = True
            report.warnings.append(
                f"{name}: STRUCTURAL_CHANGE — 変化した構造項目: {', '.join(changed)}"
                "　→ human approval が必要"
            )
        else:
            structural = False
            report.notes.append(f"{name}: STALE（構造的変化なし）")

        if not write:
            continue

        if structural and name not in approve_set:
            report.notes.append(
                f"{name}: 承認待ちのため metadata_source_hash を更新しない"
                f"（承認する場合は `--approve {name}`）"
            )
            continue

        meta["metadata_source_hash"] = computed
        new_text = "---\n" + dump_frontmatter(meta) + "\n---\n" + body.lstrip("\n")
        # .gitattributes が *.md を eol=lf に固定しているため、Windowsでも
        # 改行変換を起こさないよう newline を明示する。
        path.write_text(new_text, encoding="utf-8", newline="\n")
        state["metadata_source_hash"] = computed
        state["structure"] = signature
        state["regenerations"] = prune_regenerations(
            state.get("regenerations", []) + [today.isoformat()], today
        )
        report.notes.append(
            f"{name}: metadata_source_hash を再生成"
            + ("（承認済みの構造的変更）" if structural else "")
        )

    for stale_key in set(files_state) - set(MANAGED_FILES):
        del files_state[stale_key]

    # ---- 4. INDEX再生成 ----
    link_targets: list[Path] = []
    for index_rel, heading, pattern in INDEX_LAYERS:
        index_path = REPO_ROOT / index_rel
        rows = []
        for path in collect_layer_files(pattern):
            link_targets.append(path)
            text = path.read_text(encoding="utf-8")
            try:
                fm_text, body = split_frontmatter(text, where=relpath(path))
            except BuildError as exc:
                report.errors.append(str(exc))
                continue
            # 正本OS 5本のみ本スキーマで検査する。docs/ の設計メモは独自の
            # frontmatter規約を持つ確定済み文書であり、こちらの規約を後付けで
            # 強制しない（第0原則：依頼範囲外を変更しない）。INDEXへ載せる際は
            # best-effortで読み、解釈できなければ「—」として扱う。
            meta = {}
            if fm_text is not None:
                try:
                    meta = parse_frontmatter(fm_text, where=relpath(path))
                except BuildError as exc:
                    if relpath(path) in MANAGED_FILES:
                        report.errors.append(str(exc))
            domain = meta.get("domain", [])
            rows.append(
                {
                    "title": title_of(body, path.name),
                    "href": index_href(index_path, path),
                    "type": str(meta.get("type", "—")),
                    "status": str(meta.get("status", "—")),
                    "domain": (
                        ", ".join(domain) if isinstance(domain, list) and domain
                        else str(domain or "—")
                    ),
                    "summary": first_summary_line(body).replace("|", "\\|"),
                }
            )
        rendered = render_index(heading, rows, index_rel)
        if write:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.write_text(rendered, encoding="utf-8", newline="\n")
            report.notes.append(f"{index_rel}: 再生成（{len(rows)}件）")
        else:
            existing = index_path.read_text(encoding="utf-8") if index_path.exists() else None
            if existing != rendered:
                report.errors.append(
                    f"{index_rel}: 内容が古い（`knowledge_build.py build` で再生成する）"
                )
            else:
                report.notes.append(f"{index_rel}: 最新（{len(rows)}件）")

    # ---- 5. リンク検査 ----
    for problem in check_links(link_targets):
        report.errors.append(problem)

    # ---- search-friction ログの形式検査 ----
    for problem in check_friction_log():
        report.errors.append(problem)

    if write:
        save_snapshot(snapshot)
        report.notes.append(f"{relpath(SNAPSHOT_PATH)}: 更新")

    return report.emit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "command", choices=("check", "build"), help="check=検査のみ / build=生成と更新"
    )
    parser.add_argument(
        "--approve",
        action="append",
        default=[],
        metavar="FILE",
        help="STRUCTURAL_CHANGE を人間が承認したファイル（buildでのみ有効）",
    )
    parser.add_argument(
        "--today", default=None, help="基準日 (YYYY-MM-DD)。省略時はシステム日付"
    )
    args = parser.parse_args(argv)

    # Windowsの既定コンソールコードページでも日本語の診断結果が読めるようにする。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    today = _dt.date.fromisoformat(args.today) if args.today else _dt.date.today()
    try:
        return run(write=args.command == "build", approve=args.approve, today=today)
    except BuildError as exc:
        print(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
