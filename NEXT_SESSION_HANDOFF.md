# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-03（P63.4 動工完成 + dry-run 驗證後更新）
- **狀態**：**P63.4 全部 7 commits 已 push ✅**，待 Exit Criteria C-B/C-C/C-D 驗收

---

## 🔥 下個視窗最優先任務

### T1 — P63.4 Exit Criteria 驗收（優先）

P63.4 代碼已全數落地（7 commits pushed，含 dry-run 修補）。

**剩餘 Exit Criteria**：

| # | 條件 | 方式 | 狀態 |
|---|---|---|---|
| C-B | `workflow_dispatch` 手動觸發 2 次（間隔 ≥10min），第 2 次 cache hit ≥80% | 主公到 GitHub Actions 頁面點「Run workflow」 | ⬜ 待做 |
| C-C | 下次排程跑完，commit 訊息**不出現** `(Fallback)`，報告頂 `mode: production` | 等 UTC 00:00 自動跑 | ⬜ 待做 |
| C-D | 主公親點一次排程結果驗收 | 主公確認 | ⬜ 待做 |
| C-E | 5 commit hash + 3 GHA run URL + metadata 前後對比，全數記入 TASK_HISTORY | Claude 執行（需主公提供 GHA run URL） | ⬜ 待做 |

**C-B 操作步驟**：
1. GitHub repo → Actions → AoV Daily Monitor → 右上「Run workflow」
2. 等第一次跑完，看 commit 訊息是否有 `(Fallback)`
3. 間隔 ≥10min 再跑第二次
4. 打開第二次的報告 HTML 第一行：`<!-- cache_hit: X/Y (≥80%) | mode: production -->`

#### 7 commit 清單

| Commit | Stage | 內容 |
|---|---|---|
| `5f5e598` | S1a | 併發數 3→1 |
| `2d4f4b0` | S1b | 429 wait 60→120s，while 迴圈解耦 MAX_RETRIES |
| `3a981a1` | S1c | CONCURRENCY_LIMIT 抽常數 |
| `346e3fe` | S2 | git config 移至 python main.py 之前 |
| `933566b` | S3 | cache 跨日 + metadata + .gitignore 例外 |
| `5372ff4` | S4 | TASK_HISTORY + Postmortem |
| `eb97508` | 補丁 | outer except 路徑補注 _meta，修 mode: unknown |

---

### T2 — P63.4 修復後第一週監控（G3 紅色警報 SOP）

修復推上後 7 天觀察期：
- 每日 09:00（台北時間）主公親檢 commit 訊息無 `(Fallback)`、報告 metadata `mode: production`、cache hit ≥ 50%
- **連 2 日任一失敗 → 立刻 disable cron**（指令見 `docs/PHASE_63_4_PLAN.md` 第 12 章）

---

### T3 — Phase 65（P63.4 全收官後排序）

**計畫書**：`docs/PHASE_65_PLAN.md`（已凍結，重大影響，META4 16 分，**需主公再次口頭確認**才能動工）

---

## 📂 關鍵檔案位置

| 檔案 | 用途 |
|---|---|
| `docs/PHASE_63_4_PLAN.md` | v0.4 凍結計畫書（過期 2026-07-03） |
| `docs/PHASE_65_PLAN.md` | Phase 65 計畫書（已凍結） |
| `docs/postmortems/2026-05-03-phase-63-4-showcase-rootcause.md` | P63.4 Postmortem（已完成） |
| `.github/workflows/daily_report.yml` | CI workflow（已修：Git Config step + Fallback + llm_cache） |
| `analyzer/gemini_client.py` | Gemini client（S1a/b/c 已修，while 迴圈 + 計數器） |
| `analyzer/sentiment.py` | 分析器（S1a 已修：concurrency=CONCURRENCY_LIMIT） |
| `main.py` | S3 _meta 注入 + outer except 補丁 |
| `data/llm_cache.json` | 已入版控（目前 12 筆 key） |
| `data/.cache_policy.md` | cache 入版控約定（過期 2026-08-03） |
| `tests/test_429_retry.py` | S1b 單元測試（2 cases 全綠） |
| `scripts/history-tail.sh` | 拿末尾 Phase，不全讀 |

---

## 🛡️ Token 優化 SOP（新視窗開局）

```bash
bash scripts/history-tail.sh        # 拿末尾 Phase，不全讀
```
Hook 已自動注入鐵律，開局無需手動設定。

---

## 📌 給下個視窗 Claude 的提醒

1. **P63.4 代碼已全部 push**，不要再動 P63.4 相關檔案，除非 C-B/C-C 驗證失敗需要補丁
2. C-E 需要主公提供 3 個 GHA run URL，才能完成 TASK_HISTORY 最後留痕
3. dry-run 本機測試遇到 429 全滅→showcase 是正常的（本機配額不足），GHA 真跑才能驗證 production mode
4. Phase 65 需主公**親口再次確認**（META4 16 分）才能動工，不可自行開工
5. push 必問

---

*本交接筆記由 2026-05-03 視窗更新（P63.4 動工完成 + dry-run 驗證 + 補丁 push 後），下視窗接手 C-B 驗收。*
