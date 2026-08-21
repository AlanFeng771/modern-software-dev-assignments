# Feature: Add search endpoint for notes

## 需求
- `GET /notes/search?q=...`，大小寫不敏感（SQLAlchemy filter）
- `frontend/app.js` 串接搜尋
- `backend/tests/test_notes.py` 新增測試

## Todo
| # | 項目 | 狀態 |
|---|---|---|
| 1 | 規劃 (this file) | done |
| 2 | 設計測試案例 | done |
| 3 | 後端：`search_notes` 改用 `ilike` 明確大小寫不敏感，路徑改為 `/notes/search`（去除尾斜線，對齊需求） | done |
| 4 | 前端：`index.html` 新增搜尋輸入框；`app.js` 串接 `/notes/search?q=...` | done |
| 5 | 測試全數通過 | done |
| 6 | commit | done |

## 備註
- 本機沙盒無 `cs146s` conda 環境，改用臨時 venv（Python 3.13 + fastapi/sqlalchemy/pytest/black/ruff）驗證，用完即刪除，未污染專案。
- 既有 Windows-only 的 `conftest.py` teardown（`os.unlink(db_path)` 因檔案控制代碼未釋放而 `PermissionError`）在 master 分支即存在，與本次修改無關，未處理。

## 測試案例設計
- `test_search_notes_case_insensitive`：標題/內容以不同大小寫查詢皆可命中
- `test_search_notes_no_match`：查無資料回傳空陣列
- `test_search_notes_empty_query`：不帶 `q` 時等同列出全部（沿用既有斷言，路徑改為無尾斜線）

僅測功能邏輯本身（filter 正確性、大小寫不敏感、空結果），不做需求驗收。
