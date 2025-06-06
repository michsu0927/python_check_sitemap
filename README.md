繁體中文版說明請點這裡 (For Traditional Chinese version, click here): [README.zh-TW.md](README.zh-TW.md)

# Automated Website Analysis System

## Project Overview
This project builds an automated system that parses website sitemaps, uses browser-use to visit pages automatically, and analyzes screenshots with GPT to produce reports.
The focus is on building the core modules; no tests are required.
Docker files are provided, but you need to build and run containers manually.

## Quick Start (Local Development)
```bash
# 1. Clone the project and navigate into the directory
git clone <repository_url>
cd website_analyzer

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# Or `venv\Scripts\activate`  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit the .env file to set API keys

# 5. Run analysis
python src/main.py --url https://example.com
```

**Note: Docker-related files will be created, but container building and execution will be handled manually by the developer.**

## System Architecture

### 1. Core Module Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                  Automated Website Analysis System          │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Sitemap Parser  │ Browser Automation│   AI Analysis Engine    │
│     Module      │      Module     │        Module           │
└─────────────────┴─────────────────┴─────────────────────────┘
│                                                             │
└────────────────── Report Generation Module ─────────────────┘
```

### 2. Technology Stack
- **Python 3.12** - Main development language (updated to the latest stable version)
- **browser-use** - Browser automation (based on Playwright)
- **Azure OpenAI / OpenAI GPT API** - Image analysis and content understanding (default Azure OpenAI)
- **Requests/aiohttp** - HTTP request handling
- **BeautifulSoup/lxml** - XML/HTML parsing
- **Pillow** - Image processing
- **Jinja2** - Report template engine
- **Docker** - Containerized deployment
- **Docker Compose** - Multi-container application orchestration

## Features

### Module 1: Sitemap Parser (`sitemap_parser.py`)
- Fetches sitemap.xml from the target website.
- Parses sitemap structure to extract all URLs.
- Supports nested sitemaps and sitemap indexes.
- Filters and categorizes different types of pages.

### Module 2: Browser-Use Automation Module (`browser_automation.py`)
- Uses browser-use (based on Playwright) for browser automation.
- Performs page screenshots and basic interaction tests.
- Collects page performance and usability data.
- Handles dynamic content and JavaScript rendering.

### Module 3: GPT Image Analysis Engine (`gpt_analyzer.py`)
- Analyzes webpage screenshots using GPT-4 Vision API (defaults to Azure OpenAI, with an option for standard OpenAI API).
- Identifies page structure, design elements, and content quality.
- Evaluates user experience and accessibility.
- Generates improvement suggestions.

### Module 4: Report Generator (`report_generator.py`)
- Integrates all analysis results.
- Generates visual reports.
- Provides optimization suggestions and prioritization.
- Supports multiple output formats.

## Workflow

### Phase 1: Data Collection
1. Input target website URL.
2. Automatically parse sitemap to obtain a list of pages.
3. Use browser-use to batch visit pages.
4. Generate standardized screenshots and collect metadata.

### Phase 2: AI Analysis
1. Send screenshots to GPT-4 Vision API.
2. Perform multi-dimensional analysis and evaluation.
3. Generate structured analysis data.
4. Calculate overall scores and rankings.

### Phase 3: Report Generation
1. Integrate all analysis results.
2. Apply report templates.
3. Generate visual charts.
4. Output final report files.

## Configuration

### Environment Variables
```bash
# Azure OpenAI Configuration (Default)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
# Or use Standard OpenAI API
OPENAI_API_KEY=your_openai_api_key

# System Configuration
BROWSER_HEADLESS=true
MAX_PAGES_PER_BATCH=10
SCREENSHOT_QUALITY=high
REPORT_OUTPUT_DIR=./reports
```

### Configuration File (`config.yaml`)
```yaml
# API Service Configuration (Default: Azure OpenAI)
api_service: "azure_openai"  # or "openai"

# Azure OpenAI Configuration (Default)
azure_openai:
  deployment_name: gpt-4-vision
  model: gpt-4-vision-preview
  max_tokens: 2000
  temperature: 0.1
  api_version: "2024-02-15-preview"

# Standard OpenAI API Configuration (Alternative)
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

## Project Structure
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

# Docker related files (to be created, but not executed)
├── docker/                  # Docker configuration directory
│   └── Dockerfile          # Docker container configuration file
├── .dockerignore           # Docker ignore file
└── docker-compose.yml      # Docker Compose configuration
```

## Docker Usage (Optional)

**Note: The following Docker configurations are for manual execution and are not included in the main development workflow.**

### Basic Run
```bash
# Manually build and run (Dockerfile needs to be created first)
docker build -t website-analyzer .
docker run -it --rm \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/reports:/app/reports \
  -e AZURE_OPENAI_API_KEY=your_key \
  website-analyzer
```

### Development Mode
```bash
# Enter the container for debugging (docker-compose.yml needs to be created first)
docker-compose exec app bash
```

### Environment Variable Configuration
Create a `.env` file:
```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Or use Standard OpenAI API
OPENAI_API_KEY=your_openai_api_key

# System Configuration
BROWSER_HEADLESS=true
MAX_PAGES_PER_BATCH=10
SCREENSHOT_QUALITY=high
REPORT_OUTPUT_DIR=./reports

# Database Configuration (Optional)
DB_PASSWORD=secure_password
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
