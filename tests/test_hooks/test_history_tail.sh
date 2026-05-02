#!/bin/bash
# 測試 scripts/history-tail.sh
# 執行：bash tests/test_hooks/test_history_tail.sh

PASS=0; FAIL=0
PROJECT_DIR="$PWD"

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

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Case 1：HISTORY 檔案不存在 → 應 exit 1 並輸出明確錯誤
cd "$TMP_DIR"
output=$(bash "$PROJECT_DIR/scripts/history-tail.sh" 2>&1)
exit_code=$?
assert_exit_code "HISTORY 不存在 → exit 1" 1 "$exit_code"
assert_contains "HISTORY 不存在 → 輸出錯誤訊息" "找不到" "$output"

# Case 2：HISTORY 存在，末尾 Phase 短於 MAX_LINES → 輸出 Phase 內容
cat > "$TMP_DIR/TASK_HISTORY.md" << 'EOF'
早期內容行 1
早期內容行 2
### Phase 99 測試 Phase
這是測試 Phase 內容
第二行內容
EOF
cd "$TMP_DIR"
output=$(bash "$PROJECT_DIR/scripts/history-tail.sh" 2>&1)
exit_code=$?
assert_exit_code "短 Phase 正常輸出 → exit 0" 0 "$exit_code"
assert_contains "短 Phase 應顯示 ✅" "✅" "$output"
assert_contains "短 Phase 應包含 Phase 內容" "Phase 99 測試 Phase" "$output"

# Case 3：HISTORY 存在，末尾 Phase 超過 MAX_LINES → 輸出截斷警示
{
    echo "### Phase 100 超長 Phase"
    for i in $(seq 1 250); do
        echo "行 $i：測試內容"
    done
} > "$TMP_DIR/TASK_HISTORY.md"
cd "$TMP_DIR"
output=$(bash "$PROJECT_DIR/scripts/history-tail.sh" 200 2>&1)
exit_code=$?
assert_exit_code "超長 Phase → exit 0（截斷但不崩潰）" 0 "$exit_code"
assert_contains "超長 Phase → 輸出截斷警示" "超過" "$output"

cd "$PROJECT_DIR"
echo ""
echo "結果：PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
