import sys
import os
sys.path.insert(0, 'src')

try:
    from models.schedule import ScheduleType
    print("Schedule import OK")
except Exception as e:
    print(f"Schedule import error: {e}")

try:
    from models.action import ActionType
    print("Action import OK")
except Exception as e:
    print(f"Action import error: {e}")

try:
    import tkinter as tk
    print("Tkinter import OK")
except Exception as e:
    print(f"Tkinter import error: {e}")