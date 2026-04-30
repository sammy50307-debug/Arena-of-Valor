# 📦 Claude Code Token 優化計畫 v0.4-final

- **凍結日期**：2026-05-01
- **狀態**：📋 草案定版、待動工
- **權威等級**：細節衝突時以本檔為準

---

## 🎯 痛點界定

| 項目 | 現況 |
|---|---|
| TASK_HISTORY.md 規模 | 4316+ 行 ≈ **13.5 萬 tokens** |
| 觸發時機 | 每次新視窗開局 + 每次 Edit 該檔 |
| 後果 | 單次請求 token 灌爆，主公口袋吃不消 |
| 限制 | 必須遵守 **LOSSLESS_TECH_ARCHIVE_PROTOCOL**（不准摘要、不准動原檔內容） |

## 🎯 設計哲學

**「不需要就不讀，需要就精準切片」**——徹底擁抱 Claude Code 終端機原生工具：
- `Grep`：跨檔搜關鍵字、回傳命中行號（~50-200 tokens）
- `Read offset:N limit:M`：只讀指定行區間
- `Bash sed/awk/grep + heredoc >>`：shell 級精準擷取與追加

Antigravity 沒有這套——它靠長 context 硬吃。Claude Code 該走自己的路。

---

## 🛡️ 四層防線架構（壓縮免疫）

| 層級 | 機制 | 壓縮免疫? | 用途 |
|---|---|---|---|
| **Layer 1** | `.claude/settings.json` UserPromptSubmit hook | ✅ 完美 | 每 turn 重注鐵律 |
| **Layer 2** | `memory/MEMORY.md` 根層內容 | ✅ 完美 | auto-load 系統提示 |
| **Layer 3** | 專案根 `CLAUDE.md` | ✅ 完美 | 主代理 + 子代理共同繼承 |
| **Layer 4** | `TASK_HISTORY.md` 第一行警語 | ✅ 物理硬碰 | 萬一全讀也會立刻看到 |

任一層失守，其他三層仍在守。**災難性失守機率：0%**。

---

## 📋 完整元件清單（已主公拍板）

### 元件 1：Hook B 案（~50 tokens）

`.claude/settings.json`：

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "echo '[鐵律 v0.4-OK] TASK_HISTORY 禁全讀（除非主公說「這次需要全讀」）。查→grep錨點+Read offset≤200。寫→cat>>heredoc。子代理必傳此禁令。一次對話最多查 3 個 Phase。'"
      }]
    }],
    "PreToolUse": [{
      "matcher": "Read|Grep",
      "hooks": [{
        "type": "command",
        "command": "bash .claude/check_history_budget.sh"
      }]
    }]
  }
}
```

### 元件 2：專案根 CLAUDE.md（治 R10）

`D:/Coding Project/Arena of Valor/CLAUDE.md`：

```markdown
# Arena of Valor 專案 — Claude 工作守則

## 🚫 TASK_HISTORY.md 鐵律（含子代理）

- **禁止全讀** TASK_HISTORY.md（4316+ 行 ≈ 135K tokens）
- 查歷史先 `grep -n "^### 📦 Phase" TASK_HISTORY.md` 探錨點 → `Read offset:N limit:200` 精讀
- 寫新 Phase 用 `cat >> TASK_HISTORY.md << 'EOF'`，不用 Edit 工具
- 主公唯一觸發詞「這次需要全讀」+ 二次確認才放行
- 一次對話最多查 3 個 Phase（**原子查詢守則**：主公一次提問 = 一次原子查詢）

## 📚 歷史查詢工具區
詳見 `memory/history_lookup/lookup_guide.md`

## 👑 稱呼
使用者為「主公」
```

### 元件 3：原子查詢守則（治 R11 行為層）

寫進 `lookup_guide.md`：

> **一次主公提問 = 一次原子查詢**
> - 1 次 Grep（廣域）+ 1-3 次 Read offset（精讀）即交付答覆
> - 後續查詢必須等主公明確 follow-up（「再查 X」「順帶看 Y」）
> - Claude 自我判斷「我覺得還要再看 P56.5」→ **禁止**
> - 例外：主公一個提問裡明列多個目標 → 算同一原子

### 元件 4：Hook 狀態檔（治 R11 機制層）

`.claude/check_history_budget.sh`：

```bash
#!/bin/bash
COUNTER_FILE=".claude/.history_query_count"
TOOL_INPUT="$CLAUDE_TOOL_INPUT"

if echo "$TOOL_INPUT" | grep -q "TASK_HISTORY.md"; then
    COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
    COUNT=$((COUNT + 1))
    echo "$COUNT" > "$COUNTER_FILE"
    if [ "$COUNT" -gt 3 ]; then
        echo "⚠️ [預算警示] 本對話已查 TASK_HISTORY $COUNT 次，建議先回報主公後再續查"
    fi
fi
```

UserPromptSubmit hook 補一行重置（每次主公新提問計數歸零，對應原子查詢邊界）：
```bash
echo 0 > .claude/.history_query_count
```

### 元件 5：phase_map.md（按 Milestone 分組）

`memory/history_lookup/phase_map.md`：

```markdown
# Phase 索引地圖

> 用法：grep 該 Phase 標題錨點 → Read offset/limit ≤200 精讀
> 不存行號（會漂移）；存錨點 + 1 行重點 + 最後更新時間

## 🏆 Milestone 1：基礎（P45-P48）
| P | 錨點 | 重點 | 狀態 | 更新 |
|---|---|---|---|---|
| 45 | `### 📦 Phase 45` | landing-page 戰報門面初版 | ✅ | 2026-05-01 |
| ... | | | | |

## 🏆 Milestone 5：跨域協作（P60-P63+）
| P | 錨點 | 重點 | 狀態 | 更新 |
|---|---|---|---|---|
| 60 | `### 📦 Phase 60` | session-handoff-packager | ✅ | 2026-05-01 |
| 61 | `### 📦 Phase 61` | history-trend-query | ✅ | 2026-05-01 |
| 63 | `### 📦 Phase 63` | GitHub Actions 排程 | ⏳ CI 除錯中 | 2026-05-01 |
```

**建檔時動作**：一次性掃過 TASK_HISTORY.md 全部 Phase 標題，整理進此檔。

### 元件 6：WIP_PHASES.md（進行中 Phase 獨立檔）

`memory/history_lookup/WIP_PHASES.md`：

```markdown
# 進行中 / 待動工 Phase 清單

## ⏳ 進行中

| Phase | 卡點 | 下一步 | 阻塞於 |
|---|---|---|---|
| 63 | CI 除錯收尾 | 查 GitHub Actions log | 主公確認 |
| 63.1.0 | landing page 結構未動 | index.html 3→5 個 history-item | 主公令下 |
| 63.2 | LINE 滑不動 | 主公手機原生瀏覽器對照測試 | 主公測試 |

## 📋 凍結待動工

| Phase | 草案位置 | 阻塞於 |
|---|---|---|
| 63.1.1 | docs/PHASE_63_PLAN.md | 依賴 63.1.0 |
| 63.1.2 | docs/PHASE_63_PLAN.md | 依賴 63.1.1 |
| 63.3 | docs/PHASE_63_PLAN.md | 中長期 |
| 61.1 | project_status.md | 統包優化 |
| 64 (本計畫) | docs/CLAUDE_CODE_TOKEN_OPTIMIZATION_v0.4.md | 待主公新視窗動工 |
```

### 元件 7：lookup_guide.md（cookbook 形式）

`memory/history_lookup/lookup_guide.md`：

```markdown
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
```

### 元件 8：history-tail.sh 輔助腳本

`scripts/history-tail.sh`：

```bash
#!/bin/bash
# 擷取 TASK_HISTORY.md 末尾最後一個 Phase
# 用法：bash scripts/history-tail.sh [max_lines=200]

MAX_LINES="${1:-200}"
HISTORY="TASK_HISTORY.md"

START=$(grep -n "^### 📦 Phase" "$HISTORY" | tail -1 | cut -d: -f1)
TOTAL=$(wc -l < "$HISTORY")
PHASE_LEN=$((TOTAL - START + 1))

if [ "$PHASE_LEN" -gt "$MAX_LINES" ]; then
    echo "⚠️ 末尾 Phase 共 $PHASE_LEN 行，超過 $MAX_LINES 上限"
    echo "📍 起始行：$START / 總行數：$TOTAL"
    echo "👉 建議：Read offset:$START limit:$MAX_LINES（截前段）或主公明示要看完整段"
    sed -n "${START},$((START + MAX_LINES - 1))p" "$HISTORY"
else
    echo "✅ 末尾 Phase 共 $PHASE_LEN 行（行 $START-$TOTAL）"
    sed -n "${START},${TOTAL}p" "$HISTORY"
fi
```

### 元件 9：finalize-phase.sh 收官一鍵腳本

`scripts/finalize-phase.sh`：

```bash
#!/bin/bash
# 用法：bash scripts/finalize-phase.sh 64 "新 Phase 重點"
# 自動：提示補紀錄 + phase_map append + WIP 移除 + Obsidian 同步 + git diff

PHASE_NUM="$1"
SUMMARY="$2"

if [ -z "$PHASE_NUM" ] || [ -z "$SUMMARY" ]; then
    echo "用法：bash scripts/finalize-phase.sh <Phase編號> <1行重點>"
    exit 1
fi

echo "📝 [Step 1/4] 請主公先在 TASK_HISTORY.md 末尾用 cat >> heredoc 追加完整 Phase $PHASE_NUM 紀錄"
echo "    完成後按 Enter 繼續..."
read

# Step 2: phase_map 追加
TODAY=$(date +%Y-%m-%d)
cat >> memory/history_lookup/phase_map.md << EOF
| $PHASE_NUM | \`### 📦 Phase $PHASE_NUM\` | $SUMMARY | ✅ | $TODAY |
EOF
echo "✅ [Step 2/4] phase_map.md 已 append"

# Step 3: 提示移除 WIP
echo "📝 [Step 3/4] 請主公手動編輯 memory/history_lookup/WIP_PHASES.md 移除 Phase $PHASE_NUM"
echo "    完成後按 Enter 繼續..."
read

# Step 4: Obsidian 同步
cp TASK_HISTORY.md "D:/Obsidian_vault/Arena of Valor/TASK_HISTORY.md"
echo "✅ [Step 4/4] Obsidian 已同步"

# 收尾：git diff
echo ""
echo "📊 git status:"
git status --short
echo ""
echo "👀 git diff（請主公審）:"
git diff --stat
```

### 元件 10：規則登記簿（治規則演化漂移）

`docs/RULES_REGISTRY.md`：

```markdown
# 規則登記簿 v0.4

> 修改任一規則 → 對照本表掃一遍同步點 → 防止漏改

| 規則 | hook | MEMORY.md | CLAUDE.md | TASK_HISTORY 警語 | lookup_guide |
|---|:---:|:---:|:---:|:---:|:---:|
| 禁全讀 TASK_HISTORY | ✅ | ✅ | ✅ | ✅ | ✅ |
| 觸發詞「這次+全讀」 | ✅ | — | ✅ | — | ✅（詳版+正則）|
| 原子查詢守則 / 3-Phase 上限 | ✅ | — | ✅ | — | ✅（詳版） |
| 子代理禁令傳遞 | ✅ | — | ✅ | — | ✅ |
| Hook 狀態檔計數 | ✅（PreToolUse） | — | — | — | ✅（機制說明） |
| Bash heredoc 追加 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 失誤恢復 SOP | — | — | — | — | ✅ |
```

### 元件 11：TASK_HISTORY.md 第一行警語

在檔頭加（不取代任何內容）：

```markdown
> ⛔ **此檔 4316+ 行勿全讀**。請先 `grep -n "^### 📦 Phase" TASK_HISTORY.md` 探錨點，再 Read offset/limit 精讀（≤200 行）。詳見 `memory/history_lookup/lookup_guide.md`。

# Arena of Valor — 任務編年史
（原內容...）
```

### 元件 12：MEMORY.md 根層加鐵律

在現有索引列表後追加：

```markdown
- [TASK_HISTORY 追加策略](feedback_task_history_append.md) — Edit 工具強制全讀 4000+ 行，必須改用 Bash cat >> heredoc 追加

⛔ **鐵律 v0.4：TASK_HISTORY.md 禁全讀**
查歷史 → `grep -n "^### 📦 Phase" TASK_HISTORY.md | tail -1` → `Read offset:N limit:200`
新 Phase → `cat >> TASK_HISTORY.md << 'EOF'`，不用 Edit
觸發詞「這次+全讀」+二次確認才放行
詳見 `memory/history_lookup/lookup_guide.md`
```

### 元件 13：feedback_history_lookup_workflow.md（新增記憶）

`memory/feedback_history_lookup_workflow.md`：

```markdown
---
name: 歷史查詢工作流（v0.4）
description: TASK_HISTORY.md 禁全讀、Grep+Read offset 精讀、原子查詢、子代理禁令傳遞
type: feedback
---

# 歷史查詢工作流

詳細規則見 `memory/history_lookup/lookup_guide.md`，本檔僅提示要點。

**Why:** 2026-05-01 主公裁示推 v0.4 token 優化方案，TASK_HISTORY 4316+ 行 ≈ 135K tokens 不能每對話全讀。

**How to apply:**
- 開新視窗開局 → 跑 `bash scripts/history-tail.sh` 拿末尾 Phase（不全讀）
- 主公問歷史 → Grep 探錨點 + Read offset ≤200 精讀
- 寫新 Phase → `cat >> TASK_HISTORY.md << 'EOF'`，不用 Edit
- 呼叫子代理 → prompt 必帶禁令
- 一次對話最多查 3 個 Phase（原子查詢）
- 失誤觸發全讀 → 按 lookup_guide 的「失誤恢復 SOP」處理
```

---

## 📂 完整檔案結構（落地後）

```
D:/Coding Project/Arena of Valor/
├── CLAUDE.md                              ← 🆕 元件 2
├── TASK_HISTORY.md                        ← 修：第一行加警語（元件 11）
├── .claude/
│   ├── settings.json                      ← 🆕 / 修：加 hooks（元件 1+4）
│   └── check_history_budget.sh            ← 🆕 元件 4
├── scripts/
│   ├── history-tail.sh                    ← 🆕 元件 8
│   └── finalize-phase.sh                  ← 🆕 元件 9
├── docs/
│   ├── CLAUDE_CODE_TOKEN_OPTIMIZATION_v0.4.md  ← 🆕 本檔
│   └── RULES_REGISTRY.md                  ← 🆕 元件 10
└── (其他現有檔案不動)

C:/Users/sammy/.claude/projects/d--Coding-Project-Arena-of-Valor/memory/
├── MEMORY.md                              ← 修：加鐵律 4 行（元件 12）
├── feedback_history_lookup_workflow.md    ← 🆕 元件 13
├── feedback_startup_ritual.md             ← 修：第 21 行起改為「禁全讀+grep+offset」
└── history_lookup/                        ← 🆕 資料夾
    ├── phase_map.md                       ← 🆕 元件 5
    ├── WIP_PHASES.md                      ← 🆕 元件 6
    └── lookup_guide.md                    ← 🆕 元件 7
```

---

## 🤖 模型選擇建議（執行注意事項）

| 情境 | 建議模型 | 理由 |
|---|---|---|
| 主執行（建檔、寫腳本、改 settings） | **Sonnet 4.6** | 規格已定版、屬照單執行，成本約 Opus 的 1/5 |
| 撞到架構判斷卡點 | **切換 Opus 4.7** | 如「這個 hook 會跟 P61 衝突怎麼辦」等模糊決策 |
| 卡點解完繼續執行 | **切回 Sonnet 4.6** | 用 `/model sonnet` 或 `/model default` |

**切換指令**：`/model sonnet`（切 Sonnet）、`/model opus`（切 Opus）、`/model default`（依系統預設）

**Opus 救援觸發訊號**：
- 出現非預期的衝突（hook 格式問題、CLAUDE.md 覆蓋既有設定）
- 需要判斷「要不要改計畫書」（草案共核制要求）
- 任何「不確定怎麼做比較對」的情境

---

## 🛠️ 落地步驟清單（給下個視窗動工用）

### Phase 1：建立工具區（~10 分鐘）
1. 建 `memory/history_lookup/` 資料夾
2. 寫 `lookup_guide.md`（元件 7）
3. 一次性掃 TASK_HISTORY.md 整理 `phase_map.md`（元件 5）
4. 寫 `WIP_PHASES.md`（元件 6）
5. 寫 `feedback_history_lookup_workflow.md`（元件 13）

### Phase 2：建立四層防線（~10 分鐘）
6. 建專案根 `CLAUDE.md`（元件 2）
7. 改 `.claude/settings.json` 加 hooks（元件 1+4）
8. 寫 `.claude/check_history_budget.sh`（元件 4）
9. TASK_HISTORY.md 檔頭加警語（元件 11，**用 Edit 但只動第一行可接受**）
10. MEMORY.md 加鐵律（元件 12）
11. 修 `feedback_startup_ritual.md` 第 21 行起

### Phase 3：建立工具腳本（~5 分鐘）
12. 寫 `scripts/history-tail.sh`（元件 8）
13. 寫 `scripts/finalize-phase.sh`（元件 9）
14. `chmod +x` 兩個腳本（Windows 略過）

### Phase 4：建立規則登記簿（~5 分鐘）
15. 寫 `docs/RULES_REGISTRY.md`（元件 10）

### Phase 5：驗收（~5 分鐘）
16. 跑 `bash scripts/history-tail.sh` 驗證末尾擷取正常
17. 重開新視窗驗證 hook 注入「[鐵律 v0.4-OK]」字樣
18. TASK_HISTORY 補上本 Phase 完整紀錄（用 Bash heredoc）
19. 同步 Obsidian
20. git add + commit + 等主公授權 push

**預估總時間：~35 分鐘**

---

## ⚠️ 風險矩陣（落地後最終預估）

| 等級 | 編號 | 風險 | 處置 | 殘餘 |
|---|---|---|---|---|
| 🟢 | R9 | 規則消失 | 四層防線 | **0%** |
| 🟢 | R10 | subagent 不繼承 | CLAUDE.md 物理繼承 | **0.5%** |
| 🟢 | R11 | 遞歸爆量 | 原子查詢 + Hook 計數 | **1%** |
| 🟢 | R12 | auto-compaction | hook 重注 | **0%** |
| 🟢 | R15-R25 | 邊緣情境 | 已逐一處置 | 可接受 |

**整體：災難性失守 0%、偶發性浪費 ~1%**。

---

## 📊 預期效益

| 維度 | 改造前 | 改造後 | 收益 |
|---|---|---|---|
| 一般對話 token | ~135K | ~5-10K | **省 92-96%** |
| 查歷史 token | ~135K | ~5-15K | **省 89-96%** |
| 寫新 Phase token | ~135K | ~0 | **省 100%** |
| 維護成本 | 4 步靠記憶 | finalize-phase.sh 一鍵 | 紀律無關 |
| Hook 健檢 | 無 | v0.4-OK 標記 | 一秒判活 |
| 規則演化 | 4 處跑著改 | 對照登記簿 | 無漏改 |

---

## 🔮 未來改良（v0.5+ 候選，現階段不做）

延後到實際使用 1-2 週後依實戰資料決定：
- pre-commit hook 檢查 TASK_HISTORY 第一行警語
- token 消耗 metrics 儀表板
- 自動化 regression test

---

## 📌 落地時機

- **凍結日期**：2026-05-01
- **主公裁示**：草案已定版、待新視窗動工
- **下個視窗開局時**：先讀本檔、確認落地清單、依 Phase 1-5 順序執行
- **動工前**：必須再次與主公確認啟動授權（草案共核制）

---

*本檔由 Claude Code 視窗 2026-05-01 凍結。下個視窗請先讀此檔再動工。*
