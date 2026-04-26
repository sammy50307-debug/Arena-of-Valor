---
description: 把自然語言轉成五段式結構化 Prompt（呼叫 nl-to-prompt-structurer skill）
allowed-tools: Bash, Read
argument-hint: <自然語言內容> [--lang zh|en] [--role <角色>] [--mode full|lite] [--context <背景>]
---

# /prompt

把口語化的需求轉成五段式 Markdown Prompt（角色 / 背景 / 任務 / 限制 / 輸出格式）。
純規則式、零 LLM 成本，呼叫 `.agent/skills/nl-to-prompt-structurer/` skill。

> **執行此 slash 時，回覆首段必須先標 `[nl-to-prompt-structurer 已啟動]`**（依本專案 skill 啟動標記鐵律）。

## 使用語法

| 模式 | 範例 | 說明 |
|---|---|---|
| 預設 | `/prompt 用 markdown 整理今天戰報，300 字以內` | 自動偵測語言、推斷角色、五段全出 |
| 強制英文 | `/prompt 整理戰報 --lang en` | 中文輸入但用英文模板 |
| 覆寫角色 | `/prompt 翻譯這段 --role 法律譯者` | 不走自動推斷 |
| 精簡模式 | `/prompt 列重點 --mode lite` | 只輸出 task + output_format 兩段 |
| 補背景 | `/prompt 寫一篇文 --context "目標讀者：高中生"` | 背景段手動補 |

## 你（AI）應做的事

1. **首段標註** `[nl-to-prompt-structurer 已啟動]`
2. 解析參數，呼叫 inline Python：

   ```bash
   py -c "
   import sys
   sys.path.insert(0, '.agent/skills/nl-to-prompt-structurer')
   from scripts.structurer import PromptStructurer
   s = PromptStructurer()
   print(s.structure('<text>', lang=<lang or None>, role=<role or None>, mode='<mode>', context=<context or None>))
   "
   ```

3. **回覆主公**：
   - 直接呈現五段式 Markdown 輸出
   - 若使用者覆寫了 `--lang` / `--role`，明確告知「已套用覆寫」
   - 若 mode='lite'，提醒「精簡兩段；要完整版改 `--mode full`」

## 限制與契約

- **escape 防護**：slot 中行首 `#` 會被跳脫成 `\#`（避免破壞五段式結構），caller 不需自己 escape
- **constraints overlap dedupe**：抽到的限制詞若互為 substring（例「字以內」vs「個字以內」），自動保長者
- **預設語言**：空輸入 / 短句（< 5 字元）→ `zh`
- **預設角色 fallback 鏈**：手動 `--role` > 依 task_verb 推斷（如 "翻譯"→"譯者"）> 通用助理
- **無 LLM 呼叫**：純 Python 規則式，所有抽取走 `keyword_dict.json`

## 範例輸出

```
主公：/prompt 用 markdown 整理今天戰報，300 字以內

AI：[nl-to-prompt-structurer 已啟動]

## 角色 (Role)
資料整理員

## 背景 (Context)
（未指定）

## 任務 (Task)
用 markdown 整理今天戰報，300 字以內

## 限制 (Constraints)
- 字以內
- markdown

## 輸出格式 (Output Format)
markdown
```
