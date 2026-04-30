
import json
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Load json
with open('data/analysis_20260501.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Set up jinja
env = Environment(loader=FileSystemLoader('reporter/templates'))
template = env.get_template('report.html')

html = template.render(
    date='2026-05-01',
    daily_summary=data.get('daily_summary', '無資料'),
    posts=data.get('posts', [])
)

for p in ['data/reports/aov_report_2026-05-01.html', 'ui_previews/aov_report_2026-05-01.html']:
    if Path(p).parent.exists():
        Path(p).write_text(html, encoding='utf-8')
print('Successfully regenerated reports with correct encoding!')

