"""Report generator module for creating test reports."""

import datetime
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from website_test_bot.config import Config
from website_test_bot.runner.models import TestResults, TestCase, TestFile


def generate_summary_json(test_results: TestResults, output_path: str) -> str:
    """
    Generate a summary JSON file.
    
    Args:
        test_results: Test results
        output_path: Output path for the summary file
        
    Returns:
        str: Path to the generated file
    """
    # Create summary data
    summary = {
        "timestamp": datetime.datetime.now().isoformat(),
        "summary": test_results.summary,
        "browsers": test_results.browsers,
        "files": [
            {
                "path": file.file_path,
                "passed": sum(1 for tc in file.test_cases if tc.status == "passed"),
                "failed": sum(1 for tc in file.test_cases if tc.status == "failed"),
                "skipped": sum(1 for tc in file.test_cases if tc.status == "skipped"),
                "duration": file.duration
            }
            for file in test_results.test_files
        ]
    }
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    return output_path


def copy_report_files(test_results: TestResults, output_dir: str) -> Dict[str, str]:
    """
    Copy report files to the output directory.
    
    Args:
        test_results: Test results
        output_dir: Output directory
        
    Returns:
        Dict[str, str]: Mapping of report type to file path
    """
    report_files = {}
    
    # Copy HTML report
    if test_results.html_report:
        html_dest = os.path.join(output_dir, "report.html")
        shutil.copy2(test_results.html_report, html_dest)
        report_files["html"] = html_dest
    
    # Copy JUnit report
    if test_results.junit_report:
        junit_dest = os.path.join(output_dir, "report.xml")
        shutil.copy2(test_results.junit_report, junit_dest)
        report_files["junit"] = junit_dest
    
    return report_files


def collect_screenshots(test_results: TestResults, output_dir: str) -> List[str]:
    """
    Collect screenshots for failed tests.
    
    Args:
        test_results: Test results
        output_dir: Output directory
        
    Returns:
        List[str]: List of screenshot paths
    """
    screenshot_dir = os.path.join(output_dir, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    screenshot_paths = []
    
    # Collect screenshots for all failed tests
    for test_file in test_results.test_files:
        for test_case in test_file.test_cases:
            if test_case.status == "failed" and test_case.screenshot_path:
                # Create filename
                base_name = os.path.basename(test_case.screenshot_path)
                dest_path = os.path.join(screenshot_dir, base_name)
                
                # Copy file
                shutil.copy2(test_case.screenshot_path, dest_path)
                screenshot_paths.append(dest_path)
    
    return screenshot_paths


def collect_videos(test_results: TestResults, output_dir: str) -> List[str]:
    """
    Collect videos for tests.
    
    Args:
        test_results: Test results
        output_dir: Output directory
        
    Returns:
        List[str]: List of video paths
    """
    video_dir = os.path.join(output_dir, "videos")
    os.makedirs(video_dir, exist_ok=True)
    
    video_paths = []
    processed_videos = set()
    
    # Collect videos for all tests
    for test_file in test_results.test_files:
        for test_case in test_file.test_cases:
            if test_case.video_path and test_case.video_path not in processed_videos:
                # Create filename
                base_name = os.path.basename(test_case.video_path)
                dest_path = os.path.join(video_dir, base_name)
                
                # Copy file
                shutil.copy2(test_case.video_path, dest_path)
                video_paths.append(dest_path)
                processed_videos.add(test_case.video_path)
    
    return video_paths


def collect_traces(test_results: TestResults, output_dir: str) -> List[str]:
    """
    Collect traces for failed tests.
    
    Args:
        test_results: Test results
        output_dir: Output directory
        
    Returns:
        List[str]: List of trace paths
    """
    trace_dir = os.path.join(output_dir, "traces")
    os.makedirs(trace_dir, exist_ok=True)
    
    trace_paths = []
    
    # Collect traces for all failed tests
    for test_file in test_results.test_files:
        for test_case in test_file.test_cases:
            if test_case.status == "failed" and test_case.trace_path:
                # Create filename
                base_name = os.path.basename(test_case.trace_path)
                dest_path = os.path.join(trace_dir, base_name)
                
                # Copy file
                shutil.copy2(test_case.trace_path, dest_path)
                trace_paths.append(dest_path)
    
    return trace_paths


def create_archive(base_dir: str, output_path: str) -> str:
    """
    Create a ZIP archive of the report directory.
    
    Args:
        base_dir: Base directory to archive
        output_path: Output path for the archive
        
    Returns:
        str: Path to the archive
    """
    # Create archive
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(base_dir):
            for file in files:
                # Get full path
                file_path = os.path.join(root, file)
                
                # Get relative path
                rel_path = os.path.relpath(file_path, os.path.dirname(base_dir))
                
                # Add to archive
                zipf.write(file_path, rel_path)
    
    return output_path


def generate_html_index(
    test_results: TestResults,
    report_files: Dict[str, str],
    artifacts: Dict[str, List[str]],
    output_path: str
) -> str:
    """
    Generate an HTML index file.
    
    Args:
        test_results: Test results
        report_files: Mapping of report type to file path
        artifacts: Mapping of artifact type to file paths
        output_path: Output path for the index file
        
    Returns:
        str: Path to the generated file
    """
    # Count artifacts
    num_screenshots = len(artifacts.get("screenshots", []))
    num_videos = len(artifacts.get("videos", []))
    num_traces = len(artifacts.get("traces", []))
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Test Bot Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #333; }}
        .summary {{ display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; }}
        .card {{ background: #f5f5f5; border-radius: 5px; padding: 15px; flex: 1; min-width: 200px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ margin-top: 0; }}
        .passed {{ color: #4caf50; }}
        .failed {{ color: #f44336; }}
        .skipped {{ color: #ff9800; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .links {{ margin-bottom: 20px; }}
        .links a {{ display: inline-block; margin-right: 15px; padding: 8px 15px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; }}
        .links a:hover {{ background: #0b7dda; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Website Test Bot Report</h1>
        <p>Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary">
            <div class="card">
                <h3>Test Results</h3>
                <p><span class="passed">Passed: {test_results.passed}</span></p>
                <p><span class="failed">Failed: {test_results.failed}</span></p>
                <p><span class="skipped">Skipped: {test_results.skipped}</span></p>
                <p>Total: {test_results.passed + test_results.failed + test_results.skipped}</p>
                <p>Duration: {test_results.duration:.2f}s</p>
            </div>
            
            <div class="card">
                <h3>Browsers</h3>
                {''.join(f'<p>{browser}: {count}</p>' for browser, count in test_results.browsers.items())}
            </div>
            
            <div class="card">
                <h3>Artifacts</h3>
                <p>Screenshots: {num_screenshots}</p>
                <p>Videos: {num_videos}</p>
                <p>Traces: {num_traces}</p>
            </div>
        </div>
        
        <div class="links">
            <h2>Reports</h2>
            {'<a href="report.html" target="_blank">HTML Report</a>' if 'html' in report_files else ''}
            {'<a href="report.xml" target="_blank">JUnit Report</a>' if 'junit' in report_files else ''}
            <a href="summary.json" target="_blank">Summary JSON</a>
        </div>
        
        <h2>Test Files</h2>
        <table>
            <tr>
                <th>File</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Skipped</th>
                <th>Duration</th>
            </tr>
            {''.join(f'''<tr>
                <td>{os.path.basename(file.file_path)}</td>
                <td class="passed">{sum(1 for tc in file.test_cases if tc.status == 'passed')}</td>
                <td class="failed">{sum(1 for tc in file.test_cases if tc.status == 'failed')}</td>
                <td class="skipped">{sum(1 for tc in file.test_cases if tc.status == 'skipped')}</td>
                <td>{file.duration:.2f}s</td>
            </tr>''' for file in test_results.test_files)}
        </table>
        
        {f'''<div class="links">
            <h2>Screenshots</h2>
            {''.join(f'<a href="{os.path.relpath(screenshot, os.path.dirname(output_path))}" target="_blank">{os.path.basename(screenshot)}</a> ' for screenshot in artifacts.get('screenshots', []))}
        </div>''' if artifacts.get('screenshots') else ''}
        
        {f'''<div class="links">
            <h2>Videos</h2>
            {''.join(f'<a href="{os.path.relpath(video, os.path.dirname(output_path))}" target="_blank">{os.path.basename(video)}</a> ' for video in artifacts.get('videos', []))}
        </div>''' if artifacts.get('videos') else ''}
        
        {f'''<div class="links">
            <h2>Traces</h2>
            {''.join(f'<a href="{os.path.relpath(trace, os.path.dirname(output_path))}" target="_blank">{os.path.basename(trace)}</a> ' for trace in artifacts.get('traces', []))}
        </div>''' if artifacts.get('traces') else ''}
    </div>
</body>
</html>
"""
    
    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return output_path


def generate_report(test_results: TestResults, config: Config) -> str:
    """
    Generate a report from test results.
    
    Args:
        test_results: Test results
        config: Bot configuration
        
    Returns:
        str: Path to the report
    """
    # Create timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create output directory
    output_dir = os.path.join(config.report.output_dir, "report", timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy report files
    report_files = copy_report_files(test_results, output_dir)
    
    # Collect artifacts
    artifacts = {}
    
    if config.report.include_screenshots:
        artifacts["screenshots"] = collect_screenshots(test_results, output_dir)
    
    if config.report.include_videos:
        artifacts["videos"] = collect_videos(test_results, output_dir)
    
    if config.report.include_traces:
        artifacts["traces"] = collect_traces(test_results, output_dir)
    
    # Generate summary JSON
    summary_path = generate_summary_json(test_results, os.path.join(output_dir, "summary.json"))
    
    # Generate HTML index
    index_path = generate_html_index(
        test_results,
        report_files,
        artifacts,
        os.path.join(output_dir, "index.html")
    )
    
    # Create archive
    archive_path = os.path.join(config.report.output_dir, f"report_{timestamp}.zip")
    create_archive(output_dir, archive_path)
    
    return index_path 