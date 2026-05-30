# 1. 清除可能衝突的舊變數 (確保萬無一失)
Remove-Item Env:\ANTHROPIC_API_KEY -ErrorAction SilentlyContinue

# 2. 注入滿血版魔改格式
$env:ANTHROPIC_BASE_URL="https://sub.chatones.site"
$env:ANTHROPIC_AUTH_TOKEN="sk-50a1e6689da8821e1053039d0667d4b65b7eee39db3d6b434d53f81e0f8e2806" # allowlist-secret chatones proxy token
$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " 🔥 滿血版戰車啟動！準備碾碎 502 錯誤！" -ForegroundColor Red
Write-Host "======================================" -ForegroundColor Cyan

# 3. 啟動 Claude
claude