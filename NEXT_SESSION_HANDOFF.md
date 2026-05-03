# 🛎️ 下個視窗開局交接筆記

- **建立日期**：2026-04-27（原版）
- **更新日期**：2026-05-03（P64 全 5 Stage 完成 + push）
- **狀態**：**P64 S1-S5 已 push ✅**，待 E-C/E-D 配額重置後驗收（明日 UTC 00:00）

---

## 🔥 下個視窗最優先任務

### T1 — P64 Exit Criteria E-C/E-D 驗收

P64 代碼全數落地（5 Stage，commits `f0c0096`→`e6f60f5`）。  
今日（2026-05-03）Gemini 配額已耗盡，E-C/E-D 必須等明日 UTC 00:00 reset 後執行。

**剩餘 Exit Criteria**：

| # | 條件 | 方式 | 狀態 |
|---|---|---|---|
| E-C | 本機 `--dry-run` 跑兩次，第二次 L1 hit ≥ 95% | `py -3 main.py --dry-run` × 2 | ⬜ 待配額重置 |
| E-D | GHA `workflow_dispatch` 連跑兩次（間隔 ≥5min），第二次 `mode: production` + L1 hit ≥ 80% | GitHub Actions 手動點 | ⬜ 待配額重置 |

**E-C 驗收指令**：
```bash
# 第一次（cache miss，正常打 API）
py -3 main.py --dry-run

# 第二次（L1 應命中，零 LLM 呼叫）
py -3 main.py --dry-run --force
# 觀察 log：「L1 快取命中 (hero:combined:YYYY-MM-DD)」
# 觀察 _meta.l1_hits ≥ 1, llm_calls = 0
```

**E-D 驗收步驟**：
1. GitHub repo → Actions → AoV Daily Monitor → 右上「Run workflow」
2. 等第一次跑完，確認 commit msg 含 `[mode:production ...]`
3. 間隔 ≥5min 再跑第二次
4. 第二次報告第一行：`<!-- l1_hits: X | mode: production -->`

---

### T2 — P65 B1 修項：analyze_posts showcase 回傳型別不一致

**問題**：`analyze_posts` showcase 路徑回傳 `list`，main.py 預期 `dict`  
**症狀**：TypeError 被 outer except 吃掉，降級 `_empty_summary`，showcase 報告品質損失  
**位置**：[analyzer/sentiment.py](analyzer/sentiment.py) L198（showcase 路徑 `return analyzed`）  
**修法**：改為 `return {"posts": analyzed, "is_showcase": True}` 與正常路徑統一  
**優先級**：P1，P65 開工第一項

---

## P64 完成摘要

| Stage | Commit | 內容 |
|---|---|---|
| S1 | `f0c0096` | CacheManager + schema v2 + migration + config 參數 |
| S2 | `53a233a` | gemini_client 接入 CacheManager + pre-flight + wait 加長 + secret 遮罩 |
| S3 | `bdd968e` | L1 hero cache + daily_summary cache + Apify cache |
| S4 | `9399aac` | Lockfile 防重複 + _meta L1/L2/apify stats + commit msg + B2 concurrency |
| S5 | `e6f60f5` | 10 項單元測試全綠 |

---

## 後置不做（P64 明列，留後續）

- P65：analyze_posts showcase 回傳型別修正（B1 — 本視窗已登記）
- P65 候選：partial result 保護（O6）
- P65 候選：多 API key 輪換（O7）
- P66：每日健康巡檢 GHA（O5）
- P67 候選：OpenAI fallback（O8，觀察期）
- P68 候選：SQLite 取代 JSON（O9，條目 > 1000 才考慮）
