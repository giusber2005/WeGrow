"""
Installation script for Plant Growth Forecasting Dashboard
(Without opencv-cv and seaborn dependencies)
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def main():
    print("🌱 Plant Growth Forecasting Dashboard - Installation Script")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Check tkinter availability
    if not check_tkinter():
        print("❌ tkinter is not available!")
        print("Please install tkinter using your system package manager:")
        print("  Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  CentOS/RHEL: sudo yum install tkinter")
        print("  macOS: tkinter should be included with Python")
        print("  Windows: tkinter should be included with Python")
        sys.exit(1)
    
    print("✅ tkinter is available")
    
    # Install requirements
    requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    
    if not os.path.exists(requirements_file):
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    print("\n📦 Installing required packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ])
        print("✅ All packages installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        print("\nTrying to install core packages individually...")
        
        core_packages = [
            "matplotlib>=3.5.0",
            "pandas>=1.3.0", 
            "numpy>=1.21.0",
            "Pillow>=10.1"
        ]
        
        failed_packages = []
        for package in core_packages:
            print(f"Installing {package}...")
            if install_package(package):
                print(f"✅ {package} installed")
            else:
                print(f"❌ Failed to install {package}")
                failed_packages.append(package)
        
        if failed_packages:
            print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
            print("Please install these packages manually")
            sys.exit(1)
    
    print("\n🎉 Installation completed successfully!")
    print("\nTo run the application:")
    print("  python3 PlantDashboard/launcher.py")
    print("\nOr run the main dashboard directly:")
    print("  python3 PlantDashboard/main_dashboard.py")
    

if __name__ == "__main__":
    main()
