# Website Test Bot

An intelligent test automation tool that crawls websites, automatically generates Playwright tests with Pytest, and provides comprehensive reports - all without writing a single line of code.

## Overview

Website Test Bot is designed to simplify web application testing by automating the entire process from discovery to reporting. It accepts any URL, crawls the website to map its structure, generates meaningful tests based on the discovered elements, and executes those tests across multiple browsers with detailed reporting.

## Key Features

- 🤖 **Zero-Code Automation**: Just provide a URL and get comprehensive test coverage
- 🌐 **Cross-Browser Testing**: Run tests on Chromium, Firefox, and WebKit
- 🔍 **Smart Crawling**: Automatically discovers pages, forms, and interactive elements
- 📊 **Detailed Reports**: Rich HTML reports with screenshots, videos, and Playwright traces
- 🔄 **CI/CD Integration**: Seamless GitHub Actions workflow for continuous testing
- ⚡ **Parallel Execution**: Run tests concurrently for faster results
- 📱 **Responsive Testing**: Test websites across different viewport sizes

## Installation

### Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/user/Test-Automation-Bot.git
   cd Test-Automation-Bot
   ```

2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

3. Install Playwright browsers:
   ```bash
   poetry run playwright install --with-deps chromium firefox webkit
   ```

## Usage

### Quick Start

Generate and run tests for any website:

```bash
poetry run bot run https://example.com
```

The bot will:
1. Crawl the website to a default depth of 3
2. Generate test files based on discovered pages and elements
3. Run the tests in headless mode on Chromium
4. Generate HTML and JUnit reports with screenshots and videos

### Advanced Options

```bash
# Run with increased crawl depth and multiple browsers
poetry run bot run https://example.com --depth 4 --browsers "chromium,firefox,webkit"

# Run in headful mode to watch the tests execute
poetry run bot run https://example.com --headful

# Run with increased concurrency for faster crawling and testing
poetry run bot run https://example.com --concurrency 8

# Specify a custom output directory
poetry run bot run https://example.com --output-dir ./my-reports
```

## Configuration

Create a `bot.yaml` file in your project root to customize behavior:

```yaml
# Bot configuration with all available options
crawler:
  # Maximum crawl depth from the seed URL
  depth: 3
  
  # Maximum number of pages to crawl
  max_pages: 100
  
  # Number of concurrent crawling tasks
  concurrency: 2
  
  # Timeout for page load in milliseconds
  page_timeout_ms: 30000
  
  # Patterns to exclude from crawling (regex)
  exclude_patterns:
    - "/logout"
    - "/admin"
    - "/account/delete"
    - "\\?sort="
    - "\\.pdf$"
  
  # Whether to capture screenshots during crawling
  capture_screenshots: true

test:
  # Browsers to test with
  browsers:
    - chromium
    - firefox
    - webkit
  
  # Whether to run in headless mode
  headless: true
  
  # Viewport settings
  viewport:
    width: 1280
    height: 720
  
  # Whether to record video of test execution
  video: true
  
  # When to capture traces: "on", "off", or "on-failure"
  traces: "on-failure"
  
  # Concurrency for test execution
  concurrency: 4
  
  # How many times to retry failed tests
  retry_failed: 1

report:
  # Output directory for reports
  output_dir: "./reports"
  
  # Report format: "html", "junit", or "both"
  format: "both"
  
  # Whether to generate a summary report
  generate_summary: true
```

## Workflow Architecture

```
┌────────┐   crawl   ┌──────────┐   generate   ┌──────────┐   run   ┌──────────┐
│  CLI   │──────────▶│  Crawler │─────────────▶│ Generator│────────▶│  Runner  │
└────────┘           └──────────┘              └──────────┘         └──────────┘
      ▲                                                                  │ 
      └─────────────────────────  report  ◀───────────────────────────────┘
```

## Project Structure

```
website-test-bot/
├── src/website_test_bot/        # Main package
│   ├── crawler/                 # Website discovery
│   ├── generator/               # Test generation
│   ├── runner/                  # Test execution
│   └── reporter/                # Report creation
├── tests/                       # Tests for the bot itself
├── reports/                     # Generated test results
├── bot.yaml                     # Default configuration
└── pyproject.toml               # Poetry configuration
```

## CI/CD Integration

The project includes a GitHub Actions workflow that:

1. Runs linting checks with Black
2. Executes unit and integration tests
3. Runs a demo test against a sample website
4. Uploads test artifacts for review

## Limitations and Known Issues

- SPA frameworks with complex client-side routing may not be fully discovered
- Websites requiring authentication need manual configuration
- Advanced interactions like drag-and-drop are not yet supported
- Very deep websites may require adjusting the crawler depth and timeout settings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Acknowledgments

- Built with [Playwright](https://playwright.dev/) and [Pytest](https://docs.pytest.org/)
