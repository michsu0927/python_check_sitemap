# Automated Website Analysis System

This project aims to build a tool that automatically analyzes websites by parsing sitemaps, running browser automation tasks, and leveraging GPT-based image analysis. The objective is to generate comprehensive reports about site design, user experience, technical quality, and content.

All development milestones and detailed task breakdowns are documented in [Task.md](Task.md). Refer to that file for in-depth planning and module descriptions.

## Quick Start

Follow these steps to set up a local development environment:

```bash
# 1. Clone this repository and enter the directory
git clone <repository_url>
cd python_check_sitemap  # or your cloned folder name

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # on Linux/Mac
# or venv\Scripts\activate  # on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit the .env file to set API keys and other settings

# 5. Run the analyzer
python src/main.py --url https://example.com
```

**Note:** Docker-related files will be included, but building and running containers is left to the developer to execute manually.
