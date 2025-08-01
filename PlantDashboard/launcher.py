"""
Plant Growth Forecasting Dashboard Launcher
"""

import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from main_dashboard import PlantGrowthDashboard
    import tkinter as tk
    
    def main():
        print("🌱 Starting Plant Growth Forecasting Dashboard...")
        print("Loading AI models and initializing interface...")
        
        root = tk.Tk()
        
        # Set application icon and styling
        try:
            root.iconname("Plant Growth Forecaster")
        except:
            pass
            
        app = PlantGrowthDashboard(root)
        
        print("✅ Dashboard ready!")
        print("Features available:")
        print("  • AI-powered plant growth prediction")
        print("  • Real-time parameter control")
        print("  • Visual growth simulation")
        print("  • Environmental analysis")
        print("  • Data export/import")
        print("  • Multiple ambient modes")
        print("  • Plant evolution visualization")
        
        root.mainloop()
        
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Please ensure all required packages are installed:")
    print("  pip install matplotlib pandas pillow numpy joblib")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting application: {e}")
    sys.exit(1)
