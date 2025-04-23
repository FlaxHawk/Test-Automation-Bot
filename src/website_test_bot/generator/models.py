"""Models for the test generator module."""

from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ElementLocator(BaseModel):
    """
    Represents a locator for a page element.
    
    Contains information about how to locate an element in the DOM.
    """
    
    name: str = Field(..., description="Name of the element")
    selector: str = Field(..., description="CSS or XPath selector for the element")
    selector_type: str = Field("css", description="Type of selector (css, xpath)")
    description: str = Field("", description="Description of the element")
    element_type: str = Field("", description="Type of element (button, link, etc.)")


class PageObject(BaseModel):
    """
    Represents a page object for a test.
    
    Contains information about the page and its elements.
    """
    
    name: str = Field(..., description="Class name for the page object")
    file_name: str = Field(..., description="File name for the page object")
    url: str = Field(..., description="URL of the page")
    title: str = Field("", description="Page title")
    elements: Dict[str, ElementLocator] = Field(
        default_factory=dict, description="Element locators by name"
    )
    forms: Dict[str, List[ElementLocator]] = Field(
        default_factory=dict, description="Form elements by form name"
    )
    methods: Dict[str, str] = Field(
        default_factory=dict, description="Method implementations by name"
    )
    imports: Set[str] = Field(
        default_factory=set, description="Required imports"
    )


class GeneratedTest(BaseModel):
    """
    Represents a generated test.
    
    Contains information about the test and its test cases.
    """
    
    name: str = Field(..., description="Test name")
    file_name: str = Field(..., description="File name for the test")
    page_objects: List[str] = Field(
        default_factory=list, description="Page objects used in the test"
    )
    test_cases: Dict[str, str] = Field(
        default_factory=dict, description="Test case implementations by name"
    )
    imports: Set[str] = Field(
        default_factory=set, description="Required imports"
    )


class GeneratedFile(BaseModel):
    """
    Represents a generated file.
    
    Contains information about the file and its content.
    """
    
    file_path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="Content of the file")
    file_type: str = Field(..., description="Type of file (page_object, test, etc.)") 