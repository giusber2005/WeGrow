"""
Plant Growth Graphics Demo Launcher
Simple version focusing on visual capabilities
"""

import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_requirements():
    """Check if required packages are available"""
    required_packages = {
        'tkinter': 'tkinter',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn', 
        'numpy': 'numpy',
        'PIL': 'Pillow'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"\n📦 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    print("🎨 Plant Growth Graphics Demo")
    print("=" * 40)
    print("Checking requirements...")
    
    if not check_requirements():
        print("\n❌ Please install missing packages first!")
        return
    
    print("\n🚀 Starting graphics demo...")
    
    try:
        from graphics_demo import PlantGrowthGraphicsDemo
        import tkinter as tk
        
        root = tk.Tk()
        app = PlantGrowthGraphicsDemo(root)
        
        print("✅ Graphics demo ready!")
        print("\nDemo features:")
        print("  • 6 plants, driven by the WeGrow growth model")
        print("  • Growth chart with an outcome range in Dynamic/Chaotic scenarios")
        print("  • Plant evolution, health heatmap and 3D height surface")
        print("  • Live statistics, health gauge and condition radar")
        print("  • 'Animate growth' sweeps through the season; Chaotic mode drifts with the weather")

        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error starting demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
