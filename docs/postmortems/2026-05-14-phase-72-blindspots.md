# P72 Blindspots — M4 追溯

> **M4 協議**：每個 Phase 收官後寫此檔，記錄「計畫書沒寫但實際撞到的問題」≥ 3 條，
> 通則化後加入 PHASE_TEMPLATE 體檢清單並升版。

- **Phase**：P72（P72.0 ~ P72.4 + P72.5 收尾）
- **日期**：2026-05-14
- **對應 Postmortem**：[2026-05-14-phase-72-metrics-and-m3m4-stitching.md](./2026-05-14-phase-72-metrics-and-m3m4-stitching.md)

---

## 計畫書沒寫、實際撞到的問題

### B-006：M4 `--sync-rules` anchor heuristic 召回率低

**計畫書原寫**：P72.3 設計 `--sync-rules` 比對 B-NNN 通則化規則 vs PHASE_TEMPLATE.md，印「建議納入」清單。

**實際撞到**：實測 PHASE_TEMPLATE v1.1 明明已含 B-001/B-003/B-005 對應規則（雙端 diff / test_skill.py 必要 / Exit Criteria 機械化），但 anchor heuristic 比對結果顯示「已涵蓋 0 條」，明顯低估。原因是 heuristic 只比對「規則字面相似度」，沒有處理「同義改寫」「結構性改寫」「規則被拆成多項」三種變體。

**通則化**：
> 任何「字面比對啟發式」自動化工具，必須在 design phase 明文標注「召回率僅供參考、人工審核仍必要」的免責邊界，並在 CLI 輸出最後一行印出該邊界。

**待加入**：PHASE_TEMPLATE STR9 「自動化建議性工具」段落，要求列出 false-negative 已知模式（同義改寫 / 結構性改寫 / 規則拆分）。

---

### B-007：PowerShell 與 bash here-doc 不互通

**計畫書原寫**：CLAUDE.md 鐵律寫「寫 → cat >> heredoc」，假設所有開發環境都支援 bash here-doc。

**實際撞到**：本機是 Windows 10，Claude Code 在 bash 環境執行 OK，但主公手動跑 PowerShell 命令做 commit 時，`cat << 'EOF'` 直接 syntax error。多次 commit 卡在這，最終靠先寫暫存 .md 再 `cat tmp.md >> target.md` 繞過。AI 與主公對 here-doc 在哪個 shell 可用沒有共識。

**通則化**：
> 任何跨平台 shell 操作（heredoc / pipe / redirect）必須在「鐵律」級指令明文標注「適用 shell」（bash only / PowerShell-compatible / 雙環境），不可假設單一 shell 通行。

**待加入**：CLAUDE.md 鐵律 v0.5 升版：在「寫 → cat >> heredoc」後加「（bash 限定；PowerShell 用 `Add-Content` 或寫暫存檔再 `cat tmp >> target`）」。

---

### B-008：test_dynamic_focus 3 個 pre-existing 失敗連跑 5 Phase 未處理

**計畫書原寫**：P72.0~P72.4 計畫書都標「全套無回歸」「3 個 pre-existing 失敗不阻擋本 Phase」。

**實際撞到**：5 個 Phase 連跑期間，沒有任何一個 Phase 把這 3 個失敗納入處理範圍，每個 Phase 都用「pre-existing」當免死金牌。事件迴圈隔離問題（單檔跑 OK / 全套跑掛）愈拖愈深，未來修起來成本更高。

**通則化**：
> 任何測試失敗連續被 ≥ 3 個 Phase 標為「pre-existing 不阻擋」時，**必須**強制升級為獨立 Phase 處理；Phase 計畫書若再次嘗試以「pre-existing」放行，lint 須阻擋。

**待加入**：PHASE_TEMPLATE M2 紅藍對抗段加「pre-existing 失敗計次」欄位；`lint_phase_plan.py` 加 P-PRE-3 規則（同一 failing test 名稱連 3 個 Phase 出現則 fail）。

---

### B-009：metrics JSONL 無 size cap 與輪轉策略

**計畫書原寫**：P72.0 `skill_metrics_logger._run_with_metrics()` 寫入 `~/.claude/skill_metrics.jsonl` append-only。

**實際撞到**：計畫書完全沒處理「跑久了 JSONL 會無限長」這件事。19 個 skill × 每天若干次呼叫 × 365 天 ≈ 數萬筆，雖然單檔大小可控（< 100MB 等級），但缺乏輪轉策略意味著未來某天必須做 migration。新觀察性工具上線即累積 known debt。

**通則化**：
> 任何 append-only 觀察性檔案（log / metrics / audit trail）落地當 Phase **必須**同時規劃 size cap / rolling policy / retention SOP 三項中至少一項，不能延後。

**待加入**：PHASE_TEMPLATE 「可觀察性層」段加「append-only 檔案 retention 政策」必填欄位。

---

### B-010：B-NNN 編號為全域連續但無防衝突機制（本 Phase 自踩）

**計畫書原寫**：M4 協議規定每個 Phase 寫 blindspots，但**沒明確定義 B-NNN 編號規則**（全域連續 vs Phase 內局部）。

**實際撞到**：本 Phase 寫 P72 blindspots 時，AI 只讀了 P71 blindspots 前 60 行（看到 B-001~B-004）就誤判最高編號是 B-004，從 B-005 開始續編。實際上 P71 用了 B-001~B-005（5 條），造成 P71-B-005 與 P72-B-005 同編號衝突。`m4_track_blindspots.py --sync-rules` 輸出 9 條規則時並列兩個 B-005，肉眼可見的編號重複。發現後人工重編 P72 為 B-006~B-009，並追加本條 B-010 作為自我盲點。

**通則化**：
> 任何「全域連續編號」的標識（B-NNN / R-NNN / D-NNN 等）必須：(a) 在協議文件明示「全域連續，禁止 Phase 內局部編號」；(b) 提供「下個編號」查詢命令（`grep -h '^### [BR]-' docs/**.md | sort -u | tail`）；(c) blindspots scaffold 工具在生成 B-XXX 占位符時，預先填入下個可用編號（而非 X X X）。

**待加入**：
- PHASE_TEMPLATE「Postmortem 預埋點 §11」加「B-NNN / R-NNN 編號查詢命令」備註
- `m4_track_blindspots.py --scaffold` 升級：自動掃描現有最大 B-NNN，預填 `### B-NNN：` 的 NNN（而非 XXX）

---

## 體檢清單升版摘要

| 版本 | 升版內容 | 驅動 Phase |
|---|---|---|
| v1.2（待議）| STR9 自動化工具免責邊界（B-006）/ CLAUDE.md heredoc shell 標注（B-007）/ PHASE_TEMPLATE pre-existing 失敗計次（B-008）/ 可觀察性層 retention 政策（B-009）+ P71 待議：deployed_to lint 強制（B-004）/ Orphan 狀態定義（B-002）+ B-NNN 編號衝突防範（B-010）| **P72** |

> ⚠️ 本表為「待議」狀態。X1 不可逆動作隔離原則下，PHASE_TEMPLATE.md 升版需主公人工核可，本 Phase 不自動寫入。

---

## 給下一個 Phase 的提醒

1. **B-006**：用「比對啟發式」做自動化前，先想好「召回率低」的免責輸出
2. **B-007**：寫 shell 命令到鐵律前，先標清楚適用哪個 shell（bash / PowerShell / both）
3. **B-008**：發現 pre-existing failing test 連 ≥ 3 phase 沒解 → 開獨立 Phase 處理，不能再用「不阻擋」放行
4. **B-009**：新增 append-only 觀察性檔案時，同 Phase 規劃 retention 策略，不延後
5. **B-010**：寫 blindspots 前先 `grep -h '^### B-' docs/postmortems/*.md | sort -u` 確認最後編號，避免衝突
