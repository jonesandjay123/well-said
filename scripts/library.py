#!/usr/bin/env python3
"""Validate the Markdown library and generate its deterministic navigation index."""

import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
TAG_FIELDS = ("intents", "scenes", "audiences", "tones")
SECTIONS = ("情境", "台詞版本", "選用建議", "使用者回饋", "來源與整理註記")
FIELDS = {"id", "title", "category", "status", "created_at", "updated_at", "sources", *TAG_FIELDS}
SOURCE_FIELDS = {"kind", "title", "locator", "url", "discussed_on", "collected_on"}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class InvalidLibrary(ValueError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    """Do not silently discard provenance due to duplicate YAML keys."""


def unique_mapping(loader, node):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        try:
            if key in mapping:
                raise InvalidLibrary("YAML 欄位重複：{}".format(key))
            mapping[key] = loader.construct_object(value_node)
        except TypeError as exc:
            raise InvalidLibrary("YAML 欄位名稱必須是純量") from exc
    return mapping


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def require(condition, message):
    if not condition:
        raise InvalidLibrary(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip()) and "\n" not in value and "\r" not in value


def parse_date(value, label, nullable=False):
    if value is None and nullable:
        return None
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value),
            label + ' 必須是加引號的 "YYYY-MM-DD"')
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidLibrary(label + " 不是有效日期") from exc


def exact_fields(value, expected, label):
    require(isinstance(value, dict), label + " 必須是物件")
    require(set(value) == expected, label + " 欄位不符（缺少：{}；多餘：{}）".format(
        ", ".join(sorted(expected - set(value))), ", ".join(sorted(str(x) for x in set(value) - expected))))


def read_entry(path, root, taxonomy):
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", raw, re.DOTALL)
    require(match is not None, "缺少 YAML front matter")
    try:
        meta = yaml.load(match.group(1), Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise InvalidLibrary("YAML 格式錯誤：{}".format(exc)) from exc
    exact_fields(meta, FIELDS, "條目")
    require(nonempty(meta["id"]) and re.fullmatch(r"ws-[a-z0-9]+(?:-[a-z0-9]+)*", meta["id"]), "id 格式錯誤")
    require(nonempty(meta["title"]), "title 不可空白或換行")
    category = meta["category"]
    require(isinstance(category, str) and category in taxonomy, "未知 category")
    relative = path.relative_to(root / "entries")
    require(len(relative.parts) == 2 and relative.parts[0] == category, "目錄必須是 entries/<category>/<slug>.md")
    require(SLUG.fullmatch(path.stem) is not None, "檔名必須是小寫英文數字與連字號")
    require(meta["status"] in ("example", "collected"), "status 必須是 example 或 collected")
    for field in TAG_FIELDS:
        values = meta[field]
        require(isinstance(values, list) and len(values) > 0 and all(nonempty(v) for v in values), field + " 必須是非空字串清單")
        require(all(v == v.strip() for v in values), field + " 不得有前後空白")
        require(len(set(values)) == len(values), field + " 有重複標籤")
    created = parse_date(meta["created_at"], "created_at")
    updated = parse_date(meta["updated_at"], "updated_at")
    require(created <= updated, "updated_at 不得早於 created_at")
    sources = meta["sources"]
    require(isinstance(sources, list) and len(sources) > 0, "sources 不可為空")
    source_keys = set()
    for source in sources:
        exact_fields(source, SOURCE_FIELDS, "來源")
        require(source["kind"] in ("origin-note", "chatgpt", "manual"), "未知來源 kind")
        require(nonempty(source["title"]) and nonempty(source["locator"]), "來源 title 與 locator 不可空白")
        url = source["url"]
        if url is not None:
            require(nonempty(url) and not any(c.isspace() for c in url), "來源 url 必須是完整 HTTP(S) URL 或 null")
            try:
                parsed = urlparse(url)
                require(parsed.scheme in ("http", "https") and bool(parsed.hostname), "來源 url 必須是完整 HTTP(S) URL 或 null")
            except ValueError as exc:
                raise InvalidLibrary("來源 url 格式錯誤") from exc
        discussed = parse_date(source["discussed_on"], "discussed_on", nullable=True)
        collected = parse_date(source["collected_on"], "collected_on")
        require(created <= collected <= updated, "collected_on 必須位於 created_at 與 updated_at 之間")
        require(discussed is None or discussed <= collected, "討論日不得晚於收錄日")
        key = json.dumps(source, sort_keys=True, ensure_ascii=False)
        require(key not in source_keys, "來源完全重複")
        source_keys.add(key)
    body = match.group(2)
    visible_body = re.sub(r"^```[^\n]*\n.*?^```\s*$", "", body, flags=re.MULTILINE | re.DOTALL)
    require("# " + meta["title"] in visible_body.splitlines(), "H1 標題須與 title 相同")
    sections = list(re.finditer(r"^## (.+?)\s*$", visible_body, re.MULTILINE))
    for name in SECTIONS:
        found = [i for i, section in enumerate(sections) if section.group(1) == name]
        require(len(found) == 1, "必須有且只有一個區塊：" + name)
        i = found[0]
        end = sections[i + 1].start() if i + 1 < len(sections) else len(visible_body)
        require(bool(visible_body[sections[i].end():end].strip()), "區塊不可空白：" + name)
    return {"meta": meta, "path": path.relative_to(root).as_posix()}


def load_library(root):
    try:
        taxonomy = json.loads((root / "taxonomy.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InvalidLibrary("無法讀取 taxonomy.json：{}".format(exc)) from exc
    require(isinstance(taxonomy, dict) and bool(taxonomy), "taxonomy 不可為空")
    for slug, info in taxonomy.items():
        require(SLUG.fullmatch(slug) is not None, "分類鍵格式錯誤")
        exact_fields(info, {"name", "description"}, "分類")
        require(nonempty(info["name"]) and nonempty(info["description"]), "分類名稱與說明不可空白")
    require((root / "entries").is_dir(), "缺少 entries 目錄")
    entries, errors, ids = [], [], set()
    for path in sorted((root / "entries").rglob("*.md")):
        try:
            require(not path.is_symlink(), "條目不可使用符號連結")
            entry = read_entry(path, root, taxonomy)
            identity = entry["meta"]["id"]
            require(identity not in ids, "重複 ID：" + identity)
            ids.add(identity)
            entries.append(entry)
        except (InvalidLibrary, OSError, UnicodeError) as exc:
            errors.append("{}：{}".format(path.relative_to(root), exc))
    require(not errors, "\n".join(errors))
    return taxonomy, entries


def escape(value):
    for char in ("\\", "`", "*", "_", "[", "]", "<", ">", "|", "#"):
        value = value.replace(char, "\\" + char)
    return value


def entry_link(entry):
    return "[{}]({})".format(escape(entry["meta"]["title"]), entry["path"])


def render_index(taxonomy, entries):
    lines = ["# 台詞索引", "", "<!-- 由 scripts/library.py build 產生，請勿手動編輯。 -->", "",
             "以溝通目的為主分類；下方亦可依細部目的、場景、對象與語氣查找。", "",
             "共 {} 筆：{} 筆示例、{} 筆討論收錄。日期是來源參考，不作分類。".format(
                 len(entries), sum(e["meta"]["status"] == "example" for e in entries),
                 sum(e["meta"]["status"] == "collected" for e in entries)), "", "## 依溝通目的", ""]
    ordered = sorted(entries, key=lambda e: (e["meta"]["title"], e["meta"]["id"]))
    for slug, info in taxonomy.items():
        lines.extend(["### " + escape(info["name"]), "", escape(info["description"]), ""])
        group = [e for e in ordered if e["meta"]["category"] == slug]
        if not group:
            lines.extend(["尚待收錄。", ""])
            continue
        lines.extend(["| 情境 | 場景 | 對象 | 狀態 | 原討論日 | 首次收錄 |", "| --- | --- | --- | --- | --- | --- |"])
        for entry in group:
            meta = entry["meta"]
            dates = sorted({s["discussed_on"] or "未知" for s in meta["sources"]})
            cells = [entry_link(entry), escape("、".join(meta["scenes"])), escape("、".join(meta["audiences"])),
                     "示例" if meta["status"] == "example" else "已收錄", "、".join(dates), meta["created_at"]]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    for field, heading in zip(TAG_FIELDS, ("細部目的", "場景", "對象", "語氣")):
        lines.extend(["## 依" + heading, ""])
        groups = defaultdict(list)
        for entry in ordered:
            for tag in entry["meta"][field]:
                groups[tag].append(entry)
        for tag in sorted(groups):
            lines.extend(["### " + escape(tag), ""])
            lines.extend("- " + entry_link(entry) for entry in groups[tag])
            lines.append("")
        if not groups:
            lines.extend(["尚待收錄。", ""])
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build", "check-index"))
    args = parser.parse_args(argv)
    try:
        taxonomy, entries = load_library(ROOT)
        if args.command == "check":
            print("檢查通過：{} 筆條目。".format(len(entries)))
        else:
            expected = render_index(taxonomy, entries)
            target = ROOT / "CATALOG.md"
            if args.command == "build":
                target.write_text(expected, encoding="utf-8")
                print("已更新 CATALOG.md：{} 筆條目。".format(len(entries)))
            else:
                require(target.exists() and target.read_text(encoding="utf-8") == expected,
                        "CATALOG.md 缺少或過期，請執行 python scripts/library.py build")
                print("索引與條目一致。")
    except (InvalidLibrary, OSError) as exc:
        print("檢查失敗：{}".format(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
