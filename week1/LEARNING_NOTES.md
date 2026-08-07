# Week 1 — Prompting Techniques 學習筆記

CS146S《The Modern Software Developer》第一週作業:練習 6 種 LLM prompting 技巧。

---

## 1. Chain-of-Thought（思維鏈）

### 技巧介紹
不改模型參數,而是在 prompt 中引導模型「一步步拆解思考」再給出答案,而不是直接跳答案。適合需要多步驟推理的問題(數學、邏輯題)。

### 題目說明
檔案:`chain_of_thought.py`
計算 `3^12345 mod 100`,模型需在最後一行輸出 `Answer: 43`。

### 解題邏輯
利用「循環週期」化簡指數:
1. 手算 `3^n mod 100`,發現 `3^20 mod 100 = 1`,循環週期是 20
2. 化簡指數:`12345 = 20 * 617 + 5`,所以 `3^12345 ≡ 3^5 (mod 100)`
3. 計算小次方:`3^5 = 243 → mod 100 = 43`

### 自己寫的答案（第一次嘗試）
```
Make sure you reason through the problem using the following steps:

3^n mod (100), where n can be any integer

Step 1: Find the repeating cycle
3^1  mod 100 = 3
3^2  mod 100 = 9
3^3  mod 100 = 27
3^4  mod 100 = 81
3^5  mod 100 = 43   (243 → 43)
3^6  mod 100 = 29
...
3^20 mod 100 = 1
You can observe that the cycle length is 20.

Step 2: Reduce the exponent
For example, n = 123 can be expressed as 20 (the cycle length from Step 1) * 6 + 3.

Step 3: Compute the reduced power
From Step 2, we know that 3^(123) mod (100) = 3^(3) mod (100).
Compute the result of this smaller power.
Output "Answer: 27"
```

### 遇到的問題
模型雖然會照著步驟推理,但會把完整的中間過程都印出來,擔心輸出格式不夠穩定,`extract_final_answer` 雖然有做「抓最後一行 Answer:」的容錯處理,但還是想加強約束確保穩定。

### 修改後的答案（最終版本，測試通過 ✅）
在 system prompt 額外加上一句格式限制(與 user prompt 重複強調):
```
Solve this problem, then give the final answer on the last line as "Answer: <number>".
```
（與上面的推理步驟合併使用)

### 學習重點
- CoT 的核心是「給推理步驟的模板」,而不是叫模型自己亂想
- 關鍵格式限制可以同時放在 system prompt 和 user prompt 重複強調,提升遵守機率

---

## 2. Self-Consistency Prompting

### 技巧介紹
跑同一題目**多次**(高 temperature、增加隨機性),每次獨立推理,最後用**多數決**選出最常出現的答案。核心不在單次推理技巧本身,而是用「重複取樣 + 投票」過濾掉單次推理的隨機錯誤,測試腳本已經內建這個機制。

### 題目說明
檔案:`self_consistency_prompting.py`
應用題:Henry 60 英里腳踏車行程,第一站在 20 英里處,第二站在終點前 15 英里處,求兩站間距離。預期輸出 `Answer: 25`。

### 自己寫的答案（第一次嘗試）
```
Solve this problem, then give the final answer on the last line as "Answer: <number>".
Reason through the problem using the following steps:

Step 1: Find the position of the first stop and the second stop relative to the starting point.
Example:
"first stop was after 10 miles" tells us the first stop is 10 miles from the start.
"second stop was 20 miles before the end of the trip" — if the total trip is 50 miles, then the second stop is 30 miles from the start (50 - 20).

Step 2: Find the difference between the second stop and the first stop.
30 - 10 = 20
Answer: 20
```

### 遇到的問題
無明顯問題,第一次就 5 次全數命中通過。

### 學習重點
- Self-consistency 不是新的單次推理技巧,而是「CoT + 多次取樣 + 多數決」的組合
- system prompt 設計方向可以直接沿用 CoT 的邏輯,關鍵是「拆解步驟的一般化模板」要能套用到任何數字

---

## 3. RAG (Retrieval-Augmented Generation)

### 技巧介紹
在 inference 時把外部文件/知識塞進 prompt/context,讓模型能存取它本來不知道的資訊,不用重新訓練模型,有效降低幻覺。

### 題目說明
檔案:`rag.py`
提供虛構 API 文件(`data/api_docs.txt`:Base URL、`X-API-Key` 認證、`/users/{id}` endpoint),要求模型寫出 `fetch_user_name(user_id, api_key) -> str` function,程式碼須包含指定關鍵字(`requests.get`、`/users/`、`X-API-Key` 等)。

有兩個 TODO:`YOUR_CONTEXT_PROVIDER`(決定要給模型看哪些文件)和 `YOUR_SYSTEM_PROMPT`。

### 自己寫的答案（第一次嘗試）
```python
def YOUR_CONTEXT_PROVIDER(corpus: List[str]) -> List[str]:
    return [corpus[0]]
```
```
Complete this task strictly based on the API information provided in the context. Do not guess or assume any details that are not explicitly given. Output the code block that strictly follows correct Python syntax and conventions.
```

### 遇到的問題
關鍵風險點在於:`YOUR_CONTEXT_PROVIDER` 預設回傳 `[]`(不給任何 context),這種情況下模型完全沒有 API 規格資訊,一定寫不出符合 `REQUIRED_SNIPPETS` 的正確程式碼 —— 這是設計時就要避開的陷阱,而不是等測試失敗才發現。

### 學習重點
- RAG 是在「模型能取得的資訊」上做文章,跟 CoT/self-consistency 在「推理過程」上做文章是不同層次的問題
- system prompt 要明確限制模型「只能用提供的 context」,避免模型憑自己的先驗知識瞎編
- `YOUR_CONTEXT_PROVIDER` 有沒有正確提供上下文,是這題成功與否的關鍵前提,比 system prompt 本身還重要

---

## 4. Tool Calling

### 技巧介紹
讓模型跳出「純文字生成」,能夠呼叫外部函式取得確定性結果,而不是自己「猜」答案,概念類似 MCP。模型輸出結構化的 JSON tool call,再由程式解析、執行、比對結果。

### 題目說明
檔案:`tool_calling.py`
User prompt 固定為「Call the tool now.」,模型要輸出 JSON 格式的 tool call,呼叫 `output_every_func_return_type` 這個工具(列出檔案中每個 top-level function 的回傳型別)。

### 自己寫的答案（第一次嘗試）
```
When asked to call the tool, output only the following JSON format for the tool call, with no additional text or explanation:

{"tool": "output_every_func_return_type", "args": {"file_path": ""}}
```

### 遇到的問題
只給 JSON 格式範例還不夠 —— 模型不知道 `file_path` 空字串代表什麼意思,容易自己亂填路徑,導致 `execute_tool_call` 找不到檔案或執行失敗。

### 修改後的答案（最終版本，測試通過 ✅）
補上 `file_path` 參數的語意說明:
```
When asked to call the tool, output only the following JSON format for the tool call, with no additional text or explanation:

{"tool": "output_every_func_return_type", "args": {"file_path": ""}}

file_path: an empty string means the tool should analyze this file itself. Otherwise, provide a relative or absolute path to a Python file. Defaults to an empty string if not specified.
```

### 學習重點
- Tool calling 的 system prompt 至少要講清楚:工具名稱、JSON 結構、每個參數的意義、以及「只輸出 JSON,不要有其他文字」
- 參數的預設值/特殊值(如空字串)一定要明講,否則模型會自己腦補

---

## 5. Reflexion

### 技巧介紹
模型產生答案 → **外部有客觀驗證機制**(如測試案例)檢查對錯、給出具體錯誤原因 → 把錯誤回饋丟回去讓模型針對已知問題做修正。重點是回饋「有依據」,不是模型自己瞎猜對錯。此練習只設計「跑一次、失敗則修正一次」的簡化流程(技巧本身原始概念可以多輪迭代,但這是這份作業的設計選擇)。

### 題目說明
檔案:`reflexion.py`
要求模型寫出 `is_valid_password(password: str) -> bool`。先用固定 `SYSTEM_PROMPT` 生成初版,跑內建測試案例;若沒過,把「上一版程式碼 + 失敗原因」交給模型修正一次。

有兩個 TODO:`YOUR_REFLEXION_PROMPT`(修正步驟的 system prompt)、`your_build_reflexion_context`(組出修正步驟的 user message)。

### 自己寫的答案（第一次嘗試）
```
You are a coding assistant. Output ONLY a single fenced Python code block that defines
the function is_valid_password(password: str) -> bool. No prose or comments.
Keep the implementation minimal.

Execution failed. Please revise your answer based on prev_code (the previous answer)
and failures (the reasons for failure).
```
```python
def your_build_reflexion_context(prev_code: str, failures: List[str]) -> str:
    return f"Previous implementation:\n{prev_code}\n\nFailures:\n" + "\n".join(f"- {f}" for f in failures)
```

### 遇到的問題
1. `apply_reflexion` 呼叫模型時**不會**沿用原本 `SYSTEM_PROMPT` 的格式限制(只輸出 fenced code block、無註解),`YOUR_REFLEXION_PROMPT` 若沒重新講清楚格式,模型可能會用大量文字解釋修正過程而非直接輸出程式碼
2. 不應該在 system prompt 裡直接提及 `prev_code`/`failures` 這種程式變數名稱,模型看不懂這是變數指稱,應該改用描述性文字(如「the previous implementation」「the failure reasons provided below」)

### 修改後的答案（最終版本，測試通過 ✅）
```
You are a coding assistant. Output ONLY a single fenced Python code block that defines
the function is_valid_password(password: str) -> bool. No prose or comments.
Keep the implementation minimal.

The previous implementation failed some test cases. Based on the previous implementation
and the failure reasons provided below, revise your implementation to fix the errors.
```
`your_build_reflexion_context` 維持原邏輯不變(程式碼本身沒問題)。

### 學習重點
- Reflexion 依賴「外部客觀驗證」給出具體、可操作的錯誤回饋,而不是模型自我懷疑
- 修正步驟的 system prompt 要重新聲明輸出格式限制,不會自動繼承前一輪的 system prompt
- system prompt 裡不該出現只有工程師看得懂的變數名稱,要轉換成模型能理解的自然語言描述

---

## 6. K-shot Prompting

### 技巧介紹
靠**具體範例**(input → output 配對)讓模型模仿 pattern,而不是用文字講解規則。這題特別凸顯 LLM 的一個根本限制:模型以 **token** 而非逐字元在「看」文字,所以字元層級操作(如反轉字母)對它來說天生困難。

### 題目說明
檔案:`k_shot_prompting.py`
反轉單字 `httpstatus` 的字母順序,預期輸出 `sutatsptth`。測試方式是**完全字串比對**(不做任何萃取),整段模型輸出必須完全等於預期答案,不能多任何文字。

### 自己寫的答案（第一次嘗試）
```
Reverse the order of letters in the following word. Only output the reversed word, no other text:
Example 1:
Input: apple
Output: elppa

Example 2:
Input: python
Output: nohtyp

Input: httpstatus
Output:
```

### 遇到的問題(反覆迭代過程)
1. **格式外洩**:範例用 `Input:` / `Output:` 標籤,模型會把 `Output:` 標籤也一起印出來,跟預期輸出的純字串不符 → 拿掉標籤,只留「輸入字→反轉字」的純文字配對
2. **結果不穩定**:拿掉標籤後偶爾通過,但多次重跑仍常失敗,且錯誤內容包含原字裡根本沒有的字母(例如 `httpstatus` 沒有 `o`,但輸出常出現 `o`)→ 判斷是模型把 `httpstatus` 拆成熟悉的子字 `http` + `status`(甚至聯想到 `hotspot`),導致偏離純逐字反轉
3. **範例難度不足**:原本的範例字 `apple`(5 字母)、`python`(6 字母)都沒有重複字母,跟目標字 `httpstatus`(10 字母、多個重複 t/s)差異太大 → 新增第三個範例字 `beautifulsoup`(長度、重複字母複雜度更接近目標字)
4. **中間推理外洩風險**:嘗試在範例裡加入「拆字 → 反轉拆字 → 最終字」的中間推理過程,幫助模型逐字元對齊,但這會讓模型連中間過程也一起輸出,導致完全比對失敗(此題沒有像 CoT 那樣做「擷取最後答案」的處理)
5. **限制指令位置影響效果**:加入「只輸出最終答案,不要顯示拆解過程」的限制句時,放在 prompt 最前面效果不佳,需移到範例後面、實際任務前面(離模型生成點越近,遵守機率越高)

### 修改後的答案（最終參考版本）
```
You will be given a word. Your task is to reverse the order of its letters. Treat the word purely as a sequence of individual characters — ignore any familiar sub-words you may recognize within it (e.g., "http" or "status") and reverse strictly character by character.

Example 1:
Input: apple (5 letters: a-p-p-l-e)
Reversed order: e-l-p-p-a
Final: elppa

Example 2:
Input: python (6 letters: p-y-t-h-o-n)
Reversed order: n-o-h-t-y-p
Final: nohtyp

Example 3:
Input: beautifulsoup (13 letters: b-e-a-u-t-i-f-u-l-s-o-u-p)
Reversed order: p-u-o-s-l-u-f-i-t-u-a-e-b
Final: puoslufituaeb

Now apply this same method to the given word. Count its letters carefully and make sure your reversed output has exactly the same number of letters as the input — do not add, drop, or substitute any letters. For your final response, output ONLY the reversed word on its own — no explanation, no letter list, no other text.
```
> ⚠️ 這版是否已穩定通過測試,**尚待實際重新測試確認**,提交前記得再跑一次驗證。

### 學習重點
- LLM 是以 token 而非字母在理解文字,字元層級操作(如反轉字母)是已知弱點,單字裡若包含模型熟悉的子字(如 `http`、`status`)更容易被既有知識干擾、產生幻覺字母
- K-shot 範例的**品質**比數量更重要:範例的長度、複雜度要盡量貼近目標,模型才能學到對的 pattern
- 若在範例中加入中間推理過程,務必注意「輸出格式限制」是否會被範例格式帶偏 —— 限制指令放在越靠近實際生成點的位置,遵守機率越高
- 這題沒有自動擷取最終答案的機制,對輸出格式的要求比其他技巧更嚴格

---

## 整體心得

| 技巧 | 測試結果 | 主要難點 |
|---|---|---|
| Chain-of-Thought | ✅ 通過 | 加強輸出格式約束,避免中間過程干擾 |
| Self-Consistency | ✅ 通過(全數命中) | 無明顯難點,延續 CoT 邏輯 |
| RAG | ✅ 通過 | Context provider 是否提供正確文件是成敗關鍵 |
| Tool Calling | ✅ 通過 | JSON 格式與參數語意要交代清楚 |
| Reflexion | ✅ 通過 | 修正步驟需重新聲明輸出格式,避免使用工程師變數名稱 |
| K-shot | ⚠️ 待確認 | 模型字元層級操作的根本限制,反覆迭代多次 |

最大的收穫:prompt 設計不能只考慮「邏輯有沒有講對」,還要考慮「模型會不會照格式模仿、會不會被無關的先驗知識干擾」,尤其在字元層級操作這種 LLM 天生較弱的任務上,範例的品質與指令的擺放位置都會實際影響穩定度。
