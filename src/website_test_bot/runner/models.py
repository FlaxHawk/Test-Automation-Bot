"""Models for the test runner module."""

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """
    Represents a test case result.
    Contains information about the test case and its result.
    """
    name: str = Field(..., description="Test case name")
    status: str = Field(..., description="Test status (passed, failed, skipped)")
    message: str | None = Field(None, description="Test message")
    duration: float = Field(0.0, description="Test duration in seconds")
    browser: str = Field(..., description="Browser used for the test")
    screenshot_path: str | None = Field(None, description="Path to screenshot")
    video_path: str | None = Field(None, description="Path to video")
    trace_path: str | None = Field(None, description="Path to trace")
    html_path: str | None = Field(None, description="Path to HTML result")
class TestFile(BaseModel):
    """
    Represents a test file result.
    Contains information about the test file and its test cases.
    """
    file_path: str = Field(..., description="Path to the test file")
    test_cases: list[TestCase] = Field(
        default_factory=list, description="Test cases in the file"
    )
    duration: float = Field(0.0, description="Total duration in seconds")
    error: str | None = Field(None, description="Error message if any")
class TestResults(BaseModel):
    """
    Contains all test results.
    Includes test files, test cases, and summary information.
    """
    passed: int = Field(0, description="Number of passed tests")
    failed: int = Field(0, description="Number of failed tests")
    skipped: int = Field(0, description="Number of skipped tests")
    duration: float = Field(0.0, description="Total duration in seconds")
    test_files: list[TestFile] = Field(
        default_factory=list, description="Test files"
    )
    browsers: dict[str, int] = Field(
        default_factory=dict, description="Tests per browser"
    )
    summary: dict[str, int] = Field(
        default_factory=dict, description="Summary information"
    )
    report_dir: str = Field("", description="Directory containing reports")
    html_report: str | None = Field(None, description="Path to HTML report")
    junit_report: str | None = Field(None, description="Path to JUnit report") 