"""Exercise malformed entries and stale-index detection in isolated libraries."""

import contextlib
from copy import deepcopy
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("library", REPO / "scripts" / "library.py")
library = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(library)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "taxonomy.json").write_text((REPO / "taxonomy.json").read_text(encoding="utf-8"), encoding="utf-8")
        self.path = self.root / "entries" / "appraisal" / "test-scene.md"
        self.path.parent.mkdir(parents=True)
        raw = (REPO / "entries" / "appraisal" / "ordinary-chair.md").read_text(encoding="utf-8")
        _, front, self.body = raw.split("---", 2)
        self.meta = yaml.safe_load(front)
        self.write()

    def write(self, meta=None, path=None):
        (path or self.path).write_text("---\n" + yaml.safe_dump(meta or self.meta, allow_unicode=True, sort_keys=False)
                                      + "---\n" + self.body.lstrip(), encoding="utf-8")

    def invalid(self, message):
        with self.assertRaisesRegex(library.InvalidLibrary, message):
            library.load_library(self.root)

    def command(self, name):
        with patch.object(library, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return library.main([name])

    def test_unknown_discussion_date_is_preserved(self):
        taxonomy, entries = library.load_library(self.root)
        self.assertIsNone(entries[0]["meta"]["sources"][0]["discussed_on"])
        self.assertIn("未知", library.render_index(taxonomy, entries))

    def test_duplicate_id_across_files_is_rejected(self):
        self.write(path=self.path.with_name("second-scene.md"))
        self.invalid("重複 ID")

    def test_category_must_match_directory(self):
        self.meta["category"] = "refusal"
        self.write()
        self.invalid("目錄必須")

    def test_malformed_metadata_has_actionable_error(self):
        for field, value, expected in (("category", ["appraisal"], "未知 category"),
                                       ("intents", "保留評價", "非空字串清單"),
                                       ("sources", [], "sources 不可為空")):
            with self.subTest(field=field):
                meta = deepcopy(self.meta)
                meta[field] = value
                self.write(meta)
                self.invalid(expected)

    def test_duplicate_yaml_key_is_not_silently_overwritten(self):
        raw = self.path.read_text(encoding="utf-8").replace("---\n", "---\ntitle: 另一個標題\n", 1)
        self.path.write_text(raw, encoding="utf-8")
        self.invalid("YAML 欄位重複")

    def test_invalid_or_unquoted_dates_are_rejected(self):
        for value in ("2026-02-30", "2026-1-1", None, library.date(2026, 10, 26)):
            with self.subTest(value=value):
                self.meta["created_at"] = value
                self.write()
                self.invalid("created_at")

    def test_chronology_is_checked(self):
        cases = [("discussed_on", "2026-10-27", "討論日不得晚於"),
                 ("collected_on", "2026-10-25", "collected_on 必須"),
                 ("collected_on", "2026-10-27", "collected_on 必須")]
        for key, value, message in cases:
            with self.subTest(key=key, value=value):
                meta = deepcopy(self.meta)
                meta["sources"][0][key] = value
                self.write(meta)
                self.invalid(message)

    def test_append_source_keeps_original_dates(self):
        self.meta["updated_at"] = "2026-10-28"
        source = deepcopy(self.meta["sources"][0])
        source.update(kind="chatgpt", locator="新增版本的討論", discussed_on="2026-10-27", collected_on="2026-10-28")
        self.meta["sources"].append(source)
        self.write()
        _, entries = library.load_library(self.root)
        self.assertEqual(len(entries[0]["meta"]["sources"]), 2)
        self.assertEqual(entries[0]["meta"]["sources"][0]["collected_on"], "2026-10-26")

    def test_incomplete_or_duplicate_provenance_is_rejected(self):
        source = self.meta["sources"][0]
        source["locator"] = " "
        self.write()
        self.invalid("locator 不可空白")
        source["locator"] = "討論中的問題"
        self.meta["sources"].append(deepcopy(source))
        self.write()
        self.invalid("來源完全重複")

    def test_invalid_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "https://", "https://[", "https://example.com/a b"):
            with self.subTest(url=url):
                self.meta["sources"][0]["url"] = url
                self.write()
                self.invalid("來源 url")

    def test_empty_or_missing_body_sections_are_rejected(self):
        self.body = self.body.replace("尚未記錄。", "")
        self.write()
        self.invalid("區塊不可空白：使用者回饋")
        self.body = self.body.replace("## 使用者回饋", "## 其他")
        self.write()
        self.invalid("必須有且只有一個區塊：使用者回饋")

    def test_stale_index_fails_and_build_is_idempotent(self):
        self.assertEqual(self.command("check-index"), 1)
        self.assertEqual(self.command("build"), 0)
        first = (self.root / "CATALOG.md").read_bytes()
        self.assertEqual(self.command("check-index"), 0)
        self.assertEqual(self.command("build"), 0)
        self.assertEqual(first, (self.root / "CATALOG.md").read_bytes())
        self.meta["scenes"].append("職場")
        self.write()
        self.assertEqual(self.command("check-index"), 1)

    def test_invalid_library_does_not_overwrite_index(self):
        target = self.root / "CATALOG.md"
        target.write_text("existing index\n", encoding="utf-8")
        self.meta["category"] = "unknown"
        self.write()
        self.assertEqual(self.command("build"), 1)
        self.assertEqual(target.read_text(encoding="utf-8"), "existing index\n")

    def test_special_characters_are_escaped_in_index(self):
        self.meta["scenes"] = ["[甲]|乙<丙>"]
        self.write()
        taxonomy, entries = library.load_library(self.root)
        self.assertIn(r"\[甲\]\|乙\<丙\>", library.render_index(taxonomy, entries))


if __name__ == "__main__":
    unittest.main()
