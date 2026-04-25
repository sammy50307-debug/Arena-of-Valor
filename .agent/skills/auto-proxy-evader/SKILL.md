---
name: auto-proxy-evader
description: 抗封鎖自適應偽裝兵，專為爬蟲部隊提供動態 User-Agent 輪替、自動指數退避 (Exponential Backoff) 與請求重試機制，徹底防禦 403 Forbidden 與 429 Too Many Requests 阻擋。
version: 1.0.0
---

> ⚡ **啟動標記**：請在執行此 skill 時，先在回覆中明確標註 `[auto-proxy-evader 已啟動]`。

# 抗封鎖自適應偽裝兵 (Auto Proxy Evader)

這是「芽芽戰情室」Milestone 1 的最終防線 (Phase 48)。當爬蟲頻繁訪問各大論壇時，極易觸發對方伺服器的 WAF (Web Application Firewall) 防禦，導致 IP 被 Ban 或遭遇 `403 Forbidden` / `429 Too Many Requests`。

本 Skill 作為爬蟲系統的「外部裝甲」，透過隨機切換瀏覽器指紋 (User-Agent) 偽裝成不同裝置，並在遇到封鎖時自動進行帶有「指數退避 (Exponential Backoff)」的喘息重試，力保每一次情報抓取任務不致崩潰。

## 🎯 核心工作流程

1. **隨機偽裝 (UA Rotation)**：請求發出前，自動從超過 20 組真實的 Desktop/Mobile User-Agent 池中隨機挑選一組作為指紋。
2. **網路掛載 (Request Wrapping)**：將原生的 `requests.get()` 封裝至我們的安全殼層中。
3. **退避重試 (Exponential Backoff)**：若遭遇封鎖或網路超時，程式不會立刻報錯崩潰，而是等待 `1秒 -> 2秒 -> 4秒 -> 8秒` 後依序自動更換身份重試，最高 3 次。
4. **安全落地**：成功取得 HTML 後交由我們的「網頁蒸餾器 (Phase 45)」接手。

## 🛠️ 目錄結構

```
auto-proxy-evader/
├── SKILL.md                 # 您正在閱讀的技能指令核心
├── scripts/
│   └── evader.py            # 外殼防禦裝甲 (包含 UAPool 與 RetryTracker)
└── test_skill.py            # 抗壓測試：模擬遭阻擋後的自適應表現
```

## 🚀 相依套件要求
- `requests`：標準 HTTP 客戶端 (需用我們封裝過後的版本)
- `tenacity` (可選)：用來實現更高級的重試邏輯，但為了輕量化，我們在此版直接使用純 Python 原生實作。
