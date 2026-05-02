#!/bin/bash
# 用法：bash scripts/finalize-phase.sh <Phase編號> <1行重點>
# 自動：提示補紀錄 + phase_map append + WIP 移除 + Obsidian 同步 + git diff
# fail-loud：每步驟失敗時 stderr 明確報錯，exit 非零

set -euo pipefail

if [ $# -lt 2 ]; then
    echo "用法：bash scripts/finalize-phase.sh <Phase編號> <1行重點>" >&2
    exit 1
fi

PHASE_NUM="$1"
SUMMARY="$2"

echo "📝 [Step 1/4] 請主公先在 TASK_HISTORY.md 末尾用 cat >> heredoc 追加完整 Phase $PHASE_NUM 紀錄"
echo "    完成後按 Enter 繼續..."
read -r

# Step 2: phase_map 追加
TODAY=$(date +%Y-%m-%d)
PHASE_MAP="memory/history_lookup/phase_map.md"
if [ ! -f "$PHASE_MAP" ]; then
    echo "❌ [finalize-phase] 找不到 $PHASE_MAP，請確認路徑正確" >&2
    exit 1
fi
cat >> "$PHASE_MAP" << EOF
| $PHASE_NUM | \`Phase $PHASE_NUM\` | $SUMMARY | ✅ | $TODAY |
EOF
echo "✅ [Step 2/4] phase_map.md 已 append"

# Step 3: 提示移除 WIP
echo "📝 [Step 3/4] 請主公手動編輯 memory/history_lookup/WIP_PHASES.md 移除 Phase $PHASE_NUM"
echo "    完成後按 Enter 繼續..."
read -r

# Step 4: Obsidian 同步
OBSIDIAN_TARGET="D:/Obsidian_vault/Arena of Valor/TASK_HISTORY.md"
if ! cp TASK_HISTORY.md "$OBSIDIAN_TARGET" 2>/dev/null; then
    echo "⚠️ [finalize-phase] Obsidian 同步失敗，目標路徑：$OBSIDIAN_TARGET" >&2
    echo "   請確認 Obsidian vault 路徑存在，或手動複製 TASK_HISTORY.md" >&2
fi
echo "✅ [Step 4/4] Obsidian 已同步（或請手動同步，見上方警示）"

# 收尾：git diff
echo ""
echo "📊 git status:"
git status --short
echo ""
echo "👀 git diff（請主公審）:"
git diff --stat
