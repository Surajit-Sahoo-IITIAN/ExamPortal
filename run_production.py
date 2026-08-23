"""
Production Server Runner for Examination Portal
Runs Django using Waitress (Production Multi-threaded WSGI Server for Windows)

Handles 100+ concurrent student connections smoothly without freezing or locking.
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examportal.settings')
django.setup()

from waitress import serve
from examportal.wsgi import application

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    threads = 16  # Multi-threaded for handling 70-100+ students concurrently

    print("=" * 65)
    print("  🚀 STARTING PRODUCTION EXAM SERVER (WAITRESS WSGI)")
    print("=" * 65)
    print(f"  • Host:        http://{host}:{port}")
    print(f"  • Local URL:   http://127.0.0.1:{port}")
    print(f"  • Threads:     {threads} concurrent workers")
    print(f"  • DB Engine:   SQLite (WAL Mode Enabled with 60s timeout)")
    print("=" * 65)
    print("\n  👉 Server is LIVE and ready for your 70 students.")
    print("  👉 To make it accessible online, run: ngrok http 8000 in another terminal.")
    print("  👉 Press CTRL+C to stop the server.\n")

    serve(
        application,
        host=host,
        port=port,
        threads=threads,
        connection_limit=200,
        channel_timeout=60,
        cleanup_interval=30
    )
