# Week 2 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## INSTRUCTIONS

Fill out all of the `TODO`s in this file.

## SUBMISSION DETAILS

Name: **TODO** \
SUNet ID: **TODO** \
Citations: **TODO**

This assignment took me about **TODO** hours to do. 


## YOUR RESPONSES
For each exercise, please include what prompts you used to generate the answer, in addition to the location of the generated response. Make sure to clearly add comments in your code documenting which parts are generated.

### Exercise 1: Scaffold a New Feature
Prompt: 
```
分析現有的 extract_action_items()，實作一個 LLM 版本 extract_action_items_llm()，
用 Ollama 做 action item 抽取，輸出用 structured output（JSON array of strings）。

追問與決策過程：
1. 用哪個 model？→ 本機已有 llama3.1:8b、mistral-nemo:12b，選 llama3.1:8b（較小、較快）
2. Schema 用 pydantic 定義更好，並用 Field(description=...) 把欄位語意整合進 schema
3. System prompt 是否還需要？→ 需要，因為 Ollama 的 format schema 只保證 JSON 結構，
   不保證回傳內容語意正確；system prompt 負責告訴模型「任務是什麼」，
   Field description 負責文件化「這個欄位代表什麼」，兩者分工不同、缺一不可
4. 解析失敗（ValidationError）時如何處理？→ 回傳空 list，維持與原本
   extract_action_items() 一致的行為（不拋例外）
``` 

Generated Code Snippets:
```
week2/app/services/extract.py
- Line 8: 新增 pydantic import (BaseModel, Field, ValidationError)
- Line 68: DEFAULT_OLLAMA_MODEL
- Line 70-73: LLM_SYSTEM_PROMPT
- Line 76-85: ActionItemsResponse (pydantic schema)
- Line 88-121: extract_action_items_llm()
```

### Exercise 2: Add Unit Tests
Prompt: 
```
為 extract_action_items_llm() 寫 unit tests，涵蓋 bullet lists、keyword-prefixed
lines、empty input 等多種輸入情境。

決策過程：
- 是否 mock 掉 ollama.chat()？→ 選擇不 mock，測試直接呼叫本機 Ollama
  （llama3.1:8b），屬於整合測試，會實際驗證 prompt + schema 的效果，
  代價是測試較慢（3 次真實呼叫約 25 秒）且需要本機 Ollama 服務運行中
- 因為 LLM 輸出用字可能與預期不完全一致，斷言改用 substring 比對
  （小寫化後檢查關鍵字是否出現），而非要求完全相等，降低脆弱度
``` 

Generated Code Snippets:
```
week2/tests/test_extract.py
- Line 4-5: import extract_action_items_llm, LLMServiceError
- Line 22-24: 說明測試策略的註解
- Line 27-40: test_extract_llm_bullet_list()
- Line 43-54: test_extract_llm_keyword_prefixed_lines()
- Line 57-59: test_extract_llm_empty_input()
- Line 65-80: test_extract_llm_connection_error_raises_llm_service_error() /
  test_extract_llm_response_error_raises_llm_service_error()
  （這兩個是 TODO3 補強錯誤處理時追加的，見 Exercise 3）
```

### Exercise 3: Refactor Existing Code for Clarity
Prompt: 
```
重構後端程式碼，聚焦四個面向：API contracts/schemas、資料庫層清理、
app lifecycle/configuration、錯誤處理。（與 LLM 功能無關，純粹是既有
notes/action-items 後端的程式碼品質重構）

討論與決策過程：
1. 資料庫層是否改用 SQLAlchemy？→ 不改，保持原生 sqlite3，只做清理
   （開啟 foreign_keys pragma、修正連線洩漏、包裝例外），避免不必要的大改動
2. Lifecycle/config 是否引入 pydantic-settings？→ 不加新 dependency，
   改用簡單的 config.py 模組集中管理 DB_PATH / OLLAMA_MODEL，
   並把 init_db() 從 import-time 副作用改成 FastAPI lifespan
3. HTTPException 的運作原理釐清：FastAPI 專門認得 HTTPException 這個
   類別，建立 app 時就自動註冊處理器攔截並轉成 JSON 錯誤回應；但自訂的
   DatabaseError 不在這個名單裡，需要額外轉換
4. DatabaseError 要怎麼轉成 HTTPException？→ 選擇在 main.py 用
   @app.exception_handler(DatabaseError) 註冊全域 handler，
   而非在每個 router 重複寫 try/except，符合「集中管理錯誤處理」的目標

追加討論（把錯誤處理補完整）：
5. extract_action_items_llm() 目前只處理「LLM 回應解析失敗」，沒處理
   「Ollama 服務打不到」這種情況（chat() 呼叫本身失敗）→ 查看 ollama
   套件原始碼（_client.py）確認會丟出 ConnectionError（連線失敗）或
   ResponseError（服務端錯誤，如 model 不存在）
6. 服務打不到時要回傳空 list 還是拋例外？→ 拋例外（新增 LLMServiceError），
   因為「服務掛了」和「模型沒找到 action item」語意不同，回空 list 會誤導
   使用者以為真的沒有 action item；main.py 對應註冊 503 的 exception handler
7. 為這個新行為加測試？→ 用 monkeypatch 假造 ollama.chat 拋出
   ConnectionError/ResponseError（真實觸發需要真的關掉本機 Ollama，
   不實際可行），其餘測試維持真實呼叫不變
``` 

Generated/Modified Code Snippets:
```
week2/app/config.py (新增)
- 集中管理 DATA_DIR / DB_PATH / OLLAMA_MODEL，load_dotenv() 統一在此呼叫

week2/app/schemas.py (新增)
- NoteCreate / NoteOut / ActionItemOut / ExtractedItem / ExtractRequest /
  ExtractResponse / MarkDoneRequest / MarkDoneResponse，取代原本的
  Dict[str, Any] request/response

week2/app/db.py
- Line 10-11: 新增 DatabaseError exception
- Line 18-29: get_connection() 改成 @contextmanager，開啟
  PRAGMA foreign_keys = ON，修正原本連線用完不會 close() 的洩漏問題，
  並把 sqlite3.Error 包裝成 DatabaseError
- DB_PATH 改從 config.py 匯入，移除 db.py 內重複的路徑設定

week2/app/main.py
- Line 16-19: 新增 lifespan context manager，init_db() 改在 app 啟動時
  才執行，而不是 import 當下
- Line 25-27: 新增 @app.exception_handler(DatabaseError) 全域錯誤處理器
- 移除未使用的 import（HTTPException、Any、Dict、Optional）

week2/app/routers/notes.py
- 全面改用 schemas.NoteCreate / NoteOut 取代手動 dict 存取與組裝

week2/app/routers/action_items.py
- 全面改用 schemas.ExtractRequest / ExtractResponse / ActionItemOut /
  MarkDoneRequest / MarkDoneResponse 取代手動 dict 存取與組裝

week2/app/services/extract.py
- Line 8: DEFAULT_OLLAMA_MODEL 改從 config.OLLAMA_MODEL 讀取，
  移除重複的 os.getenv 呼叫
- 新增 LLMServiceError exception，包裝 ConnectionError / ResponseError
- chat() 呼叫改用 try/except 包住，失敗時 raise LLMServiceError from exc

week2/app/main.py（追加）
- 新增 @app.exception_handler(LLMServiceError) 全域錯誤處理器，回傳 503

week2/tests/test_extract.py（追加）
- test_extract_llm_connection_error_raises_llm_service_error()
- test_extract_llm_response_error_raises_llm_service_error()
  （用 monkeypatch 假造 ollama.chat 失敗，驗證 LLMServiceError 行為）
```


### Exercise 4: Use Agentic Mode to Automate a Small Task
Prompt: 
```
1. 把 extract_action_items_llm() 接成新的 endpoint，前端加一個 "Extract LLM"
   按鈕，點擊後透過新 endpoint 觸發抽取
2. 新增一個取得所有 notes 的 endpoint，前端加一個 "List Notes" 按鈕，
   點擊後 fetch 並顯示

決策過程：
- 新 endpoint 命名為 POST /action-items/extract-llm，直接複用既有的
  ExtractRequest / ExtractResponse schema，邏輯與 /extract 幾乎相同，
  只是內部呼叫 extract_action_items_llm() 而非 extract_action_items()
- LLMServiceError（TODO3 定義）不用在這個 endpoint 額外處理，因為
  main.py 已經有全域 exception handler 會自動轉成 503
- GET /notes 直接用既有的 db.list_notes()，回傳 List[NoteOut]
- 前端把 extract 呼叫邏輯抽成共用函式 runExtract(endpoint)，
  Extract 和 Extract LLM 兩顆按鈕共用同一段渲染/勾選邏輯，只是打不同 endpoint
- 順手修正一個資安問題：前端原本用 innerHTML 直接把使用者輸入的
  note content / action item text 插入 DOM，沒有轉義，屬於 XSS 風險；
  加了 escapeHtml() 統一處理
``` 

Generated Code Snippets:
```
week2/app/routers/action_items.py
- Line 16: import extract_action_items_llm
- Line 41-56: 新增 extract_llm() endpoint (POST /action-items/extract-llm)

week2/app/routers/notes.py
- Line 3: import List
- Line 24-28: 新增 list_all_notes() endpoint (GET /notes)

week2/frontend/index.html
- 新增 "Extract LLM" / "List Notes" 按鈕與對應的 notes 顯示區塊
- runExtract(endpoint) 共用函式，取代原本寫死在 extract 按鈕上的邏輯
- escapeHtml() 輔助函式，修正 XSS 風險
```


### Exercise 5: Generate a README from the Codebase
Prompt: 
```
分析目前 week2 的 codebase（app/main.py、config.py、schemas.py、db.py、
routers/、services/extract.py、frontend/index.html、tests/），產生一份
week2/README.md，至少包含：專案概述、如何 setup/run、API endpoints 與
功能說明、如何跑測試。

備註：這個作業原本是設計給 Cursor 用的 exercise（練習「AI 讀 codebase
自動生成文件」的能力），這裡改用 Claude Code 完成同樣的目標，而不是
在 Cursor 裡操作。
``` 

Generated Code Snippets:
```
week2/README.md (新增)
- 專案概述（heuristic vs LLM 兩種抽取方式）
- Setup 步驟（含 Ollama pull model）
- API endpoints 表格（notes / action-items，含 extract-llm）
- 錯誤碼說明（400/422/500/503，對應 DatabaseError / LLMServiceError）
- Configuration（app/config.py 的環境變數）
- 跑測試的指令與注意事項（LLM 測試需要本機 Ollama 服務）
```


## SUBMISSION INSTRUCTIONS
1. Hit a `Command (⌘) + F` (or `Ctrl + F`) to find any remaining `TODO`s in this file. If no results are found, congratulations – you've completed all required fields. 
2. Make sure you have all changes pushed to your remote repository for grading.
3. Submit via Gradescope. 