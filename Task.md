# 自動化網站分析系統 - 任務規劃書

## 專案概述
開發一個自動化系統，能夠解析網站 sitemap、使用 browser-use 進行自動化瀏覽器操作來檢測網頁，並透過 GPT 分析畫面截圖產生分析報告。
不要做測試，專注於實現核心功能模組。
要建立 Docker 相關檔案，不要執行建立容器，由開發者手動處理。
## 快速啟動 (本地開發)
```bash
# 1. 複製專案並進入目錄
git clone <repository_url>
cd website_analyzer

# 2. 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 配置環境變數
cp .env.example .env
# 編輯 .env 檔案設定 API keys

# 5. 運行分析
python src/main.py --url https://example.com
```

**注意：Docker 相關檔案會建立，但容器建構和執行將由開發者手動處理**

## 系統架構

### 1. 核心模組架構
```
┌─────────────────────────────────────────────────────────────┐
│                    自動化網站分析系統                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Sitemap 解析  │   Browser 自動化 │      AI 分析引擎        │
│     模組        │      模組        │        模組             │
└─────────────────┴─────────────────┴─────────────────────────┘
│                                                             │
└─────────────────── 報告生成模組 ──────────────────────────┘
```

### 2. 技術堆疊
- **Python 3.12** - 主要開發語言 (更新至最新穩定版本)
- **browser-use** - 瀏覽器自動化操作 (基於 Playwright)
- **Azure OpenAI / OpenAI GPT API** - 圖像分析和內容理解 (預設 Azure OpenAI)
- **Requests/aiohttp** - HTTP 請求處理
- **BeautifulSoup/lxml** - XML/HTML 解析
- **Pillow** - 圖像處理
- **Jinja2** - 報告模板引擎
- **Docker** - 容器化部署
- **Docker Compose** - 多容器應用編排

## 功能模組詳細說明

### 模組 1: Sitemap 解析器 (`sitemap_parser.py`)
**功能描述：**
- 從目標網站獲取 sitemap.xml
- 解析 sitemap 結構，提取所有 URL
- 支援嵌套 sitemap 和 sitemap index
- 過濾和分類不同類型的頁面

**核心功能：**
- [ ] 解析 XML 格式的 sitemap
- [ ] URL 去重和分類
- [ ] 優先級排序

**輸入：** 網站根域名
**輸出：** 結構化的 URL 列表和元數據

### 模組 2: Browser-Use 自動化檢測器 (`browser_automation.py`)
**功能描述：**
- 使用 browser-use (基於 Playwright) 進行瀏覽器自動化操作
- 執行頁面截圖和基本互動測試
- 收集頁面性能和可用性數據
- 處理動態內容和 JavaScript 渲染

**核心功能：**
- [ ] 自動化瀏覽器啟動和配置
- [ ] 頁面加載和等待策略
- [ ] 全頁面截圖生成
- [ ] 基本互動測試（點擊、滾動、表單）
- [ ] 響應式設計檢測（多尺寸截圖）
- [ ] 頁面加載時間監控
- [ ] 錯誤和異常處理

**輸入：** URL 列表
**輸出：** 截圖文件、性能數據、互動測試結果

### 模組 3: GPT 圖像分析引擎 (`gpt_analyzer.py`)
**功能描述：**
- 使用 GPT-4 Vision API 分析網頁截圖（預設使用 Azure OpenAI，可選標準 OpenAI API）
- 識別頁面結構、設計元素和內容品質
- 評估用戶體驗和可訪問性
- 生成改進建議

**分析維度：**
- [ ] **視覺設計分析**
  - 色彩搭配和品牌一致性
  - 排版和視覺層次
  - 圖片品質和優化
- [ ] **用戶體驗評估**
  - 導航結構清晰度
  - 內容可讀性
  - 行動號召按鈕效果
- [ ] **技術品質檢查**
  - 響應式設計實現
  - 頁面加載速度影響
  - 可訪問性問題識別
- [ ] **內容品質分析**
  - 文字內容相關性
  - SEO 優化程度
  - 多媒體使用效果

**輸入：** 截圖文件和頁面元數據
**輸出：** 結構化分析結果和評分

### 模組 4: 報告生成器 (`report_generator.py`)
**功能描述：**
- 整合所有分析結果
- 生成可視化報告
- 提供優化建議和優先級排序
- 支援多種輸出格式

**報告內容：**
- [ ] **執行摘要**
  - 整體評分和關鍵指標
  - 主要發現和建議摘要
- [ ] **詳細分析報告**
  - 各頁面詳細評估
  - 問題分類和優先級
  - 改進建議具體方案
- [ ] **視覺化展示**
  - 截圖對比和標註
  - 數據圖表和趨勢分析
- [ ] **行動計劃**
  - 短期和長期改進建議
  - 技術實施指導

**輸出格式：** HTML、PDF、JSON

## 工作流程

### 階段 1: 資料收集
1. 輸入目標網站 URL
2. 自動解析 sitemap，獲取頁面列表
3. 使用 browser-use 批量訪問頁面
4. 生成標準化截圖和收集元數據

### 階段 2: AI 分析
1. 將截圖傳送到 GPT-4 Vision API
2. 執行多維度分析評估
3. 生成結構化分析數據
4. 計算綜合評分和排名

### 階段 3: 報告生成
1. 整合所有分析結果
2. 應用報告模板
3. 生成可視化圖表
4. 輸出最終報告文件

## 配置和設定

### 環境變數
```bash
# Azure OpenAI 配置 (默認)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
# 或使用標準 OpenAI API
OPENAI_API_KEY=your_openai_api_key

# 系統配置
BROWSER_HEADLESS=true
MAX_PAGES_PER_BATCH=10
SCREENSHOT_QUALITY=high
REPORT_OUTPUT_DIR=./reports
```

### 配置文件 (`config.yaml`)
```yaml
# API 服務配置 (默認使用 Azure OpenAI)
api_service: "azure_openai"  # 或 "openai"

# Azure OpenAI 配置 (默認)
azure_openai:
  deployment_name: gpt-4-vision
  model: gpt-4-vision-preview
  max_tokens: 2000
  temperature: 0.1
  api_version: "2024-02-15-preview"

# OpenAI 標準 API 配置 (備選)
openai:
  model: gpt-4-vision-preview
  max_tokens: 2000
  temperature: 0.1

# 瀏覽器配置
browser:
  headless: true
  window_size: [1920, 1080]
  timeout: 30
  
# 分析配置
analysis:
  max_pages: 50
  screenshot_formats: [desktop, tablet, mobile]
  
# 輸出配置
output:
  formats: [html, pdf]
  include_screenshots: true
```

### Docker 使用說明 (可選配置)

**注意：以下 Docker 配置為手動執行項目，不包含在主要開發流程中**

#### 基本運行
```bash
# 手動建構和運行 (需先建立 Dockerfile)
docker build -t website-analyzer .
docker run -it --rm \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/reports:/app/reports \
  -e AZURE_OPENAI_API_KEY=your_key \
  website-analyzer
```

#### 開發模式
```bash
# 進入容器進行調試 (需先建立 docker-compose.yml)
docker-compose exec app bash
```

#### 環境變數配置
建立 `.env` 檔案：
```bash
# Azure OpenAI 配置
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# 或使用標準 OpenAI API
OPENAI_API_KEY=your_openai_api_key

# 系統配置
BROWSER_HEADLESS=true
MAX_PAGES_PER_BATCH=10
SCREENSHOT_QUALITY=high
REPORT_OUTPUT_DIR=./reports

# 資料庫配置 (可選)
DB_PASSWORD=secure_password
```

## 專案結構
```text
website_analyzer/
├── src/
│   ├── sitemap_parser.py      # Sitemap 解析模組
│   ├── browser_automation.py  # Browser-use 自動化模組  
│   ├── gpt_analyzer.py       # GPT 分析引擎
│   ├── report_generator.py   # 報告生成器
│   ├── config_manager.py     # 配置管理（支援 OpenAI/Azure OpenAI）
│   └── main.py              # 主程式入口
├── templates/
│   ├── report_template.html  # HTML 報告模板
│   └── email_template.html   # 郵件通知模板
├── config/
│   └── config.yaml          # 系統配置文件
├── .env.example             # 環境變數範例檔案
├── requirements.txt         # Python 依賴
├── README.md               # 專案說明
└── Task.md                 # 本任務規劃書

# Docker 相關檔案 (需要建立，但不執行)
├── docker/                  # Docker 配置目錄
│   └── Dockerfile          # Docker 容器配置文件
├── .dockerignore           # Docker 忽略檔案
└── docker-compose.yml      # Docker Compose 配置
```

## 開發里程碑

### 第一階段 (Week 1-2)
- [ ] 設置專案環境和依賴
- [ ] 實現 Sitemap 解析器
- [ ] 完成基本的 browser-use 整合

### 第二階段 (Week 3-4)  
- [ ] 實現 GPT 圖像分析功能
- [ ] 開發報告生成器基礎功能
- [ ] 完成端到端功能整合

### 第三階段 (Week 5-6)
- [ ] 優化性能和錯誤處理
- [ ] 完善報告模板和樣式
- [ ] 新增進階分析功能

## 預期挑戰和解決方案

### 挑戰 1: 大量頁面處理效能
**解決方案：** 
- 實施批次處理和並行執行
- 使用佇列系統管理任務
- 實施智能重試機制

### 挑戰 2: GPT API 成本控制
**解決方案：**
- 圖片壓縮和尺寸優化
- 批次 API 調用
- 結果快取機制

### 挑戰 3: 動態網頁內容檢測
**解決方案：**
- 使用 browser-use 的智能等待
- 實施多重截圖策略
- JavaScript 執行狀態檢測

## 成功指標
- 能夠成功分析 95% 以上的標準網頁
- 單頁面分析時間控制在 30 秒內
- GPT 分析準確性達到 85% 以上
- 報告生成時間不超過總分析時間的 10%

## 詳細實施步驟

### 步驟 1: 專案初始化和環境設置
- [ ] 1.1 建立專案目錄結構
  ```bash
  mkdir -p website_analyzer/{src,templates,config,reports,docker}
  ```
- [ ] 1.2 建立 requirements.txt 檔案
- [ ] 1.3 建立 .env 環境變數檔案
- [ ] 1.4 建立 config.yaml 配置檔案
- [ ] 1.5 設置虛擬環境並安裝依賴
- [ ] 1.6 建立 .gitignore 檔案

### 步驟 2: 配置管理模組開發 (`config_manager.py`)
- [ ] 2.1 實現環境變數讀取功能
- [ ] 2.2 實現 YAML 配置檔案解析
- [ ] 2.3 建立 Azure OpenAI 和 OpenAI 配置切換邏輯
- [ ] 2.4 實現配置驗證和預設值設定
- [ ] 2.5 建立配置單例模式管理器

### 步驟 3: Sitemap 解析模組開發 (`sitemap_parser.py`)
- [ ] 3.1 實現基本 HTTP 請求功能 (使用 requests)
- [ ] 3.2 建立 XML sitemap 解析器 (使用 BeautifulSoup/lxml)
- [ ] 3.3 實現嵌套 sitemap 和 sitemap index 處理
- [ ] 3.4 建立 URL 過濾和分類功能
- [ ] 3.5 實現 URL 去重和優先級排序
- [ ] 3.6 建立 robots.txt 檢查功能
- [ ] 3.7 實現錯誤處理和重試機制

### 步驟 4: Browser 自動化模組開發 (`browser_automation.py`)
- [ ] 4.1 安裝和配置 browser-use 套件
- [ ] 4.2 實現瀏覽器啟動和配置管理
- [ ] 4.3 建立頁面導航和等待策略
- [ ] 4.4 實現全頁面截圖功能
- [ ] 4.5 建立多尺寸響應式截圖 (desktop, tablet, mobile)
- [ ] 4.6 實現頁面性能監控 (加載時間、資源大小)
- [ ] 4.7 建立基本互動測試功能 (點擊、滾動、表單填寫)
- [ ] 4.8 實現動態內容檢測和 JavaScript 渲染等待
- [ ] 4.9 建立錯誤處理和異常恢復機制

### 步驟 5: GPT 分析引擎開發 (`gpt_analyzer.py`)
- [ ] 5.1 建立 Azure OpenAI/OpenAI API 客戶端
- [ ] 5.2 實現圖片壓縮和格式優化
- [ ] 5.3 建立 GPT-4 Vision API 調用功能
- [ ] 5.4 設計分析提示詞模板 (視覺設計、UX、技術品質、內容品質)
- [ ] 5.5 實現批次圖片分析功能
- [ ] 5.6 建立分析結果結構化處理
- [ ] 5.7 實現評分和排名計算邏輯
- [ ] 5.8 建立結果快取機制
- [ ] 5.9 實現 API 成本控制和限流

### 步驟 6: 報告生成模組開發 (`report_generator.py`)
- [ ] 6.1 設計 HTML 報告模板 (使用 Jinja2)
- [ ] 6.2 建立 PDF 生成功能 (使用 weasyprint 或 pdfkit)
- [ ] 6.3 實現數據可視化圖表 (使用 matplotlib 或 plotly)
- [ ] 6.4 建立截圖對比和標註功能
- [ ] 6.5 實現執行摘要生成
- [ ] 6.6 建立詳細分析報告結構
- [ ] 6.7 實現改進建議和行動計劃生成
- [ ] 6.8 建立多格式輸出支援 (HTML, PDF, JSON)

### 步驟 7: 主程式整合 (`main.py`)
- [ ] 7.1 建立命令列介面 (使用 argparse 或 click)
- [ ] 7.2 實現工作流程協調器
- [ ] 7.3 建立批次處理和並行執行邏輯
- [ ] 7.4 實現進度追蹤和日誌記錄
- [ ] 7.5 建立錯誤處理和恢復機制
- [ ] 7.6 實現結果輸出和通知功能

### 步驟 8: 模板和配置檔案建立
- [ ] 8.1 設計 HTML 報告模板 (`report_template.html`)
- [ ] 8.2 建立郵件通知模板 (`email_template.html`)
- [ ] 8.3 完善系統配置檔案 (`config.yaml`)
- [ ] 8.4 建立範例環境變數檔案 (`.env.example`)

### 步驟 9: 性能優化和錯誤處理
- [ ] 9.1 實現異步處理 (asyncio)
- [ ] 9.2 建立任務佇列系統 (可選用 Redis)
- [ ] 9.3 實現智能重試和容錯機制
- [ ] 9.4 優化記憶體使用和垃圾回收
- [ ] 9.5 建立監控和日誌系統
- [ ] 9.6 實現限流和速率控制

### 步驟 10: Docker 容器化配置檔案建立 (手動執行)
**注意：此步驟需要建立 Docker 相關檔案，但不執行容器建構，容器建立由開發者手動處理**

需要建立的 Docker 相關檔案：
- [ ] 10.1 建立 Dockerfile 配置檔案
- [ ] 10.2 建立 docker-compose.yml 設定檔案
- [ ] 10.3 建立 .dockerignore 檔案
- [ ] 10.4 準備部署腳本範例
- [ ] 10.5 編寫 Docker 使用說明文檔

**不包含在此步驟：**
- 容器建構和測試 (由開發者手動執行)
- 容器部署 (由開發者手動執行)

### 步驟 11: 文檔和部署準備
- [ ] 11.1 撰寫 README.md 使用說明
  - 基本安裝和使用說明
  - 環境配置指導
- [ ] 11.2 建立範例使用腳本
- [ ] 11.3 準備部署文檔
  - 環境配置說明
  - 故障排除指南
- [ ] 11.4 建立 CI/CD 配置 (可選)
  - GitHub Actions 或 GitLab CI
  - 自動化部署流程

## 優先執行順序建議

### 第一週重點 (核心基礎)
1. 步驟 1: 專案初始化
2. 步驟 2: 配置管理模組
3. 步驟 3: Sitemap 解析模組

### 第二週重點 (自動化基礎)
1. 步驟 4: Browser 自動化模組
2. 步驟 7.1-7.2: 基本主程式架構

### 第三週重點 (AI 分析核心)
1. 步驟 5: GPT 分析引擎
2. 步驟 7.3-7.4: 工作流程整合

### 第四週重點 (報告生成)
1. 步驟 6: 報告生成模組
2. 步驟 8: 模板建立

### 第五-六週重點 (優化完善)
1. 步驟 9: 性能優化
2. 步驟 10: Docker 配置檔案建立
3. 步驟 11: 文檔和部署

**注意：步驟 10 建立 Docker 檔案但不執行容器建構，容器操作由開發者手動處理**

## 關鍵技術決策點

### 1. 依賴套件選擇
- **HTTP 請求**: `aiohttp` (支援異步) + `requests` (同步備用)
- **XML/HTML 解析**: `lxml` (性能) + `BeautifulSoup` (易用性)
- **圖片處理**: `Pillow` + `opencv-python` (進階處理)
- **PDF 生成**: `weasyprint` (推薦) 或 `pdfkit`
- **數據可視化**: `plotly` (互動式) 或 `matplotlib` (靜態)

### 2. 並行處理策略
- 使用 `asyncio` 進行 I/O 密集型任務
- 使用 `concurrent.futures` 進行 CPU 密集型任務
- 考慮 `celery` + `Redis` 進行分散式任務處理

### 3. 錯誤處理模式
- 實現指數退避重試機制
- 建立詳細的日誌記錄系統
- 提供優雅的降級處理

### 4. 容器化和部署策略
- 使用 **Python 3.12-slim** 作為基礎映像 (平衡大小和功能)
- 實施 **多階段建構** 優化映像大小
- 配置 **非 root 使用者** 提升安全性
- 使用 **Docker Compose** 進行本地開發和測試
- 支援 **環境變數** 配置各種部署環境
- 考慮使用 **Kubernetes** 進行生產環境部署

---
*創建日期: 2025-06-04*  
*最後更新: 2025-06-04*  
*版本: v1.2*  
*負責人: 開發團隊*
