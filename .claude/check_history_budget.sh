#!/bin/bash
# PreToolUse hook — 追蹤本對話查詢 TASK_HISTORY.md 次數，超過 3 次發出警示
# fail-loud：counter 寫入失敗時 stderr 紅字提示，但 exit 0 不攔截工具使用

COUNTER_FILE=".claude/.history_query_count"
TOOL_INPUT="$CLAUDE_TOOL_INPUT"

if echo "$TOOL_INPUT" | grep -q "TASK_HISTORY.md"; then
    COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
    COUNT=$((COUNT + 1))
    if ! echo "$COUNT" > "$COUNTER_FILE" 2>/dev/null; then
        echo "⚠️ [hook/check_history_budget] 無法寫入 $COUNTER_FILE，計數失效" >&2
    fi
    if [ "$COUNT" -gt 3 ]; then
        echo "⚠️ [預算警示] 本對話已查 TASK_HISTORY $COUNT 次，建議先回報主公後再續查"
    fi
fi
