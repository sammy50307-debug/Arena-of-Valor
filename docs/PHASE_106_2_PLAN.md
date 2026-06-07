# Phase 106.2 — combat_stats 假戰績誠實化（飛輪版：半自動真數據 + 防復發護欄）

> 狀態：**✅ 已凍結（2026-06-07）｜外包 Antigravity Gemini 3.5 Flash (High) 實作 → Claude 審核驗收**
> 戰線：**內容可信度 / 資料層**（誠實紅線）+ 治理（防假數據復發）——獨立於已收官 P109
> 方案：阿喜 2026-06-07 選 **方案 D 飛輪版**（自我優化飛輪模式）= 移除假數據 + 讀手動 yaml 真數據 + **反假數據 checker** + **data_source 可信度標記貫穿** + postmortem 通則化
> 鐵律：`py` 不用 `python`；TASK_HISTORY 禁全讀；改動前計畫書等同意；芽芽優先（本 Phase 是移除芽芽假數據 ≠ 過濾芽芽文）；push 前問阿喜。

---

## 📜 緣由（PoC 實測 + 飛輪分析，2026-06-07）

- PoC 實證：Garena 官方勝率子域 `herowinrate.moba.garena.tw` **已下線**（tw/vn/th 全 NXDOMAIN）；無公開 API；第三方只導流；遊戲內 API 逆向違 ToS+封號（紅線）。
- 飛輪「不壞」目標：**系統永遠不再呈現偽裝成真實的假數據**——即使阿喜忘更新、源變動、未來有人改 code，都能自我檢查潛入的假數據、永遠標明數據真假與新鮮度。
- 解法 = 半自動真數據（阿喜遊戲內看真值 → 填 yaml）+ 機械防復發護欄（checker + data_source 標記）。

---

## 🎯 動工確定數據（阿喜 2026-06-07 親自提供，已核對）

S1 建 `configs/hero_combat_stats.yaml` **直接填下方真實數據（非空範本）**：

```yaml
# 傳說對決 英雄戰績數據（半自動・手動維護）
# 📌 更新方式（每改版/每週一次即可，勝率變化慢）：
#   1. 打開傳說對決 → 英雄數據區塊
#   2. 把芽芽的 勝率/出場率/Ban率 填到下方
#   3. updated_date 改成今天日期，存檔即可
# ⚠️ 只填數值不含 %（例 51.2）
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

> 已與阿喜核對：勝率 **51.20%** / 出場率 **13.41%** / Ban率 **36.32%**、熱度 **T1**、**不分段位**。皮皮未提供（不填；watchlist 仍含皮皮但無數據→空態）。

---

## 0. Phase 元資料

| 欄位 | 內容 |
|---|---|
| **Phase 編號** | P106.2 |
| **Phase 名稱** | combat_stats 假戰績誠實化（飛輪版） |
| **凍結日期** | （待阿喜凍結） |
| **影響半徑** | **重大（10 檔）** ─ META3：4 新增 + 6 修改 |
| **預估投入時數** | 4 h |
| **Token budget** | ~90K tokens |
| **負責模型** | Opus 4.8（誠實紅線 + 跨資料流 + 防復發設計） |

## 0.5 狀態轉換清單 ─ B-002

| 對象 | 原狀態 | 新狀態 | 狀態定義 | 轉換條件 | 執行者/核准者 |
|---|---|---|---|---|---|
| `scrapers/hero_stats.py` | 偽 scraper（假裝真爬、寫死 mock） | 誠實 loader（讀手動 yaml + 帶 data_source） | 不謊稱真爬、無寫死假值、讀 yaml 真值、無資料回空、標 data_source | mock 移除+改讀 yaml+checker 鎖定 | AI 實作/阿喜核准 |
| `scripts/check_no_fake_stats.py` | （不存在） | active advisory checker | 掃 code 偵測寫死戰績潛入、誤報不阻斷 | 新增+自測 | AI 實作/阿喜核准 |

---

## 1. 目標 (Objective)

(1) 移除 combat_stats 兩路徑寫死假數據；(2) 戰績區讀 `configs/hero_combat_stats.yaml`（阿喜手填真實官方數據），顯示真值 + 「真實官方數據・更新於 X」+ 過期警示；(3) **每筆 combat_stats 帶 `data_source`（manual_yaml/none/showcase_demo），貫穿報告/archive/預警誠實標示**；(4) **新增 advisory checker 機械偵測未來寫死戰績潛入**。量化：code 內 combat_stats 區塊寫死數值 grep 零命中（showcase/測試白名單除外）、checker 能抓出植入的假數據、戰績區「真數據(標日期)/空態」二選一。

## 2. 觸發背景 (Why Now)

P106 計畫書只查到 showcase 假值、漏 production mock（hero_stats.py `# 模擬數據` pick=12.5），報告每天用 pulse-high 紅光呈現假戰績踩誠實紅線。阿喜二次追問觸發飛輪模式 → 不只止血，要裝防復發護欄（避免假數據哪天又被塞回沒人知道）+ 全鏈可追溯真假。

## 3. Entry Criteria

- [x] 前置 Phase 收官：P109(489 passed)、P108.4
- [x] 依賴已備：PyYAML 已是專案依賴
- [x] 主公核准：方案 D 飛輪版**已凍結（2026-06-07）**；段位=不分段位、stale=30天、META4≈6.5 接受
- [x] 風險登記簿無未解高風險

## 4. Exit Criteria

- [ ] A：`hero_stats.py` 無寫死假值（grep 52.8/12.5/45.2 零命中）、docstring 不謊稱真爬
- [ ] B：`configs/hero_combat_stats.yaml` 存在（schema+教學註解），loader 正確讀真值 + 帶 data_source
- [ ] C：報告真數據時顯示「真實官方數據・更新於 {date}」+ 超 stale 天數警示；無數據/壞檔 → 誠實空態不 crash
- [ ] D：showcase 顯示「演示數據」標籤（data_source=showcase_demo）
- [ ] E：data_source 貫穿——history 勝率預警只對 manual_yaml 真數據生效（不被假數據觸發假預警）；manifest `_meta.combat_stats_source`/`_age_days`
- [ ] F：`scripts/check_no_fake_stats.py` 存在、能抓植入假數據、誤報不阻斷（advisory）、含自測
- [ ] G：`tests/test_combat_stats_honesty.py` ≥7 案例全綠
- [ ] H：全套零回歸（基線 489 動工實跑確認，不可退）
- [ ] I：postmortem + yaml 更新 SOP + RISK_REGISTRY（B′ 巴哈帖待 PoC + 歷史 archive 污染期登記）

> B-001/B-003：不建多端、不新增 skill → N/A。

## 5. ROI 評估

| 項目 | 內容 |
|---|---|
| 投入 | 4 h |
| 收益等級 | **高** |
| 收益 | 解誠實紅線 + 真數據（合規）+ **機械防復發護欄**（checker 永久擋假數據潛入）+ 全鏈可追溯真假 + 修復死掉的勝率預警 |
| ROI | ✅ 值得（飛輪一次裝好防線，未來零復發成本） |

---

## 6. 17 層稽核表（重大半徑 → 全層）

### S 級（必填）
| 層 | 採用優化項 | 風險 | 緩解 |
|---|---|---|---|
| **1. 代碼** | hero_stats mock→yaml loader+data_source；checker 新增；移除 httpx；模板真數據/空態/標籤 | orphan import；async 混同步讀檔 | 清 import；保留 async 簽名不動 main.py |
| **2. 邏輯** | yaml→stats 映射、stale 計算、data_source 判定、預警只對真數據 | 日期解析失敗、缺鍵、預警誤判 | safe_load+try/except、.get 預設、解析失敗視為過期 |
| **4. 測試** | test_combat_stats_honesty(7案例)+checker 自測 | 漏驗空態/stale/data_source 貫穿 | 案例涵蓋全路徑+checker 能抓植入假數據 |
| **10. 安全** | yaml `safe_load`、模板不對 yaml 值 `\|safe` | 反序列化 RCE/XSS | safe_load 硬規；yaml 本地非外部輸入 |

### A 級（提示填）
| 層 | 採用/N-A | 風險 | 緩解 |
|---|---|---|---|
| **3. 架構** | hero_stats 偽scraper→誠實loader；checker 獨立腳本 | 介面名仍叫 scraper | docstring 明示官方源已下線、現讀手動 yaml |
| **5. 資料** | yaml schema+新鮮度+data_source 標記（核心層） | schema 漂移、阿喜填錯 | yaml 含範例教學；loader 容錯回空態 |
| **6. 可觀察性** | logger 標讀取結果；manifest `_meta.combat_stats_source/_age_days` | 無 append-only 檔 → N/A B-009 | — |
| **7. 韌性** | yaml 缺/壞/缺英雄全回空態不中斷 | loader 異常炸 main | main.py:575 已 try/except + loader 自身雙保險 |
| **13. 可維護性** | yaml 自帶教學+SOP+docstring 誠實 | 阿喜半年後忘更新法 | yaml 頂註解+SOP 入收官 |
| **14. 文件** | 計畫書+TASK_HISTORY+RISK_REGISTRY+postmortem+SOP | — | 收官五件套 |
| **15. 流程** | 標準 Phase 7 stage | — | — |

### B 級（條件式）
| 層 | 觸發 | 採用 | 風險 | 緩解 |
|---|---|---|---|---|
| **9. UX/A11y** | 改 report.html | 真數據+更新日期+過期警示+空態+演示標籤 | 過期/空態誤解成故障 | 友善誠實文案+stale 警示+SOP |
| **8 效能/11 部署/12 成本/16 隱私/17 i18n** | 未觸發 | — | — | N/A（讀小 yaml 無效能/不碰部署/零付費 API/yaml 本地非個資/單語） |

### 層級互鎖 ─ META5
- [x] Logic→Testing｜[x] Architecture→Documentation｜[x] Data→Maintainability｜[x] Security→Testing｜[ ] Performance→N/A

---

## 7. 跨切面 ─ X1-X4

### X1 可逆性
| 動作 | 可逆性 | 確認 |
|---|---|---|
| 改 6 檔 code + 新增 4 檔 | 可逆（git revert/刪檔） | — |
| commit | 可逆 | — |
| push origin/main | 半可逆 | **push 前問阿喜** |

### X2 盲區掃描
- [x] log：hero_stats logger 改標讀取結果；checker 輸出
- [x] 中間檔：dry-run 產 index.html/llm_cache → 收官 `git checkout` 還原
- [x] 系統狀態：cron 報告戰績區變真數據/空態；manifest 多 combat_stats_source 欄位；history 預警行為改變（對真數據生效）

### X3 時間敏感性
- 凍結日期：（待）／過期日期：2026-09-07（重審 stale 天數）／風險帶日期：✅
- 資料新鮮度：yaml updated_date + stale 30 天警示（可調）

### X4 多角度審查
- **主公**：移除假數據 + 接你抄的真官方數據 + 機械擋假數據復發，三贏。代價=偶爾手動更新。
- **紅隊**：唯一新輸入是本地 yaml（你維護）。硬規 `safe_load` 防 RCE、模板不 `|safe` 防 XSS。checker 本身只讀不改 code、無 injection 面。
- **接手者**：hero_stats 誠實 docstring + yaml 教學 + SOP + postmortem，半年後可懂數據來源/更新法/為何曾有假數據。
- **X4-J 自動化工具邊界**：checker 是**字面/AST 比對啟發式**——會偵測寫死戰績數值但無法判斷語意對錯，**召回率僅供參考、人工覆核仍必要**，故設 advisory 不阻斷；CLI 末行印此邊界。
- **X4-K 使用者端審查官**：阿喜可能忘更新 yaml → stale 警示主動標過時；空態/過期文案友善誠實避免誤判故障。

---

## 8. 風險清單

| # | 風險 | 機率 | 影響 | 類型 | 緩解 |
|---|---|---|---|---|---|
| R1 | 阿喜忘更新 yaml→顯示過時數據 | 高 | 中 | 業務 | stale 警示+SOP 提醒每改版更新 |
| R2 | yaml 格式填錯→解析失敗 | 中 | 中 | 業務 | safe_load+try/except 回空態；yaml 自帶範例 |
| R3 | 移除 httpx 後 orphan import | 高 | 低 | 代碼 | 移除後檢查清未用 import |
| R4 | showcase is_showcase 透傳漏接 | 中 | 低 | 代碼 | S3 端到端測試 |
| R5 | 既有測試契約鎖定假值 | 低 | 中 | 代碼 | **已查證 tests/ 零契約**，解除 |
| R6 | 基線 489 漂移 | 中 | 低 | 環境 | S6 第一步實跑 pytest |
| R7 | checker 誤報（誤抓測試/showcase 數值） | 中 | 低 | 代碼 | advisory 不阻斷+白名單(tests/__main__/showcase) |
| R8 | data_source 貫穿改多檔引回歸 | 中 | 中 | 代碼 | 每 stage 測試+小批次 |
| R9 | 改 history 預警邏輯撞既有預警測試 | 中 | 中 | 代碼 | S4 先查 history 既有預警測試契約（B-024） |

**META4 加權**：高=0；中(R1,R2,R8,R9)=4；低(R3,R4,R5,R6,R7)=2.5 → **≈6.5 分 ≥5 須請示**。已攤開：多為代碼可控/業務型且逐項緩解，無技術不可控項，請阿喜凍結時確認。

---

## 9. 工作階段 (Stages)

| Stage | 內容 | 解風險 | 驗收 |
|---|---|---|---|
| **S1 資料層地基** | 建 yaml(空範本+schema+教學)；config 加路徑+stale 天數；hero_stats mock→yaml loader（safe_load+容錯+**data_source 欄位**）+修 docstring+清 import | R2,R3 | grep 假值零命中+loader 單元測試 |
| **S2 顯示層誠實化** | report.html 真 win/pick/ban+「真實官方數據・更新於{date}」+stale 警示+空態；generator 透傳 update_date/stale/data_source | R1 | 渲染測試:有資料顯日期/無則空態/過期警示 |
| **S3 showcase 標示** | sentiment showcase 保留;generator 透傳 is_showcase;report.html「演示數據」標籤+data_source=showcase_demo | R4 | is_showcase 端到端測試 |
| **S4 data_source 貫穿** | history 勝率預警只對 manual_yaml 生效(排除假預警，先查既有預警測試契約);manifest `_meta` 加 combat_stats_source/_age_days | R8,R9 | 預警測試:真數據觸發/假數據不觸發 |
| **S5 反假數據 checker** | `scripts/check_no_fake_stats.py`(掃 production 檔偵測寫死 win/pick/ban，白名單 tests/__main__/showcase，advisory，末行印邊界)+自測 | — | checker 能抓植入假數據、誤報降級 |
| **S6 防復發測試** | test_combat_stats_honesty.py(7案例:無寫死/讀yaml/缺檔缺英雄/空態/日期+stale/showcase/data_source);**第一步實跑基線**;全套零回歸 | R5,R6 | 7 綠+489→496 零回歸 |
| **S7 收官** | TASK_HISTORY+RISK_REGISTRY(B′待PoC+歷史污染期)+postmortem+memory+yaml SOP | — | 五件套+R-NNN 連續 |

---

## 10. 影響檔案清單 ─ STR7

**新增（4）**：`configs/hero_combat_stats.yaml`｜`tests/test_combat_stats_honesty.py`｜`scripts/check_no_fake_stats.py`｜`docs/postmortems/2026-06-07-phase-106-2-combat-stats-honesty.md`

**修改（6）**：`config.py`(+2行)｜`scrapers/hero_stats.py`(mock→loader)｜`reporter/generator.py`(透傳 data_source/is_showcase/manifest)｜`reporter/templates/report.html`(真數據+日期+stale+空態+演示標籤)｜`analyzer/sentiment.py`(showcase data_source)｜`analyzer/history.py`(預警對真數據生效)

**不改（查證確認）**：`analyzer/audio_briefing.py`（消費誠實化後 combat_stats 自動誠實；:99 寫死值在 `__main__`）｜`quick_demo.py`（demo）

---

## 11. Postmortem 預埋點 ─ G6

必寫 postmortem（本 Phase 已預定寫，含通則化）：`docs/postmortems/2026-06-07-phase-106-2-combat-stats-honesty.md`

> 通則化教訓：(a) **查寫死值/假數據根因要查盡所有生產路徑**（production+fallback+showcase），P106 只查一條漏 production（延續 B-023/B-024）；(b) **假數據會讓依賴它的下游邏輯靜默失效**（history 勝率預警因假數據 52.8% 永不觸發 <47 警戒，死了很久沒人知）→ 通則：呈現假數據不只騙人，還會讓真實 guard 失靈。

---

## ✈️ Pre-flight 多視角體檢 ─ STR10（凍結前必過）

### M1 強制填表（十一視角）

| 視角 | 具體發現 |
|---|---|
| **X4-A 紅隊攻擊者** | 攻擊面：新輸入僅本地 yaml（阿喜維護非外部）。硬規緩解：yaml 必 `yaml.safe_load`（禁 full_load 防任意物件反序列化 RCE）；模板不對 yaml 值用 `\|safe`（防 XSS）。checker 只讀 code 不執行、無注入面。嚴重度低但 safe_load 不可省。 |
| **X4-B 接手者** | hero_stats 誠實 docstring（官方源已下線、現讀手動 yaml）+ yaml 自帶教學 + SOP + postmortem，接手者能完整理解數據來源、更新方式、歷史假數據成因。 |
| **X4-C 災難情境** | 情境：yaml 被改壞或缺檔致報告中斷／或顯示舊數據誤導使用者。緩解：loader safe_load+try/except 回空態不 crash；stale 警示標過時；checker 防新假數據潛入。 |
| **X4-D 5 年後** | 5 年後若官方重開數據源/API，hero_stats loader 介面可平滑換真爬；data_source 標記讓新舊源混用仍可辨識真假；yaml 半自動不會過期失效。 |
| **X4-E 終端 vs IDE** | 純 Python+Jinja+yaml+checker 腳本，無終端與 IDE 環境差異；pytest 與 checker 在兩環境結果一致，不依賴互動式輸入。 |
| **X4-F 跨平台 Win/Mac/Linux** | 無平台相依：yaml/checker 路徑用 pathlib、無硬編碼分隔符、無 shell 呼叫；雲端 cron(Linux) 與本地(Win) 行為一致。 |
| **X4-G 主公個人視角** | 阿喜手機看報告：戰績區從固定假 52.8% 變真實數據(你抄的)・更新於 X 或空態。收官須明告數據由你手動維護、忘更新會標過時。 |
| **X4-H 觀測/治理** | logger 標讀取結果；manifest 記 combat_stats_source/age_days 可追溯；checker 進治理防線；B′ 巴哈帖真爬登記待 PoC。 |
| **X4-I 主公可見性** | 自動行為：cron 報告戰績區呈現 yaml 內容/空態/stale 警示、manifest 多欄位、history 預警行為變。攤開：收官文件+SOP+下次 cron 親見。 |
| **X4-J 自動化建議性工具邊界** | checker 是字面/AST 比對啟發式：能偵測寫死戰績數值但無法判語意對錯，召回率僅供參考、人工覆核必要，故 advisory 不阻斷、CLI 末行印邊界免責。 |
| **X4-K 使用者端審查官/Patric** | 阿喜可能忘更新 yaml→數據變舊或長期空態。緩解：stale 警示主動標過時、SOP 建議每改版更新、空態/過期文案友善誠實避免誤判故障。 |

> **主公裁決錨點(B-005)**：2 裁決點 =（1）yaml schema/stale 天數確認(凍結時~2分，AI 給 yaml 範本一眼審)；（2）META4≈6.5 分+凍結核准(~2分)。

### M1.5 八人格顧問團

| 人格 | 觸發 | 發現 |
|---|---|---|
| **Jarvis 總控** | 固定 | ✅ 目標四段清楚、邊界明確(不爬遊戲API/不碰歷史竄改/不動demo/audio不改)、7 stage |
| **Ken 紅隊** | 固定 | ✅ safe_load 硬規、零自動化存取遊戲API(避封號)、checker 只讀、push 前問 |
| **Patric 使用者審查** | 固定 | ⚠️ 過期/空態誤解→友善文案+stale+SOP（X4-K） |
| **Jimmy 文件主筆** | 觸發(改 docstring/yaml/postmortem/template) | ✅ 誠實 docstring+yaml 教學+postmortem 通則化+SOP |
| **Marcus 數據分析** | 觸發(數據真偽/新鮮度) | ✅ 真數據標來源+日期、沒數據空態、過時警示、data_source 全鏈追溯 |
| **Oliver 設計審查** | 觸發(報告視覺) | ✅ 更新日期小字、stale 警示不喧賓、空態不破版 |
| **Penny CFO** | N/A | 不碰付費API/不爬，零外部成本 |
| **Jason DevOps** | 觸發(Git/dry-run/config/checker) | ✅ 全可逆、dry-run git checkout、跨平台路徑、checker 可 CI 化、push 前問 |

### M2 紅藍對抗（≥5 條，≥2 條 S 級）

| # | 紅隊質疑 | 攻擊力 | pre-existing | 藍隊回應 | 處置 |
|---|---|---|---|---|---|
| 1 | **【S 級】** 只查兩路徑，會不會還有第三條 production 塞 combat_stats？ | S | 0 | grep 全專案寫入點僅 main.py:574(prod)/sentiment:708(showcase)/audio:99(__main__)/quick_demo:39(demo)，prod+showcase 已涵蓋，後兩非 prod。checker 進一步機械防新潛入。 | 入計畫範圍(S1/S5/S6) |
| 2 | **【S 級】** yaml full_load 或模板 `\|safe` 會 RCE/XSS？ | S | 0 | 強制 safe_load；模板不對 yaml 值 `\|safe`。yaml 本地阿喜維護非外部，攻擊面極小但硬規仍套。 | 入計畫範圍(S1+X4-A) |
| 3 | data_source 貫穿改 6 檔，會不會引回歸？尤其 history 預警邏輯。 | B | 0 | 每 stage 測試+小批次；S4 先查 history 既有預警測試契約(B-024)再改；history 改動本身修復「假數據致預警死掉」隱藏 bug。 | 入計畫範圍(S4/R9) |
| 4 | checker 是啟發式，誤報多會不會變雜訊被忽略？ | B | 0 | advisory 不阻斷、白名單(tests/__main__/showcase)、CLI 末行印邊界免責；誤報多則降級。呼應 P108 check_report_credibility advisory 前例。 | 入計畫範圍(S5/R7) |
| 5 | 半自動最大弱點＝阿喜忘更新，數據過時不就又變假數據？ | B | 0 | stale 警示讓過時數據誠實自曝(>30天標可能過時)、不偽裝即時；SOP 建議每改版更新。過時但標示≠假裝即時。 | 入計畫範圍(R1+stale) |
| 6 | 基線 489 是 memory 記的、可能漂移？ | B | 0 | S6 第一步實跑 pytest 確認真實基線，不信 memory；pre-existing 失敗記計次(≥3 Phase 跳過則升 Phase)。 | 入計畫範圍(S6) |

> 未解質疑：無（6 條皆納入計畫範圍）。

---

## 12. 凍結戳記

- **凍結人**：阿喜 + Claude（雙方確認）
- **凍結時間**：2026-06-07
- **實作者**：Antigravity Gemini 3.5 Flash (High)（外包執行手）
- **審核者**：Claude（獨立 grep / pytest / checker 交叉驗收）
- **審核結果（2026-06-07）**：✅ **通過**。5 判準全綠（假值零命中 / 496 passed 零回歸 / checker / 渲染端到端真實路徑 loader 讀到 51.2 / git 範圍）；Claude 補 tier 顯示 + 還原 2 越界檔（NEXT_SESSION_HANDOFF/ACTIVE_OPERATION）+ 清 dry-run 副作用。
- **狀態**：✅ **S1-S7 收官**（commit 待建，push 必問阿喜）
- **凍結後變更**：禁止；如需改，新增「Phase 106.2 補遺」章節

---

*受 17 層品質框架 v3.1 + STR1/STR10 保護。狀態：草案（方案 D 飛輪版），待阿喜凍結。*
*建立 2026-06-07｜飛輪模式選定全飛輪一次到位後重寫，未動工。前版 C/D 草稿已被本版取代。*
