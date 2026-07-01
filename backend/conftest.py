# conftest.py  (à la racine, à côté de /app et /tests)
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))