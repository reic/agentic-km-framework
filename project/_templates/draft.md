---
title: <專案中文名> — 成稿 / 交付物清單（draft manifest）
type: draft
project: <proj-slug>
created: YYYY-MM-DD
updated: YYYY-MM-DD
source_report: ["[[<proj-slug>-report]]"]
tags: [draft, deliverable]
---

# <專案中文名> — 成稿 / 交付物清單

> 9-draft 是 `4-report` markdown 內容的**格式化交付物**。內容唯一真相源仍是 report；本頁只登記交付物的格式規格、版本、產生器與 QA 狀態。

## 交付物清單
| 交付物（檔名） | 格式 | 來源 report | 版本 | QA 狀態 |
|---|---|---|---|---|
| <第一章_….docx> | docx | [[<proj-slug>-report]] | v0.1 | 待人工開檔 QA |

## 格式規格
- **docx**：（例）版面/邊界、中英字型、標題與內文字級、行距、表格編號＋來源列、頁首頁尾。依 `0-project-raw` 的格式要求填寫。
- **pptx**：（例）配色 / 字型 / 字級、每章獨立 deck。

## 產生器
- 腳本：`9-draft/_build/<build-docx.js / build-pptx.js>`（可重跑；列依賴）。

## 出版清理檢查
- [ ] 移除 frontmatter 與撰稿署名
- [ ] 內部 wiki 連結 `[[…]]` → 可讀來源標註
- [ ] 圖／表編號與來源列齊

## 交付前 QA（本機無渲染引擎時務必人工確認）
- [ ] 分頁 / 頁首頁尾　- [ ] 字型正確（中文不變方框）　- [ ] 表格未溢出版面

## 相關
- 內容草稿：[[<proj-slug>-report]]
- 進度：[[<proj-slug>-status]]
