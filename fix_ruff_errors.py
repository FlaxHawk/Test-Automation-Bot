#!/usr/bin/env python3
"""Script to automatically fix common ruff errors."""

import re
from pathlib import Path


def fix_typing_annotations(content):
    """Replace old-style typing annotations with new ones."""
    # Replace typing.X import statements
    content = re.sub(r'from typing import ([^,]*?)(Dict|List|Set|Tuple|Optional|Union|Any)([^,]*?)(,|\n)',
                    lambda m: m.group(0) if m.group(2) in content else m.group(1) + m.group(3) + m.group(4), 
                    content)
    
    # Replace List[X] with list[X], Dict[X, Y] with dict[X, Y], etc. in type annotations
    content = re.sub(r'List\[', 'list[', content)
    content = re.sub(r'Dict\[', 'dict[', content)
    content = re.sub(r'Set\[', 'set[', content)
    content = re.sub(r'Tuple\[', 'tuple[', content)
    
    # Replace Optional[X] with X | None
    content = re.sub(r'Optional\[([^]]+)\]', r'\1 | None', content)
    
    # Replace Union[X, Y] with X | Y
    content = re.sub(r'Union\[([^,]+),\s*([^]]+)\]', r'\1 | \2', content)
    
    return content


def fix_imports(content):
    """Fix import sorting."""
    # A proper fix would use isort, but this is a simplified approach
    
    # Match import blocks (consecutive import statements)
    import_pattern = r'((?:from [^\n]+ import [^\n]+\n|import [^\n]+\n)+)'
    import_blocks = re.findall(import_pattern, content)
    
    for block in import_blocks:
        # Sort import statements
        lines = block.strip().split('\n')
        sorted_lines = sorted(lines)
        sorted_block = '\n'.join(sorted_lines) + '\n'
        
        # Replace block with sorted version
        content = content.replace(block, sorted_block)
    
    return content


def fix_line_length(content, max_length=88):
    """Attempt to fix lines that are too long."""
    # This is a very simple approach - a proper fix would be more complex
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Skip comments and multi-line strings
        if line.strip().startswith('#') or line.strip().startswith('"""'):
            continue
        
        # If line is too long and has parameters, try to break it
        if len(line) > max_length and ('(' in line or '{' in line):
            # Add line break after open bracket
            for bracket in ['(', '{', '[']:
                if bracket in line:
                    pos = line.find(bracket)
                    lines[i] = line[:pos+1] + '\n    ' + line[pos+1:]
                    break
    
    return '\n'.join(lines)


def fix_unused_imports(content):
    """Remove unused imports based on F401 errors."""
    # This is a very simplified approach
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # If it's an import line with F401 comment, try to remove the unused import
        if 'import' in line and 'F401' in line:
            # Extract the unused import name
            match = re.search(r'([A-Za-z0-9_]+) imported but unused', line)
            if match:
                unused_name = match.group(1)
                # Remove the unused import and the F401 comment
                line = re.sub(r',\s*' + unused_name, '', line)
                line = re.sub(r'' + unused_name + ',\s*', '', line)
                line = re.sub(r'import ' + unused_name + '\s*#.*F401.*', '', line)
                line = re.sub(r'from .+ import ' + unused_name + '\s*#.*F401.*', '', line)
                line = re.sub(r'#.*F401.*', '', line)
        
        if line.strip():  # Skip empty lines
            new_lines.append(line)
    
    return '\n'.join(new_lines)


def fix_open_mode(content):
    """Fix unnecessary open mode parameters."""
    # Replace 'r' mode which is the default
    content = re.sub(r"open\(([^,]+),\s*'r'", r"open(\1", content)
    # Replace encoding='utf-8' when it's redundant (Python 3.9+)
    # This is simplified and might not work for all cases
    content = re.sub(r"open\(([^,]+),\s*encoding='utf-8'\)", r"open(\1)", content)
    
    return content


def process_file(file_path):
    """Process a single Python file."""
    print(f"Processing {file_path}")
    
    # Read the file
    with open(file_path, encoding='utf-8') as f:
        content = f.read()
    
    # Apply fixes
    content = fix_typing_annotations(content)
    content = fix_imports(content)
    content = fix_unused_imports(content)
    content = fix_line_length(content)
    content = fix_open_mode(content)
    
    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    """Main function."""
    # Get the src directory
    src_dir = Path('src')
    
    # Find all Python files
    py_files = list(src_dir.glob('**/*.py'))
    
    # Process each file
    for file_path in py_files:
        process_file(file_path)
    
    print(f"Processed {len(py_files)} files")
    print("Now run: poetry run ruff --fix .")
    print("For remaining issues, you'll need to manually fix:")
    print("1. Unused function arguments (ARG001)")
    print("2. Complex line length issues (E501)")
    print("3. Remaining import issues")


if __name__ == '__main__':
    main() 