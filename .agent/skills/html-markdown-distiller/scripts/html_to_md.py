import json
import os
import argparse
from typing import Optional
from bs4 import BeautifulSoup
import markdownify

class DOMTrimmer:
    def __init__(self, resource_path: str):
        self.ignore_rules = self._load_rules(resource_path)

    def _load_rules(self, path: str) -> dict:
        if not os.path.exists(path):
            return {"tags": [], "classes": [], "ids": []}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def trim(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Remove specific tags
        for tag in self.ignore_rules.get("tags", []):
            for element in soup.find_all(tag):
                element.decompose()
                
        # 2. Remove elements by class
        for cls in self.ignore_rules.get("classes", []):
            for element in soup.find_all(class_=cls):
                element.decompose()
                
        # 3. Remove elements by ID
        for element_id in self.ignore_rules.get("ids", []):
            for element in soup.find_all(id=element_id):
                element.decompose()
                
        # 4. Remove empty paragraphs or spans
        for element in soup.find_all(['p', 'div', 'span', 'article']):
            if not element.get_text(strip=True) and not element.find(['img', 'iframe']):
                element.decompose()
        
        return str(soup)

class Markdownizer:
    @staticmethod
    def to_markdown(html_content: str) -> str:
        # Convert trimmed HTML to markdown
        text = markdownify.markdownify(html_content, heading_style="ATX", bypass_tables=False)
        
        # Post-process: Remove excessive blank lines
        lines = text.split('\n')
        cleaned_lines = []
        consecutive_blanks = 0
        for line in lines:
            if not line.strip():
                consecutive_blanks += 1
            else:
                consecutive_blanks = 0
            
            if consecutive_blanks <= 2:
                cleaned_lines.append(line)
                
        return '\n'.join(cleaned_lines).strip()

class HTMLDistiller:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        resource_path = os.path.join(script_dir, '..', 'resources', 'ignore_tags.json')
        self.trimmer = DOMTrimmer(resource_path)

    def process(self, html_content: str) -> str:
        trimmed_html = self.trimmer.trim(html_content)
        markdown_text = Markdownizer.to_markdown(trimmed_html)
        return markdown_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTML to Markdown Distiller")
    parser.add_argument("--input", required=True, help="Path to input HTML file")
    parser.add_argument("--output", help="Path to output Markdown file (optional)")
    args = parser.parse_args()

    # pip install beautifulsoup4 markdownify 
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            html_data = f.read()

        distiller = HTMLDistiller()
        result_md = distiller.process(html_data)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result_md)
            print(f"[Success] Distilled markdown saved to {args.output}")
        else:
            print(result_md)

    except Exception as e:
        print(f"[Error] Failed to distill HTML: {e}")
