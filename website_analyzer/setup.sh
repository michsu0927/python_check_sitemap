#!/bin/bash

# Website Analyzer Setup Script
# This script helps set up the website analyzer environment

set -e

echo "🚀 Website Analyzer Setup"
echo "========================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python 3.11+ is available
check_python() {
    echo -e "${BLUE}Checking Python version...${NC}"
    
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [ "$(echo "$PYTHON_VERSION >= 3.11" | bc -l 2>/dev/null || echo 0)" -eq 1 ]; then
            echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
        else
            echo -e "${RED}✗ Python 3.11+ required, found $PYTHON_VERSION${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Python 3.11+ not found${NC}"
        echo "Please install Python 3.11 or later"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Using $PYTHON_CMD${NC}"
}

# Create virtual environment
setup_venv() {
    echo -e "${BLUE}Setting up virtual environment...${NC}"
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${YELLOW}! Virtual environment already exists${NC}"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
}

# Install dependencies
install_dependencies() {
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Install Playwright browsers
install_browsers() {
    echo -e "${BLUE}Installing Playwright browsers...${NC}"
    
    playwright install chromium
    
    echo -e "${GREEN}✓ Playwright browsers installed${NC}"
}

# Create directories
create_directories() {
    echo -e "${BLUE}Creating necessary directories...${NC}"
    
    mkdir -p reports logs templates/email examples/reports
    
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Setup environment file
setup_env() {
    echo -e "${BLUE}Setting up environment configuration...${NC}"
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo -e "${YELLOW}! Please edit .env file with your API keys${NC}"
        echo -e "${YELLOW}  - Add your OpenAI API key${NC}"
        echo -e "${YELLOW}  - Configure Azure OpenAI if needed${NC}"
    else
        echo -e "${YELLOW}! .env file already exists${NC}"
    fi
}

# Validate configuration
validate_config() {
    echo -e "${BLUE}Validating configuration...${NC}"
    
    if python main.py validate-config 2>/dev/null; then
        echo -e "${GREEN}✓ Configuration is valid${NC}"
    else
        echo -e "${YELLOW}! Configuration validation failed${NC}"
        echo -e "${YELLOW}  Please check your .env file and API keys${NC}"
    fi
}

# Run a test analysis
run_test() {
    echo -e "${BLUE}Running test analysis...${NC}"
    
    if [ -f ".env" ] && grep -q "OPENAI_API_KEY=sk-" .env; then
        echo "Testing with a simple analysis..."
        timeout 60 python main.py analyze https://example.com --max-pages 1 --output-dir test_reports || {
            echo -e "${YELLOW}! Test analysis timed out or failed${NC}"
            echo -e "${YELLOW}  This is normal if API keys are not configured${NC}"
        }
    else
        echo -e "${YELLOW}! Skipping test - no API key configured${NC}"
    fi
}

# Docker setup
setup_docker() {
    echo -e "${BLUE}Setting up Docker configuration...${NC}"
    
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✓ Docker found${NC}"
        
        # Build Docker image
        read -p "Build Docker image? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker build -f docker/Dockerfile -t website-analyzer .
            echo -e "${GREEN}✓ Docker image built${NC}"
        fi
    else
        echo -e "${YELLOW}! Docker not found - skipping Docker setup${NC}"
    fi
}

# Print usage instructions
print_usage() {
    echo
    echo -e "${GREEN}🎉 Setup completed!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Edit .env file with your API keys:"
    echo "   nano .env"
    echo
    echo "2. Activate virtual environment:"
    echo "   source venv/bin/activate"
    echo
    echo "3. Run your first analysis:"
    echo "   python main.py analyze https://example.com"
    echo
    echo "4. View example usage:"
    echo "   python examples/example_usage.py"
    echo
    echo "5. Check documentation:"
    echo "   cat README.md"
    echo
    echo -e "${BLUE}Docker usage:${NC}"
    echo "   docker-compose -f docker/docker-compose.yml up -d"
    echo "   docker-compose -f docker/docker-compose.yml exec website-analyzer python main.py analyze https://example.com"
    echo
}

# Main setup process
main() {
    echo "This script will set up the Website Analyzer environment."
    echo
    
    # Ask for confirmation
    read -p "Continue with setup? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Run setup steps
    check_python
    setup_venv
    install_dependencies
    install_browsers
    create_directories
    setup_env
    validate_config
    
    # Optional steps
    read -p "Run test analysis (requires API key)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_test
    fi
    
    read -p "Setup Docker? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_docker
    fi
    
    print_usage
}

# Handle script arguments
case "${1:-}" in
    --quick)
        echo "Running quick setup (no interactive prompts)..."
        check_python
        setup_venv
        install_dependencies
        install_browsers
        create_directories
        setup_env
        echo -e "${GREEN}✓ Quick setup completed${NC}"
        ;;
    --docker-only)
        echo "Setting up Docker only..."
        setup_docker
        ;;
    --help|-h)
        echo "Website Analyzer Setup Script"
        echo
        echo "Usage:"
        echo "  ./setup.sh          # Interactive setup"
        echo "  ./setup.sh --quick  # Quick setup without prompts"
        echo "  ./setup.sh --docker-only  # Docker setup only"
        echo "  ./setup.sh --help   # Show this help"
        ;;
    *)
        main
        ;;
esac
