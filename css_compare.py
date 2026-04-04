import re

# Read Showcase (golden source for CSS)
with open('ui_previews/Phase39_Flagship_Showcase.html', 'r', encoding='utf-8') as f:
    showcase = f.read()
# Read Template (has Jinja2 logic)
with open('reporter/templates/report.html', 'r', encoding='utf-8') as f:
    template = f.read()

# Extract <style>...</style> from each
showcase_style = re.search(r'<style>(.*?)</style>', showcase, re.DOTALL).group(1)
template_style = re.search(r'<style>(.*?)</style>', template, re.DOTALL).group(1)

print(f'Showcase CSS length: {len(showcase_style)}')
print(f'Template CSS length: {len(template_style)}')

if showcase_style.strip() == template_style.strip():
    print('CSS IDENTICAL - no changes needed')
else:
    print('CSS DIFFERS - applying showcase CSS to template')
    # Replace template CSS with showcase CSS
    new_template = template.replace(template_style, showcase_style)
    with open('reporter/templates/report.html', 'w', encoding='utf-8') as f:
        f.write(new_template)
    print('DONE - Template CSS replaced with Showcase CSS')
