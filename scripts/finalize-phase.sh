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
| $PHASE_NUM | \`Phase $PHASE_NUM\` | $SUMMARY | ✅ | $TODAY |
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
