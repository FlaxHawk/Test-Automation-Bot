#!/usr/bin/env python3
"""Script to finalize fixes for the remaining linter issues."""

import re
from pathlib import Path


def fix_long_lines(content: str, max_length: int = 88) -> str:
    """Fix lines that exceed the maximum length."""
    lines = content.split("\n")
    result = []
    
    for line in lines:
        if len(line) <= max_length or line.strip().startswith("#"):
            result.append(line)
            continue
            
        # Handle string concatenation for HTML templates
        if "}" in line and "{" in line and ("f\"" in line or "f'" in line):
            # Split at a reasonable point - typically after a space near the limit
            split_pos = max_length - 10
            while split_pos > 0 and line[split_pos] != " ":
                split_pos -= 1
            
            if split_pos > 0:
                # For f-strings, split and use string concatenation
                if "f\"" in line:
                    result.append(line[:split_pos] + "\" +")
                    result.append("    f\"" + line[split_pos:])
                elif "f'" in line:
                    result.append(line[:split_pos] + "' +")
                    result.append("    f'" + line[split_pos:])
                else:
                    result.append(line)
            else:
                result.append(line)
        # Handle function calls by breaking at commas
        elif "(" in line and ")" in line and "," in line:
            open_idx = line.find("(")
            if open_idx > 0:
                prefix = line[:open_idx+1]
                suffix = line[open_idx+1:]
                # Calculate indentation
                indentation = " " * (len(prefix))
                
                # Split by commas
                parts = []
                current_part = ""
                in_quotes = False
                quote_char = None
                
                for char in suffix:
                    if char in ["'", "\""]:
                        if not in_quotes:
                            in_quotes = True
                            quote_char = char
                        elif char == quote_char:
                            in_quotes = False
                            quote_char = None
                    
                    current_part += char
                    
                    if char == "," and not in_quotes:
                        parts.append(current_part)
                        current_part = ""
                
                if current_part:
                    parts.append(current_part)
                
                # Reconstruct with line breaks
                new_line = prefix + parts[0].strip()
                for part in parts[1:]:
                    new_line += f"\n{indentation}" + part.strip()
                
                result.append(new_line)
            else:
                result.append(line)
        else:
            result.append(line)
    
    return "\n".join(result)


def fix_unused_args(content: str) -> str:
    """Fix unused function arguments by prefixing with underscore."""
    # Find ARG001 errors in the content
    arg001_pattern = r'ARG001 Unused function argument: `([^`]+)`'
    matches = re.findall(arg001_pattern, content)
    
    for arg in matches:
        # Replace function parameter with _parameter
        content = re.sub(
            rf"(\W)({re.escape(arg)})(\W)", 
            lambda m: m.group(1) + "_" + m.group(2) + m.group(3),
            content
        )
    
    return content


def fix_subprocess_calls(content: str) -> str:
    """Replace stdout=PIPE, stderr=PIPE with capture_output=True."""
    if "subprocess.run" in content and "subprocess.PIPE" in content:
        pipe_pattern = r'subprocess\.run\(\s*([^,]+),\s*.*?\s*stdout=subprocess\.PIPE,\s*stderr=subprocess\.PIPE'
        replacement = r'subprocess.run(\1, capture_output=True'
        content = re.sub(pipe_pattern, replacement, content)
        
        # Remove individual PIPE arguments if they weren't caught by the main pattern
        content = re.sub(r'stdout=subprocess\.PIPE,?\s*', '', content)
        content = re.sub(r'stderr=subprocess\.PIPE,?\s*', '', content)
    
    return content


def fix_not_in_style(content: str) -> str:
    """Replace 'not x in y' with 'x not in y' for better readability."""
    content = re.sub(r'not\s+([a-zA-Z0-9_\'\"]+)\s+in\s+', r'\1 not in ', content)
    return content


def fix_unnecessary_mode(content: str) -> str:
    """Remove unnecessary mode='r' in open() calls."""
    content = re.sub(r"open\(([^,]+),\s*['\"]r['\"],\s*", r"open(\1, ", content)
    return content


def fix_crawler_errors(content: str) -> str:
    """Fix specific errors in crawler.py."""
    # Fix line continuations in HTML strings
    if "input:not(" in content:
        content = content.replace(
            "\"input:not([type='submit']):not([type='button']):not([type='reset']), select, textarea\"",
            '"input:not([type=\'submit\']):not([type=\'button\']):not([type=\'reset\']), select, textarea"'
        )
    
    return content


def process_file(file_path: Path) -> None:
    """Process a single file, applying all fixes."""
    print(f"Processing {file_path}")
    
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
        
        # Apply fixes
        content = fix_long_lines(content)
        content = fix_unused_args(content)
        content = fix_subprocess_calls(content)
        content = fix_not_in_style(content)
        content = fix_unnecessary_mode(content)
        
        # Special case for crawler.py
        if file_path.name == "crawler.py":
            content = fix_crawler_errors(content)
        
        # Write back the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def main() -> None:
    """Run all fixers on the codebase."""
    # Process all Python files
    for py_file in Path('src').glob('**/*.py'):
        process_file(py_file)
    
    # Process our fix scripts
    for script_file in ['fix_syntax_errors.py', 'fix_imports.py', 'fix_github_actions.py', 'fix_ruff_errors.py']:
        if Path(script_file).exists():
            process_file(Path(script_file))
    
    print("All fixes applied. Now try running the GitHub action again.")


if __name__ == '__main__':
    main() 