# 跨 Phase 風險登記簿（STR6）

> **用途**：登記跨 Phase 不滅的風險、待解隱患、需長期觀察的議題。每個 Phase 收官時主動掃一次，新風險入帳、已解風險標記關閉。
> **建立日期**：2026-05-07（隨 P69 模型選擇指引啟用）
> **格式**：每筆 = 編號 + 標題 + 來源 Phase + 風險級 + 狀態 + 描述 + 緩解策略

---

## 開放風險（Open）

### R-001：模型選擇指引三檔同步無自動檢測（G5-4）

- **來源**：P69（2026-05-07）
- **風險級**：🟡 中
- **狀態**：Open
- **描述**：`docs/MODEL_SELECTION_GUIDE.md` 主檔變更時，需手動同步 `~/.claude/CLAUDE.md` 與 `~/.gemini/GEMINI.md` 的全域縮版章節。沒有自動檢測機制，可能漂移。
- **緩解策略**：
  - 短期：每次修主檔時手動跑 diff（人工自律）
  - 長期：寫個 `scripts/check-model-guide-sync.sh`（v1.x 後續視需求做）
- **觸發升級**：若漂移導致 Claude / Gemini 端建議不一致 → 升 🔴 高

### R-002：Gemini / Anthropic 新模型大版本上線時的指引腐化

- **來源**：P69（2026-05-07）
- **風險級**：🟡 中
- **狀態**：Open
- **描述**：Gemini 4 / Claude 5 等大版本發布後，本指引內模型清單、價格、能力對照即過時。沒有自動偵測機制。
- **緩解策略**：
  - 已寫入指引 §8.3：「廠商發布新模型大版本」為強制升版觸發
  - 預設 90 天回顧週期（下次：2026-08-05）
- **觸發升級**：若主公連 3 次選擇與指引建議不符 → 立即升 v2.0

### R-003：AI 是否實際遵循「Opus 卡住主動提醒」強制條款（觀察期）

- **來源**：P69（2026-05-07）
- **風險級**：🟡 中
- **狀態**：Open（觀察期）
- **描述**：指引 §3.3 規定 AI 達卡住判定須主動提醒換 Gemini，但這是**行為條款**，需實際使用後驗證 AI 是否真的遵循。
- **緩解策略**：
  - 主公在實戰中觀察至少 3 次「應提醒」情境，記錄 AI 是否主動提醒
  - 若漏提醒次數 ≥ 1 → 在 CLAUDE.md / GEMINI.md 全域章節**強化**該條款
- **觀察截止**：2026-08-05（同 90 天回顧）

---

### R-004：UI/UX 修補無 LINE WebView 自動化迴歸測試（P70.3）

- **來源**：P70.3 收官（2026-05-08）
- **風險級**：🟡 中
- **狀態**：Open（人工 SOP 緩解中）
- **描述**：`reporter/templates/report.html` 的 CSS / touch event / position 規則改動可能在 LINE in-app browser（WKWebView / Chrome WebView）破壞滑動或互動，但其他環境（桌面、一般行動瀏覽器）正常難以察覺。P70.3 的 `overflow-x: hidden on html` 即此類沉默損壞案例，從 P63.2 拖到 P70.3 約 5 週。
- **緩解策略**：
  - 短期（人工 SOP）：任何 `reporter/templates/` 的修改收官前，主公在 LINE 實機點開 1 個樣本報告驗收
  - 中期：評估 Playwright + iOS WKWebView 模擬（非 LINE app 直測，但接近）的 ROI
  - 長期：若同類沉默損壞 ≥ 2 次再發，升級為自動化 smoke test 必做項
- **觀察截止**：下次 `templates/` 重大改動時 review

---

### R-006：報告頁回戰略門戶按鈕需同步修補現有報告（P70.3.1 衍生）

- **來源**：P70.3.1 收官（2026-05-08）
- **風險級**：🟡 中
- **狀態**：Open（人工 SOP 緩解中）
- **描述**：`reporter/templates/` 的 HTML 結構改動（如加回首頁按鈕）不會自動反映到已生成的舊報告，需批次 patch 腳本手動補做。目前 10 個 5 月報告已補齊，但未來若有更多改動，仍需人工維護批次腳本。
- **緩解策略**：
  - 短期：結構性 template 改動收官時，附帶一份 idempotent Python patch 腳本，同步更新現有報告
  - 中期：評估 report 生成改為 server-side render（SSR）以消除靜態複製問題
- **觸發升級**：若同步遺漏導致報告體驗分裂 ≥ 2 次 → 中期方案升為必做

---

### R-007：`.back-to-landing` 未列入 mobile backdrop-filter 停用清單（P70.3.1 審計）

- **來源**：P70.3.1 63 維度審計（2026-05-08）
- **風險級**：🟢 低
- **狀態**：✅ 已修補（2026-05-08）
- **描述**：行動版（`@media max-width 768px`）停用 `backdrop-filter` 的 selector 清單未含 `.back-to-landing`，導致按鈕在 mobile 仍觸發模糊效果 → 滑動卡頓風險。
- **緩解策略**：已將 `.back-to-landing` 加入 selector；template + 10 舊報告同步修補。
- **關閉條件**：已修補，觀察下次 LINE 實機驗收結果。

---

### R-008：`.back-to-landing` 缺少 :focus 樣式與 aria-label（P70.3.1 審計）

- **來源**：P70.3.1 63 維度審計（2026-05-08）
- **風險級**：🟢 低
- **狀態**：✅ 已修補（2026-05-08）
- **描述**：按鈕缺少 `:focus` 可見輪廓（無障礙 a11y 標準），且無 `aria-label`（螢幕閱讀器無法正確識別）。
- **緩解策略**：已補 `.back-to-landing:focus { outline: 2px solid #f472b6; outline-offset: 3px; }` 及 `aria-label="返回戰略門戶首頁"`；template + 10 舊報告同步修補。
- **關閉條件**：已修補，無需進一步觀察。

---

### R-005：`-webkit-overflow-scrolling: touch` 已 deprecated（G5-1 退化偵測）

- **來源**：P70.3 收官（2026-05-08）
- **風險級**：🟢 低
- **狀態**：Open（觀察期）
- **描述**：`-webkit-overflow-scrolling: touch` 為 iOS 13+ 已 deprecated 屬性，目前保留是「不傷害」原則。若未來 WebKit 移除支援或改為 hard error，可能影響 momentum scroll。
- **緩解策略**：90 天後 review，若 iOS 14+ 普及度 ≥ 95% 則移除此屬性。
- **觀察截止**：2026-08-08

---

## 已關閉風險（Closed）

（暫無）

---

## 變更紀錄

- **2026-05-07**：建立檔案（隨 P69 模型選擇指引啟用 STR6）；登記 R-001/R-002/R-003。
- **2026-05-08**：P70.3 收官登記 R-004（UI/UX LINE 迴歸盲區）+ R-005（webkit deprecated 屬性 90 天 review）。P70.3.1 審計追加 R-006（舊報告同步風險）+ R-007（mobile blur fix，已關閉）+ R-008（a11y fix，已關閉）。
