"""
Test file to verify router imports.
"""

from fastapi import FastAPI

def test_router_imports():
    """Test that all routers can be imported successfully."""
    import_results = {}
    
    # Import API routers
    try:
        from app.api.health import health_router
        import_results['health_router'] = True
        print("Successfully imported health_router")
    except ImportError as e:
        import_results['health_router'] = False
        print(f"Failed to import health_router: {e}")

    try:
        from app.api.metrics import metrics_router
        import_results['metrics_router'] = True
        print("Successfully imported metrics_router")
    except ImportError as e:
        import_results['metrics_router'] = False
        print(f"Failed to import metrics_router: {e}")

    try:
        from app.api.admin import admin_router
        import_results['admin_router'] = True
        print("Successfully imported admin_router")
    except ImportError as e:
        import_results['admin_router'] = False
        print(f"Failed to import admin_router: {e}")

    # Import feature routers
    try:
        from app.routers.auth_router import router as auth_router
        import_results['auth_router'] = True
        print("Successfully imported auth_router")
    except ImportError as e:
        import_results['auth_router'] = False
        print(f"Failed to import auth_router: {e}")

    try:
        from app.routers.chat_router import router as chat_router
        import_results['chat_router'] = True
        print("Successfully imported chat_router")
    except ImportError as e:
        import_results['chat_router'] = False
        print(f"Failed to import chat_router: {e}")

    try:
        from app.routers.learning_router import router as learning_router
        import_results['learning_router'] = True
        print("Successfully imported learning_router")
    except ImportError as e:
        import_results['learning_router'] = False
        print(f"Failed to import learning_router: {e}")

    try:
        from app.routers.user_router import router as user_router
        import_results['user_router'] = True
        print("Successfully imported user_router")
    except ImportError as e:
        import_results['user_router'] = False
        print(f"Failed to import user_router: {e}")

    try:
        from app.routers.onboarding_router import router as onboarding_router
        import_results['onboarding_router'] = True
        print("Successfully imported onboarding_router")
    except ImportError as e:
        import_results['onboarding_router'] = False
        print(f"Failed to import onboarding_router: {e}")

    try:
        from app.routers.embedding_router import router as embedding_router
        import_results['embedding_router'] = True
        print("Successfully imported embedding_router")
    except ImportError as e:
        import_results['embedding_router'] = False
        print(f"Failed to import embedding_router: {e}")

    print("Import test complete!")
    return import_results

if __name__ == "__main__":
    test_router_imports()