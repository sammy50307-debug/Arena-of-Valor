#!/bin/bash
# 測試 UserPromptSubmit hook 的內聯指令邏輯
# 對應 settings.json 中第一個 UserPromptSubmit hook command
# 執行：bash tests/test_hooks/test_user_prompt_submit.sh

PASS=0; FAIL=0

assert_contains() {
    local desc="$1" needle="$2" haystack="$3"
    if echo "$haystack" | grep -qF "$needle"; then
        echo "  ✅ PASS: $desc"; PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL: $desc（期望含：$needle）"; echo "     實際：$haystack"; FAIL=$((FAIL + 1))
    fi
}
assert_eq() {
    local desc="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then
        echo "  ✅ PASS: $desc"; PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL: $desc（期望：$expected，實際：$actual）"; FAIL=$((FAIL + 1))
    fi
}
assert_exit_code() {
    local desc="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then
        echo "  ✅ PASS: $desc (exit=$actual)"; PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL: $desc（期望 exit=$expected，實際 exit=$actual）"; FAIL=$((FAIL + 1))
    fi
}

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT
mkdir -p "$TMP_DIR/.claude"
COUNTER_FILE="$TMP_DIR/.claude/.history_query_count"

# hook 指令（從 settings.json 摘出，替換 COUNTER_FILE 路徑供測試）
HOOK_CMD="echo '[鐵律 v0.4-OK] TASK_HISTORY 禁全讀（除非主公說「這次需要全讀」）。查→grep錨點+Read offset≤200。寫→cat>>heredoc。子代理必傳此禁令。一次對話最多查 3 個 Phase。' && echo 0 > '$COUNTER_FILE'"

# Case 1：hook 指令應輸出鐵律標記
output=$(bash -c "$HOOK_CMD" 2>&1)
exit_code=$?
assert_exit_code "hook 指令 → exit 0" 0 "$exit_code"
assert_contains "hook 應輸出 v0.4-OK 標記" "v0.4-OK" "$output"
assert_contains "hook 應輸出 TASK_HISTORY 禁令" "TASK_HISTORY 禁全讀" "$output"

# Case 2：hook 指令應重置 counter 為 0
echo "5" > "$COUNTER_FILE"
bash -c "$HOOK_CMD" > /dev/null 2>&1
counter_val=$(cat "$COUNTER_FILE" 2>/dev/null)
assert_eq "hook 應重置 counter 為 0" "0" "$counter_val"

# Case 3：hook 執行後，budget check 對計數 0 的情況不應觸發警示
bash -c "$HOOK_CMD" > /dev/null 2>&1  # 重置 counter
budget_output=$(CLAUDE_TOOL_INPUT="TASK_HISTORY.md" bash -c "
  COUNTER_FILE='$COUNTER_FILE'
  TOOL_INPUT=\$CLAUDE_TOOL_INPUT
  if echo \"\$TOOL_INPUT\" | grep -q 'TASK_HISTORY.md'; then
    COUNT=\$(cat \"\$COUNTER_FILE\" 2>/dev/null || echo 0)
    COUNT=\$((COUNT + 1))
    echo \"\$COUNT\" > \"\$COUNTER_FILE\"
    if [ \"\$COUNT\" -gt 3 ]; then echo '⚠️ [預算警示]'; fi
  fi
" 2>&1)
# After hook reset (0) + 1 query = 1, should not trigger budget warning
if echo "$budget_output" | grep -qF "預算警示"; then
    echo "  ❌ FAIL: hook reset 後第 1 次查詢不應觸發預算警示"; FAIL=$((FAIL + 1))
else
    echo "  ✅ PASS: hook reset 後第 1 次查詢不觸發預算警示"; PASS=$((PASS + 1))
fi

echo ""
echo "結果：PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
