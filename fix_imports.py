#!/usr/bin/env python3
"""Script to fix import issues in Python files."""

import re
from pathlib import Path


def fix_deprecated_typing_imports(content: str) -> str:
    """Replace deprecated typing imports with built-in types."""
    # Replace from typing import Dict, List, etc. with proper types
    content = re.sub(r'from typing import ([^,\n]*)Dict([^,\n]*)',
                     r'from typing import \1\2',
                     content)
    content = re.sub(r'from typing import ([^,\n]*)List([^,\n]*)',
                     r'from typing import \1\2',
                     content)
    content = re.sub(r'from typing import ([^,\n]*)Set([^,\n]*)',
                     r'from typing import \1\2',
                     content)
    content = re.sub(r'from typing import ([^,\n]*)Tuple([^,\n]*)',
                     r'from typing import \1\2',
                     content)
    content = re.sub(r'from typing import ([^,\n]*)Optional([^,\n]*)',
                     r'from typing import \1\2',
                     content)
    content = re.sub(r'from typing import ([^,\n]*)Union([^,\n]*)',
                     r'from typing import \1\2',
                     content)
    
    # Fix our fix script imports too
    if 'from typing import Dict, List, Optional, Tuple' in content:
        content = content.replace(
            'from typing import Dict, List, Optional, Tuple', 
            'from typing import Any  # Using built-in types instead of typing equivalents'
        )
    
    return content


def remove_unused_imports(content: str) -> str:
    """Remove imports that are marked as unused."""
    # Check for F401 errors in comments
    f401_pattern = r'# .*F401 .*`([^`]+)` imported but unused'
    unused_imports = re.findall(f401_pattern, content)
    
    for unused in unused_imports:
        # Remove if it's the only import
        content = re.sub(rf'from [^\n]+ import {unused}(\s+#' +
    f' .*F401.*)?[\r\n]', '', content)
        
        # If it's part of a multi-import, remove just that part
        content = re.sub(rf',\s*{unused}(\s+# .*F401.*)?', '', content)
        content = re.sub(rf'{unused},\s*', '', content)
    
    # Special handling for Path in reporter.py
    if 'from pathlib import Path' in content and 'Path' not in content.split('from pathlib import Path')[1]:
        content = content.replace('from pathlib import Path\n', '')
    
    return content


def fix_import_sorting(content: str) -> str:
    """Sort imports according to PEP8 style."""
    # This is simplified - for more thorough sorting, use isort or better yet, ruff's import fixer
    lines = content.split('\n')
    import_block_start = None
    import_block_end = None
    
    # Find import blocks
    for i, line in enumerate(lines):
        if import_block_start is None and line.startswith(('import ', 'from ')):
            import_block_start = i
        elif import_block_start is not None and not line.startswith(('import ',
                                                                    'from ')) and line.strip():
            import_block_end = i
            break
    
    # If no import block found or already at the end, return
    if import_block_start is None or import_block_end is None:
        return content
    
    # Extract and sort the import block
    import_lines = lines[import_block_start:import_block_end]
    
    # Sort standard library first, then third-party, then local modules
    std_libs = []
    third_party = []
    local_modules = []
    
    for line in import_lines:
        if not line.strip():  # Skip empty lines
            continue
        if line.startswith('from typing import') or line.startswith('import re') or line.startswith('import os'):
            std_libs.append(line)
        elif 'website_test_bot' in line:
            local_modules.append(line)
        else:
            third_party.append(line)
    
    # Sort each category
    std_libs.sort()
    third_party.sort()
    local_modules.sort()
    
    # Combine the sorted blocks with a blank line between categories
    sorted_imports = '\n'.join(std_libs)
    if std_libs and third_party:
        sorted_imports += '\n'
    sorted_imports += '\n'.join(third_party)
    if (std_libs or third_party) and local_modules:
        sorted_imports += '\n'
    sorted_imports += '\n'.join(local_modules)
    
    # Replace the original import block
    new_lines = lines[:import_block_start] + sorted_imports.split('\n') + lines[import_block_end:]
    
    return '\n'.join(new_lines)


def process_file(file_path: Path) -> None:
    """Process a single Python file."""
    print(f"Processing {file_path}")
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
        
        # Apply fixes
        content = fix_deprecated_typing_imports(content)
        content = remove_unused_imports(content)
        content = fix_import_sorting(content)
        
        # Write the file back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def main() -> None:
    """Main function to process all Python files."""
    # Process all Python files in the src directory
    for py_file in Path('src').glob('**/*.py'):
        process_file(py_file)
    
    # Process our fix scripts as well
    script_files = [
        Path('fix_syntax_errors.py'),
        Path('fix_github_actions.py'),
        Path('fix_ruff_errors.py')
    ]
    for script_file in script_files:
        if script_file.exists():
            process_file(script_file)
    
    print("Imports fixed. Now try running the GitHub action again.")


if __name__ == '__main__':
    main() 