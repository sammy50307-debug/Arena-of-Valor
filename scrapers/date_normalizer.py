"""
巴哈姆特時間字串正規化（P108.3）。

巴哈論壇文章列表的時間顯示為相對/短格式（「昨天 22:39」「05-29 11:39」
「10 小時前」），缺年份或為相對基準。下游 top5_picker 的 _compute_decay /
_is_too_old 只認 ISO 絕對格式 → 巴哈文 decay 全部觸底 _DECAY_MIN、age filter
失效 → 排序退化純 score → 最新動態每天選同一批（R-030）。

治本策略：在爬蟲「爬取當下」把 published_date 正規化成 ISO
`YYYY-MM-DD HH:MM:SS`。相對時間（昨天 / N 小時前）的基準必須是爬取那一刻，
故只能在爬蟲端、爬取當下解析——這是本模組存在於 scrapers/ 而非 picker 的理由。
無法解析時回傳 None，由呼叫端決定回退（bahamut_scraper 保留原值，不丟資料）。

涵蓋格式（PoC 驗證真實全集 37/37，見 docs/P108.3_PLAN.md 附錄）：
  ① ISO 完整        2025-12-26 / 2026-06-02 22:39:00
  ② N 小時/分鐘/天前  10 小時前 / 30 分鐘前 / 3 天前（分鐘/天前為同源防禦性支援）
  ③ 昨天 HH:MM      昨天 22:39
  ④ 前天 HH:MM      前天 15:17
  ⑤ MM-DD HH:MM     05-29 11:39（無年份 → 補 now.year，跨年回退去年）
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

# 所有 pattern 皆 ^...$ 錨定且無巢狀量詞（X4-A：避免 ReDoS）
_ISO_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$")
_HOURS_AGO_RE = re.compile(r"^(\d+)\s*小時前$")
_MINUTES_AGO_RE = re.compile(r"^(\d+)\s*分鐘前$")
_DAYS_AGO_RE = re.compile(r"^(\d+)\s*天前$")
_REL_DAY_RE = re.compile(r"^(昨天|前天)\s+(\d{1,2}):(\d{2})$")
_MMDD_RE = re.compile(r"^(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})$")

_ISO_FMT = "%Y-%m-%d %H:%M:%S"


def normalize_published_date(raw: str | None, *, now: datetime | None = None) -> str | None:
    """
    巴哈時間字串 → ISO 'YYYY-MM-DD HH:MM:SS'；無法解析回 None。

    Args:
        raw: 巴哈論壇顯示的時間字串（可能為相對/短格式）。
        now: 爬取當下時間（相對時間的基準）；預設 datetime.now()。測試可注入。

    Returns:
        ISO 格式字串，或 None（呼叫端決定回退，例如保留原值）。
    """
    s = (raw or "").strip()
    if not s:
        return None
    now = now or datetime.now()

    # ① ISO 完整
    m = _ISO_RE.match(s)
    if m:
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
        hh, mi, ss = int(m[4] or 0), int(m[5] or 0), int(m[6] or 0)
        try:
            return datetime(y, mo, d, hh, mi, ss).strftime(_ISO_FMT)
        except ValueError:
            return None

    # ② N 小時 / 分鐘 / 天前
    m = _HOURS_AGO_RE.match(s)
    if m:
        return (now - timedelta(hours=int(m[1]))).strftime(_ISO_FMT)
    m = _MINUTES_AGO_RE.match(s)
    if m:
        return (now - timedelta(minutes=int(m[1]))).strftime(_ISO_FMT)
    m = _DAYS_AGO_RE.match(s)
    if m:
        return (now - timedelta(days=int(m[1]))).strftime(_ISO_FMT)

    # ③④ 昨天 / 前天 HH:MM
    m = _REL_DAY_RE.match(s)
    if m:
        delta = 1 if m[1] == "昨天" else 2
        base = now - timedelta(days=delta)
        try:
            return base.replace(hour=int(m[2]), minute=int(m[3]),
                                second=0, microsecond=0).strftime(_ISO_FMT)
        except ValueError:
            return None

    # ⑤ MM-DD HH:MM（無年份 → 補 now.year；補後超過 now+1 天視為去年，跨年回退）
    m = _MMDD_RE.match(s)
    if m:
        mo, d, hh, mi = int(m[1]), int(m[2]), int(m[3]), int(m[4])
        try:
            cand = datetime(now.year, mo, d, hh, mi)
        except ValueError:
            return None
        if cand > now + timedelta(days=1):
            try:
                cand = datetime(now.year - 1, mo, d, hh, mi)
            except ValueError:
                return None
        return cand.strftime(_ISO_FMT)

    return None
