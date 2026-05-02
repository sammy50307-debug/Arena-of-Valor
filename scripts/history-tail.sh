#!/bin/bash
# 擷取 TASK_HISTORY.md 末尾最後一個 Phase
# 用法：bash scripts/history-tail.sh [max_lines=200]
# fail-loud：HISTORY 不存在或 grep 失敗時 stderr 明確報錯，exit 非零

set -euo pipefail

MAX_LINES="${1:-200}"
HISTORY="TASK_HISTORY.md"

if [ ! -f "$HISTORY" ]; then
    echo "❌ [history-tail] 找不到 $HISTORY，請確認執行目錄是否為專案根目錄" >&2
    exit 1
fi

START=$(grep -n "^### " "$HISTORY" | tail -1 | cut -d: -f1)

if [ -z "$START" ]; then
    echo "❌ [history-tail] $HISTORY 中找不到任何 '### ' 開頭的 Phase 錨點" >&2
    exit 1
fi

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
