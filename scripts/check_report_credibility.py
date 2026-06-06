"""P108 報告數據可信度 checker（advisory）。

偵測報告 daily_summary 兩類靜默失真，防 R-028 復發：
  1. real_hot_topics 為空（jieba 缺失，或當日確實無足量文章）
  2. platform_breakdown 漏掉真實貼文平台（LLM 幻覺固定子集回潮）

advisory 性質：只回報警告字串、【不】阻斷報告生成（韌性層）。
可被 main.py 報告流程呼叫，也可獨立 CLI 跑既有 analysis.json。
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

# X4-J 自動化建議性工具邊界：本檢查為啟發式 advisory，無法判斷數據實質正確性
DISCLAIMER = "（此檢查為啟發式 advisory，僅供參考；人工覆核仍必要）"


def check_report_credibility(
    daily_summary: Dict[str, Any],
    analyzed_posts: Optional[Iterable[Dict[str, Any]]] = None,
) -> List[str]:
    """回傳警告字串列表（空＝通過）。不 raise、不阻斷。"""
    warnings: List[str] = []

    # 1. 熱詞非空
    if not (daily_summary.get("real_hot_topics") or []):
        warnings.append(
            "real_hot_topics 為空——熱詞統計區將不渲染"
            "（可能缺 jieba，或當日確實無足量文章，請人工確認）"
        )

    # 2. platform_breakdown 含真實平台
    pb = daily_summary.get("platform_breakdown") or {}
    pb_platforms = {
        k for k, v in pb.items()
        if isinstance(v, dict) and v.get("post_count", 0) > 0
    }
    if analyzed_posts is not None:
        from analyzer.local_analyzer import _canonical_platform
        real_platforms = {
            _canonical_platform(p)
            for e in analyzed_posts
            for p in [(e.get("post") or {}).get("platform")]
            if p
        }
        missing = real_platforms - pb_platforms
        if missing:
            warnings.append(
                "platform_breakdown 漏掉真實平台 %s——平台圖將失真"
                "（LLM 幻覺子集回潮？）" % sorted(missing)
            )
    elif not pb_platforms:
        warnings.append("platform_breakdown 為空或全 0——平台圖將失真")

    return warnings


def format_warnings(warnings: List[str]) -> str:
    if not warnings:
        return "[報告可信度] ✅ 通過 " + DISCLAIMER
    lines = ["[報告可信度] ⚠️ advisory（%d 項）：" % len(warnings)]
    lines += ["  - " + w for w in warnings]
    lines.append("  " + DISCLAIMER)
    return "\n".join(lines)


if __name__ == "__main__":
    import json
    import os
    import sys

    # CLI 直跑時 sys.path[0]＝scripts/，需把專案根加入才能 import analyzer
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if len(sys.argv) < 2:
        print("用法：py scripts/check_report_credibility.py <analysis.json> [raw.json]")
        sys.exit(0)

    with open(sys.argv[1], encoding="utf-8") as f:
        summary = json.load(f)
    posts = None
    if len(sys.argv) > 2:
        with open(sys.argv[2], encoding="utf-8") as f:
            raw = json.load(f)
        posts = [{"post": p, "analysis": {}} for p in raw]

    print(format_warnings(check_report_credibility(summary, posts)))
