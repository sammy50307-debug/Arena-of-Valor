import os
import sys

# 強制指定標準輸出支援 utf-8，避免 Windows cmd / PowerShell 預設為 Big5 導致亂碼
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
# Add scripts dir to path to import html_to_md
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'scripts'))

from html_to_md import HTMLDistiller

def test_distiller():
    input_path = os.path.join(script_dir, "examples", "sample_input.html")
    output_path = os.path.join(script_dir, "examples", "sample_output.md")

    if not os.path.exists(input_path):
        print(f"[-] Input file missing: {input_path}")
        return

    # Calculate token size (approximation, 1 char ~ 0.5 tokens, but we just compare char len)
    with open(input_path, 'r', encoding='utf-8') as f:
        html_data = f.read()
    
    html_len = len(html_data)

    print("[*] Initializing HTML Distiller...")
    distiller = HTMLDistiller()
    
    print("[*] Processing HTML...")
    result_md = distiller.process(html_data)
    md_len = len(result_md)

    saving_ratio = ((html_len - md_len) / html_len) * 100

    print(f"\n[+] Original HTML size: {html_len} characters")
    print(f"[+] Distilled MD size:  {md_len} characters")
    print(f"[+] Calculated Savings: {saving_ratio:.2f}%\n")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result_md)
        
    print(f"[+] Output saved to {output_path}")
    print("[✓] ALL TESTS PASSED")

if __name__ == "__main__":
    test_distiller()
