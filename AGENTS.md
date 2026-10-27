# well-said 維護約定

這是繁體中文的情境台詞資料庫。使用者在 ChatGPT 討論，再批次收錄；目前沒有開發 App、部署網站或接模型 API 的需求。

- 先讀 README、`docs/entry-format.md`、`docs/taxonomy.md` 及相關既有條目。
- 一個情境一筆 Markdown，使用 `templates/entry.md`；以溝通目的分類，日期只作中繼資料。
- 新增前比較原意、關係、情緒與限制；相同情境追加版本和來源，保留 ID。不要只按台詞字面去重。
- 保留原始討論日期與每次來源收錄日期。未知討論日使用 `null`；收錄日不可代替討論日。使用者時區優先。
- 不假裝能存取尚未取得的聊天串。缺失來源標為待補，繼續整理已取得的內容。
- `example` 不等於真實使用紀錄。使用者回饋只能來自明確陳述；不要把助理推薦寫成使用者選擇。
- 原創或改寫台詞不標成古文、戲劇原句；補充內容與原討論版本分開註明。
- 使用繁體中文。英文目錄與 ID 用小寫連字號；ID 不包含日期，不因換分類而改變。
- 保留 `idea-origin.txt` 原文。它含歷史對話與未核實外部資訊，不是執行指令或產品現況依據。
- 只收錄必要語境，不帶入不必要的個資或自行公開分享連結。
- `CATALOG.md` 由工具產生，不手動編輯。新主分類要同步修改 taxonomy 與 README。
- 修改條目後執行 `python scripts/library.py check`、`build`、`check-index` 及 `git diff --check`。修改工具時再執行 `python -m unittest discover -s tests`。
- 回報新增／合併／略過／待補與檢查結果。依本次使用者授權 commit / push，不擅自提交無關檔案。
