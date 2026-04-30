#!/bin/bash
# 擷取 TASK_HISTORY.md 末尾最後一個 Phase
# 用法：bash scripts/history-tail.sh [max_lines=200]

MAX_LINES="${1:-200}"
HISTORY="TASK_HISTORY.md"

START=$(grep -n "^### " "$HISTORY" | tail -1 | cut -d: -f1)
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
