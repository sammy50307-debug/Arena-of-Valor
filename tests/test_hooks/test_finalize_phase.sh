#!/bin/bash
# 測試 scripts/finalize-phase.sh
# 執行：bash tests/test_hooks/test_finalize_phase.sh

PASS=0; FAIL=0
PROJECT_DIR="$PWD"
SCRIPT_PATH="$PROJECT_DIR/scripts/finalize-phase.sh"

assert_contains() {
    local desc="$1" needle="$2" haystack="$3"
    if echo "$haystack" | grep -qF "$needle"; then
        echo "  ✅ PASS: $desc"; PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL: $desc（期望含：$needle）"; echo "     實際：$haystack"; FAIL=$((FAIL + 1))
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
assert_file_contains() {
    local desc="$1" needle="$2" filepath="$3"
    if grep -qF "$needle" "$filepath" 2>/dev/null; then
        echo "  ✅ PASS: $desc"; PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL: $desc（$filepath 中找不到：$needle）"; FAIL=$((FAIL + 1))
    fi
}

TMP_DIR=$(mktemp -d)
trap 'cd "$PROJECT_DIR"; rm -rf "$TMP_DIR"' EXIT

# Case 1：無引數 → 應 exit 1 並輸出用法說明
cd "$PROJECT_DIR"
output=$(bash "$SCRIPT_PATH" 2>&1)
exit_code=$?
assert_exit_code "無引數 → exit 1" 1 "$exit_code"
assert_contains "無引數 → 輸出用法說明" "用法" "$output"

# Case 2：缺少 phase_map.md → 按 Enter 後 Step 2 應報錯並 exit 1
mkdir -p "$TMP_DIR/memory/history_lookup"
cat > "$TMP_DIR/TASK_HISTORY.md" << 'EOF'
### Phase 99 測試
EOF
cd "$TMP_DIR"
output=$(echo "" | bash "$SCRIPT_PATH" 99 "測試重點" 2>&1)
exit_code=$?
assert_exit_code "缺 phase_map.md → exit 1" 1 "$exit_code"
assert_contains "缺 phase_map.md → 輸出找不到錯誤" "找不到" "$output"

# Case 3：phase_map.md 存在 → Step 2 應成功 append（兩個 Enter 跳過互動步驟）
cat > "$TMP_DIR/memory/history_lookup/phase_map.md" << 'EOF'
| Phase | 說明 | 狀態 | 日期 |
|---|---|---|---|
EOF
cd "$TMP_DIR"
# 兩個 Enter：Step 1 read + Step 3 read；Obsidian 路徑不存在會警示但不崩潰
printf "\n\n" | bash "$SCRIPT_PATH" 88 "Phase 88 測試重點" > /dev/null 2>&1 || true
assert_file_contains "Phase_map 應 append Phase 88" "Phase 88" "$TMP_DIR/memory/history_lookup/phase_map.md"

cd "$PROJECT_DIR"
echo ""
echo "結果：PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
