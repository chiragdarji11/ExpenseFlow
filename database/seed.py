"""
ExpenseFlow - Root Seed Script Forwarder
Allows running: python database/seed.py directly from the project root directory.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Switch working directory to backend so relative paths work as expected
os.chdir(BACKEND_DIR)

# Import and execute the backend seed logic
from database.seed import seed_database

if __name__ == "__main__":
    seed_database()
