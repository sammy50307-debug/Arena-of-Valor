---
name: hot-deployer
description: 熱部署儀。自動偵測 data/reports/ 中最新的 HTML 戰報，同步複製至 ui_previews/，更新 index.html 連結，並執行 git push 將戰報即時部署至 GitHub Pages 戰情看板。
version: 1.0.0
---

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
