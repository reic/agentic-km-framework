#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_diff.py — 匯入比對工具（內容定址 manifest），通用於三種來源區：

  區域                     manifest（自動預設）                  匯入意義
  raw/                  → wiki/_import/raw-manifest.tsv          深編譯成 wiki 文章
  trend-raw/YYYY/       → trend-wiki/_import/news-manifest.tsv   stream 一行
  trend-raw/reports/    → trend-wiki/_import/reports-manifest.tsv 更新指標頁（每版）

用內容雜湊（MD5）當來源檔身分證，比對「磁碟現況」vs「manifest 已知狀態」，回報：
  🆕新檔(待匯入) / ♻️同文重複 / ✏️改名(內容同舊檔換名) / ❌失蹤 / ✅已匯入。
去重：full MD5 抓位元組相同；對 .md 另算 body_md5（去 frontmatter＋收斂空白）抓「同文重 clip」。
鐵則：只讀來源，永不修改 raw/trend-raw；manifest 與 log 寫在工作流目錄的 _import/ 下。

用法：
  python tools/import_diff.py status    raw
  python tools/import_diff.py bootstrap  raw
  python tools/import_diff.py commit     raw --batch 2026-06-24 --target "articles/xxx"
  python tools/import_diff.py status    trend-raw/2026
  python tools/import_diff.py bootstrap  trend-raw/reports        # reports 自動遞迴子系列夾
選項：
  --manifest <path>   覆寫自動預設
  --log <path>        覆寫自動預設
  --recursive         遞迴子目錄（reports 自動開啟）
  --date YYYY-MM-DD   commit/bootstrap 記的日期（預設今天）
  --batch / --target  commit 用：批次名 / 去向（stream 批次或 wiki 文章）
"""
import os, re, sys, csv, hashlib, argparse, unicodedata, datetime

COLS = ["md5","body_md5","rel_path","filename","size","mtime","published","status","import_date","target","dup_of","note"]
EXCLUDE_NAMES = {"README.md", "readme.md"}
EXCLUDE_DIRS = {"attachments"}  # 圖片沉澱區（trend-raw/attachments）：屬 raw 但非匯入來源，永不掃描

def norm(s):
    """比對用正規化：NFC＋去尾端反斜線（表格內 \\| 跳脫）＋收斂空白。"""
    s = unicodedata.normalize('NFC', s)
    s = s.rstrip('\\').strip()
    return re.sub(r'\s+', ' ', s).strip()

def file_md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()

def body_md5(path):
    """.md 內文指紋：去開頭 frontmatter、NFC、收斂空白後 hash。非 .md 回空字串。"""
    if not path.lower().endswith('.md'):
        return ''
    try:
        txt = open(path, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''
    if txt.startswith('---'):
        end = txt.find('\n---', 3)
        if end != -1:
            txt = txt[end+4:]
    txt = unicodedata.normalize('NFC', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return hashlib.md5(txt.encode('utf-8')).hexdigest()

def extract_published(path):
    """讀 .md frontmatter 的 published: YYYY-MM-DD（新聞發布日，非匯入/mtime）。抓不到回空字串。"""
    if not path.lower().endswith('.md'):
        return ''
    try:
        txt = open(path, encoding='utf-8', errors='replace').read()
    except Exception:
        return ''
    if not txt.startswith('---'):
        return ''
    end = txt.find('\n---', 3)
    if end == -1:
        return ''
    m = re.search(r'^published:\s*"?(\d{4}-\d{2}-\d{2})"?\s*$', txt[3:end], re.MULTILINE)
    return m.group(1) if m else ''

def scan_area(area, recursive=False):
    """掃描 area 下的檔，回傳 list[dict]。跳隱藏檔、README、_import/_templates 等底線目錄。"""
    out = []
    area_n = area.replace('\\', '/').rstrip('/')
    if recursive:
        walk = []
        for root, dirs, files in os.walk(area_n):
            dirs[:] = [d for d in dirs if not d.startswith('_')
                       and not d.startswith('.') and d not in EXCLUDE_DIRS]
            for fn in files:
                walk.append(os.path.join(root, fn))
    else:
        walk = [os.path.join(area_n, n) for n in os.listdir(area_n)
                if os.path.isfile(os.path.join(area_n, n))
                and n not in EXCLUDE_DIRS]
    skipped = []
    for full in sorted(walk):
        name = os.path.basename(full)
        if name.startswith('.') or name in EXCLUDE_NAMES:
            continue
        try:
            st = os.stat(full)
            row = {
                "md5": file_md5(full),
                "body_md5": body_md5(full),
                "rel_path": full.replace('\\', '/'),
                "filename": name,
                "size": str(st.st_size),
                "mtime": datetime.date.fromtimestamp(st.st_mtime).isoformat(),
                "published": extract_published(full),
            }
        except OSError as e:
            # 讀不到的檔（如 Windows 超長路徑 >260 字元、權限、暫時鎖定）不讓整批崩潰：
            # 跳過並警告，讓其餘檔照常比對。修正辦法見警告訊息。
            skipped.append((full, e))
            continue
        out.append(row)
    if skipped:
        warn("⚠️ 有 %d 個檔讀不到、已跳過（不影響其餘比對）：" % len(skipped))
        for full, e in skipped:
            warn("   - %s ｜ %s" % (full.replace('\\', '/'), e))
        warn("   → 多半是 Windows 檔名/路徑超過 260 字元。解法：縮短檔名，")
        warn("     或啟用長路徑（登錄檔 LongPathsEnabled=1）後重跑。")
    return out

def load_manifest(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8', newline='') as f:
        return [dict(r) for r in csv.DictReader(f, delimiter='\t')]

def save_manifest(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter='\t', extrasaction='ignore')
        w.writeheader()
        for r in sorted(rows, key=lambda x: x.get('rel_path', '')):
            w.writerow({c: r.get(c, '') for c in COLS})

def append_log(path, line):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, 'a', encoding='utf-8') as f:
        if new:
            f.write("# 匯入事件日誌（append-only；由 import_diff.py 寫入）\n\n")
            f.write("| 日期 | 區域 | 批次 | 新增 | 重複 | 失蹤 | 去向 |\n|---|---|---|---|---|---|---|\n")
        f.write(line + "\n")

def classify(disk, manifest):
    """以 rel_path 為身分鍵；md5/body_md5 偵測改名與同文。回傳分類 dict。"""
    by_path = {norm(r['rel_path']): r for r in manifest}
    by_md5, by_body = {}, {}
    for r in manifest:
        by_md5.setdefault(r['md5'], r)
        if r.get('body_md5'):
            by_body.setdefault(r['body_md5'], r)
    res = {"new": [], "dup": [], "rename": [], "known": []}
    seen_md5, seen_body = {}, {}
    for d in disk:
        if norm(d['rel_path']) in by_path and by_path[norm(d['rel_path'])]['md5'] == d['md5']:
            res["known"].append(d); continue
        if d['md5'] in by_md5:
            d['dup_of'] = by_md5[d['md5']]['filename']; res["rename"].append(d); continue
        if d['body_md5'] and d['body_md5'] in by_body:
            d['dup_of'] = by_body[d['body_md5']]['filename']; res["dup"].append(d); continue
        if d['md5'] in seen_md5:
            d['dup_of'] = seen_md5[d['md5']]; res["dup"].append(d); continue
        if d['body_md5'] and d['body_md5'] in seen_body:
            d['dup_of'] = seen_body[d['body_md5']]; res["dup"].append(d); continue
        seen_md5[d['md5']] = d['filename']
        if d['body_md5']:
            seen_body[d['body_md5']] = d['filename']
        res["new"].append(d)
    disk_paths = {norm(d['rel_path']) for d in disk}
    disk_md5 = {d['md5'] for d in disk}
    res["missing"] = [r for r in manifest
                      if norm(r['rel_path']) not in disk_paths and r['md5'] not in disk_md5]
    return res

def build_stream_target_map(stream_dir):
    """掃 stream/*.md 原檔連結，回傳 normfilename(去副檔名) -> 批次名。僅供 news bootstrap。"""
    m = {}
    linkre = re.compile(r'\[\[([^\]|]+)')
    for root, _, files in os.walk(stream_dir):
        for fn in files:
            if not fn.endswith('.md'):
                continue
            batch = os.path.splitext(fn)[0]
            txt = open(os.path.join(root, fn), encoding='utf-8', errors='replace').read()
            for mt in linkre.finditer(txt):
                m.setdefault(norm(mt.group(1).replace('trend-raw/2026/', '')), batch)
    return m

def is_news_area(area):
    a = area.replace('\\', '/').rstrip('/')
    return a.startswith('trend-raw') and 'reports' not in a

def default_manifest(area):
    a = area.replace('\\', '/').rstrip('/')
    if a == 'raw' or a.startswith('raw/'):
        return 'wiki/_import/raw-manifest.tsv'
    if 'reports' in a:
        return 'trend-wiki/_import/reports-manifest.tsv'
    return 'trend-wiki/_import/news-manifest.tsv'

def default_log(area):
    a = area.replace('\\', '/').rstrip('/')
    return 'wiki/_import/import-log.md' if (a == 'raw' or a.startswith('raw/')) \
        else 'trend-wiki/_import/import-log.md'

def out(s=""):
    sys.stdout.buffer.write((s + "\n").encode('utf-8'))

def warn(s=""):
    sys.stderr.buffer.write((s + "\n").encode('utf-8'))

def cmd_status(args):
    disk = scan_area(args.area, args.recursive)
    manifest = load_manifest(args.manifest)
    r = classify(disk, manifest)
    out("區域：%s ｜ 磁碟 %d 檔 ｜ manifest %d 列 ｜ %s"
        % (args.area, len(disk), len(manifest), args.manifest))
    out("🆕 新檔(待匯入) %d ｜ ♻️同文重複 %d ｜ ✏️改名/內容重複 %d ｜ ❌失蹤 %d ｜ ✅已匯入 %d"
        % (len(r["new"]), len(r["dup"]), len(r["rename"]), len(r["missing"]), len(r["known"])))
    if r["new"]:
        out("\n=== 🆕 新檔（只匯入這些）===")
        for d in r["new"]: out("  + " + d['filename'])
    if r["dup"]:
        out("\n=== ♻️ 同文重複（跳過）===")
        for d in r["dup"]: out("  ~ %s  ≈ %s" % (d['filename'], d.get('dup_of', '')))
    if r["rename"]:
        out("\n=== ✏️ 改名/內容重複（跳過）===")
        for d in r["rename"]: out("  = %s  ← 內容同 %s" % (d['filename'], d.get('dup_of', '')))
    if r["missing"]:
        out("\n=== ❌ manifest 有、磁碟沒了 ===")
        for d in r["missing"][:15]: out("  ? " + d['filename'])
        if len(r["missing"]) > 15:
            out("  …及其餘 %d 筆（完整見 manifest）" % (len(r["missing"]) - 15))
    return r

def cmd_bootstrap(args):
    disk = scan_area(args.area, args.recursive)
    tmap = build_stream_target_map(args.stream_dir) if is_news_area(args.area) else {}
    rows, seen, matched = [], {}, 0
    for d in disk:
        d['status'] = 'imported'; d['import_date'] = args.date
        if d['md5'] in seen:
            d['status'] = 'dup'; d['dup_of'] = seen[d['md5']]; d['target'] = ''; d['note'] = 'bootstrap-dup'
        else:
            seen[d['md5']] = d['filename']
            tgt = tmap.get(norm(os.path.splitext(d['filename'])[0]), '')
            if tgt: matched += 1
            d['target'] = tgt
            d['note'] = 'bootstrap' if (tgt or not tmap) else 'bootstrap(未匹配stream)'
        rows.append(d)
    save_manifest(args.manifest, rows)
    n_dup = sum(1 for d in rows if d.get('status') == 'dup')
    out("bootstrap 完成：%d 列寫入 %s" % (len(rows), args.manifest))
    if tmap:
        out("  對應到 stream 批次 %d 筆；未匹配 %d 筆；同檔重複 %d 筆"
            % (matched, len(disk) - matched - n_dup, n_dup))
    else:
        out("  全部登錄為已匯入(baseline)；同檔重複 %d 筆。註：raw/reports 的 target 留空，未來 commit 時填。" % n_dup)

def cmd_commit(args):
    disk = scan_area(args.area, args.recursive)
    manifest = load_manifest(args.manifest)
    r = classify(disk, manifest)
    by_path = {norm(x['rel_path']): x for x in manifest}
    n_new = 0
    for d in r["new"]:
        d['status'] = 'imported'; d['import_date'] = args.date
        d['target'] = args.target or args.batch; d['note'] = 'commit:' + (args.batch or '')
        by_path[norm(d['rel_path'])] = d; n_new += 1
    for d in (r["dup"] + r["rename"]):
        d['status'] = 'dup'; d['import_date'] = args.date; d['note'] = 'skip-dup:' + (args.batch or '')
        by_path[norm(d['rel_path'])] = d
    n_backfilled = 0
    for d in r["known"]:
        key = norm(d['rel_path'])
        row = by_path.get(key)
        if not row:
            continue
        for f in ("size", "mtime", "published"):
            if d.get(f) and row.get(f) != d[f]:
                row[f] = d[f]; n_backfilled += 1
    save_manifest(args.manifest, list(by_path.values()))
    append_log(args.log, "| %s | %s | %s | %d | %d | %d | %s |"
               % (args.date, args.area, args.batch or '', n_new,
                  len(r["dup"]) + len(r["rename"]), len(r["missing"]), args.target or ''))
    out("commit 完成：標記 %d 新檔為已匯入（批次 %s）；重複 %d；manifest 共 %d 列；既有列補上欄位 %d 個"
        % (n_new, args.batch or '', len(r["dup"]) + len(r["rename"]), len(by_path), n_backfilled))

def main():
    today = datetime.date.today().isoformat()
    p = argparse.ArgumentParser(description="匯入比對工具（內容定址 manifest）")
    p.add_argument('cmd', choices=['status', 'bootstrap', 'commit'])
    p.add_argument('area', help='來源目錄，如 raw / trend-raw/2026 / trend-raw/reports')
    p.add_argument('--manifest', default='')
    p.add_argument('--log', default='')
    p.add_argument('--stream-dir', default='trend-wiki/stream')
    p.add_argument('--recursive', action='store_true')
    p.add_argument('--batch', default='')
    p.add_argument('--target', default='')
    p.add_argument('--date', default=today)
    args = p.parse_args()
    if not os.path.isdir(args.area):
        out("找不到目錄：%s" % args.area); sys.exit(2)
    if not args.manifest: args.manifest = default_manifest(args.area)
    if not args.log: args.log = default_log(args.area)
    if 'reports' in args.area.replace('\\', '/'):
        args.recursive = True  # reports 依系列收，自動遞迴
    {'status': cmd_status, 'bootstrap': cmd_bootstrap, 'commit': cmd_commit}[args.cmd](args)

if __name__ == '__main__':
    main()
