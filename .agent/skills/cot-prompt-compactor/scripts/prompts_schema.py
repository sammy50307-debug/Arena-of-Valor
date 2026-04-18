from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# ── 單篇貼文分析結構模型 ──────────────────────────────────────
class EventDetail(BaseModel):
    name: str = Field(description="活動名稱")
    type: Literal["限時活動", "版本更新", "電競賽事", "合作活動", "其他"] = Field(description="活動類型")
    details: str = Field(description="活動細節描述")

class SinglePostAnalysisSchema(BaseModel):
    reasoning: str = Field(description="簡短推論，先在此判斷真實意圖與潛台詞（尤其是反諷）。")
    sentiment: Literal["positive", "negative", "neutral"] = Field(description="對遊戲的情緒傾向")
    sentiment_score: float = Field(ge=0.0, le=1.0, description="情緒強度")
    region: Literal["TW", "TH", "VN"] = Field(description="貼文來源區域")
    original_language: Literal["zh", "th", "vi"] = Field(description="原始語言")
    translated_content: Optional[str] = Field(None, description="如果原始內容非繁體中文，請在此提供翻譯後的繁體中文內容")
    category: Literal["遊戲體驗", "角色討論", "活動資訊", "版本更新", "Bug回報", "電競賽事", "社群互動", "其他"] = Field(description="討論主題歸類")
    keywords: List[str] = Field(description="關鍵字列表", default_factory=list)
    events: List[EventDetail] = Field(description="偵測到的活動或版本更新", default_factory=list)
    summary: str = Field(description="一句話概述這篇貼文的核心要點（請使用繁體中文）")
    relevance_score: float = Field(ge=0.0, le=1.0, description="該貼文與《傳說對決》的相關程度，0 表示完全無關，1 表示高度相關")
    is_hero_focus: bool = Field(description="如果內容明確提及焦點英雄（例如：芽芽），請將此欄位設為 true")

# ── 每日彙總報告結構模型 ──────────────────────────────────────
class SentimentDistribution(BaseModel):
    positive: int
    negative: int
    neutral: int

class HotTopic(BaseModel):
    topic: str
    mention_count: int
    sentiment: Literal["positive", "negative", "neutral"]
    description: str

class DetectedSummaryEvent(BaseModel):
    name: str
    type: str
    source_count: int
    details: str

class PlatformStats(BaseModel):
    post_count: int
    avg_sentiment: float

class PlatformBreakdown(BaseModel):
    instagram: PlatformStats
    threads: PlatformStats
    facebook: PlatformStats

class RegionInsight(BaseModel):
    summary: str
    hot_hero: str

class GlobalInsights(BaseModel):
    TW: RegionInsight
    TH: RegionInsight
    VN: RegionInsight

class HeroFocus(BaseModel):
    name: str
    summary: str
    sentiment_score: float
    top_comments: List[str]

class DailySummarySchema(BaseModel):
    date: str = Field(description="YYYY-MM-DD")
    overview: str = Field(description="今日整體輿情概述（3-5 句話）")
    sentiment_distribution: SentimentDistribution
    hot_topics: List[HotTopic] = Field(description="熱門話題 (最多列出前 10 名)")
    detected_events: List[DetectedSummaryEvent] = Field(default_factory=list)
    platform_breakdown: PlatformBreakdown
    alerts: List[str] = Field(description="需要關注的重要警訊（例：明顯的負面風暴）", default_factory=list)
    recommendation: str = Field(description="具體且可執行的營運團隊建議")
    global_insights: GlobalInsights
    hero_focus: Optional[HeroFocus] = Field(None, description="針對指定角色的專屬輿情總結")
