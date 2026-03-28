import sys
from pathlib import Path
from datetime import datetime

# 將當前目錄加入路徑以匯入專案模組
sys.path.append(str(Path(__file__).resolve().parent))

from reporter.generator import ReportGenerator

def create_mock_data():
    """建立模擬的分析數據。"""
    
    # 模擬每日總結
    daily_summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "overview": "今日《傳說對決》社群討論熱烈，尤其是英雄「芽芽」的平衡性調整引發大量轉發。同時 GCS 賽季公告也獲得了高度關注。整體輿情偏向中性偏正。我們觀察到玩家對於新版本造型的期待值很高，但也有一部分玩家回報了連線不穩的問題。",
        "sentiment_distribution": {
            "positive": 12,
            "negative": 5,
            "neutral": 20
        },
        "hot_topics": [
            {"topic": "芽芽削弱", "mention_count": 8, "sentiment": "negative", "description": "玩家不滿輔助裝備調整對芽芽的影響"},
            {"topic": "GCS 春季賽", "mention_count": 15, "sentiment": "neutral", "description": "官方發布最新賽程表"},
            {"topic": "趙雲新造型", "mention_count": 6, "sentiment": "positive", "description": "「戰鼓嘹原」造型大獲好評"}
        ],
        "detected_events": [
            {"name": "GCS 2026 春季賽", "type": "電競賽事", "source_count": 3, "details": "官方公布播報陣容與時程"}
        ],
        "platform_breakdown": {
            "instagram": {"post_count": 10, "avg_sentiment": 0.8},
            "threads": {"post_count": 7, "avg_sentiment": 0.6},
            "facebook": {"post_count": 20, "avg_sentiment": 0.5}
        },
        "recommendation": "建議官方社群團隊在回應芽芽討論時，強調輔助裝備的多樣性選擇，並盡快處理玩家反映的網路延遲報案。",
        "hero_focus": {
            "name": "芽芽",
            "summary": "芽芽今日再度成為社群焦點。玩家針對功能型輔助在關鍵時刻的扛傷策略展開激辯。大部分玩家認為芽芽在當前版本的生存壓力較大，需要更精確的進出場觀念。",
            "sentiment_score": 0.42,
            "top_comments": ["芽芽真的變難玩了", "這波砍得太兇了吧", "其實會玩的還是很強"]
        }
    }
    
    # 模擬貼文列表
    mock_posts = [
        {
            "post": {
                "platform": "dcard",
                "content": "芽芽扛傷當然比不過硬輔，畢竟是功能型輔助，但是重要的是要扛關鍵傷害。比如：圖倫的大、刀鋒的刷、對面射手的攻擊。",
                "url": "https://www.dcard.tw/f/aov/p/123456",
                "timestamp": "2026-03-29",
                "published_date": "2026-03-29",
                "author": "輔助王",
                "is_hero_focus": True
            },
            "analysis": {
                "sentiment": "neutral",
                "sentiment_score": 0.5,
                "summary": "這篇貼文討論了傳說對決英雄芽芽作為功能型補助的玩法，特別強調其在關鍵時刻扛下傷害的策略。",
                "is_hero_focus": True
            }
        },
        {
            "post": {
                "platform": "facebook",
                "content": "【GCS 2026 春季賽賽程公告】這篇貼文公告了GCS 2026春季賽的播報陣容與賽事時程，同時詳細介紹了趙雲新造型「戰鼓嘹原」的販售資訊。",
                "url": "https://www.facebook.com/AoV.GCS/posts/789012",
                "timestamp": "2026-03-28",
                "published_date": "2026-03-28",
                "author": "傳說對決官方",
                "is_hero_focus": False
            },
            "analysis": {
                "sentiment": "positive",
                "sentiment_score": 0.85,
                "summary": "官方公告了 GCS 春季賽賽程與趙雲新造型販售資訊。",
                "is_hero_focus": False
            }
        },
        {
            "post": {
                "platform": "instagram",
                "content": "芽芽又被削弱了啦！真的很討厭耶，每次想玩的角色都被砍。有人也要一起連署抗議嗎？",
                "url": "https://www.instagram.com/p/abc12345",
                "timestamp": "2026-03-29",
                "published_date": "2026-03-29",
                "author": "芽芽愛好者",
                "is_hero_focus": True
            },
            "analysis": {
                "sentiment": "negative",
                "sentiment_score": 0.2,
                "summary": "玩家表達對芽芽削弱的高度不滿，並試圖發起連署。",
                "is_hero_focus": True
            }
        }
    ]
    
    return daily_summary, mock_posts

def main():
    summary, posts = create_mock_data()
    generator = ReportGenerator()
    report_path = generator.generate(summary, posts)
    print(f"PREVIEW_REPORT_PATH={report_path.absolute()}")

if __name__ == "__main__":
    main()
