# 趨勢 Wiki 工作流 — 操作規範（TREND-WIKI）

> 涉及高頻新聞流（匯入、抽取、趨勢查詢、沉澱）先讀這份。共用慣例見 ../CLAUDE.md。

## 為什麼要這套
一般知識庫對每份來源「深編譯＋全面回填」，對高頻新聞流（約千篇/年）會燒掉大量 token。趨勢 wiki 把「捕獲」與「沉澱」分開：捕獲每篇只抽成日誌一行（便宜、常做）；沉澱只在使用者下指令時、對有料主題做一次（昂貴、低頻）。
- **快照 vs 趨勢**：wiki 回答「現在什麼為真」；trend-wiki 回答「怎麼隨時間變／有誰握什麼」（趨勢＋盤點）。
- **鐵律**：概念唯一真相源是 wiki；trend-wiki **不重建概念**，只引用、單向沉澱回填。

## 核心心智模型（兩層，全程命令觸發）
```
第一層 捕獲 Capture（便宜、高頻）
  手動選稿（Web Clipper 等）放入 ../trend-raw/YYYY/ → 指令「匯入趨勢」
        │  便宜模型批次抽取＋標籤（不過濾，選稿你已做）
        ▼
  trend-wiki/stream/YYYY-MM/YYYY-MM-DD.md   事實日誌（每批一檔，append-only）

第二層 沉澱 Consolidate（昂貴、純命令觸發）
        │  下指令「沉澱趨勢」「更新 X 趨勢」
        ▼
  trend-wiki/topics/<實體或主題>.md   趨勢追蹤頁（可組合區塊）
        │  穩定結論 →（命令觸發）回填 wiki／新興主題畢業成新文章
```

## Phase 1 — 捕獲 Capture
入口：選稿 → 放入 `../trend-raw/YYYY/` → 指令「匯入趨勢」。
**Step 0 比對新檔**：先跑 `python tools/import_diff.py status trend-raw/YYYY`，以內容雜湊比對 `trend-wiki/_import/news-manifest.tsv`，**只抽取 🆕 新檔**（同文重複/改名自動跳過；去重採 full MD5 ＋ `.md` body 指紋，抓「同文重 clip」）。抽完跑 `commit trend-raw/YYYY --batch YYYY-MM-DD --target stream/YYYY-MM/YYYY-MM-DD.md` 記帳。manifest 另有 `published` 欄（工具自動從來源 frontmatter 抽新聞發布日）。
抽取＋標籤（便宜模型批次，一次 10–20 篇）：每篇抽成 stream 日誌**一行**：
`日期 | 來源 | 實體 | 主題標籤 | 事實類型 | 關鍵內容 | 關係(選填) | 原檔連結`
- 日期＝新聞發布日；實體＝公司/人/機構（查詢錨點，可多個）；事實類型＝財報財測/政策變動/合作進展/技術里程碑/市場數據/觀點；關鍵內容＝該篇真正的新事實（簡短，不抄全文）；關係（選填）＝主體—關係—客體。
- **附圖旗標（選填）**：來源 md 若內嵌「帶數據的圖」（走勢/市占/roadmap/盤點），在原檔欄連結後加 `📊<png檔名>`（圖在 `../trend-raw/attachments/`）；純 logo/裝飾圖不標。**只標記、不讀圖**——讀圖的昂貴動作留到 Phase 2 按需觸發。
寫入：append 到 `stream/YYYY-MM/YYYY-MM-DD.md`（當批一檔）。**不寫摘要、不回填、不交叉連結**。原文保留採混合（核心主題原檔完整留、其餘可定期歸檔；帶 `📊` 旗標指到的圖檔視同核心原檔保留）。觸發語：「匯入趨勢」。

## Phase 2 — 沉澱 Consolidate（純命令觸發）
讀相關 stream 條目（依日期/實體/主題過濾，必要時 grep 跨批次）→ 更新或新建 `topics/` 頁。**採「可組合區塊」**，依實體或主題命名，每頁按需選用：①指標時序表 ②事件時間線/敘事弧 ③盤點/關係表（角色→持有什麼→動態）④現況摘要。每條附 stream 出處；用 `[[wiki 概念頁]]` 引用、不重建。**帶旗標圖的按需讀取**：沉澱/查詢命中 `📊` 旗標且該圖對本主題重要時，才用視覺模型讀 `../trend-raw/attachments/<png>` 抽數據進表格，出處標 `(來源: <md名>, 附圖 <png>)`。觸發語：「沉澱趨勢」「更新 X 趨勢」。

## Phase 2 補充 — 定期報告型來源（特例：直接維護指標頁）
適用**低頻、高價值、結構固定的定期報告**（官方/法人季報年報，內含週期性指標＋每版修訂的展望，約 4 期/年）。與一般流程三點差異：
1. **跳過一行式 stream**：一份報告含幾十個數字，壓成一行過於失真——直接維護一張專屬 `topics/` 指標頁、每版更新；**圖表即本體**，匯入時直接用視覺模型讀圖抽數字（不需 `📊` 旗標繞路）。
2. **原檔凍結＋目錄分流**：原檔放 `../trend-raw/reports/<系列>/`（**依系列收、不按年**，因 vintage 追同系列跨年修訂），與新聞剪報 `../trend-raw/YYYY/` 實體分開；檔名帶期別前綴（如 `2026Q1-…V3`），引用標版本。
3. **仍屬趨勢、不進 wiki**：指標隨期變動留本頁滾動；只有穩定長期結論才命令觸發回填 wiki。
擴充區塊：`metric-series-quarterly` 季度時序／`metric-series-annual` 年度彙總／**`forecast-vintage` 預測修訂追蹤（本型核心，鐵則：每版加列、絕不覆蓋舊列）**／`analyst-view` 分析師看法。範本：`_templates/periodic-report-topic.md`。
**兩套匯入分流（鐵則）**：「匯入趨勢」只掃 `trend-raw/YYYY/`、絕不抓 `reports/`；定期報告一律走「**匯入季報**」。reports 比對用 `python tools/import_diff.py status trend-raw/reports`（專屬 manifest `reports-manifest.tsv`，自動遞迴系列夾）。觸發語：「匯入季報」「更新 X 季報頁」。

## Phase 3 — 查詢 Query
先看 `topics/` 頁；未更新就先跑 Phase 2。臨時查詢可直接 grep `stream/` 依實體/主題聚合即時回答（有長期價值再存成 topics 頁）。**依新聞發布日查近期重點**（如「近兩週新聞重點」）：stream 日期欄＝發布日、批次可能含補抽舊文，故要跨批次依日期欄過濾（開最近 1–2 個月的 stream 檔逐列比對），可交叉核對 manifest 的 `published` 欄。

## Phase 4 — 橋接（命令觸發）
單向參考 wiki。穩定結論回填既有概念文章；新興主題在 topics 孵化、成熟後畢業成 wiki 新文章。概念永不在 trend-wiki 另立第二份。觸發語：「把 X 趨勢回填 wiki」。

## 與其他套的關係
wiki＝沉澱目的地與唯一概念真相源；project 可引用趨勢頁當報告素材（單向）；personal-km 可把趨勢頁當論述的動態佐證、把趨勢新聞當觀點原料（單向，trend-wiki 不依賴 personal-km、不收觀點）。

## 命名慣例
stream：`stream/YYYY-MM/YYYY-MM-DD.md`（同日多批加序 `-2`）。topics：實體用公司/人 slug、主題用 kebab-case。其餘見 ../CLAUDE.md。
