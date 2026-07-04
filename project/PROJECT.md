# 專案工作流 — 操作規範（PROJECT）

> 涉及專案任務（訂目標、寫指引、追進度、寫報告、結案）先讀這份。共用慣例見 ../CLAUDE.md。
> wiki 累積知識；專案把知識**用出去**：一個專案 = 一條從訂目標到結案的流水線。

## 階段與執行順序
```
0 project-raw → 1 goal → 2 guide → 3 status → 4 report → 9 draft → 5 finish
  原始交辦       目標     執行指引   進度追蹤   內容草稿    成稿交付   結案+回填wiki
   (唯讀)               ↑回讀wiki            (markdown)  (docx/pptx)  ↓回填wiki
```
> `9-draft`（成稿/交付物）排在 report 之後、finish 之前；中間編號 6–8 保留作未來彈性。**執行順序 0→1→2→3→4→9→5**。

## 階段定義
- **0 project-raw**：原始輸入（會議記錄、交辦、需求）。不可變、只讀不改。
- **1 goal**：目標、範圍（含/不含）、成功/驗收標準、里程碑。觸發語「幫 X 專案訂目標」。
- **2 guide**：從 goal＋會議記錄萃取「怎麼做」，並標注該回讀哪些 wiki 頁（`wiki_refs`）。觸發語「整理撰寫指引」。
- **3 status**：每專案一份、持續追加（新的在最上面）：進度、完成度、下一步、卡點。觸發語「更新 X 專案進度」。
- **4 report**：報告內容主體，一律 markdown（便於版控、回讀 wiki、記版本）。**動筆前先回讀 `guide.wiki_refs` 指向的最新 wiki 頁**；以 `version` 記版本。**引用數字必帶基準**：每個百分比/頭條數字標明分母/範圍/年份/口徑，轉述 wiki 數字逐字保留限定詞、不可換分母；交稿前可用 `/number-audit` 做基準稽核。觸發語「依 guide 寫報告」。格式化交付不在本階段。
- **9 draft**：把 report 依指定格式轉成實際交付物（docx/pptx/xlsx）。內容唯一真相源仍是 report，改內容先改 report 再重產。可重跑的產生器放 `9-draft/_build/`；交付前人工 QA（分頁/字型/表格）。觸發語「出 docx／簡報／定稿」。
- **5 finish**：結案三步——①對照 goal 評估；②把 1-goal/2-guide/3-status/4-report 的精華併入 finish 後**刪除流程殘留檔**（已結案專案流程階段不留資料，單一真相落在 finish；交付物 docx/pptx 保留）；③把可沉澱、跨專案可重用的洞見**回填 wiki**。觸發語「結案」。刪除前先列清單經使用者確認。

## 命名慣例
同專案文件共用 slug：`<proj>-goal/-guide/-status/-report/-draft/-finish`。多份報告用 `<proj>-report-<子題>`。9-draft 交付物依章節/交付物名命名（非 slug）。其餘見 ../CLAUDE.md。

## 橋接（單向參考 wiki + 結案回填）
寫 guide/report 前回讀最新 wiki 頁並標 `wiki_refs`；finish 把洞見回填 wiki。亦可單向引用 trend-wiki 趨勢頁、personal-km 觀點卡當報告素材（卡記 `used_in` 回指）。
> **每一步都回 index-project.md 同步**該專案的階段／完成度／下一步，並維護「執行中／待啟動／已結案」分區。

## 換視窗接續（跨對話）
project 任務常跨天、跨視窗（含 Code↔Cowork）。開始前 `/project-start [slug]`（讀 index＋最新 status 日誌接進度，只讀不寫）；告一段落或要換視窗前 `/project-end [slug]`（落一則新 status 日誌＋同步 index，收尾問 commit）。命令內容見 `.claude/commands/project-start.md`／`project-end.md`。
