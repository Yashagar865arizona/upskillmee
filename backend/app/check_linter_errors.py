"""
Simple linter check for router files.

This script does a basic static analysis on router files to catch
common issues like undefined variables and imports.
"""

import os
import re
import sys
from pathlib import Path

# Add parent directory to path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(current_dir.parent))

def check_common_issues(file_path):
    """Check file for common issues like undefined variables and imports."""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Get base filename without extension
    base_name = os.path.basename(file_path).replace('.py', '')
    
    # Check for imports
    required_imports = {
        'APIRouter': r'from\s+fastapi\s+import.*APIRouter',
        'HTTPException': r'from\s+fastapi\s+import.*HTTPException',
        'Depends': r'from\s+fastapi\s+import.*Depends',
        'logging': r'import\s+logging',
        'Session': r'from\s+sqlalchemy.orm\s+import\s+.*Session',
        'get_db': r'from\s+\.\.database\s+import\s+get_db',
    }
    
    missing_imports = []
    for import_name, pattern in required_imports.items():
        if not re.search(pattern, content):
            missing_imports.append(import_name)
    
    # Check for common undefined variables
    known_patterns = {
        'logger': r'logger\s*=\s*logging\.getLogger\(__name__\)',
        'router': r'router\s*=\s*\w+Router\(\)',
        'get_.*service': r'def\s+get_\w+_service',
    }
    
    undefined_vars = []
    for var_name, pattern in known_patterns.items():
        if var_name in content and not re.search(pattern, content):
            undefined_vars.append(var_name)
    
    # Check class-based router structure
    class_name = f"{base_name.split('_')[0].capitalize()}Router"
    if class_name not in content:
        # Check if it uses another naming pattern
        class_match = re.search(r'class\s+(\w+Router)', content)
        if not class_match:
            undefined_vars.append(f"missing class {class_name}")
    
    # Print results
    issues_found = False
    
    if missing_imports:
        issues_found = True
        print(f"Missing imports in {file_path}:")
        for imp in missing_imports:
            print(f"  - {imp}")
    
    if undefined_vars:
        issues_found = True
        print(f"Potential undefined variables in {file_path}:")
        for var in undefined_vars:
            print(f"  - {var}")
    
    if not issues_found:
        print(f"✅ No common issues found in {file_path}")
    
    return not issues_found

def main():
    """Check all router files for common issues."""
    routers_dir = current_dir / "routers"
    router_files = [
        routers_dir / "auth_router.py",
        routers_dir / "chat_router.py",
        routers_dir / "embedding_router.py",
        routers_dir / "learning_router.py",
        routers_dir / "onboarding_router.py",
        routers_dir / "user_router.py"
    ]
    
    print("Checking router files for common linter issues...")
    all_good = True
    
    for file_path in router_files:
        if not file_path.exists():
            print(f"❌ {file_path.name} does not exist")
            all_good = False
            continue
        
        print(f"\nChecking {file_path.name}...")
        if not check_common_issues(file_path):
            all_good = False
    
    if all_good:
        print("\n✅ All router files passed basic linter checks")
        return 0
    else:
        print("\n❌ Some router files have potential issues")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 