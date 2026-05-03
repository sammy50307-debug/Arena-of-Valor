# P64 Token 節省實測報告（#4 G4-1 補強）

**測量日期**：2026-05-03  
**測量對象**：Token 優化四層防線 — TASK_HISTORY 查詢策略

---

## 測量方法

```
TASK_HISTORY.md 現況（2026-05-03）：
  行數：4,744 行
  字元數：176,948 字
  估算 token（÷3）：58,982 tokens

全讀策略：載入整份 = 58,982 tokens
grep+offset 策略：grep 錨點 → Read offset:N limit:200
  200 行估算 token：1,916 tokens

節省率：(58,982 - 1,916) / 58,982 = 96.8%
```

## 結論

| 指標 | 計畫預測 | 實測結果 |
|---|---|---|
| Token 節省率 | 92–96% | **96.8% ✅** |

預測成立，且超過上限。隨 TASK_HISTORY 繼續成長，節省率只會更高。

## 備註

- token 估算採 `chars ÷ 3`（中英混合文本的保守估計）
- 實際 API token 數依模型 tokenizer 略有差異，但量級結論不變
- 下次 TASK_HISTORY 超過 8,000 行時建議重新測量一次
