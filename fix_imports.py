#!/usr/bin/env python3
"""Script to fix import sorting and cleanup typing imports."""

from pathlib import Path
import re
def fix_typing_imports(content: str) -> str:
    """Fix deprecated typing imports."""
    # Replace old-style typing imports with new ones
    content = re.sub(r'from typing import list', 'from typing import list', content)
    content = re.sub(r'from typing import dict', 'from typing import dict', content)
    content = re.sub(r'from typing import set', 'from typing import set', content)
    content = re.sub(r'from typing import tuple', 'from typing import tuple', content)
    
    # Replace if used as parameter in import list
    content = re.sub(r'from typing import ([^,\n]*)', r'from typing import \1, list', content)
    content = re.sub(r'from typing import ([^,\n]*)', r'from typing import \1, dict', content)
    content = re.sub(r'from typing import ([^,\n]*)', r'from typing import \1, set', content)
    content = re.sub(r'from typing import ([^,\n]*)', r'from typing import \1, tuple', content)
    
    # Remove unused typing imports
    unused_patterns = [
        r'(?=[^A-Za-z0-9_])', r'(?=[^A-Za-z0-9_])', 
        r'(?=[^A-Za-z0-9_])', r'(?=[^A-Za-z0-9_])',
        r'(?=[^A-Za-z0-9_])', r'(?=[^A-Za-z0-9_])',
        r'(?=[^A-Za-z0-9_])'
    ]
    
    for pattern in unused_patterns:
        content = re.sub(pattern, '', content)
    
    # If importing but not using any from typing, remove the import
    if 'from typing import' in content and re.search(r'from typing import\s*\n', content):
        content = re.sub(r'from typing import\s*\n', '', content)
    
    return content


def clean_unused_imports(content: str) -> str:
    """Remove imports marked as unused with the F401 error."""
    # Find all imports marked as unused
    unused_imports = re.findall(r'([A-Za-z0-9_]+) imported but unused', content)
    
    for unused in unused_imports:
        # Remove if it's the only import
        content = re.sub(r'from [^\n]+ import {0}(\s+# .*F401.*)?[\r\n]'.format(unused), '', content)
        
        # If it's part of a multi-import, remove just that part
        content = re.sub(r', {0}(\s+# .*F401.*)?'.format(unused), '', content)
        content = re.sub(r'{0}, '.format(unused), '', content)
    
    # Special handling for Path in reporter.py
    if 'from pathlib import Path' in content and 'Path' not in content.split('from pathlib import Path')[1]:
        content = content.replace('from pathlib import Path\n', '')
    
    return content


def sort_imports(content: str) -> str:
    """Sort imports according to PEP8 style."""
    # This is a simplified import sorter - not as full-featured as isort
    lines = content.split('\n')
    import_block_start = None
    import_block_end = None
    
    # Find the import block
    for i, line in enumerate(lines):
        if line.startswith(('import ', 'from ')) and import_block_start is None:
            import_block_start = i
        elif import_block_start is not None and not line.startswith(('import ', 'from ')) and line.strip():
            import_block_end = i
            break
    
    # If no import block found or it's already at the end of the file
    if import_block_start is None or import_block_end is None:
        import_block_end = len(lines)
    
    if import_block_start is not None and import_block_end > import_block_start:
        # Extract the imports
        imports = lines[import_block_start:import_block_end]
        
        # Group imports by standard lib, third party, and local
        std_libs = []
        third_party = []
        local = []
        
        for line in imports:
            if not line.strip():  # Skip empty lines
                continue
            if line.startswith(('from typing import', 'import re', 'import os', 'from pathlib import')):
                std_libs.append(line)
            elif 'website_test_bot' in line:
                local.append(line)
            else:
                third_party.append(line)
        
        # Sort each group
        std_libs.sort()
        third_party.sort()
        local.sort()
        
        # Combine with empty lines between groups
        sorted_imports = "\n".join(std_libs)
        if std_libs and third_party:
            sorted_imports += "\n"
        sorted_imports += "\n".join(third_party)
        if (std_libs or third_party) and local:
            sorted_imports += "\n"
        sorted_imports += "\n".join(local)
        
        # Replace the original import block
        new_lines = lines[:import_block_start] + sorted_imports.split('\n') + lines[import_block_end:]
        
        return '\n'.join(new_lines)
    
    return content


def process_file(file_path: Path) -> None:
    """Process a single Python file to fix import issues."""
    print(f"Processing {file_path}")
    
    with open(file_path, encoding='utf-8') as f:
        content = f.read()
    
    # Apply fixes
    content = fix_typing_imports(content)
    content = clean_unused_imports(content)
    content = sort_imports(content)
    
    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main() -> None:
    """Main function to fix import issues in all Python files."""
    # Find all Python files
    py_files = list(Path('.').glob('**/*.py'))
    
    # Process each file
    for file_path in py_files:
        # Skip files in .venv or other non-source directories
        if any(part.startswith('.') for part in file_path.parts) and not file_path.parts[0] == '.':
            continue
        process_file(file_path)
    
    print(f"Processed {len(py_files)} files")
    print("Finished fixing import issues.")


if __name__ == '__main__':
    main() 