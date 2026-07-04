# 知識管理與專案 Agent 系統（四工作流框架）

> 一套讓 **LLM Agent（Claude Code／Codex／Antigravity 皆可）** 幫你經營個人知識資產的**純 markdown 框架**：把 LLM 當「編譯器」與「簿記員」，你只負責策展與判斷。本 repo 是**與領域無關的空骨架**——不含任何實際資料，clone 下來就是一個乾淨系統。

## 這個 repo 提供什麼

- **可直接使用的空骨架**：四套工作流的規範檔（SPEC）、README、範本、儀表板、命令與匯入比對工具 `tools/import_diff.py`，目錄結構已就位。
- **一鍵安裝包**：[知識管理框架-安裝懶人包.md](知識管理框架-安裝懶人包.md) —— 把整份文件貼進新的 Agent 工作階段，說「請依此懶人包，在目前資料夾安裝『知識管理框架』」，即可在任何資料夾重建本骨架（本 repo 的骨架就是由它產生）。
- **就地升級包**：[知識管理框架-升級包-四工作流.md](知識管理框架-升級包-四工作流.md) —— 已安裝舊版的人用它升級到現行四套完整版，不覆蓋既有資料。

## 多 Agent 通用設計

規則正本只有一份：根目錄 [AGENTS.md](AGENTS.md)。其他都是指標檔，把 Agent 導回同一份。

| Agent | 規則載入 | skills 位置 |
|---|---|---|
| **Codex** | 原生自動讀根目錄 `AGENTS.md`（正本） | `.codex/skills/` |
| **Claude Code** | 讀 `CLAUDE.md` —— 只有一行 `@AGENTS.md` import 指標 | `.claude/skills/` |
| **Antigravity 2.0** | 讀 `.agents/AGENTS.md` —— 指標檔，導回根目錄正本 | `.agents/skills/` |

斜線命令（`/km-ready`、`/project-start`、`/project-end`、`/number-audit`）唯一定義處在 `.claude/commands/`：Claude Code 原生執行；其他 Agent 依 AGENTS.md 的「多 Agent 支援與命令對照」表讀取對應檔案照做。

## 兩種上手方式

1. **直接用本 repo**：clone（或下載 zip）→ 用 Obsidian 開啟資料夾 → 在資料夾裡啟動你的 Agent → 開始丟文件、下指令。
2. **貼安裝包**：不 clone 也行——複製《安裝懶人包》全文貼給任一 Agent，讓它在你指定的資料夾長出整套系統。

## 設計理念（一頁版）

- **四套分流**：客觀事實 → `wiki/`；你的觀點 → `personal-km/`；高頻新聞 → `trend-wiki/`；把知識用出去 → `project/`。
- **wiki 為軸心（hub-and-spoke）**：其餘三套單向參考 wiki，概念只在 wiki 一份、不重建。
- **命令觸發、無背景自動**：所有檢查／整合／回填都由使用者開口才跑；AI 只比對＋提案，裁定權永遠在使用者。
- **純文字 + git**：一切 markdown、可版控、可遷移；個人規模不需向量資料庫。

---

以下為安裝後系統自身的使用說明（骨架原文）。

# LLM 知識庫 + 專案 — 使用說明

把 LLM 當「編譯器」與「簿記員」，你只負責策展與判斷，系統幫你把零散輸入長成一座**會自己複利成長**的個人知識資產。本資料夾掛四套各司其職、彼此連動的工作流，全部純文字 markdown + git，所有筆記繁體中文。

| 工作流 | 做什麼 | 食材比喻 | 規範 | 說明 |
|---|---|---|---|---|
| **知識庫 wiki/** | 策展文件編譯成結構化 wiki（客觀事實唯一真相源） | 一般食材 | wiki/WIKI.md | wiki/README.md |
| **專案 project/** | 把知識用出去：報告/簡報六階段流水線 | 烹調 | project/PROJECT.md | project/README.md |
| **趨勢庫 trend-wiki/** | 高頻新聞低成本捕獲＋趨勢，沉澱回 wiki | 食材速記 | trend-wiki/TREND-WIKI.md | trend-wiki/README.md |
| **個人觀點庫 personal-km/** | 只收你的觀點/判斷/經驗；卡片盒 | 傳說食材 | personal-km/PERSONAL-KM.md | personal-km/README.md |

跟任一 Agent（Claude Code／Codex／Antigravity）對話時，它先讀根目錄 `AGENTS.md` 總綱判斷任務屬哪套，再讀對應子規範（Codex 原生讀取；Claude Code 經 `CLAUDE.md`、Antigravity 經 `.agents/AGENTS.md` 指標檔載入同一份）。不確定屬哪套？直接說需求即可。

## 怎麼開始（每套一句話）
- **累積知識**：文件放進 `raw/` →「匯入這份」→ 提問 →「健檢」。
- **執行任務**：交辦放進 `project/0-project-raw/` →「幫 X 專案訂目標」→ 一路到結案。
- **追趨勢**：clip 新聞放進 `trend-raw/YYYY/` →「匯入趨勢」→「X 最近趨勢」；定期季報/年報放 `trend-raw/reports/<系列>/` →「匯入季報」（自帶預測修訂追蹤）。
- **養觀點**：隨手記進 `personal-km/0-inbox/` →「消化 inbox」→ 補觀點 →「確認」進卡。

> **匯入比對助手**：`raw/`、`trend-raw/` 的匯入都先用 `tools/import_diff.py` 以**檔案內容雜湊**比對，秒判哪些是新檔、哪些是改名或重複（含同文重 clip），只匯入真正的新檔、完成後記帳。
