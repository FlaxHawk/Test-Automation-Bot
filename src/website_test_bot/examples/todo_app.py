"""
Example test for the Playwright TodoMVC example.
This demonstrates how to write tests manually for comparison with the auto-generated tests.
"""

from playwright.sync_api import Page, expect
import pytest


class TodoPage:
    """Page object for the TodoMVC app."""

    def __init__(self, page: Page) -> None:
        """Initialize the page object."""
        self.page = page
        self.new_todo_input = page.locator(".new-todo")
        self.todo_items = page.locator(".todo-list li")
        self.todo_count = page.locator(".todo-count")
        self.clear_completed_button = page.locator(".clear-completed")
        self.filters = page.locator(".filters li a")
        self.complete_all = page.locator(".toggle-all")

    async def navigate(self) -> None:
        """Navigate to the TodoMVC app."""
        await self.page.goto("https://demo.playwright.dev/todomvc")
        await self.page.wait_for_load_state("networkidle")

    async def add_todo(self, text: str) -> None:
        """Add a new todo item."""
        await self.new_todo_input.fill(text)
        await self.new_todo_input.press("Enter")

    async def get_todo_count(self) -> int:
        """Get the count of items left."""
        text = await self.todo_count.text_content() or "0"
        return int(text.split(" ")[0])

    async def complete_item(self, index: int) -> None:
        """Complete a todo item by index."""
        await self.todo_items.nth(index).locator(".toggle").click()

    async def delete_item(self, index: int) -> None:
        """Delete a todo item by index."""
        # Hover to show the delete button
        await self.todo_items.nth(index).hover()
        await self.todo_items.nth(index).locator(".destroy").click()

    async def filter_todos(self, filter_type: str) -> None:
        """Filter todos by type (all, active, completed)."""
        filter_map = {"all": 0, "active": 1, "completed": 2}
        index = filter_map.get(filter_type.lower(), 0)
        await self.filters.nth(index).click()


@pytest.mark.parametrize("filter_type", ["All", "Active", "Completed"])
async def test_todo_filtering(page: Page, filter_type: str) -> None:
    """Test that todo filtering works."""
    todo_page = TodoPage(page)
    await todo_page.navigate()
    # Add three todos
    await todo_page.add_todo("Buy groceries")
    await todo_page.add_todo("Clean the house")
    await todo_page.add_todo("Pay bills")
    # Complete one todo
    await todo_page.complete_item(1)
    # Filter todos
    await todo_page.filter_todos(filter_type)
    # Verify the filter works
    if filter_type == "Active":
        expect(todo_page.todo_items).to_have_count(2)
    elif filter_type == "Completed":
        expect(todo_page.todo_items).to_have_count(1)
    else:  # All
        expect(todo_page.todo_items).to_have_count(3)


async def test_add_and_complete_todos(page: Page) -> None:
    """Test adding and completing todos."""
    todo_page = TodoPage(page)
    await todo_page.navigate()
    # Verify no todos initially
    expect(todo_page.todo_items).to_have_count(0)
    # Add todos
    await todo_page.add_todo("Task 1")
    await todo_page.add_todo("Task 2")
    await todo_page.add_todo("Task 3")
    # Verify todos were added
    expect(todo_page.todo_items).to_have_count(3)
    expect(await todo_page.get_todo_count()).to_equal(3)
    # Complete a todo
    await todo_page.complete_item(0)
    # Verify count updates
    expect(await todo_page.get_todo_count()).to_equal(2)
    # Delete a todo
    await todo_page.delete_item(1)
    # Verify count updates
    expect(todo_page.todo_items).to_have_count(2)
    expect(await todo_page.get_todo_count()).to_equal(1)


async def test_todo_item_editing(page: Page) -> None:
    """Test editing a todo item."""
    todo_page = TodoPage(page)
    await todo_page.navigate()
    # Add a todo
    await todo_page.add_todo("Original task")
    # Edit the todo
    await todo_page.todo_items.nth(0).dblclick()
    edit_input = todo_page.todo_items.nth(0).locator(".edit")
    await edit_input.fill("Edited task")
    await edit_input.press("Enter")
    # Verify the edit took effect
    expect(todo_page.todo_items.nth(0).locator("label")).to_have_text("Edited task")


# Example of how to use crawl_website_sync
# if __name__ == "__main__":
#     config = load_config()
#     crawl_data = crawl_website_sync("https://demo.playwright.dev/todomvc", config)
#     print(f"Discovered {len(crawl_data.pages)} pages")
