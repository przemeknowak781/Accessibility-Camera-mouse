import sys
import time

print(f"Python version: {sys.version}")

try:
    import uiautomation as auto
    print(f"uiautomation imported successfully.")
    print(f"uiautomation version: {getattr(auto, 'VERSION', 'unknown')}")
except ImportError as e:
    print(f"FAILED to import uiautomation: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error importing uiautomation: {e}")
    sys.exit(1)

try:
    print("Attempting to initialize UI Automation...")
    # Some basics
    pos = auto.GetCursorPos()
    print(f"Cursor Pos: {pos}")
    
    element = auto.ControlFromPoint(pos[0], pos[1])
    if element:
        print(f"Element under cursor: {element.Name} ({element.ControlTypeName})")
    else:
        print("No element found under cursor.")

except Exception as e:
    print(f"Error using uiautomation: {e}")
    import traceback
    traceback.print_exc()

print("Diagnosis complete.")
