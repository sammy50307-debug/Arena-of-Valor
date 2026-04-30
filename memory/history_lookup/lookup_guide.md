# 歷史查詢教戰守則（給 Claude）

## 🚫 鐵律
1. 禁止 Read TASK_HISTORY.md 不帶 offset
2. 禁止用 Edit/Write 工具修改 TASK_HISTORY.md
3. 一次主公提問 = 一次原子查詢，最多 3 個 Phase

## 📋 何時該查 TASK_HISTORY.md？

✅ **該查**：主公明確問「之前 Phase X 怎麼決定」「R20 的處置」「我們有沒有做過 Y」
❌ **不該查**：日常對話、新 Phase 規劃、跑測試、寫程式

## 🔍 查詢三步驟（嚴禁全讀）

### Step 1：先用 Grep 探路
`Grep pattern="關鍵字" path="TASK_HISTORY.md" output_mode="content" -n=true -C=3`

### Step 2：拿到候選行號後用 phase_map 對照
`Read memory/history_lookup/phase_map.md` 找對應 Phase 錨點

### Step 3：精讀那段（offset/limit 嚴格控制）
`Read TASK_HISTORY.md offset:1925 limit:200`
規則：limit 預設 ≤ 200，超出主動跟主公講「需要讀更多嗎」

## 🎯 觸發詞處理（全讀放行流程）

### 觸發條件（正則容錯版）
主公訊息含 「**這次**」+「**全讀**」二字（不論順序、中間可有字）即觸發。

✅ 觸發範例：
- 「這次需要全讀」
- 「我這次需要全讀啊」
- 「這次要全讀一遍」
- 「我覺得這次有需要全讀」

❌ 非觸發（缺「這次」二字）：
- 「全部讀過」
- 「完整看一遍」
- 「讀完整 TASK_HISTORY」
- 「請完整詳細地讀」

### 觸發後標準回應
1. 報 token 預算：「會吃約 135K tokens，確定？」
2. 等主公二次確認（必須回「確定」「Y」「對」其中之一）
3. 才執行 `Read TASK_HISTORY.md`（仍建議分段，每段 limit:1000）

### 非觸發但主公明顯想讀的回覆模板
> 主公的意思是不是要查某段歷史？我建議用 Grep 精準定位後 Read offset 精讀，省 95% token。如果真的要全讀，請說「**這次需要全讀**」。

## 🆘 失誤恢復 SOP

如果 Claude 不小心觸發了全讀：
1. 主動回報主公「我剛剛失誤觸發全讀，吃了 ~135K tokens，抱歉」
2. 將該次失誤路徑寫進 `feedback_history_lookup_workflow.md` 作為改良案例
3. 檢查 hook 是否失效（看 reminder 是否含 `[鐵律 v0.4-OK]` 標記）
4. 視為 R10/R11 殘餘觸發（~1% 物理下界），按 SOP 處理即可，不需慌張

## 🤝 子代理（subagent）禁令傳遞

呼叫 Agent 工具時，prompt 必帶：
> 「禁止 Read TASK_HISTORY.md 不帶 offset。先用 Grep 探錨點再 Read offset/limit 精讀」

子代理因 CLAUDE.md 自動繼承已有第一道防線，prompt 禁令是第二道。
