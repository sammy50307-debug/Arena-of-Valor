#!/bin/bash
# 測試 .claude/check_history_budget.sh
# 執行：bash tests/test_hooks/test_check_history_budget.sh

PASS=0; FAIL=0

assert_contains() {
    local desc="$1" needle="$2" haystack="$3"
    if echo "$haystack" | grep -qF "$needle"; then
        echo "  ✅ PASS: $desc"; PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL: $desc（期望含：$needle）"; echo "     實際：$haystack"; FAIL=$((FAIL + 1))
    fi
}
assert_not_contains() {
    local desc="$1" needle="$2" haystack="$3"
    if ! echo "$haystack" | grep -qF "$needle"; then
        echo "  ✅ PASS: $desc"; PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL: $desc（不應含：$needle）"; FAIL=$((FAIL + 1))
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

# 測試環境：用 tmp 目錄隔離
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT
COUNTER_FILE="$TMP_DIR/.history_query_count"
HOOK_SCRIPT=".claude/check_history_budget.sh"

# Case 1：counter 不存在時，查詢 TASK_HISTORY.md 不應觸發警示（計數 = 1）
rm -f "$COUNTER_FILE"
output=$(CLAUDE_TOOL_INPUT="TASK_HISTORY.md" bash -c "
  COUNTER_FILE='$COUNTER_FILE'
  TOOL_INPUT=\$CLAUDE_TOOL_INPUT
  if echo \"\$TOOL_INPUT\" | grep -q 'TASK_HISTORY.md'; then
    COUNT=\$(cat \"\$COUNTER_FILE\" 2>/dev/null || echo 0)
    COUNT=\$((COUNT + 1))
    if ! echo \"\$COUNT\" > \"\$COUNTER_FILE\" 2>/dev/null; then
      echo '⚠️ 無法寫入 counter' >&2
    fi
    if [ \"\$COUNT\" -gt 3 ]; then echo '⚠️ [預算警示]'; fi
  fi
" 2>&1)
assert_not_contains "counter 不存在 + 首次查詢 → 不應觸發警示" "預算警示" "$output"
assert_eq "counter 不存在 + 首次查詢 → 計數應為 1" "1" "$(cat "$COUNTER_FILE" 2>/dev/null)"

# Case 2：計數已達 3，第 4 次查詢應觸發預算警示
echo "3" > "$COUNTER_FILE"
output=$(CLAUDE_TOOL_INPUT="TASK_HISTORY.md" bash -c "
  COUNTER_FILE='$COUNTER_FILE'
  TOOL_INPUT=\$CLAUDE_TOOL_INPUT
  if echo \"\$TOOL_INPUT\" | grep -q 'TASK_HISTORY.md'; then
    COUNT=\$(cat \"\$COUNTER_FILE\" 2>/dev/null || echo 0)
    COUNT=\$((COUNT + 1))
    echo \"\$COUNT\" > \"\$COUNTER_FILE\"
    if [ \"\$COUNT\" -gt 3 ]; then echo \"⚠️ [預算警示] 本對話已查 TASK_HISTORY \$COUNT 次\"; fi
  fi
" 2>&1)
assert_contains "計數 3 → 第 4 次查詢觸發預算警示" "預算警示" "$output"

# Case 3：tool input 不含 TASK_HISTORY.md，計數不應增加
echo "2" > "$COUNTER_FILE"
output=$(CLAUDE_TOOL_INPUT="some_other_file.py" bash -c "
  COUNTER_FILE='$COUNTER_FILE'
  TOOL_INPUT=\$CLAUDE_TOOL_INPUT
  if echo \"\$TOOL_INPUT\" | grep -q 'TASK_HISTORY.md'; then
    COUNT=\$(cat \"\$COUNTER_FILE\" 2>/dev/null || echo 0)
    COUNT=\$((COUNT + 1))
    echo \"\$COUNT\" > \"\$COUNTER_FILE\"
    if [ \"\$COUNT\" -gt 3 ]; then echo '⚠️ [預算警示]'; fi
  fi
" 2>&1)
assert_eq "非 TASK_HISTORY 輸入 → 計數不變（仍為 2）" "2" "$(cat "$COUNTER_FILE")"
assert_not_contains "非 TASK_HISTORY 輸入 → 無警示" "預算警示" "$output"

echo ""
echo "結果：PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
