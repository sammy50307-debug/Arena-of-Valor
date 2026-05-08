---
name: hot-deployer
type: exec
status: in-use
schema_version: 1
version: 1.0.0
description: 自動偵測最新 HTML 戰報並 git push 至 GitHub Pages 戰情看板

when_to_use:
  - 需要將最新 HTML 戰報部署到 GitHub Pages 時
  - 主公說「把報告推上去」「發布報告」「更新戰情看板」
  - 生成報告後需要立即上線供外部訪問
when_NOT_to_use:
  - 生成戰報內容本身 → 先跑資料分析流程
  - 查詢英雄走勢 → 用 history-trend-query
trigger_keywords: [部署, deploy, GitHub Pages, 戰報上線, 推上去, 發布報告, 更新看板, 熱部署, hot-deploy]

example_invocations:
  - input: "把最新的報告推上 GitHub Pages"
    skill: hot-deployer
    v1_trigger_block: |
      🪧 [hot-deployer 已觸發]
      ├─ 觸發理由：匹配 trigger_keyword「推上 GitHub Pages」
      ├─ 信心分數：0.94
      ├─ 來源層：主公口頭
      └─ 動作：執行 hot-deployer

entry_points:
  cli: "python -m skills.hot_deployer"
  import: "skills.hot_deployer"
  prompt_paste: "adapters/prompt_paste/hot-deployer.md"
  claude_slash: null

environments:
  ide: true
  terminal: true
  antigravity: false
  pure_llm: false

deployed_to: [claude-project]
requires:
  python: ">=3.10"
  packages: []
depends_on: []
last_used: 2026-05-09
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[hot-deployer 已啟動]`。

# 熱部署儀 (Hot Deployer)

這是「芽芽戰情室」Milestone 3 的壓軸特種兵 (Phase 54)。過去每次生成新戰報後，需要人工執行 git add / commit / push 才能更新看板。本熱部署儀將整個部署流程自動化，讓戰情看板始終保持最新狀態。

## 🎯 完整部署流程

1. **偵測最新報表**：掃描 `data/reports/` 中依修改時間排序的最新 HTML 戰報。
2. **同步至 ui_previews/**：`shutil.copy2` 複製報表，並自動補全背景圖 `yaya_bg.png`。
3. **更新 index.html**：以正規表達式替換 index.html 中指向舊報表的連結。
4. **Git 推送部署**：自動 `git add → commit → push`，帶有時間戳的 commit 訊息。

## 🛠️ 目錄結構

```
hot-deployer/
├── SKILL.md
├── scripts/
│   └── deployer.py   # HotDeployer 主類別
└── test_skill.py     # 4 項自動化測試（dry_run 模式）
```

## ⚙️ 參數

| 參數 | 說明 |
|------|------|
| `dry_run=True` | 僅本地同步，跳過 git push（測試用）|
| `dry_run=False` | 完整部署，執行 git push（正式用）|

## 📊 輸出格式

```json
{
  "status": "success",
  "report": "aov_report_2026-04-19.html",
  "synced_to": "ui_previews/aov_report_2026-04-19.html",
  "index_updated": true,
  "git": { "status": "success", "commit_message": "deploy: ..." },
  "dry_run": false,
  "deployed_at": "2026-04-19T09:00:00"
}
```

## 🚀 相依套件
- 純 Python 標準庫（`shutil`, `subprocess`, `pathlib`），無需額外安裝。
