import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import math
from datetime import datetime

class PlantGrowthGraphicsDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("🌱 Plant Growth Graphics Demo")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Demo variables
        self.current_plant = tk.StringVar(value="tomato")
        self.ambient_mode = tk.StringVar(value="controlled")
        
        # Environmental parameters for demo
        self.env_params = {
            'temperature': tk.DoubleVar(value=22.0),
            'humidity': tk.DoubleVar(value=65.0),
            'soil_acidity': tk.DoubleVar(value=6.5),
            'pressure': tk.DoubleVar(value=1013.25),
            'brightness': tk.DoubleVar(value=50.0),
            'nutrients': tk.DoubleVar(value=75.0),
            'water': tk.DoubleVar(value=80.0),
            'co2': tk.DoubleVar(value=40.0)
        }
        
        # Plant colors for visualization
        self.plant_colors = {
            'tomato': {'stem': '#228B22', 'leaf': '#32CD32', 'fruit': '#FF6347'},
            'basil': {'stem': '#228B22', 'leaf': '#90EE90', 'fruit': '#FFFFFF'},
            'mint': {'stem': '#228B22', 'leaf': '#98FB98', 'fruit': '#FFFFFF'},
            'lettuce': {'stem': '#228B22', 'leaf': '#ADFF2F', 'fruit': '#FFFFFF'},
            'rosemary': {'stem': '#8B4513', 'leaf': '#556B2F', 'fruit': '#FFFFFF'},
            'strawberry': {'stem': '#228B22', 'leaf': '#32CD32', 'fruit': '#FF1493'}
        }
        
        self.setup_ui()
        self.update_all_graphics()
        
        # Auto-update timer for dynamic effects
        self.auto_update()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title with animated effect
        self.title_label = ttk.Label(main_frame, text="🌱 Plant Growth Graphics Demo", 
                                    font=('Arial', 16, 'bold'))
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Left panel - Controls
        self.setup_control_panel(main_frame)
        
        # Center panel - Main Visualization
        self.setup_main_visualization(main_frame)
        
        # Right panel - Additional Graphics
        self.setup_additional_graphics(main_frame)
        
    def setup_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="🎛️ Graphics Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Plant selection with immediate visual feedback
        ttk.Label(control_frame, text="Plant Type:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        plant_combo = ttk.Combobox(control_frame, textvariable=self.current_plant,
                                  values=["tomato", "basil", "mint", "lettuce", "rosemary", "strawberry"])
        plant_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        plant_combo.bind('<<ComboboxSelected>>', self.on_plant_change)
        
        # Ambient mode with visual indicators
        ttk.Label(control_frame, text="Visual Mode:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(control_frame)
        mode_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Radiobutton(mode_frame, text="🎯 Controlled", variable=self.ambient_mode, 
                       value="controlled", command=self.update_all_graphics).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="🌊 Dynamic", variable=self.ambient_mode, 
                       value="semi-controlled", command=self.update_all_graphics).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="🌪️ Chaotic", variable=self.ambient_mode, 
                       value="open", command=self.update_all_graphics).pack(side=tk.LEFT)
        
        # Visual effects controls
        ttk.Separator(control_frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(control_frame, text="🎨 Visual Parameters:", 
                 font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=2, pady=(10, 5))
        
        # Parameter sliders with real-time visual updates
        param_labels = {
            'temperature': '🌡️ Temperature',
            'humidity': '💧 Humidity',
            'soil_acidity': '🧪 Soil pH',
            'pressure': '🌬️ Pressure',
            'brightness': '☀️ Light',
            'nutrients': '🌿 Nutrients',
            'water': '💦 Water',
            'co2': '🫧 CO2'
        }
        
        row = 4
        for param, label in param_labels.items():
            ttk.Label(control_frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
            
            # Create frame for slider and value display
            slider_frame = ttk.Frame(control_frame)
            slider_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            
            scale = ttk.Scale(slider_frame, from_=0, to=100,
                             variable=self.env_params[param], orient=tk.HORIZONTAL,
                             command=lambda x, p=param: self.on_param_change(p))
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Value display
            value_label = ttk.Label(slider_frame, text="0", width=4)
            value_label.pack(side=tk.RIGHT)
            
            # Store reference for updates
            setattr(self, f"{param}_label", value_label)
            
            row += 1
        
        # Action buttons with visual feedback
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="🎬 Animate Growth", 
                  command=self.animate_growth).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="🎲 Randomize", 
                  command=self.randomize_parameters).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="🔄 Reset Demo", 
                  command=self.reset_demo).pack(fill=tk.X, pady=2)
        
        control_frame.columnconfigure(1, weight=1)
        
    def setup_main_visualization(self, parent):
        viz_frame = ttk.LabelFrame(parent, text="📊 Main Visualization", padding="10")
        viz_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Notebook for different visualization modes
        self.notebook = ttk.Notebook(viz_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Growth Chart Tab
        self.setup_growth_chart_tab()
        
        # Plant Evolution Tab
        self.setup_plant_evolution_tab()
        
        # Parameter Heatmap Tab
        self.setup_heatmap_tab()
        
        # 3D Visualization Tab
        self.setup_3d_visualization_tab()
        
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(0, weight=1)
        
    def setup_growth_chart_tab(self):
        chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(chart_frame, text="📈 Growth Chart")
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.fig.patch.set_facecolor('#f0f0f0')
        
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def setup_plant_evolution_tab(self):
        evolution_frame = ttk.Frame(self.notebook)
        self.notebook.add(evolution_frame, text="🌱 Plant Evolution")
        
        # Create scrollable frame for plant images
        canvas_frame = tk.Canvas(evolution_frame, bg='white')
        scrollbar = ttk.Scrollbar(evolution_frame, orient="vertical", command=canvas_frame.yview)
        self.scrollable_frame = ttk.Frame(canvas_frame)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_frame.configure(scrollregion=canvas_frame.bbox("all"))
        )
        
        canvas_frame.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas_frame.configure(yscrollcommand=scrollbar.set)
        
        canvas_frame.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Plant evolution display
        self.plant_images_frame = ttk.Frame(self.scrollable_frame)
        self.plant_images_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def setup_heatmap_tab(self):
        heatmap_frame = ttk.Frame(self.notebook)
        self.notebook.add(heatmap_frame, text="🔥 Parameter Heatmap")
        
        # Create seaborn heatmap
        self.heatmap_fig, self.heatmap_ax = plt.subplots(figsize=(8, 6))
        self.heatmap_fig.patch.set_facecolor('#f0f0f0')
        
        self.heatmap_canvas = FigureCanvasTkAgg(self.heatmap_fig, heatmap_frame)
        self.heatmap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def setup_3d_visualization_tab(self):
        viz_3d_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_3d_frame, text="🎯 3D Analysis")
        
        # Create 3D plot
        self.fig_3d = plt.figure(figsize=(8, 6))
        self.fig_3d.patch.set_facecolor('#f0f0f0')
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
        
        self.canvas_3d = FigureCanvasTkAgg(self.fig_3d, viz_3d_frame)
        self.canvas_3d.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def setup_additional_graphics(self, parent):
        additional_frame = ttk.LabelFrame(parent, text="📋 Live Stats & Info", padding="10")
        additional_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Real-time statistics display
        stats_frame = ttk.LabelFrame(additional_frame, text="📊 Live Statistics", padding="5")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=8, width=25, wrap=tk.WORD, 
                                 font=('Courier', 9), bg='#f8f9fa')
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Visual health indicator
        health_frame = ttk.LabelFrame(additional_frame, text="🏥 Plant Health", padding="5")
        health_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.health_canvas = tk.Canvas(health_frame, height=100, bg='white')
        self.health_canvas.pack(fill=tk.X)
        
        # Parameter radar chart
        radar_frame = ttk.LabelFrame(additional_frame, text="🎯 Parameter Radar", padding="5")
        radar_frame.pack(fill=tk.BOTH, expand=True)
        
        self.radar_fig, self.radar_ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(projection='polar'))
        self.radar_fig.patch.set_facecolor('#f0f0f0')
        
        self.radar_canvas = FigureCanvasTkAgg(self.radar_fig, radar_frame)
        self.radar_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def on_plant_change(self, event=None):
        self.update_all_graphics()
        
    def on_param_change(self, param):
        # Update value display
        value = self.env_params[param].get()
        label = getattr(self, f"{param}_label")
        label.config(text=f"{value:.1f}")
        
        # Update graphics in real-time
        self.update_all_graphics()
        
    def update_all_graphics(self):
        self.update_growth_chart()
        self.update_plant_evolution()
        self.update_parameter_heatmap()
        self.update_3d_visualization()
        self.update_statistics()
        self.update_health_indicator()
        self.update_radar_chart()
        
    def update_growth_chart(self):
        self.ax.clear()
        
        # Generate mock growth data based on parameters
        days = np.arange(0, 100, 1)
        
        # Base growth influenced by parameters
        temp_factor = self.env_params['temperature'].get() / 100
        water_factor = self.env_params['water'].get() / 100
        light_factor = self.env_params['brightness'].get() / 100
        
        # Create realistic growth curve
        growth_rate = (temp_factor + water_factor + light_factor) / 3
        
        if self.ambient_mode.get() == "open":
            # Add chaos/randomness
            noise = np.random.normal(0, 0.1, len(days))
            heights = np.cumsum(np.maximum(0, growth_rate + noise)) * 2
        elif self.ambient_mode.get() == "semi-controlled":
            # Add some variation
            noise = np.random.normal(0, 0.05, len(days))
            heights = np.cumsum(np.maximum(0, growth_rate + noise)) * 2
        else:
            # Controlled growth
            heights = np.cumsum([growth_rate] * len(days)) * 2
            
        # Apply plant-specific characteristics
        plant_multipliers = {
            'tomato': 1.5, 'basil': 0.8, 'mint': 0.6,
            'lettuce': 0.4, 'rosemary': 1.2, 'strawberry': 0.5
        }
        
        multiplier = plant_multipliers.get(self.current_plant.get(), 1.0)
        heights = heights * multiplier
        
        # Plot with plant-specific colors
        colors = self.plant_colors[self.current_plant.get()]
        self.ax.plot(days, heights, color=colors['leaf'], linewidth=2, marker='o', markersize=2)
        
        # Add growth phases with different colors
        phase_colors = ['lightblue', 'lightgreen', 'lightyellow', 'lightcoral']
        phase_names = ['Germination', 'Seedling', 'Vegetative', 'Mature']
        
        for i, (color, name) in enumerate(zip(phase_colors, phase_names)):
            start_day = i * 25
            end_day = (i + 1) * 25
            if end_day <= len(days):
                self.ax.axvspan(start_day, end_day, alpha=0.3, color=color, label=name)
        
        self.ax.set_xlabel('Days')
        self.ax.set_ylabel('Height (cm)')
        self.ax.set_title(f'{self.current_plant.get().title()} Growth Simulation')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper left')
        
        # Add current parameter indicators
        current_day = int(self.env_params['temperature'].get())
        if current_day < len(heights):
            self.ax.axvline(current_day, color='red', linestyle='--', alpha=0.7, label='Current Day')
            self.ax.plot(current_day, heights[current_day], 'ro', markersize=8)
        
        self.canvas.draw()
        
    def update_plant_evolution(self):
        # Clear previous images
        for widget in self.plant_images_frame.winfo_children():
            widget.destroy()
            
        # Generate evolution stages
        stages = ['Seed', 'Sprout', 'Young', 'Mature', 'Full Growth']
        
        for i, stage in enumerate(stages):
            stage_frame = ttk.Frame(self.plant_images_frame)
            stage_frame.pack(fill=tk.X, pady=5)
            
            # Stage label
            ttk.Label(stage_frame, text=f"Stage {i+1}: {stage}", 
                     font=('Arial', 10, 'bold')).pack()
            
            # Generate plant image
            plant_image = self.generate_plant_stage_image(i+1)
            
            # Convert to PhotoImage and display
            photo = tk.PhotoImage(data=self.pil_to_tk_data(plant_image))
            image_label = tk.Label(stage_frame, image=photo)
            image_label.image = photo  # Keep reference
            image_label.pack()
            
    def generate_plant_stage_image(self, stage):
        """Generate a plant image for a specific growth stage"""
        img = Image.new('RGB', (200, 150), color='#87CEEB')  # Sky blue
        draw = ImageDraw.Draw(img)
        
        # Draw ground
        ground_y = 130
        draw.rectangle([0, ground_y, 200, 150], fill='#8B4513')  # Brown ground
        
        # Get plant colors
        colors = self.plant_colors[self.current_plant.get()]
        
        # Calculate plant size based on stage and parameters
        health_factor = (sum(param.get() for param in self.env_params.values()) / len(self.env_params)) / 100
        plant_height = stage * 15 * health_factor
        plant_width = plant_height * 0.6
        
        center_x = 100
        base_y = ground_y
        top_y = base_y - plant_height
        
        # Draw stem
        stem_width = max(2, int(plant_height * 0.1))
        draw.rectangle([center_x - stem_width//2, int(top_y), 
                       center_x + stem_width//2, base_y], fill=colors['stem'])
        
        # Draw leaves
        num_leaves = min(stage * 2, 8)
        for i in range(num_leaves):
            leaf_y = base_y - (i + 1) * (plant_height / (num_leaves + 1))
            side = 1 if i % 2 == 0 else -1
            leaf_x = center_x + side * (plant_width * 0.3)
            leaf_size = plant_width * 0.2
            
            # Draw leaf based on plant type
            if self.current_plant.get() == 'lettuce':
                # Broad leaves
                draw.ellipse([leaf_x - leaf_size, leaf_y - leaf_size//2,
                            leaf_x + leaf_size, leaf_y + leaf_size//2], fill=colors['leaf'])
            else:
                # Regular leaves
                draw.ellipse([leaf_x - leaf_size//2, leaf_y - leaf_size//3,
                            leaf_x + leaf_size//2, leaf_y + leaf_size//3], fill=colors['leaf'])
        
        # Draw fruits for mature stages
        if stage >= 4 and self.current_plant.get() in ['tomato', 'strawberry']:
            fruit_color = colors['fruit']
            for i in range(min(stage - 3, 3)):
                fruit_x = center_x + random.randint(-15, 15)
                fruit_y = int(top_y + random.randint(10, int(plant_height//2)))
                fruit_size = 5 + stage
                draw.ellipse([fruit_x - fruit_size, fruit_y - fruit_size,
                            fruit_x + fruit_size, fruit_y + fruit_size], fill=fruit_color)
        
        # Add stage indicator
        draw.text((5, 5), f"Stage {stage}", fill='black')
        
        return img
        
    def pil_to_tk_data(self, pil_image):
        """Convert PIL image to tkinter PhotoImage data"""
        import io
        import base64
        
        # Convert to PNG bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        
        # Encode to base64
        img_data = base64.b64encode(buffer.getvalue())
        
        return img_data
        
    def update_parameter_heatmap(self):
        self.heatmap_ax.clear()
        
        # Create parameter correlation matrix
        param_names = list(self.env_params.keys())
        param_values = [param.get() for param in self.env_params.values()]
        
        # Create a correlation-like matrix for visualization
        matrix = np.zeros((len(param_names), len(param_names)))
        
        for i, val_i in enumerate(param_values):
            for j, val_j in enumerate(param_values):
                if i == j:
                    matrix[i][j] = val_i
                else:
                    # Create interesting correlations
                    correlation = abs(val_i - val_j) / 100
                    matrix[i][j] = correlation * 50
        
        # Create heatmap
        sns.heatmap(matrix, annot=True, fmt='.1f', cmap='RdYlGn',
                   xticklabels=[name.replace('_', ' ').title() for name in param_names],
                   yticklabels=[name.replace('_', ' ').title() for name in param_names],
                   ax=self.heatmap_ax, cbar_kws={'label': 'Parameter Intensity'})
        
        self.heatmap_ax.set_title(f'{self.current_plant.get().title()} Parameter Heatmap')
        plt.setp(self.heatmap_ax.get_xticklabels(), rotation=45, ha='right')
        plt.setp(self.heatmap_ax.get_yticklabels(), rotation=0)
        
        self.heatmap_canvas.draw()
        
    def update_3d_visualization(self):
        self.ax_3d.clear()
        
        # Create 3D scatter plot of parameters
        temp = self.env_params['temperature'].get()
        humidity = self.env_params['humidity'].get()
        light = self.env_params['brightness'].get()
        
        # Generate some sample data points around current parameters
        n_points = 50
        temps = np.random.normal(temp, 5, n_points)
        humids = np.random.normal(humidity, 5, n_points)
        lights = np.random.normal(light, 5, n_points)
        
        # Color points based on "health" (distance from optimal)
        optimal_temp, optimal_humid, optimal_light = 25, 60, 50
        distances = np.sqrt((temps - optimal_temp)**2 + 
                          (humids - optimal_humid)**2 + 
                          (lights - optimal_light)**2)
        
        colors = plt.cm.RdYlGn_r(distances / distances.max())
        
        scatter = self.ax_3d.scatter(temps, humids, lights, c=colors, s=50, alpha=0.7)
        
        # Highlight current point
        self.ax_3d.scatter([temp], [humidity], [light], c='red', s=200, marker='*')
        
        self.ax_3d.set_xlabel('Temperature (°C)')
        self.ax_3d.set_ylabel('Humidity (%)')
        self.ax_3d.set_zlabel('Light Intensity')
        self.ax_3d.set_title(f'3D Parameter Space - {self.current_plant.get().title()}')
        
        self.canvas_3d.draw()
        
    def update_statistics(self):
        self.stats_text.delete(1.0, tk.END)
        
        # Calculate mock statistics
        params = {name: param.get() for name, param in self.env_params.items()}
        
        avg_param = sum(params.values()) / len(params)
        health_score = min(100, avg_param * 1.2)
        growth_rate = health_score / 20
        
        stats_text = f"""🌱 PLANT STATISTICS
{'='*25}

Plant Type: {self.current_plant.get().title()}
Mode: {self.ambient_mode.get().title()}

📊 Current Metrics:
Health Score: {health_score:.1f}%
Growth Rate: {growth_rate:.2f} cm/day
Avg Parameter: {avg_param:.1f}

🌡️ Environment:
Temperature: {params['temperature']:.1f}°C
Humidity: {params['humidity']:.1f}%
Soil pH: {params['soil_acidity']:.1f}
Light: {params['brightness']:.1f} lux

💧 Resources:
Water: {params['water']:.1f}%
Nutrients: {params['nutrients']:.1f}%
CO2: {params['co2']:.1f} ppm

⏰ Updated: {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.stats_text.insert(1.0, stats_text)
        
    def update_health_indicator(self):
        self.health_canvas.delete("all")
        
        # Calculate health score
        params = list(self.env_params.values())
        health_score = sum(param.get() for param in params) / len(params)
        
        # Draw health bar
        bar_width = 180
        bar_height = 20
        x_start = 10
        y_start = 40
        
        # Background
        self.health_canvas.create_rectangle(x_start, y_start, 
                                          x_start + bar_width, y_start + bar_height,
                                          fill='lightgray', outline='black')
        
        # Health bar
        health_width = (health_score / 100) * bar_width
        if health_score > 70:
            color = 'green'
        elif health_score > 40:
            color = 'orange'
        else:
            color = 'red'
            
        self.health_canvas.create_rectangle(x_start, y_start,
                                          x_start + health_width, y_start + bar_height,
                                          fill=color, outline='')
        
        # Health text
        self.health_canvas.create_text(100, 25, text=f"Health: {health_score:.1f}%",
                                     font=('Arial', 12, 'bold'))
        
        # Status emoji
        if health_score > 80:
            emoji = "🌟"
            status = "Excellent"
        elif health_score > 60:
            emoji = "😊"
            status = "Good"
        elif health_score > 40:
            emoji = "😐"
            status = "Fair"
        else:
            emoji = "😟"
            status = "Poor"
            
        self.health_canvas.create_text(100, 75, text=f"{emoji} {status}",
                                     font=('Arial', 10))
        
    def update_radar_chart(self):
        self.radar_ax.clear()
        
        # Parameter names and values
        param_names = ['Temp', 'Humid', 'pH', 'Press', 'Light', 'Nutri', 'Water', 'CO2']
        param_values = [param.get() for param in self.env_params.values()]
        
        # Number of variables
        N = len(param_names)
        
        # Compute angle for each axis
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Complete the circle
        
        # Add values
        param_values += param_values[:1]  # Complete the circle
        
        # Plot
        self.radar_ax.plot(angles, param_values, 'o-', linewidth=2, 
                          color=self.plant_colors[self.current_plant.get()]['leaf'])
        self.radar_ax.fill(angles, param_values, alpha=0.25,
                          color=self.plant_colors[self.current_plant.get()]['leaf'])
        
        # Add labels
        self.radar_ax.set_xticks(angles[:-1])
        self.radar_ax.set_xticklabels(param_names)
        self.radar_ax.set_ylim(0, 100)
        self.radar_ax.set_title(f'{self.current_plant.get().title()} Parameters', 
                               pad=20, fontsize=10)
        self.radar_ax.grid(True)
        
        self.radar_canvas.draw()
        
    def animate_growth(self):
        """Animate parameter changes to show dynamic growth"""
        def animate_step(step):
            if step < 50:  # 50 animation steps
                # Gradually change parameters
                for param in self.env_params.values():
                    current = param.get()
                    target = random.uniform(20, 80)
                    new_value = current + (target - current) * 0.1
                    param.set(new_value)
                
                self.update_all_graphics()
                self.root.after(100, lambda: animate_step(step + 1))
            
        animate_step(0)
        
    def randomize_parameters(self):
        """Randomize all parameters for demo purposes"""
        for param in self.env_params.values():
            param.set(random.uniform(10, 90))
        self.update_all_graphics()
        
    def reset_demo(self):
        """Reset all parameters to default values"""
        defaults = {
            'temperature': 22.0,
            'humidity': 65.0,
            'soil_acidity': 6.5,
            'pressure': 50.0,  # Normalized for demo
            'brightness': 50.0,
            'nutrients': 75.0,
            'water': 80.0,
            'co2': 40.0
        }
        
        for param_name, default_value in defaults.items():
            self.env_params[param_name].set(default_value)
            
        self.current_plant.set("tomato")
        self.ambient_mode.set("controlled")
        self.update_all_graphics()
        
    def auto_update(self):
        """Auto-update for dynamic effects"""
        if self.ambient_mode.get() == "open":
            # Add small random variations in open mode
            for param in self.env_params.values():
                current = param.get()
                variation = random.uniform(-1, 1)
                new_value = max(0, min(100, current + variation))
                param.set(new_value)
            
            self.update_all_graphics()
        
        # Schedule next update
        self.root.after(2000, self.auto_update)  # Update every 2 seconds

def main():
    root = tk.Tk()
    app = PlantGrowthGraphicsDemo(root)
    root.mainloop()

if __name__ == "__main__":
    main()
