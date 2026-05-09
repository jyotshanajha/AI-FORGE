#!/usr/bin/env python3
"""List routes."""
from app.api import chat

print("Routes in chat router:")
for i, route in enumerate(chat.router.routes):
    methods = getattr(route, 'methods', 'N/A')
    print(f"{i+1}. {route.path} {methods}")

print(f"\nTotal: {len(chat.router.routes)} routes")
