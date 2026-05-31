# Arena of Valor 專案 — Claude 工作守則

## 🚫 TASK_HISTORY.md 鐵律（含子代理）

- **禁止全讀** TASK_HISTORY.md（4316+ 行 ≈ 135K tokens）
- 查歷史先 `grep -n "^### " TASK_HISTORY.md` 探錨點 → `Read offset:N limit:200` 精讀
- 寫新 Phase 用 `cat >> TASK_HISTORY.md << 'EOF'`，不用 Edit 工具
- 阿喜唯一觸發詞「這次」+「全讀」才放行（二次確認後才執行）
- 一次對話最多查 3 個 Phase（**原子查詢守則**：阿喜一次提問 = 一次原子查詢）

## 📚 歷史查詢工具區

詳見 `memory/history_lookup/lookup_guide.md`

## 👑 稱呼

使用者為「阿喜」，一律使用繁體中文回覆。


---

## 📚 Andrej Karpathy LLM Coding Guidelines（追加 / 2026-05-16）

來源：https://github.com/multica-ai/andrej-karpathy-skills
適用：所有 LLM 模型（Claude / GPT / Gemini）。此區塊為跨家共用準則，與既有專案規則並存；如有衝突以**既有規則優先**（後讀覆蓋前讀）。

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
