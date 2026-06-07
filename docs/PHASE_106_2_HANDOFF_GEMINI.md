# 🛠️ P106.2 執行交接卡 — 給 Antigravity Gemini 3.5 Flash (High)

> 角色分工：**Claude = 設計腦（已凍結計畫書）｜你 Gemini = 執行手（照規格落地）｜Claude = 審核（獨立交叉驗收）**
> 凍結計畫書：`docs/PHASE_106_2_PLAN.md`（**這是唯一真相來源，本卡是執行摘要+防雷**）
> 任務本質：移除戰報「假戰績數據」誠實紅線 + 接入手動真數據 + 裝防復發護欄。

---

## 0. 開工前必讀（照順序）
1. `docs/PHASE_106_2_PLAN.md`（凍結計畫書全文，含 7 stages / Exit Criteria / 17 層稽核）
2. 本卡的「🚨 鐵律」「防幻覺要求」「明確不做」三節
3. 動工前先 `grep` 確認每個改動點的**真實行號**（行號會漂移，計畫書的行號僅供參考、以 grep 為準）

---

## 1. 確定數據（阿喜親自提供、Claude 已核對，直接用）

S1 建 `configs/hero_combat_stats.yaml` 填入：
```yaml
# 傳說對決 英雄戰績數據（半自動・手動維護）
# 📌 更新方式：遊戲內看英雄數據 → 填下方數值（不含%）→ updated_date 改今天 → 存檔
updated_date: "2026-06-07"
source: "遊戲內官方英雄數據（熱度T1・不分段位）"
heroes:
  芽芽:
    tier: "T1"
    win_rate: 51.2
    pick_rate: 13.41
    ban_rate: 36.32
    kda: ""
```
皮皮無數據 → 不填（watchlist 仍含但走空態）。

---

## 2. 七階段執行清單（細節見計畫書 §9）

| Stage | 做什麼 | 關鍵 |
|---|---|---|
| **S1** | 建上述 yaml；`config.py` 加 `HERO_COMBAT_STATS_PATH` + `HERO_STATS_STALE_DAYS=30`；`scrapers/hero_stats.py` 移除 `mock_data`(44-47)、改 `yaml.safe_load` 讀檔回 `HeroCombatStats`（**加 `data_source` 欄位**：讀到=`manual_yaml`、無檔/無英雄=回空 dict）、修不實 docstring、移除 `httpx` import | 保留 `async` 簽名（別動 main.py:573 await） |
| **S2** | `reporter/templates/report.html`(1589-1613) 顯示真 win/pick/ban + 「真實官方數據・更新於 {updated_date}」+ 超 30 天「⚠️ 數據可能過時」+ 無資料空態「📊 戰績數據暫無可靠來源」；`reporter/generator.py` 透傳 update_date/stale/data_source | 模板**不對 yaml 值用 `\|safe`** |
| **S3** | `analyzer/sentiment.py` showcase combat_stats(708-714) 保留但標 `data_source=showcase_demo`；`generator.py` 透傳 `is_showcase`(從 `_meta`)；模板 showcase 時加「演示數據」標籤 | is_showcase 要真的流到模板 |
| **S4** | `analyzer/history.py`(178-185) 勝率預警**只對 `data_source=manual_yaml` 生效**（假數據/空不觸發假預警）；`generator.py`/main 的 manifest `_meta` 加 `combat_stats_source` + `combat_stats_age_days` | 改前先 grep 既有勝率預警測試契約 |
| **S5** | 建 `scripts/check_no_fake_stats.py`（advisory checker，見下方規格）+ 自測 | advisory：印警告但**不阻斷**；末行印邊界免責 |
| **S6** | 建 `tests/test_combat_stats_honesty.py`（≥7 案例，見下）；**第一步先實跑 `py -m pytest` 確認真實基線**；跑全套零回歸 | 基線不退（約 489，以實跑為準） |
| **S7** | 留給 Claude/阿喜：TASK_HISTORY/RISK_REGISTRY/postmortem/memory（**你做到 S6 即可，收官文件 Claude 審核後處理**） | — |

### S5 checker 規格（`scripts/check_no_fake_stats.py`）
- 掃描 production 檔（至少 `scrapers/hero_stats.py`、`reporter/generator.py`、`main.py`），偵測 `win_rate`/`pick_rate`/`ban_rate` 後直接接寫死 float literal（如 `win_rate=52.8`）
- **白名單**（這些允許寫死，不報）：`tests/`、`if __name__ == "__main__"` 區塊、`sentiment.py` 的 `_generate_fallback_summary`（showcase 合法演示）、yaml 檔本身
- **advisory**：發現也 exit 0（或明確標 advisory 不阻斷 CI）；CLI 末行印「（本檢查為字面比對啟發式，召回率僅供參考、人工覆核仍必要）」
- 自測：構造一個含寫死 `win_rate=99.9` 的字串驗 checker 抓得到、白名單路徑驗不誤報

### S6 測試 7 案例（`tests/test_combat_stats_honesty.py`）
1. `hero_stats.py` 原始碼無寫死 52.8/12.5/45.2（grep 式 assert）
2. loader 讀正常 yaml → 回正確真值 + `data_source=manual_yaml`
3. loader 遇缺檔/缺英雄/壞 yaml → 回空 dict（不 crash）
4. 空 combat_stats → 模板渲染空態「暫無可靠來源」（不顯示假數據）
5. 有資料 → 模板顯示「更新於 {date}」；updated_date 超 30 天 → 顯示過期警示
6. showcase → 模板顯示「演示數據」標籤 + `data_source=showcase_demo`
7. history 勝率預警：`manual_yaml` 真數據觸發、`showcase_demo`/空不觸發

---

## 3. 🚨 鐵律（踩到 = Claude 審核退回重做）

1. **`py` 不用 `python`**（Windows 環境，`python` 會選到 WindowsApps stub）
2. **yaml 一律 `yaml.safe_load`**，禁 `yaml.load`/`full_load`（防任意物件反序列化 RCE）
3. **模板不對 yaml 值用 `|safe`**（防 XSS）
4. **不動 `analyzer/audio_briefing.py`**（它消費誠實化後的 combat_stats 會自動誠實；:99 寫死值在 `__main__` demo，非 production）
5. **不動 `quick_demo.py`**（demo 檔）
6. **不竄改歷史 archive**（`data/` 下過去報告的假數據不回溯改，X3）
7. **不碰遊戲 API 逆向/抓包**（違 ToS+封號紅線）
8. **不要 `git push`**；commit 與否聽阿喜，預設**留 working tree 給 Claude 審核**後再決定
9. **芽芽優先**：本 Phase 是「移除芽芽假數據」，**不得**順手過濾掉任何芽芽相關文章/邏輯
10. **TASK_HISTORY.md 禁全讀**（4000+ 行）：要查用 `grep -n "^### "` 找錨點 + 精讀，別整檔讀

---

## 4. 防幻覺要求（Claude 會逐項交叉驗證）
- 每個改動附 **檔案:行號** 證據；不確定就明說「不確定」，**絕不臆測**
- 動工前先確認檔案/函式**真的存在**（grep），別照本卡行號硬改（行號會漂移）
- 宣稱「測試過」不夠——要附**實跑 pytest 的輸出**（passed 數字）
- 改下游行為（S4 history 預警）前，**先 grep 既有測試契約**確認不撞既有測試（B-024 教訓）

---

## 5. 明確不做（反膨脹）
- ❌ 重構無關代碼（只動計畫書 §10 列的 10 檔）
- ❌ 重 provider plugin 架構（loader 回統一 schema 即可，YAGNI）
- ❌ 巴哈官方帖真爬（本 Phase 不實作，Claude 會登記為待 PoC）
- ❌ 自動推播催更新

---

## 6. 完成後交付（給 Claude 審核）
做完 S1~S6 後，提供：
1. 改動檔案清單（對照計畫書 §10 的 10 檔，超出要說明）
2. `py -m pytest` 全套輸出（passed/failed 數字）
3. `py scripts/check_no_fake_stats.py` 輸出
4. 每階段一句「做了什麼 + 證據行號」

### Claude 審核的收斂判準（你會被這樣檢查，反向引導品質）
1. `grep 52.8|12.5|45.2 scrapers/hero_stats.py` → **零命中**
2. `py -m pytest` → 全綠、零回歸（≥ 基線）
3. `py scripts/check_no_fake_stats.py` → 能跑、自測過
4. 渲染端到端：有 yaml→顯真值+日期；無 yaml→空態；showcase→演示標籤
5. `git status` → 只動計畫書 §10 的 10 檔，**零越界**（沒亂改 audio_briefing/quick_demo/歷史 archive）

---

*本卡依凍結計畫書 `PHASE_106_2_PLAN.md` 衍生｜建立 2026-06-07 by Claude（設計腦）｜執行：Antigravity Gemini 3.5 Flash (High)*
