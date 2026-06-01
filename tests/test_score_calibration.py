"""P105.1 S3.2 score 標度校準：sentiment_score 語意方向跨 model 一致。

根因：prompt 有範圍 0.0~1.0 但無「哪端正/負」方向 → gemini/deepseek 各自解讀
（gemini negative→低分 / deepseek negative→高分）；下游 history.py 用 daily
hero_focus.sentiment_score 算趨勢 → 切 deepseek 後趨勢翻轉失真。
校準：single + daily 兩處 prompt 注意事項 + schema description 明定 0.0=負…1.0=正。
此檔驗「校準文字落地」（單元）；跨 model 對齊驗證走真實呼叫（opt-in，見 S3.2 驗證步）。
"""

from analyzer.prompts import SYSTEM_DAILY_SUMMARY, SYSTEM_SINGLE_POST
from analyzer.sentiment import DAILY_SUMMARY_SCHEMA, SINGLE_POST_SCHEMA


def test_single_post_prompt_defines_score_direction():
    # 校準後 single post prompt 必須明定方向（極負面/極正面），消除跨 model 歧義。
    assert "極負面" in SYSTEM_SINGLE_POST
    assert "極正面" in SYSTEM_SINGLE_POST


def test_daily_summary_prompt_defines_score_direction():
    # daily hero_focus.sentiment_score 是 history 趨勢直接來源，方向同樣須明定。
    assert "極負面" in SYSTEM_DAILY_SUMMARY
    assert "極正面" in SYSTEM_DAILY_SUMMARY


def test_single_post_schema_score_has_direction_description():
    desc = SINGLE_POST_SCHEMA["properties"]["sentiment_score"].get("description", "")
    assert "極負面" in desc and "極正面" in desc


def test_daily_hero_focus_score_has_direction_description():
    hero_focus = DAILY_SUMMARY_SCHEMA["properties"]["hero_focus"]["properties"]
    desc = hero_focus["sentiment_score"].get("description", "")
    assert "極負面" in desc and "極正面" in desc
