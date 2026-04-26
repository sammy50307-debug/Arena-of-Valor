# `data/_quarantine/` — 上游髒檔隔離區

由 **Phase 56.5（data/ 上游髒檔治本）** 建立。

存放歷史上 producer 端尚未強化前產出的殘缺檔。**不參與 P61 history-trend-query 時序載入**——loader 只掃 `data/analysis_*.json`，本目錄內不會被讀到。

## 收件清單

| 檔案 | 隔離日 | 原因 | 來源風險 |
|---|---|---|---|
| `analysis_20260327.json` | 2026-04-26 | **0 bytes 空檔**（producer 寫檔中斷、無 atomic write 保護） | R7 |

## 為何保留而非刪除

當作「治本前最後一支殘檔」的歷史證據。Phase 56.5 S2 已在 `analyzer/data_writer.py` 加上 atomic write；未來理論上不應再產生 0-byte 檔。若日後又出現，代表治本機制有漏。

## 不在隔離區的處置

`analysis_20260329.json`（救難模式產出、缺 `total_posts`）走「就地修復」路線——已於 Phase 56.5 S3 補齊缺失欄位、留在原位。
