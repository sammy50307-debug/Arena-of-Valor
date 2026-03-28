import os
from jinja2 import Environment, FileSystemLoader

# 模擬資料結構 (完全對應 main.py -> generator.py)
mock_data = {
    "date": "2026-03-29",
    "hero_focus_name": "芽芽",
    "hero_focus_summary": "芽芽今日再度成為社群焦點，玩家針對功能型輔助在關鍵時刻的扛傷策略展開激辯。大部分玩家認為芽芽在當前版本的生存壓力較大，不論是「發霉芽」還是「小芽卷」在輔助裝備的選擇上引發了熱烈討論。目前討論熱度高達 72%，社群主要關注如何優化芽芽的操作空間。",
    "hero_focus_sentiment_score": 72,
    "ai_summary": "今日《傳說對決》社群討論熱烈，尤其是英雄「芽芽」的平衡性調整與 GCS 2026 春季賽賽程公告引發大量關注。整體社群氛圍偏向正面與期待，玩家對於新版本造型與賽事進度討論度極高。",
    "action_recommendations": [
        "建議官方社群團隊在回應芽芽討論時，強調輔助裝備的多樣性選擇。",
        "針對 GCS 春季賽賽程，建議在社群媒體分階段發布倒數圖文，延續討論熱度。",
        "盡快處理 Dcard 與 Facebook 上玩家反映的遊戲閃退問題。"
    ],
    "posts": [
        {
            "title": "芽芽進場時機與抗壓策略熱烈討論",
            "snippet": "最近大家討論功能型輔助在關鍵時刻的扛傷策略展開激辯。有人說出裝要改，也有人說關鍵是跟隊友的默契。這篇 Dcard 貼文引發了不少高手給予操作建議...",
            "url": "https://dcard.tw/f/aov/p/24567890",
            "platform": "DCARD",
            "published_date": "2026-03-29",
            "sentiment": "POS",
            "is_hero_focus": True
        },
        {
            "title": "【GCS 2026 春季賽賽程公告】今日正式發布！",
            "snippet": "Garena 官方公告了 GCS 2026 春季賽賽程與趙雲新造型販售資訊。賽事將於下週五正式開打，千萬不要錯過首戰的精彩預告。",
            "url": "https://facebook.com/GarenaAoV/posts/12345678",
            "platform": "FACEBOOK",
            "published_date": "2026-03-28",
            "sentiment": "NEU",
            "is_hero_focus": False
        },
        {
            "title": "發霉芽這次的造型真的太可愛了，買爆",
            "snippet": "大家有買新造型了嗎？芽芽的這款真的萌翻天，特效也做得很細緻。雖然操作變難了一點，但看在這麼可愛的面子上還是可以原諒的。",
            "url": "https://threads.net/aov_fans",
            "platform": "THREADS",
            "published_date": "2026-03-29",
            "sentiment": "POS",
            "is_hero_focus": True
        }
    ]
}

def generate_full_preview():
    # 設定 Jinja2 環境
    template_dir = os.path.join(os.getcwd(), 'reporter', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    
    try:
        template = env.get_template('report.html')
        output_html = template.render(mock_data)
        
        # 輸出最終檔案
        output_path = "FINAL_FULL_UI.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_html)
        print(f"✅ 成功生成全景報表預覽：{output_path}")
    except Exception as e:
        print(f"❌ 生成失敗: {e}")

if __name__ == "__main__":
    generate_full_preview()
