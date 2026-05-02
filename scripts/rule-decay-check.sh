#!/bin/bash
# G5-1 規則退化警示 — 偵測 N 天無更新的 memory 規則檔案
# 用法：bash scripts/rule-decay-check.sh
# 環境變數：
#   RULE_DECAY_ENABLED  預設 true（false 時完全跳過）
#   RULE_DECAY_DAYS     預設 90，最低下限 30
# 每日 gate：一天只掃一次，結果寫 data/rule_usage_index.json 與 logs/rule_decay.log
# 韌性：失敗時僅輸出 stderr，exit 0，絕不阻塞主流程（R1 + R3）

RULE_DECAY_ENABLED="${RULE_DECAY_ENABLED:-true}"
RULE_DECAY_DAYS="${RULE_DECAY_DAYS:-90}"
TODAY=$(date +%Y-%m-%d)
LAST_RUN_FILE=".claude/.rule_decay_last_run"

# G5-1 開關
[ "$RULE_DECAY_ENABLED" = "true" ] || exit 0

# 每日 gate：今天已跑過就跳過
if [ -f "$LAST_RUN_FILE" ] && [ "$(cat "$LAST_RUN_FILE" 2>/dev/null)" = "$TODAY" ]; then
    exit 0
fi

# 下限守門：閾值不能 < 30 天（防 alarm fatigue）
MIN_DAYS=30
if [ "$RULE_DECAY_DAYS" -lt "$MIN_DAYS" ]; then
    echo "⚠️ [G5-1] RULE_DECAY_DAYS=${RULE_DECAY_DAYS} 低於下限 ${MIN_DAYS}，強制使用 ${MIN_DAYS}" >&2
    RULE_DECAY_DAYS=$MIN_DAYS
fi

mkdir -p logs data

# 核心邏輯（Python 內嵌，atomic write JSON）
# Windows 使用 py -3；Linux/Mac 使用 python3
if python3 -c "pass" 2>/dev/null; then
    PY_CMD="python3"
else
    PY_CMD="py -3"
fi

$PY_CMD << PYEOF
import json, os, subprocess, glob
from datetime import date, datetime

threshold_days = $RULE_DECAY_DAYS
today = date.today()
today_iso = today.isoformat()
usage_index_path = "data/rule_usage_index.json"
decay_log_path = "logs/rule_decay.log"

# 掃描專案內 memory/ 與 Claude auto-memory（CLAUDE_MEMORY_DIR 環境變數可覆寫）
import os as _os
_project_memory = "memory"
_auto_memory = _os.environ.get(
    "CLAUDE_MEMORY_DIR",
    _os.path.expanduser("~/.claude/projects/d--Coding-Project-Arena-of-Valor/memory")
)
patterns = []
for _base in [_project_memory, _auto_memory]:
    patterns += [
        f"{_base}/feedback_*.md",
        f"{_base}/user_profile.md",
        f"{_base}/project_status.md",
        f"{_base}/reference_*.md",
        f"{_base}/future_skills.md",
    ]
rule_files = sorted(f for p in patterns for f in glob.glob(p) if os.path.isfile(f))

rules = {}
decaying = []

for f in rule_files:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci", "--", f],
            capture_output=True, text=True, check=True, timeout=10
        )
        raw = result.stdout.strip()
        last_commit = datetime.fromisoformat(raw[:10]).date() if raw else date.fromtimestamp(os.path.getmtime(f))
    except Exception:
        last_commit = date.fromtimestamp(os.path.getmtime(f))

    days_since = (today - last_commit).days
    status = "decaying" if days_since >= threshold_days else "active"
    rules[f] = {"last_updated": last_commit.isoformat(), "days_since": days_since, "status": status}
    if status == "decaying":
        decaying.append((f, last_commit.isoformat(), days_since))

# Atomic write（C2 防半寫）
tmp = usage_index_path + ".tmp"
with open(tmp, "w", encoding="utf-8") as fp:
    json.dump({"generated": today_iso, "threshold_days": threshold_days, "rules": rules}, fp, ensure_ascii=False, indent=2)
os.replace(tmp, usage_index_path)

# 追加 decay log
with open(decay_log_path, "a", encoding="utf-8") as fp:
    fp.write(f"\n=== G5-1 掃描 {today_iso}（閾值 {threshold_days} 天）===\n")
    if decaying:
        for f, last, days in decaying:
            fp.write(f"  ⚠️ DECAY: {f} | 最後更新: {last} | 距今: {days}天\n")
    else:
        fp.write("  ✅ 無退化規則\n")

if decaying:
    print(f"⚠️ [G5-1] 偵測到 {len(decaying)} 條疑似退化規則（≥{threshold_days} 天未更新）：")
    for f, last, days in decaying:
        print(f"   ⚠️  {f}（最後更新：{last}，距今 {days} 天）")
    print(f"   📋 詳細報告：{decay_log_path}")
else:
    print(f"✅ [G5-1] 規則健康 — 共 {len(rules)} 條，無退化（閾值 {threshold_days} 天）")
PYEOF
PYEXIT=$?

# 記錄今天已跑（不論成功或失敗都記，避免重複失敗轟炸）
echo "$TODAY" > "$LAST_RUN_FILE"

# R1 + R3 韌性守門：失敗只寫 stderr，exit 0 不阻塞
if [ "$PYEXIT" -ne 0 ]; then
    echo "⚠️ [G5-1] rule-decay-check 執行失敗（Python exit=${PYEXIT}），本次掃描略過。詳見 logs/rule_decay.log" >&2
fi
exit 0
