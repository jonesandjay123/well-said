# well-said｜言外之意

把日常想說的話，說得精煉、自然，帶一點古韻。

這是個持續累積的**情境台詞資料庫**：平常在 ChatGPT 專案裡用十秒鐘描述前後脈絡，討論幾種說法；累積一批後，再把值得留下的情境與台詞收進這裡。審美方向是古裝劇裡自然的半文半白，重點是貼切與語氣，而不是把每句話翻成艱深文言。

目前提供收錄規格、專案指令、批次整理提示詞、兩筆源自原始構想的示例，以及索引與檢查工具。不需要模型 API，也沒有另建聊天 App。

## 從這裡開始

- [瀏覽台詞索引](CATALOG.md)：依溝通目的、場景、對象與語氣查找。
- [ChatGPT 專案指令](prompts/project-instructions.md)：貼入你已開好的專案指令。
- [批次收錄提示詞](prompts/batch-import.md)：累積一批討論後使用。
- [收錄流程](docs/workflow.md)：如何整理、去重、檢查及提交。
- [欄位規格](docs/entry-format.md)與[條目模板](templates/entry.md)：讓不同批次維持一致。

## 分類方式：溝通目的為主，情境標籤為輔

查找時，通常先想到的是「我要委婉拒絕」或「我要說普通但不掃興」，未必是「這是哪一天」或「我在哪裡說過」。因此主目錄按**想達成的溝通目的**分類，一個情境只存一份；場景、對象及語氣則各自標記，讓同一筆能從多個角度找到。

例如「朋友推薦餐廳，覺得普通但不想掃興」歸入 **評價與讚賞**，場景是「用餐」，對象是「朋友」，語氣包含「溫和、含蓄」。換成評價電影時，可能仍能沿用其中的說法。

| 主目錄 | 用途 |
| --- | --- |
| `acceptance` | 接受與讓步 |
| `refusal` | 拒絕與婉謝 |
| `appraisal` | 評價與讚賞 |
| `gratitude` | 感謝與回禮 |
| `support` | 安慰與鼓勵 |
| `disagreement` | 異議與澄清 |
| `boundaries` | 界線與提醒 |
| `requests` | 請求與協商 |
| `connection` | 關心與親近 |
| `repair` | 致歉與圓場 |

「機智、調侃、冷淡」是語氣，可能出現在任何溝通目的裡，所以不另設成主分類。分類細節及重疊時的判斷方式見[分類指南](docs/taxonomy.md)。分類定義集中於 [taxonomy.json](taxonomy.json)，沒有條目的類別暫不建立空目錄。

## 一筆收錄包含什麼？

一筆是「一個可理解的情境＋多種候選台詞」，不是單獨一句金句，也不是整篇聊天逐字稿。

- 誰對誰說、發生什麼事、原本想說什麼，以及不想造成的誤會。
- 各版本台詞、白話意思、語氣與使用提醒。
- 整理者建議，以及使用者明確選過／不喜歡的版本；兩者分開紀錄。
- 討論日期、收錄日期與可定位的來源。原討論日期不明就填 `null`，不拿收錄日冒充。

起始的兩筆是 `idea-origin.txt` 中已有的椅子與餐廳案例，標為 `example`；它們不是新增的真實使用紀錄，也不代表使用者偏好。原始構想中涉及外部產品或服務的敘述僅保留為歷史材料，本 repo 不將那些敘述視為已驗證的現況。

## 目錄

```text
entries/<溝通目的>/<情境名稱>.md  # 手動／由助理整理的主要內容
CATALOG.md                      # 工具產生的多角度索引
taxonomy.json                   # 主分類定義
prompts/                        # 日常討論與批次收錄提示詞
templates/entry.md               # 新條目模板
docs/                           # 分類、格式與工作流程
scripts/library.py              # 檢查條目、更新索引
tests/                          # 檢查工具的測試
idea-origin.txt                  # 原始構想，保留原文
AGENTS.md                       # 後續協作助理的維護規則
```

## 本機維護

閱讀 Markdown 不需要安裝工具。要新增內容並更新索引，需要 Python 3.9 以上：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/library.py check
python scripts/library.py build
python scripts/library.py check-index
python -m unittest discover -s tests
```

`check` 檢查必填欄位、日期、分類路徑、來源及重複 ID；`build` 在檢查通過後重新產生 `CATALOG.md`；`check-index` 確認索引沒有過期。GitHub Actions 也會執行這些檢查。語氣是否合適、原意是否保留，以及相似條目是否該合併，仍需閱讀內容判斷。

日後批次整理時，先確認助理實際能讀到哪些討論與 repo。若無法存取某篇討論，提供該篇文字或匯出內容；若無法寫入 repo，請它交付依模板整理的 Markdown 檔。具體流程見[收錄流程](docs/workflow.md)。

## 後續方向

先累積真正想用的說法與明確偏好。等資料與使用習慣穩定，再考慮搜尋介面、個人語氣偏好或 App；目前維持容易閱讀、容易搬移、可用 Git 追蹤的文字庫。
