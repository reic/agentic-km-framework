#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract.py — 把 docx / pptx / xlsx / pdf / md 統一抽成 UTF-8 Markdown，並可選擇匯出內嵌圖片。

【為什麼有這支】
內建 Read 工具只吃純文字/圖像；docx/pptx/pdf 是容器格式，得先抽成純文字才讀得到。
這支把三種抽取手段收斂成一個介面：
  - docx / pptx / xlsx → markitdown（微軟官方，保留粗體/連結/表格，輸出天生是 markdown）
  - pdf                → pypdf（文字流；掃描型 PDF 仍需另外 OCR，非本工具範圍）
  - md / txt           → 直接讀（passthrough）
內嵌圖片走 zipfile 直取（docx/pptx/xlsx 本質是 ZIP，圖在 word|ppt|xl/media/），原檔無損。

【用法】
  python tools/extract.py <輸入檔> [--out <輸出.md>] [--images <資料夾>] [--print]

  --out <檔>     抽出的 markdown 寫到這個 UTF-8 檔（給 Read 工具分頁精讀，省 token）。
                 省略且未加 --print 時，預設寫到與輸入同名的 <輸入>.extract.md（放系統暫存或指定處）。
  --images <夾>  把內嵌圖片解到這個資料夾（僅 docx/pptx/xlsx 有效）；回報每張檔名與大小。
  --print        直接印到 stdout（PYTHONUTF8=1 已設，繁中不亂碼）。小檔速覽用；大檔請用 --out。

【設計原則】
  - 只讀輸入、永不改動輸入檔（raw 唯讀鐵律）。輸出/圖片一律寫到另一處。
  - 抽取失敗時明確報錯，不吞例外、不編造內容。

【相依】
  pip install "markitdown[docx,pptx,xlsx,pdf]" pypdf
"""
import argparse
import os
import sys
import zipfile

# ZIP 型 Office 檔的內嵌圖片目錄前綴
_MEDIA_PREFIXES = ("word/media/", "ppt/media/", "xl/media/", "word/embeddings/")
_MARKITDOWN_EXT = {".docx", ".pptx", ".xlsx"}
_TEXT_EXT = {".md", ".txt", ".markdown"}


def extract_text(path: str) -> str:
    """依副檔名選抽取手段，回傳 markdown/純文字字串。"""
    ext = os.path.splitext(path)[1].lower()
    if ext in _TEXT_EXT:
        with open(path, encoding="utf-8") as f:
            return f.read()
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        parts = []
        for i, page in enumerate(reader.pages, 1):
            parts.append(f"\n\n<!-- === page {i} === -->\n")
            parts.append(page.extract_text() or "")
        return "".join(parts)
    if ext in _MARKITDOWN_EXT:
        from markitdown import MarkItDown
        return MarkItDown().convert(path).text_content
    raise SystemExit(f"[extract] 不支援的副檔名：{ext}（支援 docx/pptx/xlsx/pdf/md/txt）")


def extract_images(path: str, outdir: str) -> list:
    """從 ZIP 型 Office 檔解出內嵌圖片到 outdir，回傳 (檔名, bytes) 清單。"""
    ext = os.path.splitext(path)[1].lower()
    if ext not in _MARKITDOWN_EXT:
        print(f"[extract] --images 僅支援 docx/pptx/xlsx；{ext} 略過（PDF 內圖請用 pdf skill）")
        return []
    os.makedirs(outdir, exist_ok=True)
    saved = []
    with zipfile.ZipFile(path) as z:
        media = [n for n in z.namelist()
                 if n.startswith(_MEDIA_PREFIXES) and not n.endswith("/")]
        for n in media:
            data = z.read(n)
            # 前綴用來源目錄去重命名，避免 word/ppt 同名 imageN 撞檔
            tag = n.split("/")[0]
            base = f"{tag}_{os.path.basename(n)}"
            dest = os.path.join(outdir, base)
            with open(dest, "wb") as f:
                f.write(data)
            saved.append((dest, len(data)))
    return saved


def main() -> None:
    ap = argparse.ArgumentParser(description="docx/pptx/xlsx/pdf/md → UTF-8 Markdown（+可選圖片匯出）")
    ap.add_argument("input", help="輸入檔路徑")
    ap.add_argument("--out", help="markdown 輸出檔（UTF-8）")
    ap.add_argument("--images", help="內嵌圖片匯出資料夾（僅 docx/pptx/xlsx）")
    ap.add_argument("--print", dest="to_stdout", action="store_true", help="直接印到 stdout")
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        raise SystemExit(f"[extract] 找不到輸入檔：{args.input}")

    text = extract_text(args.input)

    if args.to_stdout:
        sys.stdout.write(text)
        sys.stdout.write("\n")
    else:
        out = args.out or (args.input + ".extract.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[extract] 已寫出 {len(text):,} 字 → {out}")

    if args.images:
        saved = extract_images(args.input, args.images)
        if saved:
            print(f"[extract] 匯出 {len(saved)} 張內嵌圖片 → {args.images}")
            for dest, n in saved:
                print(f"  - {os.path.basename(dest)}  ({n:,} bytes)")
        else:
            print("[extract] 無內嵌圖片")


if __name__ == "__main__":
    main()
