import py_compile
import sys

# 強制 Windows 終端機輸出 UTF-8，防止亂碼
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    py_compile.compile('analyzer/gemini_client.py', doraise=True)
    print("gemini ok")
except Exception as e:
    print(f"gemini err: {e}")

try:
    py_compile.compile('analyzer/sentiment.py', doraise=True)
    print("sentiment ok")
except Exception as e:
    print(f"sentiment err: {e}")

try:
    py_compile.compile('analyzer/prompts.py', doraise=True)
    print("prompts ok")
except Exception as e:
    print(f"prompts err: {e}")
