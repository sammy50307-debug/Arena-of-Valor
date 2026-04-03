import os
from jinja2 import Environment, FileSystemLoader

try:
    env = Environment(loader=FileSystemLoader("reporter/templates"))
    template = env.get_template("report.html")

    # 模擬演示數據 (Showcase Data)
    mock_data = {
        "config": type("Config", (), {"HERO_FOCUS_NAME": "芽芽 YaYa"}),
        "date": "2026-04-03 旗艦預覽",
        "overview": "這是為 Phase 39 前端尊榮視覺升級準備的演示資料。我們已經套用了全新的 Responsive Grid、玻璃透視特效 (Glassmorphism) 以及芽芽的高光光暈微動畫。",
        "total_posts": 12850,
        "sentiment_distribution": {"positive": 9500, "negative": 1500, "neutral": 1850},
        "platform_breakdown": {"Facebook 討論區": 5000, "Instagram": 3000, "Threads": 2850, "YouTube 實況": 2000},
        "history_delta": {
            "overall": { "volume_pct": 12.5, "avg_baseline": 11000 },
            "weekly_vol_pulse": {
                "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                "volumes": [9500, 10200, 9800, 11500, 12000, 15000, 12850],
                "average": 11550
            },
            "alerts": [
                {
                    "label": "玩家活躍高峰",
                    "advice": "建議把握目前高正面情緒的時機，釋出新賽季預告。"
                }
            ]
        },
        "wordcloud": {
            "positive": [{"text": "特效真香", "weight": 24}, {"text": "手感好", "weight": 18}, {"text": "神缺", "weight": 10}],
            "negative": [{"text": "Bug", "weight": 20}, {"text": "爆Ping", "weight": 14}]
        },
        "hero_focus": {
            "name": "芽芽 YaYa",
            "summary": "【Phase 39 尊榮展示】芽芽近期勝率達到顛峰，社群滿意度極高，此區域已升級為帶有陰影流光折射 (Glass Sweep) 與上浮微動畫的尊榮級玻璃卡片。",
            "top_comments": ["芽芽加這件裝備根本無解，這個玻璃卡特效太美了！", "滑鼠放上去居然會有立體浮空感！"]
        },
        "combat_stats": {"芽芽 YaYa": {"win_rate": 56.4, "ban_rate": 88.2}},
        "analysis": {"overall": {"sentiment_score": 0.95}},
        "heatmap_data": {
            "hours": ["00", "04", "08", "12", "16", "20"],
            "heroes": ["芽芽", "凡恩", "刀鋒"],
            "data": [[0,0,5,1], [0,1,2,0], [0,2,8,1], [1,0,-2,-1], [1,1,6,1], [1,2,-4,-1], [2,0,10,1], [2,1,0,0], [2,2,7,1]]
        },
        "posts": [
            {
                "post": {"content": "這次的女團造型太香了，芽芽專屬的高光版面簡直是藝術品！", "platform": "facebook", "region": "TW"},
                "analysis": {"sentiment": "positive", "summary": "對英雄專屬區塊的版面感到驚艷。"}
            },
            {
                "post": {"content": "手機上看也超級清楚耶，版面排版超完美", "platform": "threads", "region": "TW"},
                "analysis": {"sentiment": "positive", "summary": "讚賞響應式格線 (CSS Grid) 升級"}
            }
        ]
    }

    html_path = "ui_previews/Phase39_Flagship_Showcase.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(template.render(**mock_data))
    print(f"SUCCESS: Created {html_path}")
except Exception as e:
    print(f"ERROR: {e}")
