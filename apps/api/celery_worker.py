#!/usr/bin/env python3
"""Celery worker entry point"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery worker
    celery_app.start()