#!/usr/bin/env python3
"""Regenerate all reading notes from original JSON data using the optimized template."""

import json
import os
from datetime import datetime
from collections import defaultdict

BOOKS_DIR = "/Users/evelyn/.trae-cn/work/6a98d643260756fee2fb414b/reading-notes/books"
OUTPUT_DIR = "/Users/evelyn/.trae-cn/work/6a98d643260756fee2fb414b/reading-notes/notes_md"
TODAY = "2026-09-04"


def esc(s):
    """Escape pipe characters for markdown tables."""
    if not s:
        return ""
    return s.replace("|", "\\|").replace("\n", " ").strip()


def format_date(ts):
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return ""


def generate_note(data):
    info = data["bookInfo"]
    title = info["title"]
    author = info.get("author", "")
    progress = info.get("readingProgress", 0)
    note_count = info.get("noteCount", 0)
    review_count = info.get("reviewCount", 0)

    bm_data = data.get("bookmarks", {})
    if isinstance(bm_data, dict):
        chapters_list = bm_data.get("chapters", [])
        bookmarks = bm_data.get("updated", [])
    else:
        chapters_list = []
        bookmarks = []

    rv_data = data.get("reviews", {})
    if isinstance(rv_data, dict):
        reviews = rv_data.get("reviews", [])
    else:
        reviews = []

    # Build chapter lookup: chapterUid -> {title, chapterIdx}
    chapter_map = {}
    for ch in chapters_list:
        uid = ch.get("chapterUid")
        if uid is not None:
            chapter_map[uid] = {
                "title": ch.get("title", "未命名章节"),
                "idx": ch.get("chapterIdx", 9999),
            }

    # Group bookmarks by chapterUid
    by_chapter = defaultdict(list)
    for bm in bookmarks:
        uid = bm.get("chapterUid", 0)
        by_chapter[uid].append(bm)

    # Sort chapters by chapterIdx
    sorted_chapters = sorted(
        by_chapter.keys(),
        key=lambda uid: chapter_map.get(uid, {"idx": 9999})["idx"],
    )

    lines = []

    # Title
    lines.append(f"# 《{title}》读书笔记")
    lines.append("")

    # Book info table
    lines.append("| 项目 | 内容 |")
    lines.append("| --- | --- |")
    lines.append(f"| 书名 | {esc(title)} |")
    lines.append(f"| 作者 | {esc(author)} |")
    lines.append(f"| 阅读进度 | {progress}% |")
    lines.append(f"| 划线 | {note_count} 条 |")
    lines.append(f"| 想法 | {review_count} 条 |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 划线笔记
    if bookmarks:
        lines.append("## 划线笔记")
        lines.append("")

        for uid in sorted_chapters:
            ch_info = chapter_map.get(uid, {"title": "未命名章节"})
            ch_title = ch_info["title"]
            bms = by_chapter[uid]
            # Sort bookmarks by createTime within chapter
            bms_sorted = sorted(bms, key=lambda b: b.get("createTime", 0))

            lines.append(f"### {ch_title}")
            lines.append("")

            for i, bm in enumerate(bms_sorted, 1):
                text = bm.get("markText", "").strip()
                if text:
                    lines.append(f"{i}. {text}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # 我的想法与点评
    if reviews:
        lines.append("## 我的想法与点评")
        lines.append("")

        reviews_sorted = sorted(reviews, key=lambda r: r.get("review", {}).get("createTime", 0))

        for rv in reviews_sorted:
            inner = rv.get("review", rv)
            abstract = inner.get("abstract", "").strip()
            content = inner.get("content", "").strip()
            ch_title = inner.get("chapterTitle", "")
            create_time = inner.get("createTime", 0)
            date_str = format_date(create_time)

            if abstract:
                lines.append(f"> 原文：{abstract}")
                lines.append("")
            if content:
                lines.append(content)
                lines.append("")
            meta_parts = []
            if ch_title:
                meta_parts.append(ch_title)
            if date_str:
                meta_parts.append(date_str)
            if meta_parts:
                lines.append(f"*{' ｜ '.join(meta_parts)}*")
                lines.append("")

            lines.append("---")
            lines.append("")

    # 金句收藏
    if bookmarks:
        # Top 10 longest bookmarks
        all_texts = [(bm.get("markText", "").strip(), bm.get("chapterUid"))
                     for bm in bookmarks
                     if bm.get("markText", "").strip()]
        all_texts_sorted = sorted(all_texts, key=lambda x: len(x[0]), reverse=True)
        top_quotes = all_texts_sorted[:10]

        lines.append("## 金句收藏")
        lines.append("")
        lines.append("| 序号 | 金句 |")
        lines.append("| --- | --- |")
        for i, (text, uid) in enumerate(top_quotes, 1):
            lines.append(f"| {i} | {esc(text)} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Footer
    lines.append(f"*整理日期：{TODAY} ｜ 数据来源：微信读书*")
    lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted([f for f in os.listdir(BOOKS_DIR) if f.endswith(".json")])
    success = 0
    errors = []

    for f in files:
        try:
            with open(os.path.join(BOOKS_DIR, f), "r", encoding="utf-8") as fh:
                data = json.load(fh)

            title = data["bookInfo"]["title"]
            md = generate_note(data)

            out_path = os.path.join(OUTPUT_DIR, f"{title}.md")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(md)

            success += 1
        except Exception as e:
            errors.append(f"{f}: {e}")

    print(f"Generated {success}/{len(files)} notes successfully")
    if errors:
        print("Errors:")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    main()
