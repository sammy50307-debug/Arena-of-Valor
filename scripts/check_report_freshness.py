#!/usr/bin/env python3
"""check_report_freshness — P110 v2 報告凍結偵測器（advisory）。

偵測「最新動態 top5 連續 N 天完全相同（凍結）」。讀 data/reports/*.freshness.json
（generator._write_freshness_sidecar 寫的 top5 指紋 sidecar）比對連續日 top5_hash。

設計理由（飛輪 #4）：source_hash 雜湊的是「爬蟲輸入」非「輸出 top5」，是凍結的
假陰性盲區（輸入每天微動 hash 變、但偵測不到輸出鎖死）。故需獨立持久化 top5 身分。

凍結可能是 bug（爬蟲掛 / picker 鎖榜），也可能是芽芽優先的預期副作用——
故為 advisory（印警告但 exit 0），由阿喜判讀，勿為求 hash 變動誤砍芽芽。
"""
import argparse
import glob
import json
import os
import sys

DEFAULT_THRESHOLD = 3  # 連續 N 天 top5_hash 相同 → 告警


def lint_freshness(sidecars, threshold=DEFAULT_THRESHOLD):
    """純函式：sidecars = [{report_date, top5_hash}, ...]（依日期排序）。

    回 (frozen: bool, streak: int, detail: str)。
    """
    if len(sidecars) < threshold:
        return False, len(sidecars), f"資料不足（{len(sidecars)} < {threshold} 天），無法判定凍結"
    recent = sidecars[-threshold:]
    hashes = [s.get("top5_hash") for s in recent]
    if len(set(hashes)) == 1 and hashes[0]:
        dates = [s.get("report_date") for s in recent]
        return True, threshold, f"top5 最近 {threshold} 筆報告相同（{dates[0]}~{dates[-1]}，hash={hashes[0]}）"
    return False, threshold, f"top5 近 {threshold} 天有輪動（hash 不全相同）"


def load_sidecars(reports_dir):
    """讀 reports_dir 下所有 *.freshness.json，依 report_date 排序。"""
    paths = glob.glob(os.path.join(reports_dir, "aov_report_*.freshness.json"))
    out = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            if d.get("report_date") and d.get("top5_hash"):
                out.append(d)
        except Exception:
            pass
    out.sort(key=lambda d: d["report_date"])
    return out


def main():
    ap = argparse.ArgumentParser(description="P110 v2 報告凍結偵測器（advisory）")
    ap.add_argument("--reports-dir", default="data/reports")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=" * 60)
    print(" 🧊 報告凍結偵測器 (Report Freshness Checker)")
    print("=" * 60)
    sidecars = load_sidecars(args.reports_dir)
    frozen, streak, detail = lint_freshness(sidecars, args.threshold)
    if frozen:
        print(f" ⚠️ 偵測到凍結：{detail}")
        print(" → 可能：爬蟲未撈到新文 / picker 鎖榜 / 或芽芽優先的預期副作用")
        print(" → 凍結可能是芽芽優先預期副作用，請阿喜判讀，勿為求變動誤砍芽芽")
    else:
        print(f" ✅ {detail}")
    print()
    print("（本檢查為字面比對啟發式：top5_hash 連續相同才報，召回率僅供參考、人工覆核仍必要）")
    print("=" * 60)
    sys.exit(0)  # advisory：永遠 exit 0，不阻斷 CI


if __name__ == "__main__":
    main()
