# Arena of Valor 專案 — Claude 工作守則

## 🚫 TASK_HISTORY.md 鐵律（含子代理）

- **禁止全讀** TASK_HISTORY.md（4316+ 行 ≈ 135K tokens）
- 查歷史先 `grep -n "^### " TASK_HISTORY.md` 探錨點 → `Read offset:N limit:200` 精讀
- 寫新 Phase 用 `cat >> TASK_HISTORY.md << 'EOF'`，不用 Edit 工具
- 主公唯一觸發詞「這次」+「全讀」才放行（二次確認後才執行）
- 一次對話最多查 3 個 Phase（**原子查詢守則**：主公一次提問 = 一次原子查詢）

## 📚 歷史查詢工具區

詳見 `memory/history_lookup/lookup_guide.md`

## 👑 稱呼

使用者為「主公」，一律使用繁體中文回覆。
