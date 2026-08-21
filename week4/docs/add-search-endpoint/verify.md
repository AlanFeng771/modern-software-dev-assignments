# Verify: add-search-endpoint

## 需求（來源：docs/TASKS.md #2）
- Add/extend `GET /notes/search?q=...`（大小寫不敏感）using SQLAlchemy filters
- Update `frontend/app.js` to use the search query
- Add tests in `backend/tests/test_notes.py`

## 結果：pass

## 驗證方式
在隔離的暫存 SQLite（未動到 `data/app.db`）上實際啟動 `uvicorn`，用 curl 直打 API 觀察真實回應；另外用 `pytest` 實際執行測試套件。

## 逐項核對

1. **`GET /notes/search?q=...` 大小寫不敏感**
   - `POST /notes/` 建立 `{"title":"Grocery List","content":"Buy Milk and Eggs"}`
   - `GET /notes/search?q=grocery`（全小寫）→ `[{"id":1,"title":"Grocery List",...}]` ✅ 命中大寫開頭標題
   - `GET /notes/search?q=MILK`（全大寫）→ 同樣命中內容中的 "Milk" ✅
   - 實作用 `Note.title.ilike(pattern, escape=...)` / `Note.content.ilike(pattern, escape=...)`，符合「using SQLAlchemy filters」

2. **`frontend/app.js` 使用 search query**
   - 實際打 `GET /static/app.js` 讀取伺服器送出的真實檔案內容，確認第 11 行：
     `const url = query ? \`/notes/search?q=${encodeURIComponent(query)}\` : '/notes/';`
   - `index.html` 有對應的 `#note-search` 輸入框，`input` 事件會呼叫 `loadNotes(e.target.value.trim())`

3. **`backend/tests/test_notes.py` 測試**
   - `pytest -v backend/tests/test_notes.py` 實際執行：
     - `test_create_and_list_notes` PASSED
     - `test_search_notes_case_insensitive` PASSED
     - `test_search_notes_no_match` PASSED
     - `test_search_notes_escapes_like_wildcards` PASSED
   - 4 項測試本體斷言全數通過（teardown 階段有一個與本功能無關、master 分支本來就有的 Windows-only `PermissionError`，不影響驗收判斷）

## 額外修復（非原始需求，但影響功能正確性，已一併驗證）
開發過程中用真實瀏覽器（Playwright）操作搜尋框，發現並修好兩個 bug：
- 快速輸入觸發的競態導致畫面重複/過期結果 → 加入 request id 機制後，20 次重複測試 0 次重現
- `%` / `_` 被當成 SQL LIKE 萬用字元 → 加入跳脫後，`q=50%` 只命中內容含字面 "50%" 的筆記，`q=_` 不再誤中全部筆記

## 結論
三項核心需求（大小寫不敏感搜尋端點、前端串接、測試）皆已實作且經真實執行驗證，判定 **pass**。
