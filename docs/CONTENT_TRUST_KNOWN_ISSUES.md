# Content Trust Known Issues

> P96 / R-017 registry. This file records content trust issues that must not rely on chat memory only.

## CT-001 wrong_focus_hero_title

- Symptom: the focus section may display or behave as if a non-focus hero belongs to the focus hero room.
- Expected behavior: the focus room title is controlled by `config.HERO_FOCUS_NAME`, currently `芽芽`.
- Current guard:
  - `ReportGenerator` locks `hero_focus.name` to config.
  - Focus recent cards require user-visible focus hero text evidence.
  - Regression: `tests/test_report_content_trust.py::test_report_locks_focus_title_to_config_and_filters_false_focus_cards`.

## CT-002 stale_article_pollution

- Symptom: articles with unknown dates can appear in `芽芽近期動態` as if they are fresh.
- Expected behavior: focus recent cards require both focus hero text evidence and a known post date.
- Current guard:
  - `top5_picker._compute_decay(None)` no longer treats missing timestamps as fresh.
  - Regression: `tests/test_report_content_trust.py::test_report_excludes_unknown_date_from_focus_recent_cards`.

