import sys
import os

path = '/home/YOUR_PYTHONANYWHERE_USERNAME/tailor-app'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
