"""
Manual test for application monitoring functionality.
"""

import tkinter as tk
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.gui.widgets.app_monitor_panel import AppMonitorPanel
from src.gui.pages.apps_page import AppsPage


def test_app_monitor_panel():
    """Test the AppMonitorPanel widget."""
    root = tk.Tk()
    root.title("App Monitor Panel Test")
    root.geometry("1200x800")
    
    # Create and pack the panel
    panel = AppMonitorPanel(root)
    panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Add a close button
    close_button = tk.Button(root, text="Close", command=root.quit)
    close_button.pack(side=tk.BOTTOM, pady=5)
    
    print("App Monitor Panel Test")
    print("- The left panel should show running applications")
    print("- Click on an application to see details on the right")
    print("- Use the search and filter options to narrow down the list")
    print("- Try the quick operation buttons on selected applications")
    print("- Close this window when done testing")
    
    root.mainloop()
    panel.destroy()
    root.destroy()


def test_apps_page():
    """Test the AppsPage."""
    root = tk.Tk()
    root.title("Apps Page Test")
    root.geometry("1200x800")
    
    # Create and pack the page
    page = AppsPage(root)
    page.get_frame().pack(fill=tk.BOTH, expand=True)
    
    # Initialize the page
    page.on_page_enter()
    
    # Add a close button
    close_button = tk.Button(root, text="Close", command=root.quit)
    close_button.pack(side=tk.BOTTOM, pady=5)
    
    print("Apps Page Test")
    print("- This shows how the Apps page would look in the main application")
    print("- The page includes title, description, and the monitor panel")
    print("- Close this window when done testing")
    
    root.mainloop()
    page.cleanup()
    root.destroy()


if __name__ == "__main__":
    print("Choose test to run:")
    print("1. App Monitor Panel")
    print("2. Apps Page")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_app_monitor_panel()
    elif choice == "2":
        test_apps_page()
    else:
        print("Invalid choice. Running App Monitor Panel test.")
        test_app_monitor_panel()