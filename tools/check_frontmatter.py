#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frontmatter 守門員 —— 供 Claude Code PostToolUse hook 呼叫。

用途：每次 Write/Edit 動到 vault 裡的 .md，就驗一次 YAML frontmatter，
把「寫壞了但 Obsidian 才會發現」的錯在當場擋下來。專抓三類記錄有案的坑：

  1. 半形「冒號＋空格」未加引號 —— YAML 當成巢狀 mapping，整段 frontmatter 在
     Obsidian 消失。英文書名／報告名、行內程式碼最常中招。
  2. frontmatter 裡的 [[wikilink]] 未加引號 —— YAML 解析成巢狀陣列，不成連結。
  3. 缺少結尾分隔線 --- —— 最常見型態是結尾的 --- 被接在欄位行尾（實測案例：
     `tags: [...]---`），Obsidian 完全無法呈現該頁 frontmatter。
     作者自用庫一次全庫掃描就找到 7 檔有此缺陷，而當時的本工具
     **全部誤報通過** —— 因為舊版用正規式抓 frontmatter，抓不到就當「這頁沒有
     frontmatter」而靜默放行。本版改為逐行判定：開頭是 --- 就一定要找到結尾。

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

# frontmatter 不該比這更長；超過就視為「找不到結尾分隔線」，避免把正文的水平線
# （內容頁大量使用 --- 分節）誤當成 frontmatter 結尾、把整段正文丟去 YAML 解析。
MAX_FM_LINES = 100

# 結尾分隔線被併進欄位行尾的簽名，如 `tags: [a, b]---`。
# 要求 --- 緊貼前一個非空白字元（`]---`、`abc---`），避免誤判正常值裡的破折號
# （`title: A --- B` 不會命中，因為它不以 --- 結尾；`title: A ---` 也不會，因為前面是空白）。
MERGED_DELIM_RE = re.compile(r"^[A-Za-z_][\w-]*\s*:.*[^\s-]---[ \t]*$")


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


def split_frontmatter(text):
    """逐行切出 frontmatter。

    回傳 (block, err)：
      (None, None)  —— 這頁沒有 frontmatter，不是本檢查的事（缺 frontmatter 屬 lint 範疇）
      (block, None) —— 切出 frontmatter 內容，交給 YAML 檢查
      (None, err)   —— 開頭有 --- 但結構壞了（找不到結尾分隔線）

    刻意不用正規式：舊版 `^---\\n(.*?)\\n---` 在結尾分隔線被併進欄位行尾時
    匹配失敗，然後被當成「沒有 frontmatter」放行，正是漏抓第三類坑的原因。
    """
    lines = [l.rstrip("\r") for l in text.split("\n")]
    if not lines or lines[0].lstrip("﻿").strip() != "---":
        return None, None

    limit = min(len(lines), MAX_FM_LINES + 1)
    for i in range(1, limit):
        s = lines[i]
        if s.strip() == "---":
            return "\n".join(lines[1:i]), None
        # 先於「找結尾」偵測併行簽名：否則正文稍後的水平線 --- 會被誤當成結尾，
        # 錯誤照樣會被抓到（YAML 解析失敗），但訊息指不到真正的病灶。
        if MERGED_DELIM_RE.match(s.rstrip()):
            return None, (
                "frontmatter 的**結尾分隔線 --- 被接在欄位行尾**，因此這頁沒有合法的"
                "結尾分隔線，Obsidian 會完全無法呈現其 frontmatter。"
                "\n  出問題那行：%s" % s.strip()[:160] +
                "\n  修法：把行尾的 --- 移到下一行、單獨成行。")

    return None, (
        "frontmatter **缺少結尾分隔線 ---**（第 1 行是 ---，但接下來 %d 行內找不到"
        "單獨成行的 ---）。Obsidian 會因此完全無法呈現這頁的 frontmatter。"
        % (limit - 1))


def check(path):
    """回傳問題描述字串；沒問題回 None。"""
    try:
        text = io.open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        return None

    block, err = split_frontmatter(text)
    if err:
        return err
    if block is None:
        return None

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
