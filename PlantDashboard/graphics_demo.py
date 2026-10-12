"""
WeGrow Lab - interactive plant growth graphics demo

Every chart is driven by the same PlantGrowthModel as the main dashboard.
"""

import random
import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
import numpy as np
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from matplotlib.figure import Figure
from PIL import Image, ImageDraw, ImageTk

from image_generator import ImageGenerator
from main_dashboard import PARAMETERS, FACTOR_LABELS, format_value
from plant_model import PlantGrowthModel
from theme import Theme, COLORS, status_color, style_axes

MODES = {
    'controlled': ('Controlled', "Fixed conditions, a single predictable forecast."),
    'semi-controlled': ('Dynamic', "Natural variation, shown as a range."),
    'open': ('Chaotic', "Open field: the weather drifts live."),
}

PHASE_COLORS = {
    'Germination': '#c9a25f', 'Seedling': '#8cbf5a', 'Vegetative': '#2e9e5b',
    'Flowering': '#e06c9f', 'Fruiting': '#e5533d', 'Mature': '#5f8f3a',
}

# Realistic ranges used by "Randomize"
RANDOM_RANGES = {
    'temperature': (8, 35), 'humidity': (30, 90), 'soil_acidity': (5.0, 8.0),
    'brightness': (10000, 90000), 'water': (30, 100), 'nutrients': (30, 100),
    'co2': (300, 1000), 'pressure': (970, 1040),
}

# Per-tick weather drift in Chaotic mode
DRIFT = {'temperature': 0.5, 'humidity': 1.5, 'brightness': 1500, 'water': 1.0}

SCORE_CMAP = LinearSegmentedColormap.from_list(
    'wegrow', [COLORS['bad'], COLORS['warn'], '#a8d5b5', COLORS['accent']])

ENSEMBLE_RUNS = 12
ANIMATION_SECONDS = 4.0

# Short axis labels for the radar
RADAR_LABELS = {
    'temperature': 'Temp', 'humidity': 'Humidity', 'ph': 'pH', 'water': 'Water',
    'nutrients': 'Nutrients', 'light': 'Light', 'co2': 'CO₂', 'pressure': 'Pressure',
}


class PlantGrowthGraphicsDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("WeGrow Lab · Growth Simulator")
        self.root.geometry("1440x900")
        self.root.minsize(1240, 800)

        self.theme = Theme(root)
        self.fonts = self.theme.fonts
        self._images = self.theme.images

        self.model = PlantGrowthModel()
        self.image_generator = ImageGenerator()

        self.current_plant = tk.StringVar(value="tomato")
        self.ambient_mode = tk.StringVar(value="controlled")
        self.default_params = {key: default for key, *_, default in PARAMETERS}
        self.env_params = {key: tk.DoubleVar(value=v) for key, v in self.default_params.items()}
        self.param_spec = {p[0]: p for p in PARAMETERS}

        self.prediction = None
        self.ensemble = None
        self._pending_update = None
        self._dirty_tabs = set()
        self._animation = None

        self.setup_ui()
        self.update_all_graphics()
        self.auto_update()

    # Layout

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = self.theme.header("WeGrow Lab", "Interactive growth simulator  ·  powered by the WeGrow model")
        header.bar.grid(row=0, column=0, sticky='ew')
        ttk.Button(header, text="Reset", style='Ghost.TButton', command=self.reset_demo).pack(side=tk.RIGHT)
        ttk.Button(header, text="Randomize", style='Ghost.TButton',
                   command=self.randomize_parameters).pack(side=tk.RIGHT, padx=8)
        self.animate_button = ttk.Button(header, text="▶  Animate growth", style='Accent.TButton',
                                         command=self.animate_growth)
        self.animate_button.pack(side=tk.RIGHT)

        body = tk.Frame(self.root, bg=COLORS['bg'])
        body.grid(row=1, column=0, sticky='nsew', padx=18, pady=16)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.setup_control_panel(body)
        self.setup_main_visualization(body)
        self.setup_additional_graphics(body)

        bar = tk.Frame(self.root, bg=COLORS['card'], highlightthickness=1, highlightbackground=COLORS['border'])
        bar.grid(row=2, column=0, sticky='ew')
        self.status_label = self.theme.label(bar, "", 'small', 'muted')
        self.status_label.pack(side=tk.LEFT, padx=20, pady=6)

    def setup_control_panel(self, parent):
        column = tk.Frame(parent, bg=COLORS['bg'])
        column.grid(row=0, column=0, sticky='nsew', padx=(0, 16))

        plant_card = self.theme.card(column, "Plant")
        plant_card.outer.pack(fill=tk.X)
        chips = tk.Frame(plant_card, bg=COLORS['card'])
        chips.pack(fill=tk.X, pady=(10, 0))
        self.plant_chips = {}
        for i, plant in enumerate(self.model.plant_characteristics):
            chip = tk.Label(chips, text=plant.title(), cursor='hand2', pady=6, width=11,
                            highlightthickness=1)
            chip.grid(row=i // 3, column=i % 3, padx=3, pady=3, sticky='ew')
            chip.bind("<Button-1>", lambda _e, p=plant: self.on_plant_change(p))
            self.plant_chips[plant] = chip
            chips.columnconfigure(i % 3, weight=1)

        mode_card = self.theme.card(column, "Scenario")
        mode_card.outer.pack(fill=tk.X, pady=(12, 0))
        self.select_mode = self.theme.segmented(
            mode_card, {m: label for m, (label, _) in MODES.items()}, self.on_mode_change, width=10)
        self.select_mode.frame.pack(fill=tk.X, pady=(10, 8))
        self.mode_description = self.theme.label(mode_card, "", 'small', 'muted', anchor='w',
                                                  justify='left', wraplength=280)
        self.mode_description.pack(fill=tk.X)

        params_card = self.theme.card(column, "Parameters")
        params_card.outer.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.value_labels, self.hint_labels = {}, {}
        for key, label, unit, lo, hi, step, _ in PARAMETERS:
            row = tk.Frame(params_card, bg=COLORS['card'])
            row.pack(fill=tk.X, pady=(8, 0))
            top = tk.Frame(row, bg=COLORS['card'])
            top.pack(fill=tk.X)
            self.theme.label(top, label, 'body_bold').pack(side=tk.LEFT)
            hint = self.theme.label(top, "", 'small', 'muted')
            hint.pack(side=tk.LEFT, padx=(8, 0))
            self.hint_labels[key] = hint
            value = self.theme.label(top, "", 'body_bold', 'accent_dark')
            value.pack(side=tk.RIGHT)
            self.value_labels[key] = value
            ttk.Scale(row, from_=lo, to=hi, variable=self.env_params[key], orient=tk.HORIZONTAL,
                      style='Knob.Horizontal.TScale',
                      command=lambda v, k=key: self.on_param_change(k, v)).pack(fill=tk.X, pady=(2, 0))

        self.refresh_controls()

    def _figure_tab(self, title, figsize=(7, 5), **subplot_kw):
        frame = tk.Frame(self.notebook, bg=COLORS['card'], highlightthickness=1,
                         highlightbackground=COLORS['border'], highlightcolor=COLORS['border'])
        self.notebook.add(frame, text=title)
        fig = Figure(figsize=figsize, dpi=100, facecolor=COLORS['card'], layout='constrained')
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().configure(bg=COLORS['card'], highlightthickness=0)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        return frame, fig, canvas

    def setup_main_visualization(self, parent):
        column = tk.Frame(parent, bg=COLORS['bg'])
        column.grid(row=0, column=1, sticky='nsew')
        column.rowconfigure(0, weight=1)
        column.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(column)
        self.notebook.grid(row=0, column=0, sticky='nsew')
        self.setup_growth_chart_tab()
        self.setup_plant_evolution_tab()
        self.setup_heatmap_tab()
        self.setup_3d_visualization_tab()
        self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self.render_visible_tab())

    def setup_growth_chart_tab(self):
        _, self.fig, self.canvas = self._figure_tab("Growth chart")
        self.ax = self.fig.add_subplot(111)

    def setup_plant_evolution_tab(self):
        frame = tk.Frame(self.notebook, bg=COLORS['card'], highlightthickness=1,
                         highlightbackground=COLORS['border'], highlightcolor=COLORS['border'])
        self.notebook.add(frame, text="Plant evolution")
        grid = tk.Frame(frame, bg=COLORS['card'])
        grid.pack(expand=True, padx=12, pady=12)
        self.evolution_cells = []
        for i in range(5):
            # Three on top, two centred below
            r, c = (0, i * 2) if i < 3 else (1, (i - 3) * 2 + 1)
            cell = tk.Frame(grid, bg=COLORS['card'])
            cell.grid(row=r, column=c, columnspan=2, padx=8, pady=8)
            image = tk.Label(cell, bg=COLORS['card'])
            image.pack()
            title = self.theme.label(cell, "", 'body_bold')
            title.pack(pady=(6, 0))
            sub = self.theme.label(cell, "", 'small', 'muted')
            sub.pack()
            self.evolution_cells.append((image, title, sub))

    def setup_heatmap_tab(self):
        _, self.heatmap_fig, self.heatmap_canvas = self._figure_tab("Parameter heatmap")
        gs = self.heatmap_fig.add_gridspec(1, 2, width_ratios=(30, 1))
        self.heatmap_ax = self.heatmap_fig.add_subplot(gs[0])
        self.heatmap_cbar_ax = self.heatmap_fig.add_subplot(gs[1])

    def setup_3d_visualization_tab(self):
        _, self.fig_3d, self.canvas_3d = self._figure_tab("3D analysis")
        self.ax_3d = self.fig_3d.add_subplot(111, projection='3d', computed_zorder=False)

    def setup_additional_graphics(self, parent):
        column = tk.Frame(parent, bg=COLORS['bg'], width=310)
        column.grid(row=0, column=2, sticky='nsew', padx=(16, 0))

        stats_card = self.theme.card(column, "Live statistics")
        stats_card.outer.pack(fill=tk.X)
        tiles = tk.Frame(stats_card, bg=COLORS['card'])
        tiles.pack(fill=tk.X, pady=(6, 0))
        self.stat_labels = {}
        for i, (key, title) in enumerate([('height', "Final height"), ('rate', "Growth rate"),
                                          ('yield', "Expected yield"), ('days', "Season")]):
            tile = tk.Frame(tiles, bg=COLORS['card'])
            tile.grid(row=i // 2, column=i % 2, sticky='w', pady=(6, 0))
            tiles.columnconfigure(i % 2, weight=1, uniform='stat')
            self.theme.label(tile, title, 'small', 'muted').pack(anchor='w')
            value = self.theme.label(tile, "–", 'h2')
            value.pack(anchor='w')
            self.stat_labels[key] = value

        health_card = self.theme.card(column, "Plant health")
        health_card.outer.pack(fill=tk.X, pady=(12, 0))
        self.gauge_label = tk.Label(health_card, bg=COLORS['card'])
        self.gauge_label.pack(pady=(6, 0))
        self.health_status = self.theme.label(health_card, "", 'small', 'muted')
        self.health_status.pack()

        radar_card = self.theme.card(column, "Condition radar", "Score per factor; dashed ring = ideal")
        radar_card.outer.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.radar_fig = Figure(figsize=(3.0, 3.0), dpi=100, facecolor=COLORS['card'], layout='constrained')
        self.radar_ax = self.radar_fig.add_subplot(111, projection='polar')
        self.radar_canvas = FigureCanvasTkAgg(self.radar_fig, master=radar_card)
        self.radar_canvas.get_tk_widget().configure(bg=COLORS['card'], highlightthickness=0)
        self.radar_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    # Events

    def on_plant_change(self, plant):
        self.current_plant.set(plant)
        self.refresh_controls()
        self.update_all_graphics()

    def on_mode_change(self, mode):
        self.ambient_mode.set(mode)
        self.refresh_controls()
        self.update_all_graphics()

    def on_param_change(self, param, raw_value=None):
        step = self.param_spec[param][5]
        if raw_value is not None:
            self.env_params[param].set(round(round(float(raw_value) / step) * step, 2))
        self._refresh_value_label(param)
        self.schedule_update()

    def schedule_update(self, delay=120):
        if self._pending_update:
            self.root.after_cancel(self._pending_update)
        self._pending_update = self.root.after(delay, self.update_all_graphics)

    def refresh_controls(self):
        plant = self.current_plant.get()
        for name, chip in self.plant_chips.items():
            chosen = name == plant
            chip.configure(bg=COLORS['accent_soft'] if chosen else COLORS['card'],
                           fg=COLORS['accent_dark'] if chosen else COLORS['text'],
                           font=self.fonts['small_bold'] if chosen else self.fonts['small'],
                           highlightbackground=COLORS['accent'] if chosen else COLORS['border'])
        self.select_mode(self.ambient_mode.get())
        self.mode_description.configure(text=MODES[self.ambient_mode.get()][1])

        info = self.model.plant_characteristics[plant]
        hints = {
            'temperature': "optimal %g–%g" % info['optimal_temp'],
            'humidity': "optimal %g–%g" % info['optimal_humidity'],
            'soil_acidity': "optimal %g–%g" % info['optimal_ph'],
            'brightness': "optimal ≥ 40k",
            'co2': "optimal ≥ 600",
            'pressure': "optimal %g–%g" % info.get('optimal_pressure', (990, 1030)),
        }
        for key, hint in self.hint_labels.items():
            hint.configure(text=hints.get(key, ""))
            self._refresh_value_label(key)

    def _refresh_value_label(self, key):
        _, _, unit, _, _, step, _ = self.param_spec[key]
        value = self.env_params[key].get()
        self.value_labels[key].configure(text=f"{format_value(value, step)} {unit}".strip())

    def current_params(self, **overrides):
        params = {key: var.get() for key, var in self.env_params.items()}
        params['plant_type'] = self.current_plant.get()
        params['ambient_mode'] = self.ambient_mode.get()
        params.update(overrides)
        return params

    # Rendering

    def update_all_graphics(self):
        self._pending_update = None
        self.stop_animation()
        params = self.current_params()
        self.prediction = self.model.predict_growth(params)
        if params['ambient_mode'] == 'controlled':
            self.ensemble = None
        else:
            runs = [self.model.predict_growth(params, seed=s)['growth_stages'] for s in range(ENSEMBLE_RUNS)]
            self.ensemble = np.array(runs)

        self.update_statistics()
        self.update_health_indicator()
        self.update_radar_chart()
        self._dirty_tabs = {0, 1, 2, 3}
        self.render_visible_tab()
        self.status_label.configure(
            text=f"Updated {datetime.now():%H:%M:%S}  ·  {self.current_plant.get().title()}  ·  "
                 f"{MODES[self.ambient_mode.get()][0]} scenario")

    def render_visible_tab(self):
        """Only the visible tab is redrawn; the others are refreshed when opened"""
        index = self.notebook.index(self.notebook.select())
        if index not in self._dirty_tabs or self.prediction is None:
            return
        self._dirty_tabs.discard(index)
        [self.update_growth_chart, self.update_plant_evolution,
         self.update_parameter_heatmap, self.update_3d_visualization][index]()

    def update_growth_chart(self):
        p = self.prediction
        ax = self.ax
        ax.clear()
        heights = np.array(p['growth_stages'])
        days = np.arange(1, len(heights) + 1)
        top = p['max_height'] * 1.12

        for phase in p['phases']:
            color = PHASE_COLORS.get(phase['name'], COLORS['muted'])
            ax.axvspan(phase['start'] + 0.5, phase['end'] + 1.5, color=color, alpha=0.08, lw=0)
            if (phase['end'] - phase['start']) / len(days) >= 0.1:
                ax.text((phase['start'] + phase['end']) / 2 + 1, top * 0.97, phase['name'],
                        ha='center', va='top', fontsize=8, color=color, fontweight='bold')

        if self.ensemble is not None:
            low, high = self.ensemble.min(axis=0), self.ensemble.max(axis=0)
            ax.fill_between(days, low, high, color=COLORS['accent'], alpha=0.18, lw=0,
                            label=f"range of {ENSEMBLE_RUNS} simulations")
            heights = np.median(self.ensemble, axis=0)
        else:
            ax.fill_between(days, heights, color=COLORS['accent'], alpha=0.10, lw=0)
        ax.plot(days, heights, color=COLORS['accent'], lw=2.4, solid_capstyle='round',
                label="expected height")
        ax.axhline(p['max_height'], color=COLORS['muted'], lw=1, ls=(0, (4, 4)), alpha=0.6)
        ax.text(2, p['max_height'], "potential", ha='left', va='bottom', fontsize=8,
                color=COLORS['muted'])

        # Playhead used by the growth animation
        self.chart_heights = heights
        self.playhead_line = ax.axvline(days[-1], color=COLORS['accent_dark'], lw=1, alpha=0)
        self.playhead_dot, = ax.plot([days[-1]], [heights[-1]], 'o', ms=7, color=COLORS['accent_dark'], zorder=4)
        self.playhead_text = ax.annotate(f"{heights[-1]:.0f} cm", (days[-1], heights[-1]), xytext=(-8, 8),
                                         textcoords='offset points', ha='right', va='bottom', fontsize=9,
                                         fontweight='bold', color=COLORS['accent_dark'])

        ax.set_xlim(1, days[-1] + 1)
        ax.set_ylim(0, top)
        ax.set_xlabel("Day", color=COLORS['muted'], fontsize=9)
        ax.set_ylabel("Height (cm)", color=COLORS['muted'], fontsize=9)
        ax.set_title(f"{self.current_plant.get().title()} growth simulation", loc='left',
                     fontsize=12, fontweight='bold', color=COLORS['text'], pad=12)
        if self.ensemble is not None:
            ax.legend(loc='lower right', frameon=False, fontsize=8,
                      labelcolor=COLORS['muted'])
        style_axes(ax)
        self.canvas.draw_idle()

    def update_plant_evolution(self):
        p = self.prediction
        frames = self.image_generator.generate_evolution(self.current_plant.get(), p)
        for i, (cell, frame) in enumerate(zip(self.evolution_cells, frames)):
            image_label, title, sub = cell
            photo = ImageTk.PhotoImage(frame['image'].resize((220, 165), Image.Resampling.LANCZOS))
            self._images[f'evo{i}'] = photo
            image_label.configure(image=photo)
            phase = next((ph['name'] for ph in p['phases'] if ph['start'] <= frame['day'] - 1 <= ph['end']),
                         p['phases'][-1]['name'])
            title.configure(text=f"Stage {i + 1}  ·  {phase}")
            sub.configure(text=f"Day {frame['day']}  ·  {frame['height']:.1f} cm")

    def update_parameter_heatmap(self):
        """Health score across temperature × humidity, all other parameters as set"""
        ax, cax = self.heatmap_ax, self.heatmap_cbar_ax
        ax.clear()
        cax.clear()
        temps = np.arange(5, 45, 5)
        humids = np.arange(100, 10, -10)
        grid = np.array([[self.model.predict_growth(
            self.current_params(temperature=float(t), humidity=float(h), ambient_mode='controlled')
        )['health_score'] for t in temps] for h in humids])

        sns.heatmap(grid, ax=ax, cbar_ax=cax, cmap=SCORE_CMAP, vmin=50, vmax=100,
                    annot=True, fmt='.0f', annot_kws={'fontsize': 8},
                    linewidths=2, linecolor=COLORS['card'],
                    xticklabels=[f"{t}°" for t in temps], yticklabels=[f"{h}%" for h in humids],
                    cbar_kws={'label': 'Health score'})

        # Optimal zone and current conditions, in cell coordinates
        info = self.model.plant_characteristics[self.current_plant.get()]
        to_x = lambda t: (t - temps[0]) / 5 + 0.5
        to_y = lambda h: (humids[0] - h) / 10 + 0.5
        (t0, t1), (h0, h1) = info['optimal_temp'], info['optimal_humidity']
        cols = [i for i, t in enumerate(temps) if t0 <= t <= t1]
        rows = [i for i, h in enumerate(humids) if h0 <= h <= h1]
        if cols and rows:
            ax.add_patch(Rectangle((cols[0], rows[0]), len(cols), len(rows), fill=False,
                                   ec=COLORS['text'], lw=1.8, ls=(0, (4, 3)), zorder=4))
        ax.scatter([to_x(self.env_params['temperature'].get())], [to_y(self.env_params['humidity'].get())],
                   s=180, marker='*', color='white', edgecolor=COLORS['text'], lw=1.2, zorder=5,
                   clip_on=False)

        ax.set_title(f"{self.current_plant.get().title()}: health by temperature and humidity", loc='left',
                     fontsize=12, fontweight='bold', color=COLORS['text'], pad=12)
        ax.set_xlabel("Temperature  (★ current, dashed box = optimal zone)", color=COLORS['muted'], fontsize=9)
        ax.set_ylabel("Humidity", color=COLORS['muted'], fontsize=9)
        ax.tick_params(colors=COLORS['muted'], labelsize=8, length=0)
        cax.tick_params(colors=COLORS['muted'], labelsize=8, length=0)
        cax.yaxis.label.set_color(COLORS['muted'])
        self.heatmap_canvas.draw_idle()

    def update_3d_visualization(self):
        """Final height surface across temperature × water"""
        ax = self.ax_3d
        ax.clear()
        temps = np.linspace(0, 45, 28)
        waters = np.linspace(0, 100, 28)
        T, W = np.meshgrid(temps, waters)
        Z = np.vectorize(lambda t, w: self.model.predict_growth(
            self.current_params(temperature=float(t), water=float(w), ambient_mode='controlled'), seed=0
        )['final_height'])(T, W)

        ax.plot_surface(T, W, Z, cmap=SCORE_CMAP, rstride=1, cstride=1, lw=0, antialiased=True, alpha=0.9)
        t, w = self.env_params['temperature'].get(), self.env_params['water'].get()
        z = self.model.predict_growth(self.current_params(ambient_mode='controlled'), seed=0)['final_height']
        ax.plot([t, t], [w, w], [0, z], color=COLORS['text'], lw=1, ls=':', zorder=5)
        ax.scatter([t], [w], [z], s=260, marker='*', color='white', edgecolor=COLORS['text'], lw=1.4,
                   depthshade=False, zorder=6)
        ax.text(t, w, z * 1.08, f"  now: {z:.0f} cm", color=COLORS['text'], fontsize=9,
                fontweight='bold', zorder=7)

        ax.set_title(f"{self.current_plant.get().title()}: final height by temperature and water",
                     loc='left', fontsize=12, fontweight='bold', color=COLORS['text'])
        ax.set_xlabel("Temperature (°C)", color=COLORS['muted'], fontsize=9)
        ax.set_ylabel("Water (%)", color=COLORS['muted'], fontsize=9)
        ax.set_zlabel("Height (cm)", color=COLORS['muted'], fontsize=9)
        ax.set_facecolor(COLORS['card'])
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.set_pane_color((1, 1, 1, 0))
            axis._axinfo['grid']['color'] = COLORS['border']
        ax.tick_params(colors=COLORS['muted'], labelsize=8)
        ax.view_init(elev=28, azim=-125)
        self.canvas_3d.draw_idle()

    def update_statistics(self):
        p = self.prediction
        self.stat_labels['height'].configure(text=f"{p['final_height']:.0f} cm")
        self.stat_labels['rate'].configure(text=f"{p['growth_rate']:.2f} cm/d")
        self.stat_labels['yield'].configure(text=p.get('yield', 'N/A'))
        self.stat_labels['days'].configure(text=f"{len(p['growth_stages'])} days")

    def update_health_indicator(self):
        health = self.prediction['health_score']
        weakest, weakest_score = min(self.prediction['stress_factors'].items(), key=lambda kv: kv[1])
        score = health / 100
        color = status_color(score)

        # Semicircular gauge drawn at 4x for smooth edges
        k, w, h = 4, 240, 130
        img = Image.new('RGBA', (w * k, h * k), COLORS['card'])
        draw = ImageDraw.Draw(img)
        box = [20 * k, 20 * k, (w - 20) * k, (w - 20) * k]
        draw.arc(box, 180, 360, fill=COLORS['track'], width=18 * k)
        draw.arc(box, 180, 180 + 180 * score, fill=color, width=18 * k)
        img = img.resize((w, h), Image.Resampling.LANCZOS)
        self._images['gauge'] = ImageTk.PhotoImage(img)
        self.gauge_label.configure(image=self._images['gauge'], text=f"{health:.0f}%", compound='center',
                                   font=self.fonts['kpi'], fg=color)

        status = ("Excellent" if health >= 85 else "Good" if health >= 70
                  else "Under stress" if health >= 50 else "Poor")
        if weakest_score < 0.6:
            status += f"  ·  limited by {FACTOR_LABELS[weakest].lower()}"
        self.health_status.configure(text=status)

    def update_radar_chart(self):
        ax = self.radar_ax
        ax.clear()
        factors = self.prediction['stress_factors']
        labels = [RADAR_LABELS[k] for k in factors]
        values = [v * 100 for v in factors.values()]
        angles = np.linspace(0, 2 * np.pi, len(values), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        ax.plot(angles, [100] * len(angles), color=COLORS['muted'], lw=1, ls=(0, (3, 3)))
        ax.plot(angles, values, color=COLORS['accent'], lw=2)
        ax.fill(angles, values, color=COLORS['accent'], alpha=0.18)
        ax.scatter(angles[:-1], values[:-1], s=22, zorder=3,
                   color=[status_color(v / 100) for v in values[:-1]])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=8, color=COLORS['text'])
        ax.set_ylim(0, 110)
        ax.set_yticks([50, 100])
        ax.set_yticklabels([])
        ax.set_facecolor(COLORS['card'])
        ax.spines['polar'].set_visible(False)
        ax.grid(color=COLORS['border'], lw=0.8)
        self.radar_canvas.draw_idle()

    # Demo actions

    def animate_growth(self):
        """Sweep a playhead across the season on the growth chart"""
        if self._animation:
            self.stop_animation()
            return
        self.notebook.select(0)
        self.render_visible_tab()
        heights = self.chart_heights
        self.playhead_line.set_alpha(0.5)
        self.animate_button.configure(text="■  Stop")
        start = time.perf_counter()

        def frame():
            day = int((time.perf_counter() - start) / ANIMATION_SECONDS * len(heights))
            if day >= len(heights):
                self.stop_animation()
                return
            x, y = day + 1, heights[day]
            self.playhead_line.set_xdata([x, x])
            self.playhead_dot.set_data([x], [y])
            self.playhead_text.xy = (x, y)
            self.playhead_text.set_text(f"Day {x}  ·  {y:.0f} cm")
            self.canvas.draw_idle()
            self._animation = self.root.after(30, frame)

        frame()

    def stop_animation(self):
        if self._animation:
            self.root.after_cancel(self._animation)
            self._animation = None
            self.animate_button.configure(text="▶  Animate growth")
            self._dirty_tabs.add(0)
            self.render_visible_tab()

    def randomize_parameters(self):
        for key, (lo, hi) in RANDOM_RANGES.items():
            step = self.param_spec[key][5]
            self.env_params[key].set(round(round(random.uniform(lo, hi) / step) * step, 2))
        self.refresh_controls()
        self.update_all_graphics()

    def reset_demo(self):
        for key, value in self.default_params.items():
            self.env_params[key].set(value)
        self.current_plant.set("tomato")
        self.ambient_mode.set("controlled")
        self.refresh_controls()
        self.update_all_graphics()

    def auto_update(self):
        """In Chaotic mode the weather-driven parameters drift every two seconds"""
        if self.ambient_mode.get() == "open" and not self._animation:
            for key, amount in DRIFT.items():
                _, _, _, lo, hi, step, _ = self.param_spec[key]
                value = self.env_params[key].get() + random.uniform(-amount, amount)
                self.env_params[key].set(round(min(hi, max(lo, value)) / step) * step)
                self._refresh_value_label(key)
            self.update_all_graphics()
        self.root.after(2000, self.auto_update)


def main():
    root = tk.Tk()
    PlantGrowthGraphicsDemo(root)
    root.mainloop()


if __name__ == "__main__":
    main()
