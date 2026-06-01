"""P105 S4 provider 對比 CLI。

同一批文章分別餵給兩個 provider/model，各跑一次分析，並排輸出篩選/分析結果差異，
供人工判斷哪個 model 篩選品質較好（服務「測篩選到完美」+「燒額度」雙目標）。

用法：
    py -m analyzer.provider_compare --provider-a gemini --provider-b openrouter \
        --model-b deepseek/deepseek-chat [--posts posts.json] [--limit 5]

* ``--posts``：文章 JSON 檔（list of {title, content, url, ...}）；省略則用內建 AOV 樣本。
* ``--limit``：限制比較篇數（控燒額度）。
* 兩個 provider 皆以裸 client 比較（不經 fallback），純看該 provider 本身的篩選表現。

⚠️ X4-J 邊界：本工具只「並排呈現」兩 provider 結果，**不做自動評分**；篩選好壞由人工判斷。
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import List, Optional

import config
from analyzer.provider_registry import build_provider
from analyzer.sentiment import SentimentAnalyzer
from scrapers.tavily_searcher import SearchResult

# 內建 AOV 樣本（開箱即用；不同英雄/情緒/平台，測篩選辨識力）
_SAMPLE_POSTS: List[SearchResult] = [
    SearchResult(
        title="芽芽新皮膚實測，團戰收割超強",
        content="今天拿到芽芽的新皮膚，打了幾場發現後期傷害真的很誇張，團戰一進去就能收一片，"
        "搭配輔助保護幾乎無解，推薦大家可以練一下，版本之子無誤。",
        url="https://example.com/aov/1",
        source="ptt",
        platform="PTT",
        region="TW",
    ),
    SearchResult(
        title="排位一直遇到雲中君，這英雄是不是太強了",
        content="昨天排位連續三場遇到雲中君，後期一個人守高地我們五個都打不進去，位移多又肉，"
        "想問大家覺得需要削弱嗎？還是只是我不會打。",
        url="https://example.com/aov/2",
        source="dcard",
        platform="Dcard",
        region="TW",
    ),
    SearchResult(
        title="新版本平衡性討論串",
        content="這次改版好多坦克被削，現在版本節奏變超快，前期一波輸就很難翻，大家覺得這樣的平衡"
        "健康嗎？官方是不是該調一下節奏。",
        url="https://example.com/aov/3",
        source="facebook",
        platform="Facebook",
        region="TW",
    ),
]

_JSON_FIELDS = {
    "title", "content", "url", "source", "platform", "score", "region", "published_date",
}


def load_posts(posts_path: Optional[str], limit: Optional[int]) -> List[SearchResult]:
    """讀文章來源：有 posts_path 讀 JSON，否則用內建樣本；limit 控篇數。"""
    if posts_path:
        with open(posts_path, encoding="utf-8") as fh:
            raw = json.load(fh)
        posts = [
            SearchResult(**{k: v for k, v in item.items() if k in _JSON_FIELDS})
            for item in raw
        ]
    else:
        posts = list(_SAMPLE_POSTS)
    if limit:
        posts = posts[:limit]
    return posts


def _fmt_analysis(a: dict) -> str:
    return (
        f"sentiment={a.get('sentiment', '?')} "
        f"score={a.get('sentiment_score', '?')} "
        f"relevance={a.get('relevance_score', '?')} "
        f"category={a.get('category', '?')}"
    )


def format_comparison(
    posts: List[SearchResult],
    res_a: dict,
    res_b: dict,
    label_a: str,
    label_b: str,
) -> str:
    """並排格式化兩 provider 對同批文章的分析結果（純函式，可測）。"""
    pa = res_a.get("posts", []) if isinstance(res_a, dict) else []
    pb = res_b.get("posts", []) if isinstance(res_b, dict) else []
    lines = [f"=== Provider 對比：{label_a}  vs  {label_b}（{len(posts)} 篇）==="]
    for i, src in enumerate(posts):
        a = pa[i].get("analysis", {}) if i < len(pa) else {}
        b = pb[i].get("analysis", {}) if i < len(pb) else {}
        lines.append(f"\n[{i + 1}] {src.title}")
        lines.append(f"  A | {label_a}: {_fmt_analysis(a)}")
        lines.append(f"       summary: {str(a.get('summary', ''))[:80]}")
        lines.append(f"  B | {label_b}: {_fmt_analysis(b)}")
        lines.append(f"       summary: {str(b.get('summary', ''))[:80]}")
    lines.append("\n⚠️ 比較僅供參考、最佳 model 需人工判斷（本工具不做自動評分）。")
    return "\n".join(lines)


async def run_compare(
    provider_a: str,
    model_a: str,
    provider_b: str,
    model_b: str,
    posts: List[SearchResult],
) -> str:
    """各 provider 以裸 client 跑一次 analyze_posts，回傳並排比較字串。"""
    client_a = build_provider(provider_a, model=model_a or None)
    client_b = build_provider(provider_b, model=model_b or None)
    res_a = await SentimentAnalyzer(llm_client=client_a).analyze_posts(posts, showcase=False)
    res_b = await SentimentAnalyzer(llm_client=client_b).analyze_posts(posts, showcase=False)
    label_a = f"{provider_a}:{model_a or 'default'}"
    label_b = f"{provider_b}:{model_b or 'default'}"
    return format_comparison(posts, res_a, res_b, label_a, label_b)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="P105 provider 對比 CLI（同批文章雙 provider 並排比較篩選/分析）"
    )
    parser.add_argument("--provider-a", default="gemini")
    parser.add_argument("--model-a", default="")
    parser.add_argument("--provider-b", default="openrouter")
    parser.add_argument("--model-b", default="")
    parser.add_argument(
        "--posts", default=None,
        help="文章 JSON 檔（list of {title,content,url,...}）；省略用內建 AOV 樣本",
    )
    parser.add_argument("--limit", type=int, default=None, help="限制比較篇數（控燒額度）")
    args = parser.parse_args()

    posts = load_posts(args.posts, args.limit)
    output = asyncio.run(
        run_compare(args.provider_a, args.model_a, args.provider_b, args.model_b, posts)
    )
    print(output)


if __name__ == "__main__":
    main()
