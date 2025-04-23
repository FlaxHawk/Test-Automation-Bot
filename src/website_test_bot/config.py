"""Configuration module for the Website Test Bot."""

from typing import List, Dict, Literal, Any, Optional
import os
from pydantic import BaseModel, Field, field_validator, model_validator
import yaml


class CrawlerConfig(BaseModel):
    """Configuration for the crawler module."""

    depth: int = Field(3, ge=1, description="Maximum depth to crawl")
    max_pages: int = Field(100, ge=1, description="Maximum number of pages to crawl")
    concurrency: int = Field(2, ge=1, description="Number of concurrent crawling tasks")
    page_timeout_ms: int = Field(
        30000, ge=1000, description="Timeout for page load in milliseconds"
    )
    wait_after_load_ms: int = Field(
        1000, ge=0, description="Wait time after page load in milliseconds"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list, description="Patterns to exclude (regex)"
    )
    user_agent: str = Field(
        "Mozilla/5.0 Website-Test-Bot", description="User agent to use"
    )
    respect_robots_txt: bool = Field(True, description="Whether to respect robots.txt")
    capture_screenshots: bool = Field(
        True, description="Whether to capture screenshots during crawling"
    )


class ViewportConfig(BaseModel):
    """Viewport configuration."""

    width: int = Field(1280, ge=320, description="Viewport width")
    height: int = Field(720, ge=240, description="Viewport height")


class TestConfig(BaseModel):
    """Configuration for the test module."""

    browsers: List[Literal["chromium", "firefox", "webkit"]] = Field(
        ["chromium"], min_length=1, description="Browsers to test"
    )
    headless: bool = Field(True, description="Whether to run in headless mode")
    viewport: ViewportConfig = Field(
        default_factory=ViewportConfig, description="Viewport settings"
    )
    video: bool = Field(True, description="Whether to record video")
    traces: Literal["on", "off", "on-failure"] = Field(
        "on-failure", description="Traces: 'on', 'off', or 'on-failure'"
    )
    concurrency: int = Field(4, ge=1, description="Concurrency for test execution")
    test_timeout_ms: int = Field(
        60000, ge=1000, description="Timeout for tests in milliseconds"
    )
    retry_failed: int = Field(1, ge=0, description="Retry failed tests")


class ReportConfig(BaseModel):
    """Configuration for the report module."""

    output_dir: str = Field("./reports", description="Output directory for reports")
    format: Literal["html", "junit", "both"] = Field(
        "both", description="Report format: 'html', 'junit', or 'both'"
    )
    include_screenshots: bool = Field(
        True, description="Whether to include screenshots in reports"
    )
    include_videos: bool = Field(
        True, description="Whether to include videos in reports"
    )
    include_traces: bool = Field(
        True, description="Whether to include traces in reports"
    )
    generate_summary: bool = Field(
        True, description="Whether to generate a summary report"
    )

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: str) -> str:
        """Ensure output directory exists and is writable."""
        if not os.path.exists(v):
            os.makedirs(v, exist_ok=True)
        if not os.access(v, os.W_OK):
            raise ValueError(f"Output directory {v} is not writable")
        return v


class Config(BaseModel):
    """Main configuration for the Website Test Bot."""

    crawler: CrawlerConfig = Field(
        default_factory=CrawlerConfig, description="Crawler configuration"
    )
    test: TestConfig = Field(
        default_factory=TestConfig, description="Test configuration"
    )
    report: ReportConfig = Field(
        default_factory=ReportConfig, description="Report configuration"
    )

    @model_validator(mode="after")
    def validate_concurrency(self) -> "Config":
        """Ensure test concurrency is not higher than crawler concurrency."""
        if self.test.concurrency > self.crawler.concurrency * 2:
            self.test.concurrency = self.crawler.concurrency * 2
        return self


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from file.
    Args:
        config_path: Path to configuration file (YAML). If None, use default.
    Returns:
        Config: Configuration object
    """
    config_dict: Dict[str, Any] = {}
    # Try to load from provided path
    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            config_dict = yaml.safe_load(f) or {}
    # If no config path provided or file doesn't exist, check for default locations
    elif not config_path:
        default_locations = ["./bot.yaml", "./bot.yml", "./config/bot.yaml"]
        for loc in default_locations:
            if os.path.exists(loc):
                with open(loc) as f:
                    config_dict = yaml.safe_load(f) or {}
                break
    # Create config object
    return Config(**config_dict)


def merge_cli_args(config: Config, cli_args: Dict[str, Any]) -> Config:
    """
    Merge CLI arguments into config.
    Args:
        config: Configuration object
        cli_args: CLI arguments
    Returns:
        Config: Updated configuration object
    """
    config_dict = config.model_dump()
    # Update config with CLI args
    if "depth" in cli_args and cli_args["depth"] is not None:
        config_dict["crawler"]["depth"] = cli_args["depth"]
    if "headful" in cli_args and cli_args["headful"]:
        config_dict["test"]["headless"] = False
    if "headless" in cli_args and cli_args["headless"]:
        config_dict["test"]["headless"] = True
    if "browsers" in cli_args and cli_args["browsers"]:
        browsers = cli_args["browsers"].split(",")
        config_dict["test"]["browsers"] = [
            b.strip()
            for b in browsers
            if b.strip() in ["chromium", "firefox", "webkit"]
        ]
    if "concurrency" in cli_args and cli_args["concurrency"] is not None:
        config_dict["crawler"]["concurrency"] = cli_args["concurrency"]
        config_dict["test"]["concurrency"] = cli_args["concurrency"]
    if "output_dir" in cli_args and cli_args["output_dir"]:
        config_dict["report"]["output_dir"] = cli_args["output_dir"]
    return Config(**config_dict)
