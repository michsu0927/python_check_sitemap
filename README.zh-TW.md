# 自動化網站分析系統

## 專案概述
開發一個自動化系統，能夠解析網站 sitemap、使用 browser-use 進行自動化瀏覽器操作來檢測網頁，並透過 GPT 分析畫面截圖產生分析報告。
專注於實現核心功能模組，不需要進行測試。
將會建立 Docker 相關檔案，但容器的建立與執行將由開發者手動處理。

## 快速啟動 (本地開發)
```bash
# 1. 複製專案並進入目錄
git clone <repository_url>
cd website_analyzer

# 2. 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 `venv\Scriptsctivate`  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 配置環境變數
cp .env.example .env
# 編輯 .env 檔案設定 API keys

# 5. 運行分析
python src/main.py --url https://example.com
```
**注意：將會建立 Docker 相關檔案，但容器的建構和執行將由開發者手動處理。**

## 系統架構

### 1. 核心模組架構
```
┌─────────────────────────────────────────────────────────────┐
│              Automated Website Analysis System              │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Sitemap Parsing│ Browser Automation│      AI Analysis Engine │
│     Module      │      Module     │        Module           │
└─────────────────┴─────────────────┴─────────────────────────┘
│                                                             │
└─────────────────── Report Generation Module ────────────────┘
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

## 功能特色

### Sitemap 解析器 (`sitemap_parser.py`)
- 從目標網站獲取 sitemap.xml。
- 解析 sitemap 結構以提取所有 URL。
- 支援巢狀 sitemap 和 sitemap 索引。
- 過濾和分類不同類型的頁面。

### Browser-Use 自動化檢測器 (`browser_automation.py`)
- 使用 browser-use (基於 Playwright) 進行瀏覽器自動化操作。
- 執行頁面截圖和基本互動測試。
- 收集頁面效能和可用性數據。
- 處理動態內容和 JavaScript 渲染。

### GPT 圖像分析引擎 (`gpt_analyzer.py`)
- 使用 GPT-4 Vision API 分析網頁截圖 (預設使用 Azure OpenAI，可選標準 OpenAI API)。
- 識別頁面結構、設計元素和內容品質。
- 評估使用者體驗和可訪問性。
- 生成改進建議。

### 報告生成器 (`report_generator.py`)
- 整合所有分析結果。
- 生成視覺化報告。
- 提供優化建議和優先級排序。
- 支援多種輸出格式。

## 工作流程

### 階段 1: 資料收集
1. 輸入目標網站 URL。
2. 自動解析 sitemap 以獲取頁面列表。
3. 使用 browser-use 批次訪問頁面。
4. 生成標準化截圖並收集元數據。

### 階段 2: AI 分析
1. 將截圖傳送至 GPT-4 Vision API。
2. 執行多維度分析評估。
3. 生成結構化分析數據。
4. 計算整體評分和排名。

### 階段 3: 報告生成
1. 整合所有分析結果。
2. 套用報告模板。
3. 生成視覺化圖表。
4. 輸出最終報告檔案。

## 組態設定

### 環境變數
```bash
# Azure OpenAI Configuration (default)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
# Or use standard OpenAI API
OPENAI_API_KEY=your_openai_api_key

# System Configuration
BROWSER_HEADLESS=true
MAX_PAGES_PER_BATCH=10
SCREENSHOT_QUALITY=high
REPORT_OUTPUT_DIR=./reports
```

### 組態檔案 (`config.yaml`)
```yaml
# API service configuration (default uses Azure OpenAI)
api_service: "azure_openai"  # or "openai"

# Azure OpenAI Configuration (default)
azure_openai:
  deployment_name: gpt-4-vision
  model: gpt-4-vision-preview
  max_tokens: 2000
  temperature: 0.1
  api_version: "2024-02-15-preview"

# OpenAI Standard API Configuration (alternative)
openai:
  model: gpt-4-vision-preview
  max_tokens: 2000
  temperature: 0.1

# Browser Configuration
browser:
  headless: true
  window_size: [1920, 1080]
  timeout: 30

# Analysis Configuration
analysis:
  max_pages: 50
  screenshot_formats: [desktop, tablet, mobile]

# Output Configuration
output:
  formats: [html, pdf]
  include_screenshots: true
```

## 專案結構
```text
website_analyzer/
├── src/
│   ├── sitemap_parser.py      # Sitemap parsing module
│   ├── browser_automation.py  # Browser-use automation module
│   ├── gpt_analyzer.py       # GPT analysis engine
│   ├── report_generator.py   # Report generator
│   ├── config_manager.py     # Configuration management (supports OpenAI/Azure OpenAI)
│   └── main.py              # Main program entry point
├── templates/
│   ├── report_template.html  # HTML report template
│   └── email_template.html   # Email notification template
├── config/
│   └── config.yaml          # System configuration file
├── .env.example             # Environment variable example file
├── requirements.txt         # Python dependencies
├── README.md               # Project description
└── Task.md                 # This task planning document

# Docker related files (need to be created, but not executed)
├── docker/                  # Docker configuration directory
│   └── Dockerfile          # Docker container configuration file
├── .dockerignore           # Docker ignore file
└── docker-compose.yml      # Docker Compose configuration
```

## Docker 用法 (選用)
**注意：以下 Docker 組態為手動執行項目，並非主要開發流程的一部分。**

### 基本執行
```bash
# Manually build and run (Dockerfile must be created first)
docker build -t website-analyzer .
docker run -it --rm   -v $(pwd)/config:/app/config   -v $(pwd)/reports:/app/reports   -e AZURE_OPENAI_API_KEY=your_key   website-analyzer
```

### 開發模式
```bash
# Enter the container for debugging (docker-compose.yml must be created first)
docker-compose exec app bash
```

### 環境變數組態
建立一個 `.env` 檔案：
```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Or use standard OpenAI API
OPENAI_API_KEY=your_openai_api_key

# System Configuration
BROWSER_HEADLESS=true
MAX_PAGES_PER_BATCH=10
SCREENSHOT_QUALITY=high
REPORT_OUTPUT_DIR=./reports

# Database Configuration (optional)
DB_PASSWORD=secure_password
```

## 授權
本專案採用 MIT 授權 - 詳情請參閱 [LICENSE](LICENSE) 檔案。
```
