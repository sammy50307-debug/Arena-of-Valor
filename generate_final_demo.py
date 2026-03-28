import json
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import sys

# 模擬數據 (來自 raw_20260329.json)
REAL_DATA = [
    {
        "title": "GCS 2026 春季賽 W5D2 戰績表 - FW 與 ONE 的絕死對決",
        "content": "FW NAILIU 展現天花板級操作，葉娜神級逆風反切 ONE 後排！GCS 賽事焦點全面延燒。",
        "url": "https://www.facebook.com/AoVGCS/posts/1551418626996690/",
        "platform": "facebook",
        "sentiment_score": 0.88,
        "summary": "FW 戰隊在生死局展現驚人韌性，目前全網瘋傳操作片段。",
        "is_hero_focus": False
    },
    {
        "title": "高雄櫻花季 × 傳說對決 🌸 羊咩羊咩悸動時刻",
        "content": "現場氛圍炸裂！櫻花樹下的約定帶動玩家熱情參與。芽芽萌度再次洗版社群。",
        "url": "https://www.instagram.com/p/DWbPi2qCDBX/",
        "platform": "instagram",
        "sentiment_score": 0.94,
        "summary": "實體聯動好評爆表，櫻花季造景與芽芽看板娘成為必打卡點。",
        "is_hero_focus": True
    },
    {
        "title": "特爾＆美娜：聖典第 88 篇章技能搶先看",
        "content": "蔚藍熱浪造型故事公開，辣妹加入將傳說戰場變成水世界！",
        "url": "https://www.facebook.com/AoVTW/videos/1347825600443763",
        "platform": "facebook",
        "sentiment_score": 0.75,
        "summary": "新聖典引爆夏季氛圍，玩家對水世界主題與技能特效反應熱烈。",
        "is_hero_focus": False
    }
]

import config # 導入專案配置

def render_final():
    base_path = Path(r"d:\Coding Project\Arena of Valor")
    template_dir = base_path / "reporter" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    # 注入全局變數與工具函數，解決模板中的 UndefinedError
    env.globals.update(
        getattr=getattr,
        config=config
    )
    
    template = env.get_template("report.html")
    
    # 建立一個模擬的 daily_summary 結構
    daily_summary = {
        "date": "2026-03-29",
        "overview": "今日輿情的核心圍繞在 GCS 春季賽 W5D2 的熱血餘威。FW NAILIU 的葉娜操作被公認為操作天花板，在與 ONE 的強強對決中成為焦點話題。同時，高雄櫻花季線下活動也迎來高峰，『芽芽』作為活動門面深受肯定，成功緩解了遊戲內部分負面聲量。聖典 88 篇章的夏日水世界主題亦大幅提升了玩家的回流意願。",
        "sentiment_distribution": {"positive": 28, "negative": 3, "neutral": 8},
        "hot_topics": ["GCS春季賽", "FW逆風翻盤", "櫻花季女神節", "聖典88篇"],
        "hero_focus": {
            "name": "芽芽",
            "summary": "今日「芽芽」在櫻花季現場展示最新系列，甜美氛圍成功消彌了部分玩家關於平衡性的吐槽。玩家紛紛敲碗實體周邊與連動造型。雖然被戲稱為『發霉芽』，但在櫻花瓣的點綴下，萌力值達到歷史新高！",
            "sentiment_score": 0.92,
            "top_comments": ["芽芽這造型必買吧！", "發霉芽也要漂漂亮亮的", "櫻花季看到芽芽真的值了"]
        },
        "platform_breakdown": {
            "instagram": {"post_count": 12, "avg_sentiment": 0.8},
            "threads": {"post_count": 8, "avg_sentiment": 0.6},
            "facebook": {"post_count": 19, "avg_sentiment": 0.75}
        },
        "recommendation": "建議官方利用櫻花季熱度，加開線上『應援芽芽』抽獎活動，將線下正面声量全面導入聖典 88 篇章的預售熱度中。"
    }

    # 合併與映射
    posts = []
    for d in REAL_DATA:
        posts.append({
            "post": {
                "title": d["title"],
                "content": d["content"],
                "url": d["url"],
                "platform": d["platform"]
            },
            "analysis": {
                "sentiment_score": d["sentiment_score"],
                "summary": d["summary"],
                "is_hero_focus": d["is_hero_focus"]
            }
        })

    html_content = template.render(
        date=daily_summary["date"],
        total_posts=39,
        overview=daily_summary["overview"],
        sentiment_distribution=daily_summary["sentiment_distribution"],
        hot_topics=daily_summary["hot_topics"],
        detected_events=daily_summary["hot_topics"],
        platform_breakdown=daily_summary["platform_breakdown"],
        recommendation=daily_summary["recommendation"],
        hero_focus=daily_summary["hero_focus"],
        hero_focus_posts=posts[:2],
        posts=posts
    )

    output_path = base_path / "aov_report_LUSH_LIVELY_FINAL.html"
    output_path.write_text(html_content, encoding="utf-8")
    print(f"旗艦報表已生成: {output_path.absolute()}")

if __name__ == "__main__":
    render_final()
