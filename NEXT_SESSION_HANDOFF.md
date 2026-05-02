# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-03（Phase 63.4 v0.4 草案凍結後更新）
- **狀態**：Phase 64.1 已收官 ✅、**Phase 63.4 v0.4 計畫書已凍結 ✅**，下視窗動工 S0 排查

---

## 🔥 下個視窗最優先任務

### T1 — Phase 63.4 動工：S0 排查階段（立刻做）

**背景**：Phase 63.4 v0.4 計畫書 2026-05-03 凍結（`docs/PHASE_63_4_PLAN.md`）。**禁止再改本檔**，如需變更走「P63.4.X 補遺」章節。

**主公指示**：依 v0.4 計畫書動工，**先完成 S0 排查再進 S1a**，不要跳 stage。

#### S0 排查三項（Entry Criteria 強制項）

| # | 排查項 | 為何必排 | 結果影響 |
|---|---|---|---|
| **S0-a** | 驗證 `data/llm_cache.json` 的 cache key 計算邏輯（grep `llm_cache` 寫入路徑） | 若 key 含時間因素，commit 後仍 100% miss | Bug 3 範圍可能擴展 |
| **S0-b** | 確認 `analyzer/llm_client.py:99`（concurrency=5）是否被 daily pipeline 呼叫 | 若是，同樣 burst → 影響檔案 +1 | 影響半徑 / 修法擴展 |
| **S0-c** | Read `main.py` 內 `git push` 實作，確認 Bug 2 真根因 | 真因可能不是 git config，而是 remote URL 的 token 注入 | Bug 2 修法可能完全不同 |

**S0 排查報告寫入 TASK_HISTORY**，若診斷錯誤須在 P63.4 動工前出「補遺章節」。

#### 7 Stage 路徑（依 v0.4）

S0 排查 → S1a 併發 3→1 → S1b 429 wait 60s→120s 重試 2 次 → S1c 抽常數 → S2 workflow 修 → S3 cache+metadata → S4 收官（Postmortem 必寫）

**5 commit + 3 GHA run URL + metadata 對比** 全數留痕。

#### 關鍵指標（v0.4）

- 預估時數：5-6 h
- Token budget：60-80 K
- 影響檔案：6-8 檔
- META4 加權：5.5 分（已請示主公以 S0 排查化解）

---

### T2 — Phase 63.4 修復後第一週監控（G3 紅色警報 SOP）

修復推上後 7 天觀察期：
- 每日 09:00（台北時間）主公親檢 commit 訊息無 `(Fallback)`、報告 metadata `mode: production`、cache hit ≥ 50%
- **連 2 日任一失敗 → 立刻 disable cron**（指令見 v0.4 第 12 章）

---

### T3 — Phase 65（P63.4 全收官後排序）

**計畫書**：`docs/PHASE_65_PLAN.md`（已凍結，重大影響，META4 16 分，需主公再次口頭確認）

---

## 📂 關鍵檔案位置

| 檔案 | 用途 |
|---|---|
| `docs/PHASE_63_4_PLAN.md` | **v0.4 凍結計畫書**（2026-05-03，過期 2026-07-03） |
| `docs/PHASE_TEMPLATE.md` | Phase 計畫書範本（v1.0 混合版） |
| `docs/PHASE_65_PLAN.md` | Phase 65 計畫書（已凍結） |
| `.github/workflows/daily_report.yml` | CI workflow（Bug 2 + Bug 3 在此） |
| `analyzer/gemini_client.py` | Gemini client（Bug 1 主體） |
| `analyzer/sentiment.py` | 分析器（Bug 1 呼叫端） |
| `analyzer/llm_client.py` | **S0-b 待排查** 是否走 CI path |
| `main.py` | **S0-c 待排查** push 實作真根因 |
| `scripts/history-tail.sh` | 拿末尾 Phase，不全讀 |

---

## 🛡️ Token 優化 SOP（新視窗開局）

```bash
bash scripts/history-tail.sh        # 拿末尾 Phase，不全讀
```
Hook 已自動注入鐵律，開局無需手動設定。

---

## 📌 給下個視窗 Claude 的提醒

1. **不要直接跳 S1a 動工**，先把 S0-a/b/c 三項排查完
2. v0.4 計畫書**已凍結**，發現問題不要直接改檔，走「P63.4.X 補遺」
3. 5 commit 拆法不可合併（S1a/S1b/S1c/S2/S3 分開）
4. Postmortem 是**必寫**不是條件式
5. push 必問

---

*本交接筆記由 2026-05-03 視窗更新（v0.4 草案凍結後），下視窗直接動工 S0 排查。*
