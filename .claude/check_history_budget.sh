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
