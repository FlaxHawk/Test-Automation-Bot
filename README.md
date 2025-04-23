# Automated Website Testing Bot

Automated Python-based bot that accepts a target website URL, discovers pages & user flows, and generates/executes Playwright tests orchestrated by Pytest with rich reporting.

## Features

- 🌐 **Multi-browser support**: Chrome, Firefox, WebKit (headless & headed)
- 🔍 **Automatic discovery**: Depth-controlled crawling of websites
- 🧪 **Test generation**: Creates page objects and test cases automatically
- 📊 **Rich reporting**: HTML reports, screenshots, videos, and Playwright traces
- 🔄 **CI/CD integration**: GitHub Actions workflow for automated testing

## Prerequisites

- Python 3.11 or higher
- Playwright 1.44 or higher

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/website-test-bot.git
   cd website-test-bot
   ```

2. Install the package with Poetry:
   ```bash
   poetry install
   ```

3. Install Playwright browsers:
   ```bash
   poetry run playwright install
   ```

## Usage

### Basic Usage

```bash
poetry run bot run https://example.com
```

### Advanced Options

```bash
poetry run bot run https://example.com --depth 3 --headful --browsers "chromium,firefox" --concurrency 4
```

## Configuration

You can customize the behavior using a `bot.yaml` configuration file:

```yaml
# Sample configuration
crawler:
  depth: 3
  max_pages: 100
  concurrency: 2
  exclude_patterns:
    - "/logout"
    - "/admin"

test:
  browsers:
    - chromium
    - firefox
  headless: true
  video: true
  traces: "on-failure"

report:
  output_dir: "./reports"
```

## Architecture

```
┌────────┐   crawl   ┌──────────┐   generate   ┌──────────┐   run   ┌──────────┐
│  CLI   │──────────▶│  Crawler │─────────────▶│ Generator│────────▶│  Runner  │
└────────┘           └──────────┘              └──────────┘         └──────────┘
      ▲                                                                  ▲ 
      └──────────────────────── report ──────────────────────────────────┘
```

## Project Structure

```
website-test-bot/
├── src/
│   └── website_test_bot/
│       ├── crawler/       # Website crawling functionality
│       ├── generator/     # Test code generation
│       ├── runner/        # Test execution
│       └── reporter/      # Report generation
├── tests/                 # Tests for the bot itself
├── reports/               # Output reports and artifacts
└── examples/              # Example configurations
```

## License

MIT License 