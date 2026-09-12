#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frontmatter 守門員 —— 供 Claude Code PostToolUse hook 呼叫。

用途：每次 Write/Edit 動到 vault 裡的 .md，就驗一次 YAML frontmatter，
把「寫壞了但 Obsidian 才會發現」的錯在當場擋下來。專抓兩類記錄有案的坑：

  1. 半形「冒號＋空格」未加引號 —— YAML 當成巢狀 mapping，整段 frontmatter 在
     Obsidian 消失。英文書名／報告名、行內程式碼最常中招。
  2. frontmatter 裡的 [[wikilink]] 未加引號 —— YAML 解析成巢狀陣列，不成連結。

用法：
  echo '{"tool_input":{"file_path":"x.md"}}' | python tools/check_frontmatter.py   # hook 模式
  python tools/check_frontmatter.py <檔案> [<檔案>...]                              # 手動模式

退出碼：0 = 通過或不適用；2 = 發現問題（stderr 內容會回饋給 Claude）。
只讀不改。
"""
import io
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit(0)  # 沒有 pyyaml 就靜默放行，不擋工作流

# 這些區域不檢查：外部原檔（唯讀事實基底）、暫存、工具設定
SKIP_DIRS = ("raw", "trend-raw", "tmp", "scratchpad", ".git", ".obsidian", ".trash",
             "__pycache__", "node_modules")
SKIP_PATH_PARTS = (os.sep + "0-project-raw" + os.sep,
                   os.sep + "_build" + os.sep)

FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.S)


def should_skip(path):
    if not path.lower().endswith(".md"):
        return True
    norm = os.path.normpath(os.path.abspath(path))
    parts = norm.split(os.sep)
    if any(d in parts for d in SKIP_DIRS):
        return True
    if any(p in norm for p in SKIP_PATH_PARTS):
        return True
    return not os.path.isfile(norm)


def nested_list_fields(data):
    """找出值被解析成巢狀陣列的欄位 —— 幾乎必然是 [[X]] 沒加引號。"""
    bad = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list) and any(isinstance(e, list) for e in v):
                bad.append(k)
    return bad


def check(path):
    """回傳問題描述字串；沒問題回 None。"""
    try:
        text = io.open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        return None

    m = FM_RE.match(text)
    if not m:
        return None  # 沒有 frontmatter 不是本檢查的事（缺 frontmatter 屬 lint 範疇）
    block = m.group(1)

    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        lineno = (mark.line + 2) if mark else None  # +2：跳過開頭的 ---、轉 1-based
        hint = ""
        if lineno and 1 <= lineno - 1 <= len(block.splitlines()):
            bad_line = block.splitlines()[lineno - 2]
            hint = "\n  出問題那行：%s" % bad_line.strip()[:160]
            if ": " in bad_line.split(":", 1)[-1]:
                hint += (
                    "\n  最可能原因：值裡有**半形冒號＋空格**，YAML 當成巢狀 mapping。"
                    "\n  修法：整個值用單引號包起來（值內的單引號寫成兩個），"
                    "或把半形「: 」改成全形「：」。"
                )
        return "YAML frontmatter 解析失敗（第 %s 行附近）：%s%s" % (
            lineno or "?", getattr(e, "problem", e), hint)

    bad = nested_list_fields(data)
    if bad:
        return (
            "frontmatter 欄位 %s 被解析成**巢狀陣列**——幾乎必然是 [[wikilink]] 沒加引號。"
            "\n  修法：寫成 related: [\"[[X]]\", \"[[Y]]\"]，"
            "不要寫 related: [[X]]（後者 YAML 視為陣列、不成連結）。"
            % "、".join(bad))

    return None


def collect_paths():
    if len(sys.argv) > 1:
        return sys.argv[1:]
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return []
    ti = payload.get("tool_input") or {}
    paths = []
    for key in ("file_path", "notebook_path"):
        if ti.get(key):
            paths.append(ti[key])
    for edit in (ti.get("edits") or []):
        if isinstance(edit, dict) and edit.get("file_path"):
            paths.append(edit["file_path"])
    return paths


def main():
    problems = []
    for path in collect_paths():
        if should_skip(path):
            continue
        msg = check(path)
        if msg:
            problems.append("⚠️ %s\n  %s" % (path, msg))
    if problems:
        sys.stderr.write("frontmatter 檢查未通過，請修正後再繼續：\n"
                         + "\n".join(problems) + "\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
