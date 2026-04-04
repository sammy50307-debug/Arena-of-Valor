import py_compile
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
