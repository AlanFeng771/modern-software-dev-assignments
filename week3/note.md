# Week 3 — MCP 核心概念筆記:Tool / Resource / Prompt

三者的本質差異不是「功能」,而是 **誰決定要不要用它**,官方分類為:

| | 控制方 | 回傳型態 | 舉例 |
|---|---|---|---|
| **Tool**(model-controlled) | 模型自己判斷 | 執行動作後的動態結果 | `get_useful_repositories` —— 模型看使用者問句自己決定要不要呼叫 |
| **Resource**(application-controlled) | Host 應用程式的邏輯(可能自動附加,也可能給 UI 讓使用者選) | 既有的靜態資料本身 | IDE 自動把「目前開啟的檔案」當 resource 附加進對話 |
| **Prompt**(user-controlled) | 使用者主動觸發(像 slash command) | 預先設計好、帶參數的提示詞範本 | `/summarize-issue 42` |

**為什麼 resource 特別歸類成「application-controlled」?**
- 不讓模型自己決定,是為了避免模型未經節制地亂讀資料(權限考量、token 浪費),把「有哪些背景資料可以用」的決定權留在應用程式端。
- 跟 prompt 的差別在於:prompt 一定要使用者**主動觸發**(明確動作,如打 `/xxx`);resource 不一定,應用程式的邏輯也可能**自動**附加(例如 IDE 自動把目前開啟的檔案當 resource),使用者不用每次手動選。

**比喻:**
- Tool 像模型手邊的按鈕,自己判斷要不要按
- Resource 像圖書館書架,使用者(或應用程式)自己去拿一本書放到模型面前
- Prompt 像套餐菜單,使用者選好套餐,server 直接組好完整內容端出來
