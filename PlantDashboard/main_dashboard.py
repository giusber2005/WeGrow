import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from PIL import Image, ImageTk
import json
import os
from datetime import datetime, timedelta
import joblib
from plant_model import PlantGrowthModel
from data_handler import DataHandler
from image_generator import ImageGenerator

class PlantGrowthDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("WeGrow")
        self.root.geometry("1000x800")  # More square dimensions
        self.root.configure(bg='#f0f0f0')
        
        image = Image.open("public/transparentLogo.png")
        # Convert to PhotoImage
        icon = ImageTk.PhotoImage(image)
        # Set as window icon
        self.root.iconphoto(False, icon)
        
        # Initialize components
        self.plant_model = PlantGrowthModel()
        self.data_handler = DataHandler()
        self.image_generator = ImageGenerator()
        
        # Variables - fixed plant type
        self.current_plant = "tomato"  # Fixed plant type
        self.ambient_mode = tk.StringVar(value="controlled")
        self.baseline_image_path = None
        
        # Environmental parameters with defaults
        self.default_params = {
            'temperature': 22.0,
            'humidity': 65.0,
            'soil_acidity': 6.5,
            'pressure': 1013.25,
            'brightness': 50000.0,
            'nutrients': 75.0,
            'water': 80.0,
            'co2': 400.0
        }
        
        self.env_params = {
            'temperature': tk.DoubleVar(value=self.default_params['temperature']),
            'humidity': tk.DoubleVar(value=self.default_params['humidity']),
            'soil_acidity': tk.DoubleVar(value=self.default_params['soil_acidity']),
            'pressure': tk.DoubleVar(value=self.default_params['pressure']),
            'brightness': tk.DoubleVar(value=self.default_params['brightness']),
            'nutrients': tk.DoubleVar(value=self.default_params['nutrients']),
            'water': tk.DoubleVar(value=self.default_params['water']),
            'co2': tk.DoubleVar(value=self.default_params['co2'])
        }
        
        self.setup_ui()
        self.update_prediction()
        
    def setup_ui(self):
        # Main container with square layout
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for square layout
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)  # Center panel wider
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🌱 Plant Growth Dashboard", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Left panel - Controls
        self.setup_control_panel(main_frame)
        
        # Center panel - Plant Visualization
        self.setup_visualization_panel(main_frame)
        
        # Right panel - Results only (no system messages)
        self.setup_results_panel(main_frame)
        
    def setup_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="Environmental Controls", padding="6")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 6))
        
        # Ambient mode
        ttk.Label(control_frame, text="Environment Mode:", font=('Arial', 9, 'bold')).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))
        
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        
        ttk.Radiobutton(mode_frame, text="Controlled", variable=self.ambient_mode, 
                       value="controlled", command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Semi-Controlled", variable=self.ambient_mode, 
                       value="semi-controlled", command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Open", variable=self.ambient_mode, 
                       value="open", command=self.on_mode_change).pack(anchor=tk.W)
        
        # Baseline image
        ttk.Button(control_frame, text="📷 Load Plant Image", 
                  command=self.load_baseline_image).grid(row=2, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Environmental parameters
        ttk.Label(control_frame, text="Parameters:", 
                 font=('Arial', 9, 'bold')).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 4))
        
        param_labels = {
            'temperature': '🌡️ Temp (°C)',
            'humidity': '💧 Humidity (%)',
            'soil_acidity': '🧪 pH',
            'pressure': '🌬️ Pressure',
            'brightness': '☀️ Light',
            'nutrients': '🌿 Nutrients (%)',
            'water': '💦 Water (%)',
            'co2': '🫧 CO2'
        }
        
        row = 4
        for param, label in param_labels.items():
            # Compact parameter layout
            param_frame = ttk.Frame(control_frame)
            param_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=1)
            
            ttk.Label(param_frame, text=label, width=11, font=('Arial', 8)).pack(side=tk.LEFT)
            
            # Scale ranges based on parameter type
            if param == 'co2':
                scale_max = 1000
            elif param == 'brightness':
                scale_max = 100000
            elif param == 'pressure':
                scale_max = 1100
            elif param == 'soil_acidity':
                scale_max = 14
            else:
                scale_max = 100
                
            scale = ttk.Scale(param_frame, from_=0, to=scale_max,
                             variable=self.env_params[param], orient=tk.HORIZONTAL,
                             command=lambda x, p=param: self.on_param_change(p))
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))
            
            # Value label
            value_label = ttk.Label(param_frame, text=f"{self.env_params[param].get():.1f}", width=5, font=('Arial', 8))
            value_label.pack(side=tk.RIGHT)
            
            # Store reference for updates
            setattr(self, f"{param}_value_label", value_label)
            
            row += 1
        
        # Set to Default button
        ttk.Button(control_frame, text="🔄 Set to Default", 
                  command=self.set_to_default).grid(row=row, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        
    def setup_visualization_panel(self, parent):
        viz_frame = ttk.LabelFrame(parent, text="Plant Visualization", padding="6")
        viz_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=3)
        
        # Notebook for different views
        notebook = ttk.Notebook(viz_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Plant Before Growth tab
        self.setup_before_growth_tab(notebook)
        
        # Plant Evolution tab
        self.setup_plant_evolution_tab(notebook)
        
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(0, weight=1)
        
    def setup_before_growth_tab(self, notebook):
        """Tab showing the plant before growth starts"""
        before_frame = ttk.Frame(notebook)
        notebook.add(before_frame, text="🌱 Initial Plant")
        
        # Create a frame for the initial plant display
        display_frame = ttk.Frame(before_frame)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Title for initial state
        title_label = ttk.Label(display_frame, text="Plant Initial State", 
                               font=('Arial', 11, 'bold'))
        title_label.pack(pady=(0, 8))
        
        # Frame for the plant image
        self.initial_plant_frame = ttk.Frame(display_frame)
        self.initial_plant_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initial plant image label
        self.initial_plant_label = ttk.Label(self.initial_plant_frame, 
                                           text="Initial plant state will appear here",
                                           font=('Arial', 9))
        self.initial_plant_label.pack(expand=True)
        
        # Plant info display
        info_frame = ttk.LabelFrame(display_frame, text="Plant Information", padding="4")
        info_frame.pack(fill=tk.X, pady=(8, 0))
        
        self.plant_info_text = tk.Text(info_frame, height=8, width=35, wrap=tk.WORD, 
                                      font=('Arial', 8), bg='#f8f9fa')
        self.plant_info_text.pack(fill=tk.BOTH, expand=True)
        
        # Submit button
        submit_frame = ttk.Frame(display_frame)
        submit_frame.pack(fill=tk.X, pady=(8, 0))
        
        ttk.Button(submit_frame, text="📤 Submit Plant Information & Photo", 
                  command=self.submit_plant_data).pack(fill=tk.X)
        
    def setup_plant_evolution_tab(self, notebook):
        """Evolution tab"""
        evolution_frame = ttk.Frame(notebook)
        notebook.add(evolution_frame, text="🌿 Growth Evolution")
        
        # Create scrollable frame for plant images
        canvas_scroll = tk.Canvas(evolution_frame)
        scrollbar = ttk.Scrollbar(evolution_frame, orient="vertical", command=canvas_scroll.yview)
        self.scrollable_frame = ttk.Frame(canvas_scroll)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        )
        
        canvas_scroll.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        
        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.image_display_frame = ttk.Frame(self.scrollable_frame)
        self.image_display_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
    def setup_results_panel(self, parent):
        results_frame = ttk.LabelFrame(parent, text="Growth Prediction", padding="6")
        results_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(6, 0))
        
        # Prediction results only (no system messages)
        ttk.Label(results_frame, text="Forecast Results:", 
                 font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        
        self.results_text = tk.Text(results_frame, height=20, width=26, wrap=tk.WORD, font=('Arial', 8))
        self.results_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)
        
    def on_mode_change(self):
        self.update_prediction()
        
    def on_param_change(self, param):
        value = self.env_params[param].get()
        
        # Update value label
        value_label = getattr(self, f"{param}_value_label")
        if param == 'soil_acidity':
            value_label.config(text=f"{value:.1f}")
        elif param in ['brightness', 'pressure', 'co2']:
            value_label.config(text=f"{value:.0f}")
        else:
            value_label.config(text=f"{value:.1f}")
            
        # Auto-update prediction when parameters change
        self.update_prediction()
        
    def set_to_default(self):
        """Reset all parameters to default values"""
        for param_name, default_value in self.default_params.items():
            self.env_params[param_name].set(default_value)
            
        self.ambient_mode.set("controlled")
        self.update_prediction()
        
    def load_baseline_image(self):
        file_path = filedialog.askopenfilename(
            title="Select baseline plant image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if file_path:
            self.baseline_image_path = file_path
            self.update_prediction()
            
    def submit_plant_data(self):
        """Submit plant information and photo"""
        try:
            # Get current parameters
            params = {param: var.get() for param, var in self.env_params.items()}
            params['plant_type'] = self.current_plant
            params['ambient_mode'] = self.ambient_mode.get()
            
            # Create submission data
            submission_data = {
                'timestamp': datetime.now().isoformat(),
                'parameters': params,
                'baseline_image_path': self.baseline_image_path,
                'plant_info': self.plant_info_text.get(1.0, tk.END),
                'results': self.results_text.get(1.0, tk.END)
            }
            
            # Show confirmation dialog
            messagebox.showinfo("Submission Successful", 
                              "Plant information and photo have been submitted successfully!\n\n"
                              f"Submission ID: {datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
        except Exception as e:
            messagebox.showerror("Submission Error", f"Error submitting data: {str(e)}")
            
    def update_prediction(self):
        try:
            # Get current parameters
            params = {param: var.get() for param, var in self.env_params.items()}
            params['plant_type'] = self.current_plant
            params['ambient_mode'] = self.ambient_mode.get()
            
            # Generate prediction
            prediction = self.plant_model.predict_growth(params)
            
            # Update initial plant display
            self.update_initial_plant_display(params, prediction)
            
            # Generate plant evolution images
            self.generate_plant_evolution(params, prediction)
            
            # Update results text
            self.update_results_display(prediction)
            
        except Exception as e:
            messagebox.showerror("Prediction Error", f"Error generating prediction: {str(e)}")
            
    def update_initial_plant_display(self, params, prediction):
        """Update the initial plant state display"""
        try:
            # Generate initial plant image (stage 0)
            initial_image = self.image_generator.generate_plant_image(
                self.current_plant, 0.5, prediction['health_score'], 0
            )
            
            # Resize image to fit better in square layout
            initial_image = initial_image.resize((280, 210), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and display
            photo = ImageTk.PhotoImage(initial_image)
            self.initial_plant_label.configure(image=photo, text="")
            self.initial_plant_label.image = photo  # Keep reference
            
            # Update plant information
            self.update_plant_info(params, prediction)
            
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not generate initial plant image: {str(e)}")
            
    def update_plant_info(self, params, prediction):
        """Update plant information display"""
        self.plant_info_text.delete(1.0, tk.END)
        
        info_text = f"""🌱 PLANT STATUS
{'='*22}

Plant Type: Tomato
Health Score: {prediction['health_score']:.1f}%
Growth Rate: {prediction['growth_rate']:.2f} cm/day

🌡️ CONDITIONS:
Temperature: {params['temperature']:.1f}°C
Humidity: {params['humidity']:.1f}%
Soil pH: {params['soil_acidity']:.1f}
Light: {params['brightness']:.0f} lux
Water: {params['water']:.1f}%
Nutrients: {params['nutrients']:.1f}%

📊 FORECAST:
Final Height: {prediction['final_height']:.1f} cm
Expected Yield: {prediction.get('yield', 'N/A')}
Optimal Conditions: {prediction['optimal_conditions']:.1f}%
"""
        
        self.plant_info_text.insert(1.0, info_text)
        
    def generate_plant_evolution(self, params, prediction):
        """Generate and display plant evolution images"""
        try:
            # Generate plant evolution images
            images = self.image_generator.generate_evolution(
                self.current_plant, params, prediction, self.baseline_image_path
            )
            
            if images:
                # Clear previous images
                for widget in self.image_display_frame.winfo_children():
                    widget.destroy()
                
                # Display evolution stages in a square grid
                stages_per_row = 2  # Square layout
                for i, image in enumerate(images):
                    row = i // stages_per_row
                    col = i % stages_per_row
                    
                    stage_frame = ttk.Frame(self.image_display_frame)
                    stage_frame.grid(row=row, column=col, padx=4, pady=4, sticky=(tk.W, tk.E))
                    
                    # Stage label
                    ttk.Label(stage_frame, text=f"Stage {i+1}", 
                             font=('Arial', 9, 'bold')).pack()
                    
                    # Resize image for compact display
                    resized_image = image.resize((180, 135), Image.Resampling.LANCZOS)
                    
                    # Convert PIL image to PhotoImage
                    photo = ImageTk.PhotoImage(resized_image)
                    image_label = tk.Label(stage_frame, image=photo)
                    image_label.image = photo  # Keep a reference
                    image_label.pack()
                
                # Configure grid weights for even distribution
                for col in range(stages_per_row):
                    self.image_display_frame.columnconfigure(col, weight=1)
                
        except Exception as e:
            messagebox.showerror("Evolution Error", f"Could not generate evolution images: {str(e)}")
            
    def update_results_display(self, prediction):
        self.results_text.delete(1.0, tk.END)
        
        results = f"""🌱 GROWTH FORECAST
{'='*18}

Final Height: {prediction['final_height']:.1f} cm
Growth Rate: {prediction['growth_rate']:.2f} cm/day
Health Score: {prediction['health_score']:.1f}/100

📅 Growth Phases:
"""
        
        for phase in prediction.get('phases', []):
            results += f"• {phase['name']}: Days {phase['start']}-{phase['end']}\n"
            
        results += f"\n✅ Optimal Conditions: {prediction['optimal_conditions']:.1f}%"
        results += f"\n🍅 Expected Yield: {prediction.get('yield', 'N/A')}"
        
        # Add environmental summary
        results += f"\n\n🌡️ ENVIRONMENT SUMMARY:"
        results += f"\nTemperature: {self.env_params['temperature'].get():.1f}°C"
        results += f"\nHumidity: {self.env_params['humidity'].get():.1f}%"
        results += f"\nSoil pH: {self.env_params['soil_acidity'].get():.1f}"
        results += f"\nLight Level: {self.env_params['brightness'].get():.0f} lux"
        results += f"\nWater Level: {self.env_params['water'].get():.1f}%"
        results += f"\nNutrients: {self.env_params['nutrients'].get():.1f}%"
        results += f"\nCO2 Level: {self.env_params['co2'].get():.0f} ppm"
        
        self.results_text.insert(1.0, results)

def main():
    root = tk.Tk()
    app = PlantGrowthDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
