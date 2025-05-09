"""Test runner module for executing generated tests."""

import os
from typing import List, Tuple, Dict
from .models import TestCase, TestFile, TestResults
import subprocess
import sys
import xml.etree.ElementTree as ET
from website_test_bot.config import Config
from website_test_bot.generator.models import GeneratedFile


def get_test_files(test_dir: str) -> List[str]:
    """
    Get all test files in a directory.
    Args:
        test_dir: Directory containing tests
    Returns:
        List[str]: List of test file paths
    """
    test_files = []
    tests_path = os.path.join(test_dir, "tests")
    if os.path.exists(tests_path):
        for file_name in os.listdir(tests_path):
            if file_name.startswith("test_") and file_name.endswith(".py"):
                test_files.append(os.path.join(tests_path, file_name))
    return test_files


def setup_pytest_environment(
    test_dir: str, config: Config
) -> Tuple[List[str], Dict[str, str]]:
    """
    Set up the Pytest environment.
    Args:
        test_dir: Directory containing tests
        config: Bot configuration
    Returns:
        Tuple[List[str], Dict[str, str]]: Pytest arguments and environment variables
    """
    # Create reports directory
    report_dir = os.path.join(test_dir, "reports")
    os.makedirs(report_dir, exist_ok=True)

    # Configure report arguments
    report_args = []
    if config.report.format in ["html", "both"]:
        html_report_path = os.path.join(report_dir, "report.html")
        # Use absolute path to avoid path resolution issues
        html_report_path = os.path.abspath(html_report_path)
        report_args.extend(["--html", html_report_path, "--self-contained-html"])
    if config.report.format in ["junit", "both"]:
        junit_report_path = os.path.join(report_dir, "report.xml")
        # Use absolute path to avoid path resolution issues
        junit_report_path = os.path.abspath(junit_report_path)
        report_args.extend(["--junitxml", junit_report_path])

    # Configure Pytest arguments
    pytest_args = [
        "-v",  # Verbose output
    ]

    # Add rootdir only if we're not in GitHub Actions
    # In GitHub Actions, we'll let pytest find the root on its own
    if "GITHUB_ACTIONS" not in os.environ:
        pytest_args.extend(
            [
                "--rootdir",
                test_dir,  # Explicitly set the root directory
            ]
        )

    # Always use importlib mode for more reliable imports
    pytest_args.append("--import-mode=importlib")

    # Add concurrency settings if more than one worker requested
    if config.test.concurrency > 1:
        pytest_args.extend(
            [
                f"--numprocesses={config.test.concurrency}",
                f"--maxfail={config.test.concurrency * 2}",
            ]
        )

    # Check if pytest-rerunfailures is installed
    try:
        import pytest_rerunfailures

        # Only add reruns if the plugin is available
        if config.test.retry_failed > 0:
            pytest_args.append(f"--reruns={config.test.retry_failed}")
    except ImportError:
        print(
            "Warning: pytest-rerunfailures not installed, --reruns flag will not be used"
        )

    # Add report arguments
    pytest_args.extend(report_args)

    # Set environment variables
    env_vars = os.environ.copy()

    # Ensure PYTHONPATH includes the test directory and its parent
    test_parent_dir = os.path.dirname(test_dir)
    pythonpath = f"{test_dir}:{test_parent_dir}"

    if "PYTHONPATH" in env_vars and env_vars["PYTHONPATH"]:
        pythonpath = f"{pythonpath}:{env_vars['PYTHONPATH']}"

    env_vars["PYTHONPATH"] = pythonpath

    # Ensure headless is always true in GitHub Actions
    force_headless = "GITHUB_ACTIONS" in os.environ
    headless = force_headless or config.test.headless

    if not headless:
        env_vars["HEADLESS"] = "0"
    else:
        env_vars["HEADLESS"] = "1"  # Explicitly set headless mode

    if config.test.traces == "on":
        env_vars["PWTRACING"] = "1"
    elif config.test.traces == "on-failure":
        env_vars["PWTRACING"] = "on-failure"
    if config.test.video:
        env_vars["PWVIDEO"] = "1"

    return pytest_args, env_vars


def run_pytest(
    test_files: List[str], test_dir: str, config: Config
) -> subprocess.CompletedProcess:
    """
    Run Pytest on test files.
    Args:
        test_files: List of test files to run
        test_dir: Directory containing tests
        config: Bot configuration
    Returns:
        subprocess.CompletedProcess: Completed process
    """
    pytest_args, env_vars = setup_pytest_environment(test_dir, config)

    # Properly set PYTHONPATH to include the test directory
    # Make sure we use absolute paths to avoid issues in CI
    abs_test_dir = os.path.abspath(test_dir)
    env_vars["PYTHONPATH"] = f"{abs_test_dir}:{env_vars.get('PYTHONPATH', '')}"

    # Use pytest directly with the test directory instead of specific files
    # This allows pytest to handle module imports and test discovery properly
    if not test_files:
        print("No test files found!")
        return subprocess.CompletedProcess(
            [], returncode=1, stdout="", stderr="No test files found"
        )

    # Use absolute paths for test files
    abs_test_files = [os.path.abspath(f) for f in test_files]

    # Build command
    cmd = [sys.executable, "-m", "pytest"] + pytest_args + abs_test_files

    # Print debug information
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {abs_test_dir}")
    print(f"PYTHONPATH: {env_vars.get('PYTHONPATH', 'Not set')}")
    print(f"Test files: {abs_test_files}")

    # Create init files in all parent directories to ensure proper imports
    parent_dirs = set()
    for test_file in abs_test_files:
        dir_path = os.path.dirname(test_file)
        while dir_path and dir_path.startswith(abs_test_dir):
            parent_dirs.add(dir_path)
            dir_path = os.path.dirname(dir_path)

    for dir_path in parent_dirs:
        init_file = os.path.join(dir_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write('"""Generated test directory."""\n')

    # Create a debug script to help with imports
    with open(os.path.join(abs_test_dir, "debug_imports.py"), "w") as f:
        f.write(
            """
import sys
import os
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")
try:
    import page_objects
    print("Successfully imported page_objects")
except ImportError as e:
    print(f"Failed to import page_objects: {e}")
"""
        )

    # Run debug script
    subprocess.run(
        [sys.executable, os.path.join(abs_test_dir, "debug_imports.py")],
        capture_output=True,
        text=True,
        cwd=abs_test_dir,
        env=env_vars,
    )

    # Run command
    process = subprocess.run(
        cmd, capture_output=True, text=True, cwd=abs_test_dir, env=env_vars
    )

    # Print output for debugging
    print(f"Pytest return code: {process.returncode}")

    if process.stdout:
        print("Pytest stdout:")
        print(process.stdout)

    if process.stderr:
        print("Pytest stderr:")
        print(process.stderr)

    return process


def parse_junit_report(report_path: str) -> List[TestCase]:
    """
    Parse a JUnit XML report.
    Args:
        report_path: Path to JUnit XML report
    Returns:
        List[TestCase]: List of test cases
    """
    test_cases = []
    # Parse XML
    try:
        tree = ET.parse(report_path)
        root = tree.getroot()
        # Find all testcase elements
        for testcase_elem in root.findall(".//testcase"):
            # Extract test case information
            name = testcase_elem.get("name", "")
            classname = testcase_elem.get("classname", "")
            duration = float(testcase_elem.get("time", "0"))
            # Determine browser from classname
            browser = "chromium"  # Default
            for browser_name in ["chromium", "firefox", "webkit"]:
                if browser_name in classname.lower():
                    browser = browser_name
                    break
            # Determine status
            status = "passed"
            message = None
            failure_elem = testcase_elem.find("failure")
            if failure_elem is not None:
                status = "failed"
                message = failure_elem.get("message", "")
            skipped_elem = testcase_elem.find("skipped")
            if skipped_elem is not None:
                status = "skipped"
                message = skipped_elem.get("message", "")
            # Create test case
            test_case = TestCase(
                name=name,
                status=status,
                message=message,
                duration=duration,
                browser=browser,
            )
            # Add to list
            test_cases.append(test_case)
    except Exception as e:
        # Handle parsing errors
        print(f"Error parsing JUnit report: {e}")
    return test_cases


def collect_artifacts(test_dir: str, test_cases: List[TestCase]) -> None:
    """
    Collect artifacts for test cases.
    Args:
        test_dir: Directory containing tests
        test_cases: List of test cases
    """
    # Define artifact directories
    screenshots_dir = os.path.join(test_dir, "screenshots")
    videos_dir = os.path.join(test_dir, "videos")
    traces_dir = os.path.join(test_dir, "traces")
    # Collect artifacts for each test case
    for test_case in test_cases:
        # Skip if not failed (only failed tests have screenshots)
        if test_case.status != "failed":
            continue
        # Generate artifact names
        test_id = f"{test_case.name}_{test_case.browser}"
        test_id = test_id.replace("/", "_").replace(":", "_")
        # Look for screenshot
        screenshot_path = os.path.join(screenshots_dir, f"{test_id}.png")
        if os.path.exists(screenshot_path):
            test_case.screenshot_path = screenshot_path
        # Look for trace
        trace_path = os.path.join(traces_dir, f"{test_id}.zip")
        if os.path.exists(trace_path):
            test_case.trace_path = trace_path
    # Collect videos (one per browser context)
    if os.path.exists(videos_dir):
        for file_name in os.listdir(videos_dir):
            if file_name.endswith(".webm"):
                # Determine browser from filename
                browser = "chromium"  # Default
                for browser_name in ["chromium", "firefox", "webkit"]:
                    if browser_name in file_name.lower():
                        browser = browser_name
                        break
                # Assign video to all test cases for that browser
                video_path = os.path.join(videos_dir, file_name)
                for test_case in test_cases:
                    if test_case.browser == browser:
                        test_case.video_path = video_path


def create_test_results(
    test_cases: List[TestCase], test_dir: str, process: subprocess.CompletedProcess
) -> TestResults:
    """
    Create test results from test cases.
    Args:
        test_cases: List of test cases
        test_dir: Directory containing tests
        process: Completed process
    Returns:
        TestResults: Test results
    """
    # Create test results
    results = TestResults(
        passed=sum(1 for tc in test_cases if tc.status == "passed"),
        failed=sum(1 for tc in test_cases if tc.status == "failed"),
        skipped=sum(1 for tc in test_cases if tc.status == "skipped"),
        duration=sum(tc.duration for tc in test_cases),
        report_dir=os.path.join(test_dir, "reports"),
    )
    # Set report paths
    html_report = os.path.join(results.report_dir, "report.html")
    if os.path.exists(html_report):
        results.html_report = html_report
    junit_report = os.path.join(results.report_dir, "report.xml")
    if os.path.exists(junit_report):
        results.junit_report = junit_report
    # Group test cases by file
    test_files: Dict[str, List[TestCase]] = {}
    for test_case in test_cases:
        # Extract file path from test case name
        file_path = test_case.name.split("::")[0]
        if file_path not in test_files:
            test_files[file_path] = []
        test_files[file_path].append(test_case)
    # Create test files
    for file_path, file_test_cases in test_files.items():
        test_file = TestFile(
            file_path=file_path,
            test_cases=file_test_cases,
            duration=sum(tc.duration for tc in file_test_cases),
        )
        results.test_files.append(test_file)
    # Calculate browser statistics
    for test_case in test_cases:
        if test_case.browser not in results.browsers:
            results.browsers[test_case.browser] = 0
        results.browsers[test_case.browser] += 1
    # Add summary information
    results.summary = {
        "total": len(test_cases),
        "passed": results.passed,
        "failed": results.failed,
        "skipped": results.skipped,
        "duration": results.duration,
        "browsers": len(results.browsers),
    }
    return results


def run_tests(generated_files: List[GeneratedFile], config: Config) -> TestResults:
    """
    Run tests from generated files.
    Args:
        generated_files: List of generated files
        config: Bot configuration
    Returns:
        TestResults: Test results
    """
    # Get test directory
    test_dir = os.path.dirname(os.path.dirname(generated_files[0].file_path))
    # Get test files
    test_files = get_test_files(test_dir)
    # Run tests
    process = run_pytest(test_files, test_dir, config)
    # Parse JUnit report
    junit_path = os.path.join(test_dir, "reports", "report.xml")
    test_cases = []
    if os.path.exists(junit_path):
        test_cases = parse_junit_report(junit_path)
    # If no test cases, create default
    if not test_cases:
        for file_path in test_files:
            test_cases.append(
                TestCase(
                    name=os.path.basename(file_path),
                    status="failed" if process.returncode != 0 else "passed",
                    message=process.stderr if process.returncode != 0 else None,
                    duration=0.0,
                    browser="chromium",
                )
            )
    # Collect artifacts
    collect_artifacts(test_dir, test_cases)
    # Create test results
    results = create_test_results(test_cases, test_dir, process)
    return results
