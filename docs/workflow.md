# 從討論到收錄

## 平常討論

把 [project-instructions.md](../prompts/project-instructions.md) 貼進已建立的 ChatGPT 專案指令。隨口說清楚對象、當下發生什麼、想表達什麼，例如：

> 朋友推薦的餐廳我覺得普通，但不想掃他的興。想說得含蓄一點，有什麼版本？

喜歡哪句、覺得哪句太酸，可以直接說。之後收錄時，這些明確回饋才是偏好依據。

## 累積一批後

1. 使用[批次收錄提示詞](../prompts/batch-import.md)，指出這一批涵蓋哪些討論；能提供討論標題、日期、連結或逐字內容就一併提供。
2. 整理者先列出實際取得的來源及無法讀取的來源。連結、專案名稱或「同一個專案」本身不保證當前助理能讀到所有討論。缺內容時提供文字／匯出資料，不宣稱已搜羅完整。
3. 掃描現有 `entries/` 與索引，按原意、關係、情緒及使用限制去重。同情境追加版本與來源；相同短句出現在不同情境可以保留，不單憑字面相同就合併。
4. 依模板建立或更新條目。保留來源日期；未知日期填 `null`。把本次新增建議與原討論內容分開標明。
5. 先移除與語境無關的姓名、聯絡方式與私人細節，改用「朋友、同事」等稱呼。若公開 repo 不適合放某個來源連結，保留足夠定位的文字說明並把 URL 設為 `null`。
6. 執行下方檢查，再查看 diff。完成後回報新增、合併、略過、待補資料各有哪些，以及建議與使用者回饋是否有變更。

```sh
python scripts/library.py check
python scripts/library.py build
python scripts/library.py check-index
python -m unittest discover -s tests
git diff --check
git diff
```

有 repo 寫入能力的助理可以直接新增檔案；沒有寫入能力時，交付每個完整 Markdown 檔及預期相對路徑，後續再由有權限的環境收進 repo。工具不會自動抓取 ChatGPT 專案，也不包含帳號登入或 API 串接。

## 提交

只提交這批相關的變更，確認 `idea-origin.txt` 沒有被改寫。使用者有要求提交／推送時再執行，例如：

```sh
git add entries/ CATALOG.md
git commit -m "docs: collect contextual dialogue entries"
git push
```

每個批次的新增／修改由 Git commit 追蹤，日期則留在條目中。不要為每次匯入建立新的日期目錄。
