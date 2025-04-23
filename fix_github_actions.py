#!/usr/bin/env python3
"""Script to fix the most critical issues flagged by GitHub Actions."""

from pathlib import Path
import re
def fix_typing_imports(content: str) -> str:
    """Fix deprecated typing imports."""
    # Remove typing imports that should be replaced with built-in types
    content = re.sub(r'from typing import ([^,
                     \n]*)(Dict|List|Set|Tuple)([^,
                     \n]*)(,
                     |\n)',
                     
                    r'from typing import \1\3\4', content)
    
    # Add missing imports if needed
    if 'dict[' in content.lower() and 'typing import dict' not in content.lower():
        content = content.replace('from typing import', 'from typing import dict,')
    if 'list[' in content.lower() and 'typing import list' not in content.lower():
        content = content.replace('from typing import', 'from typing import list,')
    if 'set[' in content.lower() and 'typing import set' not in content.lower():
        content = content.replace('from typing import', 'from typing import set,')
    if 'tuple[' in content.lower() and 'typing import tuple' not in content.lower():
        content = content.replace('from typing import', 'from typing import tuple,')
    
    # Clean up extra commas
    content = content.replace('from typing import ,', 'from typing import')
    content = re.sub(r'from typing import\s*,', 'from typing import', content)
    content = re.sub(r',\s*,', ',', content)
    content = re.sub(r',\s*\n', '\n', content)
    
    return content


def fix_typing_annotations(content: str) -> str:
    """Replace old-style type annotations."""
    # Replace list[X] with list[X], dict[X, Y] with dict[X, Y], etc.
    content = re.sub(r'List\[', 'list[', content)
    content = re.sub(r'Dict\[', 'dict[', content)
    content = re.sub(r'Set\[', 'set[', content)
    content = re.sub(r'Tuple\[', 'tuple[', content)
    content = re.sub(r'Optional\[([^]]+)\]', r'\1 | None', content)
    
    return content


def fix_unused_function_args(content: str) -> str:
    """Fix unused function arguments by prefixing with underscore."""
    # Find function definitions
    pattern = r'def ([a-zA-Z0-9_]+)\s*\((.*?)\):'
    
    def replace_args(match: str) -> None:
        func_name = match.group(1)
        args = match.group(2)
        
        # ARG001 errors in the error list
        arg001_errors = re.findall(r'ARG001 Unused function argument: `([^`]+)`',
                                   content)
        
        # Replace unused args with _arg
        for arg in arg001_errors:
            # Make sure arg is an actual parameter (not a regex false positive)
            arg_pattern = r'([,\(]\s*)(' + re.escape(arg) + r')(\s*[,:\)])'
            args = re.sub(arg_pattern, r'\1_\2\3', args)
        
        return f'def {func_name}({args}):'
    
    content = re.sub(pattern, replace_args, content)
    
    return content


def fix_long_lines(content: str, max_length: int = 88) -> str:
    """Fix some simple long lines by breaking them at commas."""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        if len(line) > max_length and ',' in line and not line.strip().startswith('#'):
            if '(' in line and ')' in line:
                # Break import lines after commas
                if 'import' in line:
                    parts = line.split('import ', 1)
                    if len(parts) > 1:
                        prefix = parts[0] + 'import '
                        imports = parts[1]
                        indentation = ' ' * len(prefix)
                        imports_list = imports.split(',')
                        formatted_imports = [imports_list[0]]
                        current_line = imports_list[0]
                        
                        for imp in imports_list[1:]:
                            if len(prefix + current_line + ',' + imp) > max_length:
                                formatted_imports.append('\n' + indentation + imp.strip())
                                current_line = imp.strip()
                            else:
                                current_line += ',' + imp
                                formatted_imports[-1] += ',' + imp
                        
                        line = prefix + ','.join(formatted_imports)
                # Function arguments
                else:
                    open_idx = line.find('(')
                    if open_idx > 0:
                        prefix = line[:open_idx+1]
                        indentation = ' ' * (len(prefix))
                        suffix = line[open_idx+1:]
                        # Break the line at a comma
                        comma_idx = suffix.find(',')
                        if comma_idx > 0:
                            line = prefix + suffix[:comma_idx+1] + '\n' + indentation + suffix[comma_idx+1:].lstrip()
        
        result.append(line)
    
    return '\n'.join(result)


def process_file(file_path: str) -> str:
    """Process a single Python file."""
    with open(file_path, encoding='utf-8') as f:
        content = f.read()
    
    # Apply fixes
    content = fix_typing_imports(content)
    content = fix_typing_annotations(content)
    content = fix_unused_function_args(content)
    content = fix_long_lines(content)
    
    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def main() -> None:
    """Main function."""
    # Get the src directory
    src_dir = Path('src')
    
    # Find all Python files
    py_files = list(src_dir.glob('**/*.py'))
    
    # Process each file
    processed = 0
    for file_path in py_files:
        print(f"Processing {file_path}")
        if process_file(file_path):
            processed += 1
    
    print(f"Processed {processed} files")
    print("Now try running GitHub Actions again")


if __name__ == '__main__':
    main() 