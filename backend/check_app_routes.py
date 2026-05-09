#!/usr/bin/env python3
"""Check FastAPI app routes."""
from app.main import app

print("All routes in FastAPI app:")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', 'N/A')
        if 'chat' in route.path:
            print(f"- {route.path} {methods}")

print("\nSearching for generate-image...")
found = False
for route in app.routes:
    if hasattr(route, 'path') and 'generate-image' in route.path:
        found = True
        print(f"FOUND: {route.path} {getattr(route, 'methods', 'N/A')}")

if not found:
    print("generate-image route NOT found in FastAPI app!")
