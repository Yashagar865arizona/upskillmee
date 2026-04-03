"""
A simplified test script that mocks out dependencies to verify router structure.
This only checks that routers are exporting the required structure.
"""

import os
import sys
from pathlib import Path
import importlib.util
import re

# Add parent directory to path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
backend_dir = current_dir.parent.parent
sys.path.insert(0, str(backend_dir))

print(f"Current directory: {os.getcwd()}")

def mock_imports():
    """
    Add mock modules to sys.modules to prevent import errors
    """
    import sys
    from unittest.mock import MagicMock
    
    # List of modules to mock
    modules_to_mock = [
        'redis', 'slowapi', 'openai', 'pinecone', 'langchain',  
        'app.services', 'app.services.auth_service', 'app.services.user_service',
        'app.services.message_service', 'app.services.embedding_service',
        'app.services.learning_service', 'app.services.onboarding_service',
        'app.services.cache_service', 'app.database', 'app.models'
    ]
    
    for module_name in modules_to_mock:
        sys.modules[module_name] = MagicMock()
        parts = module_name.split('.')
        for i in range(1, len(parts)):
            parent_module = '.'.join(parts[:i])
            if parent_module not in sys.modules:
                sys.modules[parent_module] = MagicMock()

def check_router_structure(file_path):
    """
    Check if a router file exports an object with a router attribute.
    
    This parses the file directly instead of importing it to avoid 
    dependency issues.
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Check if the file defines a class and instantiates it as 'router'
        class_pattern = r'class\s+(\w+)Router'
        class_matches = re.findall(class_pattern, content)
        
        # Check if there's an assignment like "router = SomeRouter()"
        instance_pattern = r'router\s*=\s*(\w+)Router\(\)'
        instance_matches = re.findall(instance_pattern, content)
        
        if class_matches and instance_matches:
            print(f"✅ {file_path.name} has proper structure:")
            print(f"   - Defines class: {class_matches[0]}Router")
            print(f"   - Instantiates: router = {instance_matches[0]}Router()")
            return True
        else:
            if not class_matches:
                print(f"❌ {file_path.name} doesn't define a Router class")
            if not instance_matches:
                print(f"❌ {file_path.name} doesn't instantiate router = XRouter()")
            return False
            
    except Exception as e:
        print(f"❌ Error checking {file_path}: {e}")
        return False

def main():
    """Main test function"""
    routers_dir = backend_dir / "app" / "routers"
    router_files = [
        routers_dir / "auth_router.py",
        routers_dir / "chat_router.py",
        routers_dir / "embedding_router.py",
        routers_dir / "learning_router.py",
        routers_dir / "onboarding_router.py",
        routers_dir / "user_router.py"
    ]
    
    print("\nChecking router structure...")
    all_good = True
    
    for file_path in router_files:
        if not file_path.exists():
            print(f"❌ {file_path.name} does not exist")
            all_good = False
            continue
            
        if not check_router_structure(file_path):
            all_good = False
    
    # Check the __init__.py file
    init_file = routers_dir / "__init__.py"
    if init_file.exists():
        with open(init_file, 'r') as f:
            content = f.read()
            
        # Check if all routers are imported
        required_imports = [
            "from .auth_router import router as auth_router",
            "from .chat_router import router as chat_router",
            "from .embedding_router import router as embedding_router",
            "from .learning_router import router as learning_router",
            "from .onboarding_router import router as onboarding_router",
            "from .user_router import router as user_router"
        ]
        
        all_imports_present = True
        for import_line in required_imports:
            if import_line not in content:
                print(f"❌ Missing import in __init__.py: {import_line}")
                all_imports_present = False
                all_good = False
        
        if all_imports_present:
            print("✅ __init__.py has all required router imports")
            
        # Check if all routers are in __all__
        required_exports = [
            "auth_router", "chat_router", "embedding_router",
            "learning_router", "onboarding_router", "user_router"
        ]
        
        # Extract __all__ list from the content
        all_pattern = r'__all__\s*=\s*\[(.*?)\]'
        all_match = re.search(all_pattern, content, re.DOTALL)
        
        if all_match:
            all_list = all_match.group(1)
            all_exports_present = True
            
            for export in required_exports:
                if f'"{export}"' not in all_list and f"'{export}'" not in all_list:
                    print(f"❌ Missing export in __all__: {export}")
                    all_exports_present = False
                    all_good = False
            
            if all_exports_present:
                print("✅ __init__.py exports all required routers in __all__")
        else:
            print("❌ Could not find __all__ list in __init__.py")
            all_good = False
    else:
        print(f"❌ {init_file} does not exist")
        all_good = False
    
    if all_good:
        print("\n✅ All router files have the correct structure")
        return 0
    else:
        print("\n❌ Some router files have incorrect structure")
        return 1

if __name__ == "__main__":
    mock_imports()
    sys.exit(main())