
import re
with open('reporter/templates/report.html', 'r', encoding='utf-8') as f:
    template = f.read()
match = re.search(r'<style>.*?</style>', template, re.DOTALL)
if match:
    new_style = match.group(0)
    for report_file in ['data/reports/aov_report_2026-05-01.html', 'ui_previews/aov_report_2026-05-01.html']:
        try:
            with open(report_file, 'r', encoding='utf-8') as rf:
                content = rf.read()
            content = re.sub(r'<style>.*?</style>', new_style, content, flags=re.DOTALL)
            with open(report_file, 'w', encoding='utf-8') as rf:
                rf.write(content)
            print(f'Successfully updated {report_file}')
        except FileNotFoundError:
            pass

