"""Crawler module for discovering website pages and elements."""

from typing import Tuple, List
import os
import re
from .models import CrawlData, CrawlPage, CrawlElement, CrawlForm
from playwright.async_api import async_playwright, Browser, Page
from rich.console import Console
import asyncio
import datetime
import urllib.parse
from website_test_bot.config import Config

# Create console
console = Console()


async def create_browser(config: Config, headless: bool = True) -> Browser:
    """
    Create a Playwright browser instance.
    Args:
        config: Bot configuration
        headless: Whether to run in headless mode
    Returns:
        Browser: Playwright browser instance
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    return browser


async def extract_forms(page: Page, output_dir: str) -> List[CrawlForm]:
    """
    Extract forms from a page.
    Args:
        page: Playwright page
        output_dir: Directory to save screenshots
    Returns:
        List[CrawlForm]: List of forms found on the page
    """
    forms: List[CrawlForm] = []
    # Find all forms
    form_elements = await page.query_selector_all("form")
    for i, form_element in enumerate(form_elements):
        # Get form attributes
        form_selector = f"form:nth-of-type({i + 1})"
        action = await form_element.get_attribute("action")
        method = await form_element.get_attribute("method") or "GET"
        # Create form object
        form = CrawlForm(
            form_selector=form_selector, action=action, method=method.upper()
        )
        # Find form fields
        input_elements = await form_element.query_selector_all(
            'input:not([type="submit"]):not([type="button"]):not([type="reset"]), select, textarea'
        )
        for input_element in input_elements:
            # Get field attributes
            input_type = await input_element.get_attribute("type") or "text"
            input_name = await input_element.get_attribute("name")
            input_id = await input_element.get_attribute("id")
            input_placeholder = await input_element.get_attribute("placeholder")
            # Create element selector
            element_selector = f"{form_selector} "
            if input_id:
                element_selector += f"#{input_id}"
            elif input_name:
                element_selector += f"[name='{input_name}']"
            else:
                element_selector += f"input[type='{input_type}']"
            # Create field element
            field_element = CrawlElement(
                selector=element_selector,
                element_type=f"input-{input_type}",
                text=input_placeholder,
                attributes={
                    "type": input_type,
                    "name": input_name or "",
                    "id": input_id or "",
                    "placeholder": input_placeholder or "",
                },
                is_visible=await input_element.is_visible(),
            )
            # Add field to form
            form.fields.append(field_element)
            # Generate sample data for field
            if input_name:
                if input_type == "email":
                    form.sample_data[input_name] = "test@example.com"
                elif input_type == "password":
                    form.sample_data[input_name] = "Password123!"
                elif "name" in input_name.lower():
                    form.sample_data[input_name] = "Test User"
                elif "phone" in input_name.lower():
                    form.sample_data[input_name] = "123-456-7890"
                else:
                    form.sample_data[input_name] = f"test_{input_name}"
        # Find submit button
        submit_element = await form_element.query_selector(
            "input[type='submit'], button[type='submit'], button:not([type])"
        )
        if submit_element:
            submit_text = await submit_element.text_content() or "Submit"
            submit_selector = f"{form_selector} "
            submit_id = await submit_element.get_attribute("id")
            if submit_id:
                submit_selector += f"#{submit_id}"
            else:
                submit_selector += (
                    "input[type='submit'], button[type='submit'], button:not([type])"
                )
            # Create submit button element
            form.submit_button = CrawlElement(
                selector=submit_selector,
                element_type="submit",
                text=submit_text.strip(),
                is_clickable=True,
                is_visible=await submit_element.is_visible(),
            )
        forms.append(form)
    return forms


async def extract_elements(page: Page, output_dir: str) -> List[CrawlElement]:
    """
    Extract interactive elements from a page.
    Args:
        page: Playwright page
        output_dir: Directory to save screenshots
    Returns:
        List[CrawlElement]: List of elements found on the page
    """
    elements: List[CrawlElement] = []
    # Find all interactive elements
    selectors = [
        "a[href]",
        "button",
        "input[type='button']",
        "input[type='submit']",
        "[role='button']",
    ]
    for selector in selectors:
        element_handles = await page.query_selector_all(selector)
        for element_handle in element_handles:
            try:
                # Get element attributes
                element_type = (
                    await element_handle.get_attribute("type") or selector.split("[")[0]
                )
                element_text = await element_handle.text_content() or ""
                element_href = await element_handle.get_attribute("href") or ""
                element_id = await element_handle.get_attribute("id") or ""
                element_class = await element_handle.get_attribute("class") or ""
                # Create element attributes
                attributes = {
                    "id": element_id,
                    "class": element_class,
                    "href": element_href,
                }
                # Create element selector
                custom_selector = ""
                if element_id:
                    custom_selector = f"#{element_id}"
                elif element_class:
                    classes = element_class.split()
                    class_selector = ".".join(classes)
                    custom_selector = f".{class_selector}"
                else:
                    custom_selector = selector
                # Check if element is visible and clickable
                is_visible = await element_handle.is_visible()
                is_clickable = is_visible
                # Create element
                element = CrawlElement(
                    selector=custom_selector,
                    element_type=element_type,
                    text=element_text.strip(),
                    attributes=attributes,
                    is_clickable=is_clickable,
                    is_visible=is_visible,
                )
                elements.append(element)
            except Exception:
                # Ignore elements that can't be processed
                pass
    return elements


async def extract_links(page: Page, base_url: str) -> List[str]:
    """
    Extract links from a page.
    Args:
        page: Playwright page
        base_url: Base URL of the website
    Returns:
        List[str]: List of links found on the page
    """
    links: List[str] = []
    # Find all links
    link_elements = await page.query_selector_all("a[href]")
    for link_element in link_elements:
        try:
            href = await link_element.get_attribute("href")
            if href:
                # Normalize URL
                absolute_url = urllib.parse.urljoin(base_url, href)
                # Only include same-origin URLs
                if absolute_url.startswith(base_url):
                    # Remove fragment
                    url_parts = urllib.parse.urlparse(absolute_url)
                    clean_url = urllib.parse.urlunparse(
                        (
                            url_parts.scheme,
                            url_parts.netloc,
                            url_parts.path,
                            url_parts.params,
                            url_parts.query,
                            "",
                        )
                    )
                    links.append(clean_url)
        except Exception:
            # Ignore links that can't be processed
            pass
    return links


async def crawl_page(
    browser: Browser,
    url: str,
    output_dir: str,
    depth: int,
    parent_url: str | None,
    config: Config,
) -> CrawlPage:
    """
    Crawl a single page.
    Args:
        browser: Playwright browser
        url: URL of the page to crawl
        output_dir: Directory to save artifacts
        depth: Current crawl depth
        parent_url: URL of the parent page
        config: Bot configuration
    Returns:
        CrawlPage: Crawled page data
    """
    # Create page
    context = await browser.new_context(
        viewport={
            "width": config.test.viewport.width,
            "height": config.test.viewport.height,
        },
        user_agent=config.crawler.user_agent,
    )
    page = await context.new_page()
    # Create crawl page
    crawl_page = CrawlPage(url=url, depth=depth, parent_url=parent_url)
    try:
        # Create page-specific output directory
        url_hash = str(abs(hash(url)) % 10000)
        page_dir = os.path.join(output_dir, f"page_{url_hash}")
        os.makedirs(page_dir, exist_ok=True)
        # Navigate to page
        response = await page.goto(
            url, timeout=config.crawler.page_timeout_ms, wait_until="domcontentloaded"
        )
        # Wait for page to load
        await asyncio.sleep(config.crawler.wait_after_load_ms / 1000)
        # Get page information
        crawl_page.title = await page.title()
        if response:
            crawl_page.status_code = response.status
            crawl_page.content_type = response.headers.get("content-type", "")
        # Take screenshot if enabled
        if config.crawler.capture_screenshots:
            screenshot_path = os.path.join(page_dir, "screenshot.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            crawl_page.screenshot_path = screenshot_path
        # Save HTML source
        html_path = os.path.join(page_dir, "source.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(await page.content())
        crawl_page.html_path = html_path
        # Extract forms
        crawl_page.forms = await extract_forms(page, page_dir)
        # Extract interactive elements
        crawl_page.elements = await extract_elements(page, page_dir)
        # Extract links
        base_url = urllib.parse.urlparse(url).netloc
        base_url = f"{urllib.parse.urlparse(url).scheme}://{base_url}"
        crawl_page.links = await extract_links(page, base_url)
    except Exception as e:
        # Handle errors
        crawl_page.has_errors = True
        crawl_page.error_message = str(e)
    finally:
        # Close context
        await context.close()
    return crawl_page


async def is_url_allowed(url: str, config: Config) -> bool:
    """
    Check if a URL is allowed to be crawled.
    Args:
        url: URL to check
        config: Bot configuration
    Returns:
        bool: Whether the URL is allowed
    """
    # Check exclude patterns
    for pattern in config.crawler.exclude_patterns:
        if re.search(pattern, url):
            return False
    # Check URL scheme
    url_parts = urllib.parse.urlparse(url)
    if url_parts.scheme not in ["http", "https"]:
        return False
    # Check file extensions
    path = url_parts.path.lower()
    excluded_extensions = [
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".css",
        ".js",
    ]
    if any(path.endswith(ext) for ext in excluded_extensions):
        return False
    return True


async def crawl_website(url: str, config: Config) -> CrawlData:
    """
    Crawl a website to discover pages and elements.
    Args:
        url: URL of the website to crawl
        config: Bot configuration
    Returns:
        CrawlData: Crawled website data
    """
    # Create output directory
    output_dir = os.path.join(config.report.output_dir, "crawl_data")
    os.makedirs(output_dir, exist_ok=True)
    # Create browser
    # Always use headless mode in GitHub Actions environment
    force_headless = "GITHUB_ACTIONS" in os.environ
    headless = force_headless or config.test.headless
    browser = await create_browser(config, headless)
    # Initialize crawl data
    crawl_data = CrawlData(base_url=url, output_dir=output_dir)
    # Initialize crawl queue and visited set
    to_crawl: List[Tuple[str, int, str | None]] = [(url, 0, None)]
    try:
        while to_crawl and len(crawl_data.pages) < config.crawler.max_pages:
            # Get batch of URLs to crawl concurrently
            batch = to_crawl[: config.crawler.concurrency]
            to_crawl = to_crawl[config.crawler.concurrency :]
            # Crawl batch
            crawl_tasks = [
                crawl_page(browser, url, output_dir, depth, parent_url, config)
                for url, depth, parent_url in batch
            ]
            crawled_pages = await asyncio.gather(*crawl_tasks)
            # Process crawled pages
            for page in crawled_pages:
                # Add page to crawl data
                crawl_data.pages[page.url] = page
                crawl_data.visited_urls.add(page.url)
                # Update crawl depth
                crawl_data.crawl_depth = max(crawl_data.crawl_depth, page.depth)
                # Add child pages to crawl queue if not at max depth
                if page.depth < config.crawler.depth and not page.has_errors:
                    for link in page.links:
                        if (
                            link not in crawl_data.visited_urls
                            and link not in crawl_data.failed_urls
                            and await is_url_allowed(link, config)
                        ):
                            to_crawl.append((link, page.depth + 1, page.url))
                # Add failed page to failed URLs
                if page.has_errors:
                    crawl_data.failed_urls[page.url] = (
                        page.error_message or "Unknown error"
                    )
        # Calculate statistics
        crawl_data.stats = {
            "pages": len(crawl_data.pages),
            "failed": len(crawl_data.failed_urls),
            "depth": crawl_data.crawl_depth,
            "links": sum(len(p.links) for p in crawl_data.pages.values()),
            "forms": sum(len(p.forms) for p in crawl_data.pages.values()),
            "elements": sum(len(p.elements) for p in crawl_data.pages.values()),
        }
    finally:
        # Close browser
        await browser.close()
        # Set end time
        crawl_data.end_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return crawl_data


def crawl_website_sync(url: str, config: Config) -> CrawlData:
    """
    Synchronous wrapper for crawl_website.
    Args:
        url: URL of the website to crawl
        config: Bot configuration
    Returns:
        CrawlData: Crawled website data
    """
    return asyncio.run(crawl_website(url, config))
