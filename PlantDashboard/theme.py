"""
Shared WeGrow look & feel for the Tkinter apps: colours, fonts, ttk styles and widget helpers.
"""

import os
import tkinter as tk
from tkinter import ttk, font as tkfont

import matplotlib
from PIL import Image, ImageDraw, ImageTk

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

COLORS = {
    'bg': '#f3f6f4',
    'card': '#ffffff',
    'border': '#e1e8e3',
    'text': '#1d2b23',
    'muted': '#6b7d72',
    'accent': '#2e9e5b',
    'accent_dark': '#23804a',
    'accent_soft': '#e4f4ea',
    'warn': '#d99a00',
    'bad': '#d64545',
    'track': '#e8eeea',
}

PHASE_COLORS = ['#c9a25f', '#8cbf5a', '#2e9e5b', '#e06c9f', '#e5533d']


def status_color(score):
    """Colour for a 0..1 score"""
    return COLORS['accent'] if score >= 0.85 else COLORS['warn'] if score >= 0.6 else COLORS['bad']


def style_axes(ax):
    """Minimal matplotlib axes: no box, light horizontal grid, muted ticks"""
    ax.set_facecolor(COLORS['card'])
    ax.grid(axis='y', color=COLORS['border'], lw=0.8)
    ax.set_axisbelow(True)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(COLORS['border'])
    ax.tick_params(colors=COLORS['muted'], labelsize=8, length=0, pad=6)


class Theme:
    """Applies the WeGrow style to a Tk root and provides card/label helpers"""

    def __init__(self, root):
        self.root = root
        self.images = {}  # keeps PhotoImage references alive
        root.configure(bg=COLORS['bg'])
        self._setup_fonts()
        self._setup_style()
        self._load_logo()

    def _setup_fonts(self):
        families = set(tkfont.families(self.root))
        family = next((f for f in ("Inter", "Segoe UI", "SF Pro Text", "Helvetica Neue", "Cantarell",
                                   "Noto Sans", "Ubuntu", "DejaVu Sans") if f in families), "TkDefaultFont")
        self.family = family
        self.fonts = {
            'h1': (family, 18, 'bold'),
            'h2': (family, 12, 'bold'),
            'body': (family, 10),
            'body_bold': (family, 10, 'bold'),
            'small': (family, 9),
            'small_bold': (family, 9, 'bold'),
            'kpi': (family, 22, 'bold'),
        }
        for name in ("TkDefaultFont", "TkTextFont"):
            tkfont.nametofont(name).configure(family=family, size=10)
        matplotlib.rcParams['font.family'] = [family, 'DejaVu Sans']

    def _setup_style(self):
        c = COLORS
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', background=c['bg'], foreground=c['text'], font=self.fonts['body'])

        self._setup_slider_style(style)

        style.configure('Accent.TButton', background=c['accent'], foreground='white',
                        bordercolor=c['accent'], lightcolor=c['accent'], darkcolor=c['accent'],
                        focuscolor=c['accent'], padding=(14, 8), font=self.fonts['body_bold'])
        style.map('Accent.TButton', background=[('active', c['accent_dark']), ('disabled', '#a9cdb7')],
                  lightcolor=[('active', c['accent_dark'])], darkcolor=[('active', c['accent_dark'])])

        style.configure('Ghost.TButton', background=c['card'], foreground=c['text'],
                        bordercolor=c['border'], lightcolor=c['card'], darkcolor=c['card'],
                        focuscolor=c['card'], padding=(12, 7))
        style.map('Ghost.TButton', background=[('active', c['accent_soft'])],
                  lightcolor=[('active', c['accent_soft'])], darkcolor=[('active', c['accent_soft'])])

        style.configure('TNotebook', background=c['bg'], borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure('TNotebook.Tab', background=c['bg'], foreground=c['muted'], borderwidth=0,
                        padding=(16, 8), font=self.fonts['body_bold'], lightcolor=c['bg'], focuscolor=c['card'],
                        bordercolor=c['bg'])
        style.map('TNotebook.Tab',
                  background=[('selected', c['card']), ('active', c['accent_soft'])],
                  foreground=[('selected', c['accent_dark'])],
                  lightcolor=[('selected', c['card'])], bordercolor=[('selected', c['border'])])
        style.configure('Card.TFrame', background=c['card'])

    def _setup_slider_style(self, style):
        """Image-based slider: thin rounded track with a round knob"""
        def knob(fill):
            k = 4
            img = Image.new('RGBA', (20 * k, 20 * k), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([1 * k, 1 * k, 19 * k, 19 * k], fill=fill)
            draw.ellipse([6 * k, 6 * k, 14 * k, 14 * k], fill='white')
            return ImageTk.PhotoImage(img.resize((20, 20), Image.Resampling.LANCZOS))

        k = 4
        track = Image.new('RGBA', (24 * k, 20 * k), (0, 0, 0, 0))
        ImageDraw.Draw(track).rounded_rectangle([0, 7 * k, 24 * k - 1, 13 * k], radius=3 * k,
                                                fill=COLORS['track'])
        self.images['track'] = ImageTk.PhotoImage(track.resize((24, 20), Image.Resampling.LANCZOS))
        self.images['knob'] = knob(COLORS['accent'])
        self.images['knob_active'] = knob(COLORS['accent_dark'])
        self.images['knob_disabled'] = knob('#b9c6be')

        style.element_create('Knob.trough', 'image', self.images['track'], border=(8, 0, 8, 0), sticky='ew')
        style.element_create('Knob.slider', 'image', self.images['knob'],
                             ('disabled', self.images['knob_disabled']),
                             ('pressed', self.images['knob_active']),
                             ('active', self.images['knob_active']), sticky='')
        style.layout('Knob.Horizontal.TScale',
                     [('Knob.trough', {'sticky': 'ew', 'children': [('Knob.slider', {'side': 'left', 'sticky': ''})]})])
        style.configure('Knob.Horizontal.TScale', background=COLORS['card'])
        style.map('Knob.Horizontal.TScale', background=[('disabled', COLORS['card'])])

    def _load_logo(self):
        """Window icon plus a 40px header logo (None if the asset is missing)"""
        try:
            logo = Image.open(os.path.join(ASSETS_DIR, "transparentLogo.png")).convert("RGBA")
            # Trim the empty margin around the artwork
            flat = Image.alpha_composite(Image.new('RGBA', logo.size, 'white'), logo).convert('L')
            opaque = Image.eval(flat, lambda v: 255 if v < 235 else 0)
            logo = logo.crop(opaque.getbbox())
            side = max(logo.size)
            square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
            square.paste(logo, ((side - logo.width) // 2, (side - logo.height) // 2))
            self.images['icon'] = ImageTk.PhotoImage(square.resize((64, 64), Image.Resampling.LANCZOS))
            self.images['logo'] = ImageTk.PhotoImage(square.resize((40, 40), Image.Resampling.LANCZOS))
            self.root.iconphoto(True, self.images['icon'])
        except (OSError, ValueError):
            self.images['logo'] = None

    # Widget helpers

    def card(self, parent, title=None, subtitle=None):
        """White bordered card. Returns the inner content frame (its border frame is `.outer`)."""
        outer = tk.Frame(parent, bg=COLORS['card'], highlightthickness=1,
                         highlightbackground=COLORS['border'], highlightcolor=COLORS['border'])
        inner = tk.Frame(outer, bg=COLORS['card'])
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)
        if title:
            tk.Label(inner, text=title, font=self.fonts['h2'], bg=COLORS['card'],
                     fg=COLORS['text'], anchor='w').pack(fill=tk.X)
        if subtitle:
            tk.Label(inner, text=subtitle, font=self.fonts['small'], bg=COLORS['card'],
                     fg=COLORS['muted'], anchor='w').pack(fill=tk.X, pady=(2, 0))
        inner.outer = outer
        return inner

    def label(self, parent, text="", font='body', fg='text', **kwargs):
        return tk.Label(parent, text=text, font=self.fonts[font], bg=parent['bg'],
                        fg=COLORS.get(fg, fg), **kwargs)

    def header(self, title, subtitle):
        """Full-width header bar with logo; returns the inner frame for right-side extras"""
        bar = tk.Frame(self.root, bg=COLORS['card'], highlightthickness=1,
                       highlightbackground=COLORS['border'])
        inner = tk.Frame(bar, bg=COLORS['card'])
        inner.pack(fill=tk.X, padx=20, pady=10)
        if self.images.get('logo'):
            tk.Label(inner, image=self.images['logo'], bg=COLORS['card']).pack(side=tk.LEFT, padx=(0, 10))
        titles = tk.Frame(inner, bg=COLORS['card'])
        titles.pack(side=tk.LEFT)
        self.label(titles, title, 'h1').pack(anchor='w')
        self.label(titles, subtitle, 'small', 'muted').pack(anchor='w')
        inner.bar = bar
        return inner

    def segmented(self, parent, options, on_select, width=None):
        """Pill-style segmented control. options: {value: label}. Returns a select(value) function."""
        frame = tk.Frame(parent, bg=COLORS['track'])
        buttons = {}

        def select(value):
            for v, btn in buttons.items():
                chosen = v == value
                btn.configure(bg=COLORS['card'] if chosen else COLORS['track'],
                              fg=COLORS['accent_dark'] if chosen else COLORS['muted'],
                              font=self.fonts['small_bold'] if chosen else self.fonts['small'])

        for value, text in options.items():
            btn = tk.Label(frame, text=text, cursor='hand2', pady=6, width=width or 0)
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
            btn.bind("<Button-1>", lambda _e, v=value: on_select(v))
            buttons[value] = btn
        select.frame = frame
        return select
