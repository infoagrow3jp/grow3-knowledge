# -*- coding: utf-8 -*-
"""scripts/knowledge_build.py の回帰テスト。

end-to-endテストは tmp ディレクトリに合成リポジトリを組み立てて実行し、
実リポジトリの正本OSファイルには一切書き込まない（並列実行時の正本汚染を
避けるため、モジュールグローバルを差し替えてから run() を呼ぶ）。

使い方：python tests/test_knowledge_build.py
標準ライブラリのunittestのみを使用する（pytest等の追加依存を持たない）。
"""
import datetime as dt
import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import knowledge_build as kb  # noqa: E402


VALID_FM = "\n".join(
    [
        "---",
        "id: sample-os",
        "type: os",
        "status: canonical",
        "domain: [training]",
        "metadata_source_hash: sha256:" + "0" * 64,
        "---",
    ]
)


class TestFrontmatterSplit(unittest.TestCase):
    def test_extracts_frontmatter_and_body(self):
        fm, body = kb.split_frontmatter(VALID_FM + "\n# 見出し\n本文\n", where="t")
        self.assertIn("id: sample-os", fm)
        self.assertEqual(body, "# 見出し\n本文\n")

    def test_no_frontmatter_returns_none(self):
        fm, body = kb.split_frontmatter("# 見出し\n本文\n", where="t")
        self.assertIsNone(fm)
        self.assertEqual(body, "# 見出し\n本文\n")

    def test_missing_closing_delimiter_is_error(self):
        with self.assertRaises(kb.BuildError):
            kb.split_frontmatter("---\nid: x\n本文\n", where="t")

    def test_bom_is_rejected(self):
        with self.assertRaises(kb.BuildError):
            kb.split_frontmatter("﻿---\nid: x\n---\n", where="t")

    def test_empty_frontmatter_is_invalid(self):
        with self.assertRaises(kb.BuildError):
            kb.split_frontmatter("---\n\n---\n本文\n", where="t")

    def test_later_hrule_stays_in_body(self):
        _, body = kb.split_frontmatter(VALID_FM + "\n本文\n\n---\n続き\n", where="t")
        self.assertIn("---", body)
        self.assertIn("続き", body)

    def test_leading_blank_line_means_no_frontmatter(self):
        fm, _ = kb.split_frontmatter("\n---\nid: x\n---\n", where="t")
        self.assertIsNone(fm)


class TestFrontmatterParse(unittest.TestCase):
    def test_scalar_and_list(self):
        meta = kb.parse_frontmatter(
            "id: a\ndomain: [x, y]\nempty_list: []", where="t"
        )
        self.assertEqual(meta["id"], "a")
        self.assertEqual(meta["domain"], ["x", "y"])
        self.assertEqual(meta["empty_list"], [])

    def test_quoted_values_are_unquoted(self):
        meta = kb.parse_frontmatter('id: "a b"\n', where="t")
        self.assertEqual(meta["id"], "a b")

    def test_duplicate_key_is_error(self):
        with self.assertRaises(kb.BuildError):
            kb.parse_frontmatter("id: a\nid: b", where="t")

    def test_indented_nesting_is_rejected(self):
        with self.assertRaises(kb.BuildError):
            kb.parse_frontmatter("root:\n  child: 1", where="t")

    def test_block_list_is_rejected(self):
        with self.assertRaises(kb.BuildError):
            kb.parse_frontmatter("domain:\n- a\n- b", where="t")

    def test_empty_value_is_error(self):
        with self.assertRaises(kb.BuildError):
            kb.parse_frontmatter("id:", where="t")

    def test_japanese_keys_parse(self):
        meta = kb.parse_frontmatter("基準日: 2026-07-11\nstatus: draft", where="t")
        self.assertEqual(meta["基準日"], "2026-07-11")
        self.assertEqual(meta["status"], "draft")

    def test_roundtrip_through_dump(self):
        original = {
            "id": "a",
            "type": "os",
            "status": "canonical",
            "domain": ["training"],
            "metadata_source_hash": "sha256:" + "a" * 64,
            "related": ["b", "c"],
        }
        self.assertEqual(
            kb.parse_frontmatter(kb.dump_frontmatter(original), where="t"), original
        )

    def test_dump_orders_required_keys_first(self):
        dumped = kb.dump_frontmatter({"related": ["b"], "id": "a"})
        self.assertTrue(dumped.startswith("id: a"))


class TestBodyHash(unittest.TestCase):
    def test_crlf_and_lf_hash_identically(self):
        self.assertEqual(kb.body_hash("a\r\nb\r\n"), kb.body_hash("a\nb\n"))

    def test_trailing_whitespace_is_normalized(self):
        self.assertEqual(kb.body_hash("a\n\n\n  \n"), kb.body_hash("a"))

    def test_content_change_changes_hash(self):
        self.assertNotEqual(kb.body_hash("a\n"), kb.body_hash("b\n"))

    def test_format_is_prefixed_lowercase_hex(self):
        value = kb.body_hash("a\n")
        self.assertTrue(value.startswith("sha256:"))
        self.assertEqual(len(value), len("sha256:") + 64)
        self.assertEqual(value, value.lower())


class TestHeadings(unittest.TestCase):
    def test_collects_h2_only(self):
        body = "# H1\n## A\n### B\n## C\n"
        self.assertEqual(kb.extract_headings(body), ["A", "C"])

    def test_ignores_headings_inside_code_fence(self):
        body = "## A\n```\n## NotAHeading\n```\n## B\n"
        self.assertEqual(kb.extract_headings(body), ["A", "B"])

    def test_ignores_tilde_fence(self):
        body = "## A\n~~~\n## NotAHeading\n~~~\n"
        self.assertEqual(kb.extract_headings(body), ["A"])


class TestStructuralSignature(unittest.TestCase):
    def _sig(self, **over):
        meta = {"type": "os", "status": "canonical", "domain": ["training"]}
        meta.update(over)
        return kb.structural_signature(meta, "## A\n")

    def test_identical_signatures_have_no_diff(self):
        self.assertEqual(kb.diff_signature(self._sig(), self._sig()), [])

    def test_domain_change_is_detected(self):
        changed = kb.diff_signature(self._sig(), self._sig(domain=["hr"]))
        self.assertEqual(changed, ["domain"])

    def test_status_change_is_detected(self):
        changed = kb.diff_signature(self._sig(), self._sig(status="draft"))
        self.assertEqual(changed, ["status"])

    def test_related_change_is_detected(self):
        changed = kb.diff_signature(self._sig(), self._sig(related=["x"]))
        self.assertEqual(changed, ["related"])

    def test_heading_change_is_detected(self):
        old = self._sig()
        new = kb.structural_signature(
            {"type": "os", "status": "canonical", "domain": ["training"]}, "## B\n"
        )
        self.assertEqual(kb.diff_signature(old, new), ["headings"])

    def test_domain_order_is_not_a_change(self):
        a = self._sig(domain=["training", "hr"])
        b = self._sig(domain=["hr", "training"])
        self.assertEqual(kb.diff_signature(a, b), [])


class TestValidateFrontmatter(unittest.TestCase):
    def _errors(self, meta, rel="sample-os.md"):
        errors = []
        kb.validate_frontmatter(meta, rel=rel, errors=errors)
        return errors

    def _valid(self):
        return {
            "id": "sample-os",
            "type": "os",
            "status": "canonical",
            "domain": ["training"],
            "metadata_source_hash": "sha256:" + "0" * 64,
        }

    def test_valid_frontmatter_has_no_errors(self):
        self.assertEqual(self._errors(self._valid()), [])

    def test_missing_required_key(self):
        meta = self._valid()
        del meta["status"]
        self.assertTrue(any("status" in e for e in self._errors(meta)))

    def test_unknown_key_is_rejected(self):
        meta = self._valid()
        meta["tags"] = ["x"]
        self.assertTrue(any("tags" in e for e in self._errors(meta)))

    def test_id_must_match_filename(self):
        meta = self._valid()
        meta["id"] = "wrong"
        self.assertTrue(any("id" in e for e in self._errors(meta)))

    def test_bad_type_status_domain(self):
        meta = self._valid()
        meta.update(type="policy", status="published", domain=["finance"])
        errors = self._errors(meta)
        self.assertTrue(any("type" in e for e in errors))
        self.assertTrue(any("status" in e for e in errors))
        self.assertTrue(any("domain" in e for e in errors))

    def test_bad_hash_format(self):
        meta = self._valid()
        meta["metadata_source_hash"] = "sha256:XYZ"
        self.assertTrue(
            any("metadata_source_hash" in e for e in self._errors(meta))
        )

    def test_empty_domain_is_rejected(self):
        meta = self._valid()
        meta["domain"] = []
        self.assertTrue(any("domain" in e for e in self._errors(meta)))


class TestPruneRegenerations(unittest.TestCase):
    def test_drops_entries_older_than_window(self):
        today = dt.date(2026, 8, 4)
        kept = kb.prune_regenerations(["2026-06-01", "2026-08-01"], today)
        self.assertEqual(kept, ["2026-08-01"])

    def test_keeps_boundary_date(self):
        today = dt.date(2026, 8, 4)
        self.assertEqual(kb.prune_regenerations(["2026-07-05"], today), ["2026-07-05"])

    def test_ignores_unparseable_dates(self):
        self.assertEqual(kb.prune_regenerations(["nope"], dt.date(2026, 8, 4)), [])


class TestSummaryLine(unittest.TestCase):
    def test_skips_headings_and_fences(self):
        body = "# タイトル\n```\ncode\n```\n本当の要約\n"
        self.assertEqual(kb.first_summary_line(body), "本当の要約")

    def test_strips_blockquote_and_bold(self):
        self.assertEqual(kb.first_summary_line("# T\n> **強調** 要約\n"), "強調 要約")

    def test_skips_horizontal_rule(self):
        self.assertEqual(kb.first_summary_line("# T\n---\n要約\n"), "要約")

    def test_truncates_long_line(self):
        body = "# T\n" + "あ" * 200 + "\n"
        self.assertEqual(len(kb.first_summary_line(body)), 80)


class TempRepoTestCase(unittest.TestCase):
    """モジュールグローバルを差し替え、実リポジトリに触れずに run() を回す。"""

    MANAGED = "sample-os.md"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kb-test-"))
        self._saved = {
            name: getattr(kb, name)
            for name in (
                "REPO_ROOT",
                "SNAPSHOT_PATH",
                "FRICTION_LOG_PATH",
                "MANAGED_FILES",
                "INDEX_LAYERS",
                "INDEX_EXCLUDE",
            )
        }
        kb.REPO_ROOT = self.tmp
        kb.SNAPSHOT_PATH = self.tmp / "snapshot.json"
        kb.FRICTION_LOG_PATH = self.tmp / "search-friction.yaml"
        kb.MANAGED_FILES = (self.MANAGED,)
        kb.INDEX_LAYERS = (("INDEX.md", "テスト層", "*.md"),)
        kb.INDEX_EXCLUDE = {"INDEX.md"}
        self.write_managed("## A\n\n本文\n")

    def tearDown(self):
        for name, value in self._saved.items():
            setattr(kb, name, value)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_managed(self, body, *, hash_value=None, related=None, status="canonical"):
        meta = {
            "id": self.MANAGED[:-3],
            "type": "os",
            "status": status,
            "domain": ["training"],
            "metadata_source_hash": hash_value or ("sha256:" + "0" * 64),
        }
        if related:
            meta["related"] = related
        text = "---\n" + kb.dump_frontmatter(meta) + "\n---\n" + body
        (self.tmp / self.MANAGED).write_text(text, encoding="utf-8", newline="\n")

    def managed_meta(self):
        text = (self.tmp / self.MANAGED).read_text(encoding="utf-8")
        fm, body = kb.split_frontmatter(text, where="t")
        return kb.parse_frontmatter(fm, where="t"), body

    def run_build(self, *, write=True, approve=(), today=dt.date(2026, 8, 4)):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = kb.run(write=write, approve=list(approve), today=today)
        return code, buffer.getvalue()


class TestEndToEnd(TempRepoTestCase):
    def test_build_refreshes_hash_and_writes_index(self):
        # 初回buildは構造baselineが無いためWARN(=2)で返るのが正しい挙動。
        # baselineを書いた2回目以降がクリーンになる。
        code, out = self.run_build()
        self.assertEqual(code, 2, out)
        self.assertIn("構造baselineが未記録", out)
        meta, body = self.managed_meta()
        self.assertEqual(meta["metadata_source_hash"], kb.body_hash(body))
        self.assertTrue((self.tmp / "INDEX.md").exists())

        code, out = self.run_build()
        self.assertEqual(code, 0, out)

    def test_build_is_idempotent_and_check_passes(self):
        self.run_build()
        code, out = self.run_build(write=False)
        self.assertEqual(code, 0, out)
        self.assertIn("FRESH", out)

    def test_written_files_use_lf_only(self):
        self.run_build()
        for name in (self.MANAGED, "INDEX.md"):
            raw = (self.tmp / name).read_bytes()
            self.assertNotIn(b"\r\n", raw, f"{name} にCRLFが混入した")

    def test_non_structural_edit_is_stale_then_auto_refreshed(self):
        self.run_build()
        # INDEXの要約に使われる先頭行は変えず、後段の段落だけを足す
        # （見出しもfrontmatterも変えないので構造的変化ではない）。
        self.write_managed(
            "## A\n\n本文\n\n追記した段落\n",
            hash_value=self.managed_meta()[0]["metadata_source_hash"],
        )
        code, out = self.run_build(write=False)
        self.assertIn("STALE（構造的変化なし）", out)
        self.assertEqual(code, 0, out)

        code, out = self.run_build()
        self.assertEqual(code, 0, out)
        meta, body = self.managed_meta()
        self.assertEqual(meta["metadata_source_hash"], kb.body_hash(body))

    def test_structural_change_warns_and_blocks_auto_refresh(self):
        self.run_build()
        stale_hash = self.managed_meta()[0]["metadata_source_hash"]
        self.write_managed("## A\n\n## 新しい見出し\n\n本文\n", hash_value=stale_hash)

        code, out = self.run_build(write=False)
        self.assertIn("STRUCTURAL_CHANGE", out)
        self.assertIn("headings", out)
        self.assertEqual(code, 2, out)  # WARNのみ

        # 承認なしのbuildではhashを書き換えない
        code, out = self.run_build()
        self.assertIn("承認待ち", out)
        self.assertEqual(self.managed_meta()[0]["metadata_source_hash"], stale_hash)

    def test_structural_change_refreshes_after_approval(self):
        self.run_build()
        stale_hash = self.managed_meta()[0]["metadata_source_hash"]
        self.write_managed("## A\n\n## 新しい見出し\n\n本文\n", hash_value=stale_hash)
        self.run_build()

        code, out = self.run_build(approve=[self.MANAGED])
        self.assertIn("承認済みの構造的変更", out)
        meta, body = self.managed_meta()
        self.assertEqual(meta["metadata_source_hash"], kb.body_hash(body))
        self.assertNotEqual(meta["metadata_source_hash"], stale_hash)

    def test_domain_change_is_a_structural_change(self):
        self.run_build()
        stale_hash = self.managed_meta()[0]["metadata_source_hash"]
        text = (self.tmp / self.MANAGED).read_text(encoding="utf-8")
        text = text.replace("domain: [training]", "domain: [hr]").replace(
            "\n本文\n", "\n本文を少し変えた\n"
        )
        (self.tmp / self.MANAGED).write_text(text, encoding="utf-8", newline="\n")
        _, out = self.run_build(write=False)
        self.assertIn("STRUCTURAL_CHANGE", out)
        self.assertIn("domain", out)
        self.assertEqual(self.managed_meta()[0]["metadata_source_hash"], stale_hash)

    def test_regeneration_count_is_recorded(self):
        self.run_build()
        self.write_managed(
            "## A\n\n変更\n", hash_value=self.managed_meta()[0]["metadata_source_hash"]
        )
        self.run_build(today=dt.date(2026, 8, 4))
        import json

        snapshot = json.loads(kb.SNAPSHOT_PATH.read_text(encoding="utf-8"))
        self.assertIn("2026-08-04", snapshot["files"][self.MANAGED]["regenerations"])

    def test_missing_frontmatter_is_an_error(self):
        (self.tmp / self.MANAGED).write_text("# 本文だけ\n", encoding="utf-8", newline="\n")
        code, out = self.run_build(write=False)
        self.assertIn("frontmatterがない", out)
        self.assertEqual(code, 1)

    def test_missing_managed_file_is_an_error(self):
        (self.tmp / self.MANAGED).unlink()
        code, out = self.run_build(write=False)
        self.assertIn("正本OSファイルが存在しない", out)
        self.assertEqual(code, 1)

    def test_stale_index_is_detected_by_check(self):
        self.run_build()
        (self.tmp / "INDEX.md").write_text("古い内容\n", encoding="utf-8", newline="\n")
        code, out = self.run_build(write=False)
        self.assertIn("内容が古い", out)
        self.assertEqual(code, 1)

    def test_temp_prefixed_files_are_excluded_from_index(self):
        (self.tmp / "_tmp_scratch.md").write_text("# 一時\n", encoding="utf-8", newline="\n")
        self.run_build()
        self.assertNotIn("_tmp_scratch", (self.tmp / "INDEX.md").read_text(encoding="utf-8"))


class TestLinkCheck(TempRepoTestCase):
    def test_broken_relative_link_is_reported(self):
        self.write_managed("## A\n\n[欠番](missing.md)\n")
        code, out = self.run_build(write=False)
        self.assertIn("リンク切れ", out)
        self.assertEqual(code, 1)

    def test_existing_link_passes(self):
        (self.tmp / "target.md").write_text("# T\n", encoding="utf-8", newline="\n")
        self.write_managed("## A\n\n[あり](target.md)\n")
        _, out = self.run_build()
        self.assertNotIn("リンク切れ", out)

    def test_external_and_anchor_links_are_skipped(self):
        self.write_managed(
            "## A\n\n[外](https://example.com)\n[中](#section)\n[メ](mailto:a@b.jp)\n"
        )
        _, out = self.run_build(write=False)
        self.assertNotIn("リンク切れ", out)

    def test_link_with_anchor_resolves_to_file(self):
        (self.tmp / "target.md").write_text("# T\n", encoding="utf-8", newline="\n")
        self.write_managed("## A\n\n[あり](target.md#節)\n")
        _, out = self.run_build()
        self.assertNotIn("リンク切れ", out)

    def test_links_inside_code_fence_are_skipped(self):
        self.write_managed("## A\n\n```\n[偽](missing.md)\n```\n")
        _, out = self.run_build(write=False)
        self.assertNotIn("リンク切れ", out)

    def test_image_links_are_not_treated_as_document_links(self):
        self.write_managed("## A\n\n![図](missing.png)\n")
        _, out = self.run_build(write=False)
        self.assertNotIn("リンク切れ", out)


class TestFrictionLog(TempRepoTestCase):
    def write_log(self, text):
        kb.FRICTION_LOG_PATH.write_text(text, encoding="utf-8", newline="\n")

    def test_absent_log_is_fine(self):
        self.assertEqual(kb.check_friction_log(), [])

    def test_comment_only_log_is_fine(self):
        self.write_log("# コメントだけ\n")
        self.assertEqual(kb.check_friction_log(), [])

    def test_valid_entry_passes(self):
        self.write_log(
            "- date: 2026-08-04\n  type: multi_domain\n  query: 検索語\n"
            "  domains: [training, hr]\n"
        )
        self.assertEqual(kb.check_friction_log(), [])

    def test_unknown_type_is_rejected(self):
        self.write_log("- date: 2026-08-04\n  type: something_new\n  query: q\n")
        self.assertTrue(any("something_new" in p for p in kb.check_friction_log()))

    def test_missing_required_key_is_reported(self):
        self.write_log("- date: 2026-08-04\n  type: multi_domain\n")
        self.assertTrue(any("query" in p for p in kb.check_friction_log()))

    def test_bad_date_is_reported(self):
        self.write_log("- date: 2026-13-99\n  type: multi_domain\n  query: q\n")
        self.assertTrue(any("ISO日付" in p for p in kb.check_friction_log()))

    def test_all_three_allowed_types_pass(self):
        for name in ("canonical_not_found", "multi_domain", "fallback_used"):
            self.write_log(f"- date: 2026-08-04\n  type: {name}\n  query: q\n")
            self.assertEqual(kb.check_friction_log(), [], name)

    def test_bad_log_fails_the_build(self):
        self.write_log("- date: 2026-08-04\n  type: bogus\n  query: q\n")
        code, out = self.run_build(write=False)
        self.assertEqual(code, 1)
        self.assertIn("bogus", out)


class TestRealRepositoryIsClean(unittest.TestCase):
    """実リポジトリが check を通る状態で保たれているかを確認する（書き込みなし）。"""

    def test_check_passes(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = kb.run(write=False, approve=[], today=dt.date.today())
        self.assertEqual(code, 0, buffer.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
