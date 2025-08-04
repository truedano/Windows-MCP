#!/usr/bin/env python3
"""
Test logs page syntax.
"""

import sys
import os

# Add src to path - adjust path since we're now in tests directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    print("Testing syntax...")
    
    # Try to compile the file - adjust path for tests directory
    import py_compile
    src_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'gui', 'pages', 'logs_page.py')
    py_compile.compile(src_file, doraise=True)
    print("✅ Syntax is correct")
    
    # Try to import
    from gui.pages.logs_page import ScheduleLogsPage
    print("✅ Import successful")
    
    print("🎉 All tests passed!")
    
except py_compile.PyCompileError as e:
    print(f"❌ Syntax error: {e}")
    sys.exit(1)
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)