#!/usr/bin/env python3
"""
Script per debug degli import
"""

import sys
import os

# Aggiungi directory al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== DEBUG IMPORT ===")
print(f"Python path: {sys.path[0]}")
print(f"Current dir: {os.getcwd()}")
print()

# Test import step by step
try:
    print("1. Importing PyQt5...")
    from PyQt5.QtWidgets import QApplication
    print("   ✓ PyQt5 OK")
except Exception as e:
    print(f"   ✗ PyQt5 ERROR: {e}")

try:
    print("\n2. Importing src...")
    import src
    print("   ✓ src OK")
except Exception as e:
    print(f"   ✗ src ERROR: {e}")

try:
    print("\n3. Importing src.gui...")
    import src.gui
    print("   ✓ src.gui OK")
except Exception as e:
    print(f"   ✗ src.gui ERROR: {e}")

try:
    print("\n4. Importing src.gui.main_window...")
    from src.gui.main_window import MainWindow
    print("   ✓ MainWindow OK")
except Exception as e:
    print(f"   ✗ MainWindow ERROR: {e}")

try:
    print("\n5. Importing src.gui.modules.input_module...")
    from src.gui.modules.input_module import InputModule
    print("   ✓ InputModule OK")
except Exception as e:
    print(f"   ✗ InputModule ERROR: {e}")

try:
    print("\n6. Importing src.widgets.wall_canvas...")
    from src.widgets.wall_canvas import WallCanvas
    print("   ✓ WallCanvas OK")
except Exception as e:
    print(f"   ✗ WallCanvas ERROR: {e}")

print("\n=== Directory Structure ===")
for root, dirs, files in os.walk("src"):
    level = root.replace("src", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 2 * (level + 1)
    for file in files:
        if file.endswith('.py'):
            print(f"{subindent}{file}")