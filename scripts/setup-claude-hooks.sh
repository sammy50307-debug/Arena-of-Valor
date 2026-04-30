#!/bin/bash
# 用法：bash scripts/setup-claude-hooks.sh
# 在新機器或重置後，把 v0.4 鐵律 hooks 寫入 .claude/settings.json
# 已有的 env / permissions 設定會保留，hooks 區塊會覆蓋更新

SETTINGS=".claude/settings.json"
mkdir -p .claude

if [ ! -f "$SETTINGS" ]; then
    # 全新機器：直接寫完整設定
    cat > "$SETTINGS" << 'EOF'
{
  "env": {
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1"
  },
  "permissions": {
    "allow": [
      "Bash(git commit -m ' *)",
      "Bash(py -c ' *)",
      "Bash(git log *)"
    ]
  },
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo '[鐵律 v0.4-OK] TASK_HISTORY 禁全讀（除非主公說「這次需要全讀」）。查→grep錨點+Read offset≤200。寫→cat>>heredoc。子代理必傳此禁令。一次對話最多查 3 個 Phase。' && echo 0 > .claude/.history_query_count"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Read|Grep",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/check_history_budget.sh"
          }
        ]
      }
    ]
  }
}
EOF
    echo "✅ 已建立全新 $SETTINGS（含 env / permissions / hooks）"
else
    # 已有設定：用 Python 合併 hooks（保留既有 env / permissions）
    py - << 'PYEOF'
import json, sys

SETTINGS = ".claude/settings.json"
HOOKS = {
    "UserPromptSubmit": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "echo '[鐵律 v0.4-OK] TASK_HISTORY 禁全讀（除非主公說「這次需要全讀」）。查→grep錨點+Read offset≤200。寫→cat>>heredoc。子代理必傳此禁令。一次對話最多查 3 個 Phase。' && echo 0 > .claude/.history_query_count"
                }
            ]
        }
    ],
    "PreToolUse": [
        {
            "matcher": "Read|Grep",
            "hooks": [
                {
                    "type": "command",
                    "command": "bash .claude/check_history_budget.sh"
                }
            ]
        }
    ]
}

with open(SETTINGS, "r", encoding="utf-8") as f:
    config = json.load(f)

config["hooks"] = HOOKS

with open(SETTINGS, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print(f"✅ hooks 已合併寫入 {SETTINGS}（env / permissions 保留）")
PYEOF
fi

echo ""
echo "🔍 驗證（應看到 [鐵律 v0.4-OK] 字樣）："
py -c "import json; c=json.load(open('.claude/settings.json')); print(c['hooks']['UserPromptSubmit'][0]['hooks'][0]['command'][:60])"
