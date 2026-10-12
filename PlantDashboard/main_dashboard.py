"""
WeGrow - Plant Growth Forecasting Dashboard
"""

import math
import os
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime, date

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

from plant_model import PlantGrowthModel
from data_handler import DataHandler
from image_generator import ImageGenerator
from theme import Theme, COLORS, PHASE_COLORS, status_color, style_axes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# key, label, unit, min, max, step, default
PARAMETERS = [
    ('temperature', 'Temperature', '°C', 0, 45, 0.5, 22.0),
    ('humidity', 'Humidity', '%', 0, 100, 1, 65.0),
    ('soil_acidity', 'Soil pH', '', 3, 10, 0.1, 6.5),
    ('brightness', 'Light', 'lux', 0, 100000, 500, 50000.0),
    ('water', 'Water', '%', 0, 100, 1, 80.0),
    ('nutrients', 'Nutrients', '%', 0, 100, 1, 75.0),
    ('co2', 'CO₂', 'ppm', 200, 1500, 10, 400.0),
    ('pressure', 'Pressure', 'hPa', 950, 1050, 1, 1013.0),
]

# Parameters supplied by the weather in open-field mode
WEATHER_PARAMS = ('temperature', 'humidity', 'brightness', 'water')

MODES = {
    'controlled': ('Controlled', "Greenhouse: you set every parameter."),
    'semi-controlled': ('Semi-controlled', "You set the parameters; the forecast adds natural variation."),
    'open': ('Open field', "Temperature, humidity, light and water follow the local weather."),
}

FACTOR_LABELS = {
    'temperature': 'Temperature', 'humidity': 'Humidity', 'ph': 'Soil pH', 'water': 'Water',
    'nutrients': 'Nutrients', 'light': 'Light', 'co2': 'CO₂', 'pressure': 'Pressure',
}

def simulated_weather(day=None):
    """Stand-in for a weather API: typical conditions in South Tyrol for the given date"""
    day = day or date.today()
    # 1.0 in mid-July, -1.0 in mid-January
    season = math.cos((day.timetuple().tm_yday - 196) / 365 * 2 * math.pi)
    return {
        'temperature': round((11 + 11 * season) * 2) / 2,
        'humidity': float(round(68 - 8 * season)),
        'brightness': float(round((32000 + 28000 * season) / 500) * 500),
        'water': float(round(60 - 15 * season)),
    }


def format_value(value, step):
    if step >= 1:
        return f"{value:,.0f}"
    return f"{value:.1f}"


class PlantGrowthDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("WeGrow · Plant Growth Forecast")
        self.root.geometry("1380x860")
        self.root.minsize(1180, 760)
        self.theme = Theme(root)
        self.fonts = self.theme.fonts
        self._card = self.theme.card
        self._label = self.theme.label

        self.plant_model = PlantGrowthModel()
        self.data_handler = DataHandler()
        self.image_generator = ImageGenerator()

        self.current_plant = "tomato"
        self.plant_info = self.plant_model.plant_characteristics[self.current_plant]
        self.mode = 'controlled'
        self.baseline_image_path = None
        self.prediction = None
        self._pending_update = None
        self._user_values = {}
        self._images = self.theme.images  # keeps PhotoImage references alive

        self.default_params = {key: default for key, *_, default in PARAMETERS}
        self.env_params = {key: tk.DoubleVar(value=value) for key, value in self.default_params.items()}

        self.setup_ui()
        self.update_prediction()

    # Layout

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.setup_header()

        body = tk.Frame(self.root, bg=COLORS['bg'])
        body.grid(row=1, column=0, sticky='nsew', padx=18, pady=16)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.setup_control_panel(body)
        self.setup_visualization_panel(body)
        self.setup_results_panel(body)
        self.setup_status_bar()

    def setup_header(self):
        header = self.theme.header("WeGrow", "Plant growth forecasting  ·  Tomato")
        header.bar.grid(row=0, column=0, sticky='ew')
        tk.Label(header, text=f"  {date.today():%d %b %Y}  ", font=self.fonts['small'],
                 bg=COLORS['accent_soft'], fg=COLORS['accent_dark'], padx=6, pady=4).pack(side=tk.RIGHT)

    def setup_control_panel(self, parent):
        column = tk.Frame(parent, bg=COLORS['bg'], width=320)
        column.grid(row=0, column=0, sticky='nsew', padx=(0, 16))

        # Environment mode
        mode_card = self._card(column, "Environment")
        mode_card.outer.pack(fill=tk.X)

        self.select_mode_button = self.theme.segmented(
            mode_card, {mode: label for mode, (label, _) in MODES.items()}, self.set_mode, width=13)
        self.select_mode_button.frame.pack(fill=tk.X, pady=(10, 8))
        self.mode_description = self._label(mode_card, "", 'small', 'muted', anchor='w',
                                            justify='left', wraplength=280)
        self.mode_description.pack(fill=tk.X)

        # Parameters
        params_card = self._card(column, "Growing conditions")
        params_card.outer.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        self.value_labels, self.hint_labels, self.scales = {}, {}, {}
        hints = self._optimal_hints()
        for key, label, unit, lo, hi, step, _ in PARAMETERS:
            row = tk.Frame(params_card, bg=COLORS['card'])
            row.pack(fill=tk.X, pady=(10, 0))

            top = tk.Frame(row, bg=COLORS['card'])
            top.pack(fill=tk.X)
            self._label(top, label, 'body_bold').pack(side=tk.LEFT)
            hint = self._label(top, hints.get(key, ""), 'small', 'muted')
            hint.pack(side=tk.LEFT, padx=(8, 0))
            self.hint_labels[key] = (hint, hints.get(key, ""))
            value = self._label(top, "", 'body_bold', 'accent_dark')
            value.pack(side=tk.RIGHT)
            self.value_labels[key] = (value, unit, step)

            scale = ttk.Scale(row, from_=lo, to=hi, variable=self.env_params[key], orient=tk.HORIZONTAL,
                              style='Knob.Horizontal.TScale', command=lambda v, k=key: self.on_param_change(k, v))
            scale.pack(fill=tk.X, pady=(4, 0))
            self.scales[key] = scale

        ttk.Button(params_card, text="Reset to defaults", style='Ghost.TButton',
                   command=self.set_to_default).pack(fill=tk.X, side=tk.BOTTOM, pady=(14, 0))

        self.refresh_controls()

    def _optimal_hints(self):
        info = self.plant_info
        return {
            'temperature': "optimal %g–%g" % info['optimal_temp'],
            'humidity': "optimal %g–%g" % info['optimal_humidity'],
            'soil_acidity': "optimal %g–%g" % info['optimal_ph'],
            'brightness': "optimal ≥ 40k",
            'co2': "optimal ≥ 600",
            'pressure': "optimal %g–%g" % info.get('optimal_pressure', (990, 1030)),
        }

    def setup_visualization_panel(self, parent):
        column = tk.Frame(parent, bg=COLORS['bg'])
        column.grid(row=0, column=1, sticky='nsew')
        column.columnconfigure(0, weight=1)
        column.rowconfigure(1, weight=1)

        # KPI tiles
        kpis = tk.Frame(column, bg=COLORS['bg'])
        kpis.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        self.kpi_labels = {}
        tiles = [('health', "Health score"), ('height', "Final height"),
                 ('rate', "Growth rate"), ('yield', "Expected yield")]
        for i, (key, title) in enumerate(tiles):
            kpis.columnconfigure(i, weight=1, uniform='kpi')
            tile = self._card(kpis)
            tile.outer.grid(row=0, column=i, sticky='nsew', padx=(0 if i == 0 else 6, 0 if i == 3 else 6))
            self._label(tile, title, 'small', 'muted', anchor='w').pack(fill=tk.X)
            value = self._label(tile, "–", 'kpi', anchor='w')
            value.pack(fill=tk.X, pady=(2, 0))
            sub = self._label(tile, "", 'small', 'muted', anchor='w')
            sub.pack(fill=tk.X)
            self.kpi_labels[key] = (value, sub)

        notebook = ttk.Notebook(column)
        notebook.grid(row=1, column=0, sticky='nsew')
        self.setup_forecast_tab(notebook)
        self.setup_plant_evolution_tab(notebook)
        self.setup_my_plant_tab(notebook)

    def _tab(self, notebook, title):
        frame = tk.Frame(notebook, bg=COLORS['card'], highlightthickness=1,
                         highlightbackground=COLORS['border'], highlightcolor=COLORS['border'])
        notebook.add(frame, text=title)
        return frame

    def setup_forecast_tab(self, notebook):
        frame = self._tab(notebook, "Growth forecast")
        self.figure = Figure(figsize=(6, 3.6), dpi=100, facecolor=COLORS['card'], layout='constrained')
        self.ax = self.figure.add_subplot(111)
        self.chart = FigureCanvasTkAgg(self.figure, master=frame)
        self.chart.get_tk_widget().configure(bg=COLORS['card'], highlightthickness=0)
        self.chart.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    def setup_plant_evolution_tab(self, notebook):
        frame = self._tab(notebook, "Evolution")
        grid = tk.Frame(frame, bg=COLORS['card'])
        grid.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self.evolution_cells = []
        for i in range(6):
            r, c = divmod(i, 3)
            grid.columnconfigure(c, weight=1, uniform='evo')
            grid.rowconfigure(r, weight=1, uniform='evo')
            cell = tk.Frame(grid, bg=COLORS['card'])
            cell.grid(row=r, column=c, sticky='nsew', padx=6, pady=6)
            image = tk.Label(cell, bg=COLORS['card'])
            image.pack()
            title = self._label(cell, "", 'body_bold')
            title.pack(pady=(6, 0))
            sub = self._label(cell, "", 'small', 'muted')
            sub.pack()
            self.evolution_cells.append((image, title, sub))

    def setup_my_plant_tab(self, notebook):
        frame = self._tab(notebook, "My plant")
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        left = tk.Frame(frame, bg=COLORS['card'])
        left.grid(row=0, column=0, sticky='n', padx=16, pady=16)
        self.photo_label = tk.Label(left, bg=COLORS['track'], fg=COLORS['muted'], font=self.fonts['body'],
                                    text="No photo yet\n\nLoad a picture of your plant", width=40, height=14)
        self.photo_label.pack()
        buttons = tk.Frame(left, bg=COLORS['card'])
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text="Load photo…", style='Ghost.TButton',
                   command=self.load_baseline_image).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(buttons, text="Remove", style='Ghost.TButton',
                   command=self.clear_baseline_image).pack(side=tk.LEFT, padx=(8, 0))

        right = tk.Frame(frame, bg=COLORS['card'])
        right.grid(row=0, column=1, sticky='nsew', padx=(0, 16), pady=16)
        self._label(right, "Notes", 'h2', anchor='w').pack(fill=tk.X)
        self._label(right, "Variety, planting date, anything worth recording.", 'small', 'muted',
                    anchor='w').pack(fill=tk.X, pady=(2, 8))
        self.plant_info_text = tk.Text(right, height=8, wrap=tk.WORD, font=self.fonts['body'],
                                       bg=COLORS['bg'], fg=COLORS['text'], relief=tk.FLAT,
                                       highlightthickness=1, highlightbackground=COLORS['border'],
                                       highlightcolor=COLORS['accent'], padx=10, pady=8,
                                       insertbackground=COLORS['text'])
        self.plant_info_text.pack(fill=tk.BOTH, expand=True)

        ttk.Button(right, text="Submit plant data", style='Accent.TButton',
                   command=self.submit_plant_data).pack(fill=tk.X, pady=(12, 0))
        self.submit_feedback = self._label(right, "", 'small', 'accent_dark', anchor='w',
                                           justify='left', wraplength=380)
        self.submit_feedback.pack(fill=tk.X, pady=(8, 0))

    def setup_results_panel(self, parent):
        column = tk.Frame(parent, bg=COLORS['bg'], width=300)
        column.grid(row=0, column=2, sticky='nsew', padx=(16, 0))

        factors_card = self._card(column, "Condition scores", "How close each factor is to ideal")
        factors_card.outer.pack(fill=tk.X)
        self.factor_rows = {}
        for key, label in FACTOR_LABELS.items():
            row = tk.Frame(factors_card, bg=COLORS['card'])
            row.pack(fill=tk.X, pady=(10, 0))
            self._label(row, label, 'small', width=11, anchor='w').pack(side=tk.LEFT)
            bar = tk.Canvas(row, width=130, height=8, bg=COLORS['card'], highlightthickness=0)
            bar.pack(side=tk.LEFT, padx=(4, 8))
            pct = self._label(row, "", 'small', 'muted', width=5, anchor='e')
            pct.pack(side=tk.RIGHT)
            self.factor_rows[key] = (bar, pct)

        phases_card = self._card(column, "Growth phases")
        phases_card.outer.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        for i, phase in enumerate(self.plant_model._generate_phase_info(self.plant_info)):
            row = tk.Frame(phases_card, bg=COLORS['card'])
            row.pack(fill=tk.X, pady=(10, 0))
            dot = tk.Canvas(row, width=10, height=10, bg=COLORS['card'], highlightthickness=0)
            dot.create_oval(1, 1, 9, 9, fill=PHASE_COLORS[i % len(PHASE_COLORS)], outline='')
            dot.pack(side=tk.LEFT, padx=(0, 8))
            self._label(row, phase['name'], 'body').pack(side=tk.LEFT)
            self._label(row, f"Day {phase['start'] + 1}–{phase['end'] + 1}", 'small', 'muted').pack(side=tk.RIGHT)

        self.optimal_label = self._label(phases_card, "", 'small', 'muted', anchor='w',
                                         justify='left', wraplength=260)
        self.optimal_label.pack(fill=tk.X, pady=(16, 0))

    def setup_status_bar(self):
        bar = tk.Frame(self.root, bg=COLORS['card'], highlightthickness=1,
                       highlightbackground=COLORS['border'])
        bar.grid(row=2, column=0, sticky='ew')
        self.status_label = self._label(bar, "", 'small', 'muted', anchor='w')
        self.status_label.pack(side=tk.LEFT, padx=20, pady=6)
        self._label(bar, "Rule-based growth simulator · data saved to PlantDashboard/data",
                    'small', 'muted').pack(side=tk.RIGHT, padx=20)

    def set_status(self, text, error=False):
        self.status_label.configure(text=text, fg=COLORS['bad'] if error else COLORS['muted'])

    # Events

    def set_mode(self, mode):
        if mode == self.mode:
            return
        if mode == 'open':
            self._user_values = {k: self.env_params[k].get() for k in WEATHER_PARAMS}
            for key, value in simulated_weather().items():
                self.env_params[key].set(value)
        elif self.mode == 'open':
            for key, value in self._user_values.items():
                self.env_params[key].set(value)
        self.mode = mode
        self.refresh_controls()
        self.update_prediction()

    def on_param_change(self, param, raw_value):
        step = next(p[5] for p in PARAMETERS if p[0] == param)
        self.env_params[param].set(round(round(float(raw_value) / step) * step, 2))
        self._refresh_value_label(param)
        self.schedule_update()

    def schedule_update(self, delay=120):
        """Debounce slider drags so the forecast is recomputed once the user pauses"""
        if self._pending_update:
            self.root.after_cancel(self._pending_update)
        self._pending_update = self.root.after(delay, self.update_prediction)

    def set_to_default(self):
        """Reset all parameters and the mode to their defaults"""
        for key, value in self.default_params.items():
            self.env_params[key].set(value)
        self.mode = 'controlled'
        self.refresh_controls()
        self.update_prediction()

    def refresh_controls(self):
        self.select_mode_button(self.mode)
        self.mode_description.configure(text=MODES[self.mode][1])

        for key, scale in self.scales.items():
            locked = self.mode == 'open' and key in WEATHER_PARAMS
            scale.state(['disabled'] if locked else ['!disabled'])
            hint, default_hint = self.hint_labels[key]
            if locked:
                hint.configure(text="from weather", fg=COLORS['accent'])
            else:
                hint.configure(text=default_hint, fg=COLORS['muted'])
            self._refresh_value_label(key)

    def _refresh_value_label(self, key):
        label, unit, step = self.value_labels[key]
        value = self.env_params[key].get()
        label.configure(text=f"{format_value(value, step)} {unit}".strip())

    def load_baseline_image(self):
        file_path = filedialog.askopenfilename(
            title="Select a photo of your plant",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"), ("All files", "*")]
        )
        if not file_path:
            return
        try:
            self._images['photo_full'] = ImageTk.PhotoImage(self.image_generator.photo_thumbnail(file_path))
        except OSError as e:
            self.set_status(f"Could not open image: {e}", error=True)
            return
        self.baseline_image_path = file_path
        self.photo_label.configure(image=self._images['photo_full'], text="", width=0, height=0)
        self.set_status(f"Loaded photo {os.path.basename(file_path)}")
        self.update_prediction()

    def clear_baseline_image(self):
        self.baseline_image_path = None
        self.photo_label.configure(image='', text="No photo yet\n\nLoad a picture of your plant",
                                   width=40, height=14)
        self.update_prediction()

    def current_params(self):
        params = {key: var.get() for key, var in self.env_params.items()}
        params['plant_type'] = self.current_plant
        params['ambient_mode'] = self.mode
        return params

    def submit_plant_data(self):
        """Save parameters, notes, photo and forecast to data/submissions/<id>/"""
        if self.prediction is None:
            return
        params = self.current_params()
        p = self.prediction
        payload = {
            'submitted_at': datetime.now().isoformat(timespec='seconds'),
            'plant_type': params.pop('plant_type'),
            'ambient_mode': params.pop('ambient_mode'),
            'parameters': params,
            'notes': self.plant_info_text.get("1.0", tk.END).strip(),
            'forecast': {
                'final_height_cm': round(p['final_height'], 2),
                'growth_rate_cm_per_day': round(p['growth_rate'], 3),
                'health_score': round(p['health_score'], 1),
                'optimal_conditions_pct': round(p['optimal_conditions'], 1),
                'expected_yield': p['yield'],
                'phases': p['phases'],
                'condition_scores': {k: round(v, 3) for k, v in p['stress_factors'].items()},
                'daily_height_cm': [round(h, 2) for h in p['growth_stages']],
            },
        }
        try:
            submission_id, folder = self.data_handler.save_submission(payload, self.baseline_image_path)
        except OSError as e:
            self.submit_feedback.configure(text=f"Submission failed: {e}", fg=COLORS['bad'])
            self.set_status(f"Submission failed: {e}", error=True)
            return
        rel = os.path.relpath(folder, BASE_DIR)
        self.submit_feedback.configure(text=f"✓ Submitted #{submission_id}  ·  saved to {rel}",
                                       fg=COLORS['accent_dark'])
        self.set_status(f"Submission {submission_id} saved to {rel}")

    # Rendering

    def update_prediction(self):
        self._pending_update = None
        try:
            prediction = self.plant_model.predict_growth(self.current_params())
            self.prediction = prediction
            self.update_kpis(prediction)
            self.update_chart(prediction)
            self.generate_plant_evolution(prediction)
            self.update_results_display(prediction)
        except Exception as e:
            self.set_status(f"Could not update the forecast: {e}", error=True)
            return
        self.set_status(f"Forecast updated {datetime.now():%H:%M:%S}  ·  {MODES[self.mode][0]} mode")

    def update_kpis(self, p):
        health = p['health_score']
        weakest, weakest_score = min(p['stress_factors'].items(), key=lambda kv: kv[1])
        if health >= 85:
            health_color, health_text = COLORS['accent'], "Excellent conditions"
        elif health >= 70:
            health_color, health_text = COLORS['accent'], "Good conditions"
        elif health >= 50:
            health_color, health_text = COLORS['warn'], "Plant under stress"
        else:
            health_color, health_text = COLORS['bad'], "Poor conditions"
        if weakest_score < 0.6:
            health_text = f"Limited by {FACTOR_LABELS[weakest].lower()}"
            if health >= 70:
                health_color = COLORS['warn']

        value, sub = self.kpi_labels['health']
        value.configure(text=f"{health:.0f}%", fg=health_color)
        sub.configure(text=health_text)

        value, sub = self.kpi_labels['height']
        value.configure(text=f"{p['final_height']:.0f} cm")
        sub.configure(text=f"of {p['max_height']} cm potential")

        value, sub = self.kpi_labels['rate']
        value.configure(text=f"{p['growth_rate']:.2f}")
        sub.configure(text=f"cm/day over {len(p['growth_stages'])} days")

        value, sub = self.kpi_labels['yield']
        value.configure(text=p.get('yield', 'N/A'))
        sub.configure(text="per plant")

    def update_chart(self, p):
        ax = self.ax
        ax.clear()
        heights = p['growth_stages']
        days = list(range(1, len(heights) + 1))
        top = p['max_height'] * 1.12

        for i, phase in enumerate(p['phases']):
            color = PHASE_COLORS[i % len(PHASE_COLORS)]
            ax.axvspan(phase['start'] + 0.5, phase['end'] + 1.5, color=color, alpha=0.08, lw=0)
            if phase['end'] - phase['start'] < 10:
                continue  # too narrow for a label; the legend on the right lists every phase
            ax.text((phase['start'] + phase['end']) / 2 + 1, top * 0.97, phase['name'],
                    ha='center', va='top', fontsize=8, color=color, fontweight='bold')

        ax.plot(days, heights, color=COLORS['accent'], lw=2.4, solid_capstyle='round')
        ax.fill_between(days, heights, color=COLORS['accent'], alpha=0.10, lw=0)
        ax.axhline(p['max_height'], color=COLORS['muted'], lw=1, ls=(0, (4, 4)), alpha=0.6)
        ax.text(days[-1], p['max_height'], "potential", ha='right', va='bottom', fontsize=8,
                color=COLORS['muted'])

        ax.scatter([days[-1]], [heights[-1]], s=40, color=COLORS['accent_dark'], zorder=3)
        ax.annotate(f"{heights[-1]:.0f} cm", (days[-1], heights[-1]), xytext=(-8, 8),
                    textcoords='offset points', ha='right', va='bottom', fontsize=9, fontweight='bold',
                    color=COLORS['accent_dark'])

        ax.set_xlim(1, days[-1] + 1)
        ax.set_ylim(0, top)
        ax.set_xlabel("Day", color=COLORS['muted'], fontsize=9)
        ax.set_ylabel("Height (cm)", color=COLORS['muted'], fontsize=9)
        style_axes(ax)
        self.chart.draw_idle()

    def generate_plant_evolution(self, p):
        """Render the day-0 state plus five snapshots across the season"""
        thumb_size = (240, 180)
        if self.baseline_image_path:
            first = self.image_generator.photo_thumbnail(self.baseline_image_path)
            first_title, first_sub = "Today", "your photo"
        else:
            first = self.image_generator.generate_plant_image(self.current_plant, 0, p['health_score'], 0)
            first_title, first_sub = "Day 0", "seedling"

        frames = [(first, first_title, first_sub)]
        for frame in self.image_generator.generate_evolution(self.current_plant, p):
            frames.append((frame['image'], f"Day {frame['day']}  ·  {self._phase_for_day(p, frame['day'] - 1)}",
                           f"{frame['height']:.1f} cm"))

        for i, (image, title, sub) in enumerate(frames[:len(self.evolution_cells)]):
            image_label, title_label, sub_label = self.evolution_cells[i]
            photo = ImageTk.PhotoImage(image.resize(thumb_size, Image.Resampling.LANCZOS))
            self._images[f'evo{i}'] = photo
            image_label.configure(image=photo)
            title_label.configure(text=title)
            sub_label.configure(text=sub)

    @staticmethod
    def _phase_for_day(p, day_index):
        for phase in p['phases']:
            if phase['start'] <= day_index <= phase['end']:
                return phase['name']
        return p['phases'][-1]['name'] if p['phases'] else ""

    def update_results_display(self, p):
        for key, (bar, pct) in self.factor_rows.items():
            score = p['stress_factors'].get(key, 0.0)
            color = status_color(score)
            bar.delete('all')
            width = int(bar['width'])
            self._rounded_bar(bar, 0, width, COLORS['track'])
            self._rounded_bar(bar, 0, max(8, int(width * score)), color)
            pct.configure(text=f"{score * 100:.0f}%")

        met = round(p['optimal_conditions'] / 100 * 3)
        self.optimal_label.configure(
            text=f"{met} of 3 key ranges (temperature, humidity, pH) are in the optimal zone.")

    @staticmethod
    def _rounded_bar(canvas, x0, x1, color, h=8):
        r = h / 2
        canvas.create_oval(x0, 0, x0 + h, h, fill=color, outline='')
        canvas.create_oval(x1 - h, 0, x1, h, fill=color, outline='')
        if x1 - x0 > h:
            canvas.create_rectangle(x0 + r, 0, x1 - r, h, fill=color, outline='')


def main():
    root = tk.Tk()
    PlantGrowthDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
