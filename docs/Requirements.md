## 1) 整體做法選擇

### 最穩、最省事的抓取方式：Jira Cloud REST API

* 用 API Token + email 做 Basic Auth 去打 Jira Cloud REST API。
* 拉 issue 有兩種常用方式：

  * 直接抓單一 issue（我們有 key 類似：`JSAI-123`）
  * 用 JQL 搜尋抓一批（例如某個 sprint / status / assignee）
* 大量抓取要注意分頁（例如 `maxResults`）
* 另外 Jira 近期在 search endpoint 上有調整與遷移狀況，所以你架構上最好把「JiraClient」抽象化，避免 API 變動時整個工具裂開。

---

## 2) 專案架構（建議先做 CLI 版，最快落地）

你用 Python 很順的話，我建議全 Python：抓取、整理、輸出 Markdown 會很快。

```
jira-issue-md-agent/
  README.md
  instruction.md                  # 給 Copilot 用（我也可以再補一份）
  pyproject.toml                  # 用 uv/poetry/pdm 都可
  .env.example

  src/
    jira_issue_md_agent/
      __init__.py

      config.py                   # 讀 env / 設定
      models.py                   # Issue 資料結構（pydantic）
      jira_client.py              # Jira API 存取層
      issue_fetcher.py            # 抓單筆 / 批次（JQL）
      normalizer.py               # 把 Jira fields 轉成你需要的統一格式
      renderer.py                 # 套模板輸出 md
      writer.py                   # 寫檔、資料夾命名、去重覆

      templates/
        issue.md.j2               # Jinja2 模板

      cli.py                      # `python -m ...` 或 entrypoint

  outputs/
    .gitkeep                      # 產出 md 放這裡（預設）
```

依賴建議：

* `httpx`（HTTP client）
* `pydantic`（資料模型）
* `jinja2`（模板渲染）
* `python-dotenv`（方便本機）
* （可選）`rich`（CLI 顯示漂亮）

---

## 3) 基本設計文件（MVP 規格）

### 3.1 需求

**輸入**

* Jira base url（例：`https://xxx.atlassian.net`）
* 使用者 email + API token（建議用 `.env`）
* 抓取範圍：

  1. issue key（單筆）
  2. JQL（多筆，例如 assigned to me / sprint / status）

**輸出**

* 每個 issue 產出一個 `.md`
* 檔名與路徑規則固定，方便你直接開始開發
* 內容是「模板化單子」，包含你要的欄位與你開發時的 checklist

---

### 3.2 Jira 抓取策略

#### 單一 issue

* `GET /rest/api/3/issue/{issueIdOrKey}`（常見做法）
* fields 至少抓：summary、description、status、priority、assignee、reporter、labels、components、fixVersions、created、updated、issuetype、parent、subtasks、attachments

#### 多筆（JQL）

* 用 `/rest/api/3/search/jql` 來跑 JQL，GET 或 POST 都行（JQL 很長就 POST）。([confluence.atlassian.com][2])
* 分頁用 `maxResults` 等參數控制。([Atlassian Support][3])

---

### 3.3 資料正規化（Normalizer）

你會碰到 Jira description/自訂欄位格式各種亂，建議先做一層「統一輸出模型」：

`NormalizedIssue`（建議欄位）

* key
* url
* project_key
* type
* summary
* status
* priority
* assignee
* reporter
* labels
* components
* created_at
* updated_at
* description_text（把 Jira doc 格式轉成純文字，先簡化也行）
* acceptance_criteria（先留空或從 description 擷取）
* dev_notes（留空）
* links（issue links、相關 PR 連結可後續再補）

---

### 3.4 Markdown 輸出規則（Writer）

建議路徑：

* `outputs/{project}/{key}-{slug}.md`

  * 例如：`outputs/UEP/UEP-123-fix-login-loop.md`

slug 做法：summary 小寫、空白變 `-`，移除特殊字元。

去重策略：

* 若同 key 已存在：

  * 預設覆蓋（或用 `--no-overwrite`）
  * 或輸出到 `.../UEP-123-...__v2.md`

---

## 4) CLI 設計（你做起來會很順）

指令例：

* 抓單筆：

  * `jira-md fetch --key UEP-123`
* 抓一批：

  * `jira-md fetch --jql "project = UEP AND assignee = currentUser() AND status != Done"`
* 指定輸出路徑：

  * `jira-md fetch --jql "..." --out outputs/`

---

## 5) 你要的 Markdown 模板（可直接用）

這是一個「你拿到 md 就能開做」的格式，偏工程化、好填寫：

```md
# {key} — {summary}

- Jira: {url}
- Project: {project_key}
- Type: {type}
- Status: {status}
- Priority: {priority}
- Assignee: {assignee}
- Reporter: {reporter}
- Labels: {labels}
- Components: {components}
- Created: {created_at}
- Updated: {updated_at}

---

## 背景與需求

{description_text}

---

## 目標

- [ ] （一句話描述要完成什麼）
- [ ] （必要時拆 2~3 點）

---

## 驗收條件 Acceptance Criteria

- [ ] 
- [ ] 
- [ ] 

---

## 影響範圍 Impact

- Frontend:
  - [ ] 
- Backend:
  - [ ] 
- Database / Migration:
  - [ ] 
- Infra / CI:
  - [ ] 

---

## 實作筆記 Dev Notes

- 

---

## 測試計畫 Test Plan

- [ ] 單元測試
- [ ] 整合測試
- [ ] 手動測試步驟：
  1. 
  2. 

---

## 交付物 Deliverables

- [ ] PR
- [ ] Release note（如需要）
- [ ] 相關文件 / 截圖

---

## 參考連結 Links

- 
```

---

## 6) 我建議你先做的 MVP（一天內能看到成果）

1. `.env` 讀 Jira base url / email / token
2. `fetch --key` 抓單筆 issue JSON
3. normalizer 抽出 summary/status/description
4. jinja2 套模板，輸出 md
5. 再加 `fetch --jql` 批次產出

---
