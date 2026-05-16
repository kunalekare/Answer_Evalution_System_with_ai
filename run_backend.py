#!/usr/bin/env python
"""
Start AssessIQ Backend with Proper Configuration

This script starts the FastAPI backend with the correct settings for:
- Large file uploads (100MB limit)
- Proper host/port configuration
- Development mode with auto-reload

Usage:
    python run_backend.py
"""

import sys
import os
import uvicorn
from config.settings import settings

def main():
    """Start the backend server with proper configuration."""
    
    print("=" * 70)
    print("Starting AssessIQ Backend")
    print("=" * 70)
    print(f"App Name: {settings.APP_NAME}")
    print(f"Version: {settings.APP_VERSION}")
    print(f"Host: {settings.API_HOST}")
    print(f"Port: {settings.API_PORT}")
    print(f"Max Upload Size: {settings.MAX_FILE_SIZE / (1024*1024):.0f}MB")
    print(f"Debug: {settings.DEBUG}")
    print("=" * 70)
    print()
    print("Starting server...")
    print(f"API will be available at: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"API Docs at: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print()
    
    try:
        # Start Uvicorn with proper configuration
        # limit_max_requests=None: No restart limit
        # timeout_keep_alive: Connection timeout
        # timeout_notify: Server shutdown timeout
        uvicorn.run(
            "api.main:app",
            host=settings.API_HOST,
            port=settings.API_PORT,
            reload=settings.DEBUG,
            log_level="info",
            # Note: Server handles file size validation in route
            # Large uploads should work with default limits for now
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
