# 📜 旗艦視覺總綱：Phase 40 視覺真經 (Flagship UI Bible)

## 🎨 核心視覺參數 (Core Visual Specs)

### 1. 深度玻璃質感 (Glassmorphism 2.0)
*   **背景色 (Glass Background)**: `rgba(255, 255, 255, 0.1)`
*   **模糊度 (Backdrop Blur)**: `10px` (目前桌機版卡頓主因，預計下調)
*   **邊框 (Glass Border)**: `rgba(255, 255, 255, 0.2)`
*   **霓虹光效 (Neon Glow)**: `0 0 15px rgba(219, 39, 119, 0.3)`

### 2. 定錨堡壘背景 (The Fortress Background)
*   **技術元件**: `#fixed-background-fortress` (獨立 DIV)
*   **GPU 加速**: `-webkit-transform: translate3d(0,0,0)`
*   **定錨法**: `position: fixed`, `z-index: -20`
*   **適配度**: Mobile 與 PC 已完成初步定錨，將朝 `-webkit-fill-available` 優化。

### 3. 黃金佈局比例 (Standard Layout)
*   **Desktop Grid**: `2fr 1fr` (情報中心 : 今日焦點)
*   **Mobile Flow**: `1fr` (垂直堆疊)
*   **主流配色**: 旗艦桃紅 (#db2777) 與 櫻色漸層。

## ⚠️ 性能預警紀錄
*   **卡頓成景**: 300ms 產出之櫻花粒子 (`.sakura`) + 多層 `backdrop-filter: blur(10px)`。
*   **修補策略**: 粒子產出降頻至 600ms，模糊度降維。

---
*存檔時間：2026-04-05 07:18*
*執行助理：Antigravity (AI Coding Specialist)*
