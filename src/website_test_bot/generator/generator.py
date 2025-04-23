"""Test generator module for creating test files from crawl data."""

import os
import re
from .models import GeneratedFile, PageObject, ElementLocator, GeneratedTest
import string
from website_test_bot.config import Config
from website_test_bot.crawler.models import (
    CrawlData,
    CrawlPage,
    CrawlForm,
    CrawlElement,
)


def sanitize_name(name: str) -> str:
    """
    Sanitize a name for use in Python code.
    Args:
        name: Name to sanitize
    Returns:
        str: Sanitized name
    """
    # Remove non-alphanumeric characters
    name = re.sub(r"[^a-zA-Z0-9]", "_", name)
    # Ensure name starts with a letter
    if not name[0].isalpha():
        name = f"page_{name}"
    # Convert to snake_case
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()
    # Ensure no duplicate underscores
    name = re.sub(r"_+", "_", name)
    # Remove trailing underscores
    name = name.strip("_")
    return name


def create_page_object_name(page: CrawlPage) -> str:
    """
    Create a name for a page object.
    Args:
        page: Crawled page
    Returns:
        str: Page object name
    """
    # Use title if available
    if page.title:
        name = page.title
    else:
        # Use URL path
        url_path = re.sub(r"^https?://[^/]+", "", page.url)
        url_path = url_path.strip("/")
        if not url_path:
            name = "HomePage"
        else:
            name = url_path.split("/")[-1]
            if not name:
                name = url_path.split("/")[-2]
    # Sanitize and convert to CamelCase
    words = sanitize_name(name).split("_")
    camel_case = "".join(word.title() for word in words)
    # Ensure it ends with "Page"
    if not camel_case.endswith("Page"):
        camel_case += "Page"
    return camel_case


def create_element_name(element: CrawlElement) -> str:
    """
    Create a name for an element.
    Args:
        element: Crawled element
    Returns:
        str: Element name
    """
    # Use text content if available
    if element.text:
        name = element.text
    else:
        # Use attributes
        attr_id = element.attributes.get("id", "")
        attr_class = element.attributes.get("class", "")
        if attr_id:
            name = attr_id
        elif attr_class:
            name = attr_class.split()[0]
        else:
            name = element.element_type
    # Sanitize and ensure it starts with element type
    sanitized = sanitize_name(name)
    if element.element_type not in sanitized:
        sanitized = f"{element.element_type}_{sanitized}"
    return sanitized


def create_element_locator(element: CrawlElement) -> ElementLocator:
    """
    Create an element locator from a crawled element.
    Args:
        element: Crawled element
    Returns:
        ElementLocator: Element locator
    """
    return ElementLocator(
        name=create_element_name(element),
        selector=element.selector,
        selector_type="css",
        description=element.text or "",
        element_type=element.element_type,
    )


def create_page_object(page: CrawlPage) -> PageObject:
    """
    Create a page object from a crawled page.
    Args:
        page: Crawled page
    Returns:
        PageObject: Page object
    """
    # Create page object name
    name = create_page_object_name(page)
    file_name = sanitize_name(name).lower() + ".py"
    # Create page object
    page_object = PageObject(
        name=name, file_name=file_name, url=page.url, title=page.title
    )
    # Add required imports
    page_object.imports.add("from playwright.sync_api import Page, Locator, expect")
    # Add elements
    for element in page.elements:
        if element.is_visible and element.is_clickable:
            locator = create_element_locator(element)
            page_object.elements[locator.name] = locator
    # Add forms
    for form in page.forms:
        form_name = f"form_{len(page_object.forms) + 1}"
        form_elements: list[ElementLocator] = []
        # Add form fields
        for field in form.fields:
            if field.is_visible:
                locator = create_element_locator(field)
                form_elements.append(locator)
        # Add submit button
        if form.submit_button:
            submit_locator = create_element_locator(form.submit_button)
            form_elements.append(submit_locator)
        # Add form to page object
        if form_elements:
            page_object.forms[form_name] = form_elements
    # Add methods
    page_object.methods[
        "__init__"
    ] = """def __init__(self, page: Page) -> None:
        \"\"\"Initialize the page object.\"\"\"
        self.page = page"""
    page_object.methods["navigate"] = (
        """async def navigate(self) -> None:
        \"\"\"Navigate to the page.\"\"\"
        await self.page.goto("{url}")
        await self.page.wait_for_load_state("domcontentloaded")""".format(
            url=page.url
        )
    )
    # Add element getters
    for name, locator in page_object.elements.items():
        page_object.methods[f"get_{name}"] = (
            """async def get_{name}(self) -> Locator:
        \"\"\"Get the {name} element.\"\"\"
        return self.page.locator("{selector}")""".format(
                name=name, selector=locator.selector
            )
        )
    # Add form methods
    for form_name, form_elements in page_object.forms.items():
        field_assignments = "\n        ".join(
            f'await self.page.locator("{element.selector}").fill(data.get("{element.name}", ""))'
            for element in form_elements
            if element.element_type.startswith("input")
        )
        submit_element = next(
            (e for e in form_elements if e.element_type == "submit"), None
        )
        if submit_element and field_assignments:
            submit_action = (
                f'await self.page.locator("{submit_element.selector}").click()'
            )
            page_object.methods[
                f"fill_{form_name}"
            ] = f"""async def fill_{form_name}(self, data: dict) -> None:
        \"\"\"Fill the {form_name} form.\"\"\"
        {field_assignments}
        {submit_action}"""
    return page_object


def generate_page_object_file(
    page_object: PageObject, output_dir: str
) -> GeneratedFile:
    """
    Generate a page object file.
    Args:
        page_object: Page object to generate
        output_dir: Output directory
    Returns:
        GeneratedFile: Generated file
    """
    # Create file content
    content = """\"\"\"Page object for {name}.\"\"\"
{imports}
class {name}:
    \"\"\"Page object for {url}.\"\"\"
    {methods}
""".format(
        name=page_object.name,
        url=page_object.url,
        imports="\n".join(sorted(page_object.imports)),
        methods="\n\n    ".join(page_object.methods.values()),
    )
    # Create file path
    file_path = os.path.join(output_dir, "page_objects", page_object.file_name)
    return GeneratedFile(file_path=file_path, content=content, file_type="page_object")


def create_test_name(page_object: PageObject) -> str:
    """
    Create a test name from a page object.
    Args:
        page_object: Page object
    Returns:
        str: Test name
    """
    # Remove "Page" suffix
    name = page_object.name
    if name.endswith("Page"):
        name = name[:-4]
    # Add "Test" suffix
    return f"Test{name}"


def create_test_case(page_object: PageObject, test_name: str, case_type: str) -> str:
    """
    Create a test case.
    Args:
        page_object: Page object
        test_name: Test name
        case_type: Type of test case
    Returns:
        str: Test case implementation
    """
    if case_type == "navigation":
        return """async def test_{page_name}_navigation(page: Page) -> None:
    \"\"\"Test navigation to {page_name}.\"\"\"
    page_object = {page_object_name}(page)
    await page_object.navigate()
    # Verify page title
    expect(page).to_have_title(re.compile(r"{title}"))""".format(
            page_name=sanitize_name(page_object.name),
            page_object_name=page_object.name,
            title=re.escape(page_object.title) if page_object.title else ".*",
        )
    elif case_type == "elements":
        if not page_object.elements:
            return ""
        element_assertions = []
        for element_name, element in list(page_object.elements.items())[
            :5
        ]:  # Limit to 5 elements
            element_assertions.append(
                f"""
    # Verify {element_name} is visible
    element = await page_object.get_{element_name}()
    await expect(element).to_be_visible()"""
            )
        return """async def test_{page_name}_elements(page: Page) -> None:
    \"\"\"Test elements on {page_name}.\"\"\"
    page_object = {page_object_name}(page)
    await page_object.navigate()
    {element_assertions}""".format(
            page_name=sanitize_name(page_object.name),
            page_object_name=page_object.name,
            element_assertions="\n".join(element_assertions),
        )
    elif case_type == "form":
        if not page_object.forms:
            return ""
        # Use the first form
        form_name, form_elements = next(iter(page_object.forms.items()))
        # Create sample data
        sample_data = {}
        for element in form_elements:
            if element.element_type.startswith("input"):
                if "email" in element.name:
                    sample_data[element.name] = "test@example.com"
                elif "password" in element.name:
                    sample_data[element.name] = "Password123!"
                elif "name" in element.name:
                    sample_data[element.name] = "Test User"
                else:
                    sample_data[element.name] = f"test_{element.name}"
        if not sample_data:
            return ""
        sample_data_str = (
            "{\n        "
            + ",\n        ".join(
                f'"{name}": "{value}"' for name, value in sample_data.items()
            )
            + "\n    }"
        )
        return """async def test_{page_name}_form_submission(page: Page) -> None:
    \"\"\"Test form submission on {page_name}.\"\"\"
    page_object = {page_object_name}(page)
    await page_object.navigate()
    # Fill and submit form
    form_data = {sample_data}
    await page_object.fill_{form_name}(form_data)
    # Wait for navigation or response
    await page.wait_for_load_state("networkidle")""".format(
            page_name=sanitize_name(page_object.name),
            page_object_name=page_object.name,
            form_name=form_name,
            sample_data=sample_data_str,
        )
    return ""


def create_test_from_page_object(page_object: PageObject) -> GeneratedTest:
    """
    Create a test from a page object.
    Args:
        page_object: Page object
    Returns:
        GeneratedTest: Generated test
    """
    # Create test name
    test_name = create_test_name(page_object)
    file_name = f"test_{sanitize_name(page_object.name).lower()}.py"
    # Create test
    test = GeneratedTest(
        name=test_name, file_name=file_name, page_objects=[page_object.name]
    )
    # Add required imports
    test.imports.add("import re")
    test.imports.add("import pytest")
    test.imports.add("from playwright.sync_api import Page, expect")
    test.imports.add(
        f"from page_objects.{os.path.splitext(page_object.file_name)[0]} import"
        + f" {page_object.name}"
    )
    # Add test cases
    navigation_test = create_test_case(page_object, test_name, "navigation")
    if navigation_test:
        test.test_cases["navigation"] = navigation_test
    elements_test = create_test_case(page_object, test_name, "elements")
    if elements_test:
        test.test_cases["elements"] = elements_test
    form_test = create_test_case(page_object, test_name, "form")
    if form_test:
        test.test_cases["form"] = form_test
    return test


def generate_test_file(test: GeneratedTest, output_dir: str) -> GeneratedFile:
    """
    Generate a test file.
    Args:
        test: Test to generate
        output_dir: Output directory
    Returns:
        GeneratedFile: Generated file
    """
    # Create file content
    content = """\"\"\"Tests for {name}.\"\"\"
{imports}
{test_cases}
""".format(
        name=test.name,
        imports="\n".join(sorted(test.imports)),
        test_cases="\n\n\n".join(test.test_cases.values()),
    )
    # Create file path
    file_path = os.path.join(output_dir, "tests", test.file_name)
    return GeneratedFile(file_path=file_path, content=content, file_type="test")


def generate_conftest(browsers: list[str], output_dir: str) -> GeneratedFile:
    """
    Generate a pytest conftest.py file.
    Args:
        browsers: List of browsers to test
        output_dir: Output directory
    Returns:
        GeneratedFile: Generated file
    """
    # Create content
    content = """\"\"\"Pytest configuration.\"\"\"
from typing import list, Generator
import os
import pytest
from playwright.sync_api import Playwright, Browser, Page
@pytest.fixture(scope="session")
def browser_context_args() -> Dict:
    \"\"\"Fixture to set browser context args.\"\"\"
    return {{
        "viewport": {{"width": 1280, "height": 720}}
        "record_video_dir": os.path.join("{output_dir}", "videos")
    }}
@pytest.fixture(
    params=[{browser_params}],
    scope="session"
)
def browser_type_launch_args(request) -> Dict:
    \"\"\"Fixture to set browser launch args.\"\"\"
    return {{
        "headless": True
        "slow_mo": 100
        "timeout": 30000
        "args": ["--disable-gpu", "--no-sandbox"]
    }}
@pytest.fixture(scope="session")
def browser_name(request) -> str:
    \"\"\"Fixture to get browser name.\"\"\"
    return request.param
@pytest.fixture(scope="function")
def page(browser: Browser) -> Generator[Page, None, None]:
    \"\"\"Fixture to create a new page for each test.\"\"\"
    page = browser.new_page()
    yield page
    page.close()
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    \"\"\"Hook to capture screenshots on test failure.\"\"\"
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        try:
            page = item.funcargs["page"]
            screenshot_dir = os.path.join("{output_dir}", "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(
    screenshot_dir, f"{{item.nodeid.replace('/', '_')}}.png")
            page.screenshot(path=screenshot_path, full_page=True)
            # Also save trace if available
            trace_dir = os.path.join("{output_dir}", "traces")
            os.makedirs(trace_dir, exist_ok=True)
            trace_path = os.path.join(
    trace_dir, f"{{item.nodeid.replace('/', '_')}}.zip")
            page.context.tracing.stop(path=trace_path)
        except Exception as e:
            print(f"Failed to capture screenshot: {{e}}")
""".format(
        output_dir=output_dir,
        browser_params=", ".join(f'"{browser}"' for browser in browsers),
    )
    # Create file path
    file_path = os.path.join(output_dir, "tests", "conftest.py")
    return GeneratedFile(file_path=file_path, content=content, file_type="conftest")


def generate_init_files(directories: list[str]) -> list[GeneratedFile]:
    """
    Generate __init__.py files for directories.
    Args:
        directories: List of directories
    Returns:
        list[GeneratedFile]: Generated files
    """
    files = []
    for directory in directories:
        file_path = os.path.join(directory, "__init__.py")
        content = """\"\"\"Generated test files.\"\"\"
"""
        files.append(
            GeneratedFile(file_path=file_path, content=content, file_type="init")
        )
    return files


def write_generated_files(files: list[GeneratedFile]) -> None:
    """
    Write generated files to disk.
    Args:
        files: List of files to write
    """
    for file in files:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file.file_path), exist_ok=True)
        # Write file
        with open(file.file_path, "w", encoding="utf-8") as f:
            f.write(file.content)


def generate_tests(crawl_data: CrawlData, config: Config) -> list[GeneratedFile]:
    """
    Generate tests from crawl data.
    Args:
        crawl_data: Crawled website data
        config: Bot configuration
    Returns:
        list[GeneratedFile]: Generated files
    """
    # Create output directories
    timestamp = crawl_data.end_time
    test_dir = os.path.join(config.report.output_dir, "tests", timestamp)
    page_objects_dir = os.path.join(test_dir, "page_objects")
    tests_dir = os.path.join(test_dir, "tests")
    os.makedirs(page_objects_dir, exist_ok=True)
    os.makedirs(tests_dir, exist_ok=True)
    # Create directories for artifacts
    os.makedirs(os.path.join(test_dir, "screenshots"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "videos"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "traces"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "reports"), exist_ok=True)
    # Generate page objects
    page_objects = []
    for page in crawl_data.pages.values():
        if not page.has_errors and page.status_code < 400:
            page_object = create_page_object(page)
            page_objects.append(page_object)
    # Generate page object files
    page_object_files = []
    for page_object in page_objects:
        file = generate_page_object_file(page_object, test_dir)
        page_object_files.append(file)
    # Generate test files
    test_files = []
    for page_object in page_objects:
        test = create_test_from_page_object(page_object)
        if test.test_cases:
            file = generate_test_file(test, test_dir)
            test_files.append(file)
    # Generate conftest
    conftest = generate_conftest(config.test.browsers, test_dir)
    # Generate __init__.py files
    init_files = generate_init_files([test_dir, page_objects_dir, tests_dir])
    # Combine all files
    all_files = page_object_files + test_files + [conftest] + init_files
    # Write files
    write_generated_files(all_files)
    return all_files
