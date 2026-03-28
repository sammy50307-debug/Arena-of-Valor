import json
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import config

def generate_preview():
    # ── 準備模擬數據 (Phase 33 Mock Data) ──
    
    # 1. 模擬跨區域貼文
    mock_posts = [
        {
            "post": {
                "content": "這次芽芽的新造型真的太可愛了！台服什麼時候才要出？",
                "platform": "Dcard",
                "region": "TW",
                "published_date": "2026-03-29",
                "author": "AOVer_TW",
                "url": "https://www.dcard.tw/f/aov"
            },
            "analysis": {
                "sentiment": "positive",
                "summary": "玩家對芽芽新造型充滿期待，詢問台服上架時間。"
            }
        },
        {
            "post": {
                "content": "Yaya skin baru keren banget, tapi harganya mahal sekali.",
                "translated_content": "芽芽新皮膚非常酷，但價格太貴了。",
                "platform": "Facebook",
                "region": "VN",
                "published_date": "2026-03-29",
                "author": "Nguyen_AOV",
                "url": "https://www.facebook.com/aov_vn"
            },
            "analysis": {
                "sentiment": "neutral",
                "summary": "越南玩家認可皮膚質感，但對價格表示敏感。"
            }
        },
        {
            "post": {
                "content": "ฮีโร่ใหม่เก่งเกินไปแล้ว ปรับสมดุลหน่อยเถอะ ROV Th",
                "translated_content": "新英雄強得太過分了，請稍微調整一下平衡吧，ROV 泰國服。",
                "platform": "Threads",
                "region": "TH",
                "published_date": "2026-03-29",
                "author": "Thai_Gamer",
                "url": "https://www.threads.net/rov"
            },
            "analysis": {
                "sentiment": "negative",
                "summary": "泰國玩家強烈抱怨新英雄強度失衡，要求削弱。"
            }
        }
    ]

    # 2. 全球戰略洞察 (Global Insights)
    global_insights = {
        "TW": {"summary": "台服目前聚焦於『芽芽』新造性的視覺表現，情緒穩定上揚。", "hot_hero": "芽芽"},
        "TH": {"summary": "泰區爆發大規模『英雄強度不滿』，社群負面情緒達到高峰。", "hot_hero": "明世隱"},
        "VN": {"summary": "越南地區正進行『消費力拉鋸戰』，玩家持續觀望造型促銷。", "hot_hero": "莫拉"}
    }

    # 3. 戰略級預警 (Tactical Advice)
    history_delta = {
        "alerts": [
            {
                "label": "⚠️ 泰國戰區平衡性輿論失控 (CRITICAL_VOL)",
                "advice": "建議立即發布平衡性調整公告，並在 TH 官方粉專釋出開發者筆記以安撫玩家情緒。"
            }
        ]
    }

    # 4. 其他基礎數據
    sentiment_distribution = {"positive": 45, "negative": 25, "neutral": 30}
    platform_breakdown = {
        "instagram": {"post_count": 15},
        "threads": {"post_count": 22},
        "facebook": {"post_count": 35}
    }

    # ── 渲染 HTML ──
    env = Environment(loader=FileSystemLoader('reporter/templates'))
    env.globals.update(getattr=getattr, config=config)
    template = env.get_template('report.html')

    output_html = template.render(
        date=datetime.now().strftime("%Y-%m-%d"),
        posts=mock_posts,
        global_insights=global_insights,
        history_delta=history_delta,
        sentiment_distribution=sentiment_distribution,
        platform_breakdown=platform_breakdown,
        overview="今日全球聲量平穩，但泰國地區出現異常波動，需重點關注平衡性話題。台服芽芽焦點觀察依舊熱絡。",
        recommendation="建議維持台服促銷節奏，並針對泰服負面聲量進行公關預警。",
        hot_topics=[{"topic": "芽芽新造型", "mention_count": 156}, {"topic": "泰服平衡性", "mention_count": 98}]
    )

    # 寫入預覽檔案
    with open("preview_phase33.html", "w", encoding="utf-8") as f:
        f.write(output_html)
    
    print(f"--- Phase 33 預覽報表生成成功 ---")
    print(f"預覽檔案: {os.path.abspath('preview_phase33.html')}")

if __name__ == "__main__":
    try:
        generate_preview()
    except Exception as e:
        import traceback
        print(f"--- 發生錯誤 ---")
        print(traceback.format_exc())
