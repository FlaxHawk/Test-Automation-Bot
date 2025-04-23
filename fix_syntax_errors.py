#!/usr/bin/env python3
"""Script to fix syntax errors and linting issues flagged by GitHub Actions."""

from typing import List, Optional, Tuple
import re
from pathlib import Path

def fix_runner_syntax(content: str) -> str:
    """Fix syntax errors in runner.py file."""
    # Fix missing comma in the list
    return content.replace(
        '--html", os.path.join(report_dir, "report.html")\n            "--self-contained-html"',
        '--html", os.path.join(report_dir, "report.html"),\n            "--self-contained-html"'
    )


def fix_reporter_syntax(content: str) -> str:
    """Fix syntax errors in reporter.py file."""
    # Fix missing commas in the dictionary
    fixed = content.replace(
        '"timestamp": datetime.datetime.now().isoformat()\n        "summary": test_results.summary',
        '"timestamp": datetime.datetime.now().isoformat(),\n        "summary": test_results.summary'
    )
    fixed = fixed.replace(
        '"summary": test_results.summary\n        "browsers": test_results.browsers',
        '"summary": test_results.summary,\n        "browsers": test_results.browsers'
    )
    
    return fixed


def fix_crawler_syntax(content: str) -> str:
    """Fix syntax errors in crawler.py file."""
    # Fix missing commas in arguments and fix line breaks with escapes
    fixed = content.replace(
        'form_selector=form_selector\n            action=action',
        'form_selector=form_selector,\n            action=action'
    )
    fixed = fixed.replace(
        'input:not(\n    [type=\'submit\'])',
        'input:not([type=\'submit\'])'
    )
    fixed = fixed.replace(
        'button:not(\n    [type])',
        'button:not([type])'
    )
    fixed = fixed.replace(
        'await element_handle.get_attribute(\n    "type")',
        'await element_handle.get_attribute("type")'
    )
    fixed = fixed.replace(
        '(\n    url_parts.scheme',
        '(url_parts.scheme'
    )
    fixed = fixed.replace(
        'viewport={\n    "width": config.test.viewport.width',
        'viewport={"width": config.test.viewport.width'
    )
    
    return fixed


def fix_generator_syntax(content: str) -> str:
    """Fix syntax errors in generator.py file."""
    # Fix missing commas in arguments and fix line breaks with escapes
    fixed = content.replace(
        'name=create_element_name(element)\n        selector=element.selector',
        'name=create_element_name(element),\n        selector=element.selector'
    )
    fixed = fixed.replace(
        "f'await self.page.locator(\n    \"{element.selector}\").fill(",
        "f'await self.page.locator(\"{element.selector}\").fill("
    )
    fixed = fixed.replace(
        "f'await self.page.locator(\n    \"{submit_element.selector}\").click()",
        "f'await self.page.locator(\"{submit_element.selector}\").click()"
    )
    fixed = fixed.replace(
        'list(\n    page_object.elements.items())[:5]',
        'list(page_object.elements.items())[:5]'
    )
    
    return fixed


def fix_typing_annotations(content: str) -> str:
    """Replace old-style typing annotations with new ones."""
    # Replace typing.X import statements
    content = re.sub(r'from typing import __([^,]*?)(Dict|List|Set|Tuple)__([^,]*?)(,|\n)',
                    r'from typing import \1\3\4', content)
    
    # Replace List[X] with list[X], Dict[X, Y] with dict[X, Y], etc.
    content = re.sub(r'List\[', 'list[', content)
    content = re.sub(r'Dict\[', 'dict[', content)
    content = re.sub(r'Set\[', 'set[', content)
    content = re.sub(r'Tuple\[', 'tuple[', content)
    
    # Replace Optional[X] with X | None
    content = re.sub(r'Optional\[__([^]]+)\]', r'\1 | None', content)
    
    return content


def fix_long_lines(content: str, max_length: int = 88) -> str:
    """Fix some long lines by breaking them or reformatting."""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        if len(line) > max_length and not line.strip().startswith('#'):
            # Try to break lines with function calls or parameters
            if "(" in line and ")" in line and "," in line:
                # Find open and closing parenthesis
                open_idx = line.find("(")
                if open_idx > 0:
                    prefix = line[:open_idx+1]
                    suffix = line[open_idx+1:]
                    # Split by commas and add line breaks
                    parts = suffix.split(",")
                    if len(parts) > 1:
                        indentation = " " * (len(prefix))
                        new_line = prefix + parts[0].strip() + ","
                        for part in parts[1:-1]:
                            new_line += f"\n{indentation}" + part.strip() + ","
                        new_line += f"\n{indentation}" + parts[-1].strip()
                        line = new_line
        
        result.append(line)
    
    return '\n'.join(result)


def fix_missing_commas(content: str) -> str:
    """Fix missing commas in function calls, lists, and dictionaries."""
    # Look for patterns where commas are missing between lines
    function_call_pattern = r'(\s+)([a-zA-Z0-9_]+=[^,\n]+)\n(\s+)([a-zA-Z0-9_]+=[^,\n]+)'
    content = re.sub(function_call_pattern, r'\1\2,\n\3\4', content)
    
    # Fix missing commas in cmd arrays
    cmd_pattern = r'(cmd = \[[^\]]+\])\n(\s+)([a-zA-Z0-9_]+)'
    content = re.sub(cmd_pattern, r'\1,\n\2\3', content)
    
    return content


def fix_unused_args(content: str) -> str:
    """Fix unused function arguments by prefixing with underscore."""
    # Find ARG001 errors in the file
    arg001_errors = re.findall(r'ARG001 Unused function argument: `__([^`]+)`', content)
    
    for arg in arg001_errors:
        # Replace the argument with prefixed underscore
        pattern = r'(\W)(' + re.escape(arg) + r')(\W)'
        content = re.sub(pattern, r'\1_\2\3', content)
    
    return content


def fix_open_mode(content: str) -> str:
    """Fix unnecessary open mode parameters."""
    # Replace redundant mode and encoding parameters
    content = re.sub(r"open\(__([^,]+),\s*'r',\s*encoding='utf-8'\)",
                     r"open(\1, encoding='utf-8')",
                     content)
    content = re.sub(r"open\(__([^,]+),\s*'r'\)", r"open(\1)", content)
    
    return content


def fix_missing_type_annotations(content: str) -> str:
    """Add missing return type annotations and function argument types."""
    # Find functions missing return types
    func_pattern = r'def ([a-zA-Z0-9_]+)\s*\((.*?)\):'
    
    def add_return_type(match):
        func_name = match.group(1)
        args = match.group(2)
        
        # Add parameter type hints
        typed_args = []
        for arg in args.split(','):
            arg = arg.strip()
            if arg and not ':' in arg and arg != 'self':
                typed_args.append(f"{arg}: str")
            else:
                typed_args.append(arg)
        
        typed_args_str = ', '.join(typed_args)
        
        # Determine appropriate return type
        # For simplicity, use a common default for each category
        if func_name.startswith('fix_') or func_name.startswith('process_'):
            return f"def {func_name}({typed_args_str}) -> str:"
        else:
            return f"def {func_name}({typed_args_str}) -> None:"
    
    content = re.sub(func_pattern, add_return_type, content)
    
    return content


def process_file(file_path: Path) -> None:
    """Process a single file to fix syntax and linting issues."""
    print(f"Processing {file_path}")
    
    with open(file_path, encoding='utf-8') as f:
        content = f.read()
    
    # Apply appropriate fixes based on file path
    if "runner/runner.py" in str(file_path):
        content = fix_runner_syntax(content)
    elif "reporter/reporter.py" in str(file_path):
        content = fix_reporter_syntax(content)
    elif "crawler/crawler.py" in str(file_path):
        content = fix_crawler_syntax(content)
    elif "generator/generator.py" in str(file_path):
        content = fix_generator_syntax(content)
    
    # Apply general fixes
    content = fix_typing_annotations(content)
    content = fix_missing_commas(content)
    content = fix_long_lines(content)
    content = fix_unused_args(content)
    content = fix_open_mode(content)
    
    # Save the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_existing_scripts() -> None:
    """Fix the linting errors in fix_github_actions.py and fix_ruff_errors.py."""
    script_files = ["fix_github_actions.py", "fix_ruff_errors.py"]
    
    for file_path in script_files:
        path = Path(file_path)
        if path.exists():
            with open(path, encoding='utf-8') as f:
                content = f.read()
            
            # Apply fixes
            content = fix_typing_annotations(content)
            content = fix_long_lines(content)
            content = fix_missing_type_annotations(content)
            content = fix_open_mode(content)
            
            # Remove unused imports
            if "fix_github_actions.py" in file_path:
                content = re.sub(r'import os\n',
                                 '',
                                 content) if "os.path" not in content else content
                content = re.sub(r'import sys\n',
                                 '',
                                 content) if "sys." not in content else content
            
            # Save fixes
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Fixed {file_path}")


def main() -> None:
    """Main function to fix all issues."""
    # Files with syntax errors
    syntax_error_files = [
        Path("src/website_test_bot/runner/runner.py"),
        Path("src/website_test_bot/reporter/reporter.py"),
        Path("src/website_test_bot/crawler/crawler.py"),
        Path("src/website_test_bot/generator/generator.py")
    ]
    
    # Process files with syntax errors first
    for file_path in syntax_error_files:
        if file_path.exists():
            process_file(file_path)
    
    # Fix the existing helper scripts
    fix_existing_scripts()
    
    # Process all Python files for general linting issues
    src_dir = Path('src')
    py_files = src_dir.glob('**/*.py')
    
    for file_path in py_files:
        if file_path not in syntax_error_files:
            process_file(file_path)
    
    print("Finished fixing errors. Now try running the GitHub action again.")


if __name__ == '__main__':
    main() 