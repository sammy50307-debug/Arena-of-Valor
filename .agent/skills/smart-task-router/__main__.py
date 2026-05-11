"""
smart-task-router CLI 入口（P71.6）

用法：
  python __main__.py "我要查詢芽芽最近聲量走勢"
  python __main__.py "我要查詢芽芽最近聲量走勢" --output json
  python __main__.py --list
  python __main__.py --help
  NO_COLOR=1 python __main__.py "..." --output plain
"""
import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from router import SmartTaskRouter, _is_plain


def _output_mode(forced: str | None) -> str:
    if forced:
        return forced
    return "plain" if _is_plain() else "rich"


def cmd_route(args: argparse.Namespace) -> int:
    router = SmartTaskRouter()
    if not router.skills:
        print(
            f"[!] 無法載入 registry.json（路徑：{router.registry_path}）",
            file=sys.stderr,
        )
        return 1

    result = router.route(args.query)
    mode = _output_mode(args.output)

    if mode == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    # plain / rich 共用邏輯
    action = result["action"]
    best = result.get("best_match")
    conf = result.get("confidence", 0.0)

    if action == "NO_MATCH":
        print("[smart-task-router] 無高信心匹配（<0.7），不觸發任何 skill。")
        if result.get("candidates"):
            top = result["candidates"][0]
            print(f"  最接近：{top['name']}（信心 {top['confidence']:.2f}）")
        return 0

    # 有匹配 → 印 V1 觸發塊
    skill_name = best["name"]

    # 找出命中的 trigger_keyword（回填觸發理由）
    matched_kws = _find_matched_keywords(router, skill_name, args.query)
    if matched_kws:
        reason = f"匹配 trigger_keyword 「{'、'.join(matched_kws[:2])}」"
    else:
        reason = f"匹配 when_to_use 描述（信心 {conf:.2f}）"

    v1_block = router.format_v1_block(
        skill_name=skill_name,
        trigger_reason=reason,
        confidence=conf,
        action=action,
        source="smart-task-router (L2)",
    )
    print(v1_block)

    # 列出 TOP-3 候選
    if mode == "rich" and len(result["candidates"]) > 1:
        print()
        print("候選清單：")
        for c in result["candidates"]:
            bar = "█" * int(c["confidence"] * 10) + "░" * (10 - int(c["confidence"] * 10))
            print(f"  {bar} {c['confidence']:.2f}  {c['name']}")

    if action == "CONFIRM":
        print()
        print(f"[?] 信心 {conf:.2f}（0.7~0.89），是否執行 {skill_name}？[Y/n] ", end="", flush=True)

    return 0


def _find_matched_keywords(router: SmartTaskRouter, skill_name: str, query: str) -> list[str]:
    """找出造成路由命中的 trigger_keywords。"""
    q = query.lower()
    for skill in router.skills:
        if skill["name"] == skill_name:
            return [kw for kw in skill.get("trigger_keywords", []) if kw.lower() in q]
    return []


def cmd_list(args: argparse.Namespace) -> int:
    router = SmartTaskRouter()
    if not router.skills:
        print(f"[!] 無法載入 registry.json（路徑：{router.registry_path}）", file=sys.stderr)
        return 1

    mode = _output_mode(args.output)
    skills = router.list_skills()

    if mode == "json":
        print(json.dumps(skills, ensure_ascii=False, indent=2))
        return 0

    print(f"[smart-task-router] 共 {len(skills)} 個 skill：\n")
    for s in skills:
        status_tag = f"[{s['status']}]" if s["status"] else ""
        kws = "、".join(s["trigger_keywords"][:4])
        kws_str = f"  關鍵詞：{kws}" if kws else ""
        print(f"  {s['name']} {status_tag}")
        if s["description"]:
            print(f"    {s['description']}")
        if kws_str:
            print(kws_str)
    return 0


def main() -> int:
    raw = sys.argv[1:]

    # 直接查詢模式：python __main__.py "query" [--output X]
    # 判斷：第一個非 flag 參數不是已知子命令時，視為 query
    if raw and raw[0] not in ("route", "list", "--help", "-h"):
        output = None
        if "--output" in raw:
            idx = raw.index("--output")
            if idx + 1 < len(raw):
                output = raw[idx + 1]

        class _FakeArgs:
            pass
        fa = _FakeArgs()
        fa.query = raw[0]
        fa.output = output
        return cmd_route(fa)

    parser = argparse.ArgumentParser(
        prog="smart-task-router",
        description="L2 路由引擎：根據輸入自動比對最適 skill，輸出 V1 觸發塊",
    )
    sub = parser.add_subparsers(dest="cmd")

    # route
    p_route = sub.add_parser("route", help="路由查詢（預設）")
    p_route.add_argument("query", help="輸入任務描述")
    p_route.add_argument("--output", choices=["json", "plain", "rich"], default=None)

    # list
    p_list = sub.add_parser("list", help="列出所有已登記 skill")
    p_list.add_argument("--output", choices=["json", "plain", "rich"], default=None)

    args = parser.parse_args(raw)

    if args.cmd == "route":
        return cmd_route(args)
    if args.cmd == "list":
        return cmd_list(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
