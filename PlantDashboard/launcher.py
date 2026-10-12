"""
WeGrow - Plant Growth Forecasting Dashboard launcher

Run from anywhere:  python3 PlantDashboard/launcher.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        import tkinter as tk
        from main_dashboard import PlantGrowthDashboard
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install the requirements with:  pip install -r PlantDashboard/requirements.txt")
        print("On Debian/Ubuntu tkinter comes from:  sudo apt install python3-tk")
        sys.exit(1)

    print("Starting WeGrow dashboard...")
    root = tk.Tk()
    PlantGrowthDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
