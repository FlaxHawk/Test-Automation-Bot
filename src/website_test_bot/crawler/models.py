"""Models for the crawler module."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Set


class CrawlElement(BaseModel):
    """
    Represents an element found during crawling.
    Used to track interactive elements like buttons, links, inputs, etc.
    """

    selector: str = Field(..., description="CSS or XPath selector for the element")
    element_type: str = Field(..., description="Type of element (button, link, etc.)")
    text: str | None = Field(None, description="Text content of the element")
    attributes: Dict[str, str] = Field(
        default_factory=dict, description="Element attributes"
    )
    is_clickable: bool = Field(False, description="Whether the element is clickable")
    is_visible: bool = Field(True, description="Whether the element is visible")
    screenshot_path: str | None = Field(
        None, description="Path to screenshot of the element"
    )


class CrawlForm(BaseModel):
    """
    Represents a form found during crawling.
    Contains information about form fields and submit buttons.
    """

    form_selector: str = Field(..., description="CSS or XPath selector for the form")
    action: str | None = Field(None, description="Form action URL")
    method: str = Field("GET", description="Form HTTP method")
    fields: List[CrawlElement] = Field(
        default_factory=list, description="Form input fields"
    )
    submit_button: CrawlElement | None = Field(None, description="Form submit button")
    sample_data: Dict[str, str] = Field(
        default_factory=dict, description="Sample data for form fields"
    )


class CrawlPage(BaseModel):
    """
    Represents a page found during crawling.
    Contains information about the page's URL, title, and discovered elements.
    """

    url: str = Field(..., description="URL of the page")
    title: str = Field("", description="Page title")
    depth: int = Field(0, description="Depth of the page in the crawl")
    parent_url: str | None = Field(None, description="Parent page URL")
    status_code: int = Field(200, description="HTTP status code")
    content_type: str = Field("text/html", description="Content type")
    elements: List[CrawlElement] = Field(
        default_factory=list, description="Elements found on the page"
    )
    forms: List[CrawlForm] = Field(
        default_factory=list, description="Forms found on the page"
    )
    links: List[str] = Field(
        default_factory=list, description="Links found on the page"
    )
    screenshot_path: str | None = Field(
        None, description="Path to screenshot of the page"
    )
    html_path: str | None = Field(None, description="Path to HTML source of the page")
    has_errors: bool = Field(False, description="Whether the page has errors")
    error_message: str | None = Field(
        None, description="Error message if the page has errors"
    )


class CrawlData(BaseModel):
    """
    Contains all data collected during the crawl process.
    Includes discovered pages, forms, and elements, as well as crawl statistics.
    """

    base_url: str = Field(..., description="Base URL of the crawled website")
    output_dir: str = Field(..., description="Output directory for crawl data")
    pages: Dict[str, CrawlPage] = Field(
        default_factory=dict, description="Discovered pages by URL"
    )
    crawl_depth: int = Field(0, description="Maximum crawl depth reached")
    start_time: str = Field("", description="Crawl start time")
    end_time: str = Field("", description="Crawl end time")
    visited_urls: Set[str] = Field(
        default_factory=set, description="Set of visited URLs"
    )
    failed_urls: Dict[str, str] = Field(
        default_factory=dict, description="Failed URLs with error messages"
    )
    stats: Dict[str, int] = Field(default_factory=dict, description="Crawl statistics")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
