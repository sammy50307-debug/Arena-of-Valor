
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))
from reporter.generator import ReportGenerator

# Load json
with open('data/analysis_20260501.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

gen = ReportGenerator()
gen.generate(
    daily_summary=data.get('daily_summary', data), # Sometimes the whole thing is daily_summary
    analyzed_posts=data.get('posts', data.get('analyzed_posts', [])),
    output_dir=Path('data/reports')
)
print('Successfully regenerated reports with correct encoding using generator!')

