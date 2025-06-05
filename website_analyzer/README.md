# Website Analyzer

An automated website analysis system that combines sitemap parsing, browser automation, and GPT-4 Vision API to provide comprehensive website analysis reports.

## 🚀 Features

- **Sitemap Parsing**: Automatically discover and parse website sitemaps
- **Browser Automation**: Capture screenshots across multiple device viewports (desktop, tablet, mobile)
- **GPT-4 Vision Analysis**: AI-powered analysis of visual design, UX, technical quality, and content
- **Comprehensive Reports**: Generate HTML, PDF, and JSON reports with visualizations
- **Batch Processing**: Analyze multiple websites simultaneously
- **Performance Metrics**: Collect page load times and performance data
- **Docker Support**: Containerized deployment with all dependencies
- **Flexible Configuration**: Support for both Azure OpenAI and standard OpenAI APIs

## 📋 Requirements

- Python 3.11+
- OpenAI API key (GPT-4 Vision) or Azure OpenAI access
- Docker (optional, for containerized deployment)

## 🔧 Installation

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd website_analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Docker Installation

1. **Build and run with Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

2. **Configure environment variables**
   Create a `.env` file in the project root with your configuration.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-vision-preview

# Azure OpenAI Configuration (Optional)
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30
MAX_PAGES_PER_SITEMAP=100

# Analysis Configuration
MAX_CONCURRENT_REQUESTS=5
RATE_LIMIT_DELAY=1
ANALYSIS_CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/analyzer.log
```

### Configuration File

Edit `config/config.yaml` to customize analysis parameters:

```yaml
api:
  service: "openai"  # or "azure_openai"
  openai:
    model: "gpt-4-vision-preview"
    max_tokens: 4000
    temperature: 0.1
  azure_openai:
    api_version: "2024-02-01"
    deployment_name: "gpt-4-vision"

browser:
  headless: true
  timeout: 30
  viewports:
    desktop: {width: 1920, height: 1080}
    tablet: {width: 768, height: 1024}
    mobile: {width: 375, height: 667}

analysis:
  max_concurrent: 5
  rate_limit_delay: 1
  cache_ttl: 3600
  dimensions:
    - visual_design
    - user_experience
    - technical_quality
    - content_quality
```

## 🚀 Usage

### Command Line Interface

#### Analyze a Single Website

```bash
# Basic analysis
python main.py analyze https://example.com

# Limit pages and specify output format
python main.py analyze https://example.com --max-pages 10 --format pdf

# Custom output directory
python main.py analyze https://example.com --output-dir ./my-reports

# Use custom configuration
python main.py analyze https://example.com --config custom_config.yaml
```

#### Batch Analysis

```bash
# Create a file with URLs (one per line)
echo "https://example.com" > urls.txt
echo "https://another-site.com" >> urls.txt

# Run batch analysis
python main.py batch-analyze urls.txt --max-pages 5 --output-dir ./batch-reports
```

#### Configuration Validation

```bash
# Validate configuration
python main.py validate-config
python main.py validate-config --config custom_config.yaml
```

### Docker Usage

```bash
# Run analysis in Docker container
docker-compose -f docker/docker-compose.yml exec website-analyzer \
  python main.py analyze https://example.com

# Batch analysis with Docker
docker-compose -f docker/docker-compose.yml exec website-analyzer \
  python main.py batch-analyze /app/urls.txt
```

### Programmatic Usage

```python
import asyncio
from src.config_manager import ConfigManager
from main import WebsiteAnalyzer

async def analyze_website():
    analyzer = WebsiteAnalyzer()
    results = await analyzer.analyze_website(
        url="https://example.com",
        max_pages=10,
        output_dir="./reports",
        report_format="html"
    )
    print(f"Analysis completed: {results['report_path']}")

# Run the analysis
asyncio.run(analyze_website())
```

## 📊 Analysis Dimensions

The system analyzes websites across four key dimensions:

### 1. Visual Design (25%)
- Layout and composition
- Color scheme and branding
- Typography and readability
- Visual hierarchy
- Image quality and optimization

### 2. User Experience (25%)
- Navigation usability
- Mobile responsiveness
- Loading performance
- Accessibility features
- Interactive elements

### 3. Technical Quality (25%)
- Page load speed
- HTML/CSS validation
- SEO optimization
- Security indicators
- Browser compatibility

### 4. Content Quality (25%)
- Content relevance and clarity
- Information architecture
- Call-to-action effectiveness
- Content freshness
- Multilingual support

## 📈 Report Types

### HTML Reports
- Interactive dashboards with charts
- Detailed page-by-page analysis
- Performance metrics visualization
- Responsive design for mobile viewing

### PDF Reports
- Professional formatted documents
- Executive summaries
- Printable analysis results
- Charts and screenshots included

### JSON Reports
- Raw analysis data
- API-friendly format
- Custom processing and integration
- Machine-readable results

## 🐳 Docker Services

The Docker Compose setup includes:

- **website-analyzer**: Main application container
- **redis**: Caching service (optional)
- **nginx**: Web server for report hosting

Access reports at: `http://localhost:8080/reports/`

## 🔒 Security Considerations

- API keys are stored in environment variables
- Container runs as non-root user
- Security headers configured in Nginx
- Browser sandboxing enabled
- Rate limiting implemented

## 🛠️ Development

### Project Structure

```
website_analyzer/
├── main.py                 # Main CLI entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
├── .dockerignore         # Docker ignore rules
├── config/
│   └── config.yaml       # Main configuration
├── docker/
│   ├── Dockerfile        # Container definition
│   ├── docker-compose.yml # Service orchestration
│   └── nginx.conf        # Web server config
├── src/
│   ├── config_manager.py # Configuration management
│   ├── sitemap_parser.py # Sitemap parsing logic
│   ├── browser_automation.py # Browser control
│   ├── gpt_analyzer.py   # GPT-4 Vision analysis
│   └── report_generator.py # Report generation
├── templates/            # Report templates
├── reports/             # Generated reports
└── logs/               # Application logs
```

### Key Components

1. **ConfigManager**: Handles configuration loading and API switching
2. **SitemapParser**: Discovers and parses website URLs
3. **BrowserAutomation**: Controls browser for screenshots and metrics
4. **GPTAnalyzer**: Interfaces with GPT-4 Vision for analysis
5. **ReportGenerator**: Creates comprehensive analysis reports

### Adding Custom Analysis

To extend the analysis capabilities:

1. Modify `config/config.yaml` to add new dimensions
2. Update `GPTAnalyzer` prompts in `src/gpt_analyzer.py`
3. Extend report templates in `templates/`
4. Update scoring logic in `ReportGenerator`

## 📝 Logging

Logs are written to:
- Console (stdout)
- File: `logs/analyzer.log`
- Docker logs: `docker-compose logs website-analyzer`

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 🐛 Troubleshooting

### Common Issues

1. **Browser Launch Errors**
   ```bash
   # Install system dependencies
   sudo apt-get install -y chromium-browser
   playwright install chromium
   ```

2. **API Rate Limits**
   - Increase `RATE_LIMIT_DELAY` in configuration
   - Reduce `MAX_CONCURRENT_REQUESTS`

3. **Memory Issues**
   - Increase Docker memory limits
   - Reduce concurrent processing

4. **Permission Errors**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER reports/ logs/
   chmod -R 755 reports/ logs/
   ```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py analyze https://example.com
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review configuration examples
- Open an issue on GitHub

## 🔄 Changelog

### v1.0.0 (Current)
- Initial release
- Sitemap parsing with robots.txt support
- Multi-device browser automation
- GPT-4 Vision analysis
- HTML/PDF report generation
- Docker containerization
- Batch processing capabilities
