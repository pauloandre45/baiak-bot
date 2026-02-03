# -*- coding: utf-8 -*-
"""
Baiak Bot - Interface Moderna Premium
Design inspirado no ElfBot mas com visual moderno
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.reader_v2 import TibiaMemoryReader
from modules.healing_v2 import HealingModuleV2


# Mapeamento de spells para ícones (emoji/unicode)
SPELL_ICONS = {
    # Healing Spells
    "exura": "💚",
    "exura gran": "💚",
    "exura vita": "💚",
    "exura gran mas res": "💚",
    "exura sio": "💚",
    "exana pox": "🧪",
    "exana mort": "💀",
    "exana flam": "🔥",
    "exana vis": "⚡",
    "exana kor": "❄️",
    
    # Attack Spells
    "exori": "⚔️",
    "exori gran": "⚔️",
    "exori mas": "⚔️",
    "exori min": "🗡️",
    "exori ico": "🗡️",
    "exori hur": "🗡️",
    "exori flam": "🔥",
    "exori frigo": "❄️",
    "exori vis": "⚡",
    "exori tera": "🌍",
    "exori mort": "💀",
    "exori gran flam": "🔥",
    "exori gran frigo": "❄️",
    "exori gran vis": "⚡",
    "exori gran tera": "🌍",
    "exori gran mort": "💀",
    "exevo gran mas flam": "🔥",
    "exevo gran mas frigo": "❄️",
    "exevo gran mas vis": "⚡",
    "exevo gran mas tera": "🌍",
    "exevo mas mort": "💀",
    
    # Support
    "utani hur": "💨",
    "utani gran hur": "💨",
    "utamo vita": "🛡️",
    "utamo tempo": "🛡️",
    "utura": "💗",
    "utura gran": "💗",
    "utana vid": "👁️",
    "utevo lux": "💡",
    "utevo gran lux": "💡",
    "utevo vis lux": "💡",
    
    # Runes
    "uh": "❤️",
    "uh rune": "❤️",
    "ultimate healing": "❤️",
    "sd": "💀",
    "sudden death": "💀",
    "gfb": "🔥",
    "great fireball": "🔥",
    "avalanche": "❄️",
    "avalan": "❄️",
    "thunderstorm": "⚡",
    "stone shower": "🌍",
    "icicle": "❄️",
    "fireball": "🔥",
    "stalagmite": "🌍",
    "heavy magic missile": "⚡",
    "hmm": "⚡",
    
    # Potions
    "hp": "🧴",
    "hp potion": "🧴",
    "health potion": "🧴",
    "great health": "🧴",
    "strong health": "🧴",
    "ultimate health": "🧴",
    "supreme health": "🧴",
    "mp": "🔵",
    "mp potion": "🔵",
    "mana potion": "🔵",
    "great mana": "🔵",
    "strong mana": "🔵",
    "ultimate mana": "🔵",
    "ultimate spirit": "🟣",
    "great spirit": "🟣",
    
    # Default
    "": "⬜",
}

def get_spell_icon(spell_name):
    """Retorna o ícone da spell"""
    name = spell_name.lower().strip()
    for key, icon in SPELL_ICONS.items():
        if key in name or name in key:
            return icon
    return "🔮"


class ModernBotWindow:
    """
    Interface moderna estilo ElfBot Premium
    """
    
    def __init__(self):
        # Componentes
        self.memory = TibiaMemoryReader()
        self.healing = None
        
        # Estado
        self.bot_enabled = False
        self.running = True
        self.current_tab = "Healing"
        
        # Janela principal
        self.root = tk.Tk()
        self.root.title("Baiak Bot")
        self.root.geometry("520x400")
        self.root.resizable(False, False)
        
        # Cores modernas
        self.colors = {
            'bg_gradient_top': '#1a1a2e',
            'bg_gradient_bottom': '#16213e',
            'bg_dark': '#0f0f1a',
            'bg_panel': '#1f1f3a',
            'bg_input': '#2a2a4a',
            'btn_normal': '#3a3a5a',
            'btn_hover': '#4a4a7a',
            'btn_active': '#6366f1',
            'btn_green': '#10b981',
            'btn_red': '#ef4444',
            'text': '#e2e8f0',
            'text_dim': '#94a3b8',
            'accent': '#818cf8',
            'accent2': '#a78bfa',
            'hp_color': '#ef4444',
            'mp_color': '#3b82f6',
            'border': '#4a4a6a',
            'gold': '#fbbf24',
        }
        
        self.root.configure(bg=self.colors['bg_gradient_top'])
        
        # Estilo ttk
        self._setup_styles()
        
        # Cria interface
        self._create_title_bar()
        self._create_menu_grid()
        self._create_main_content()
        self._create_status_bar()
        
        # Mostra aba inicial
        self._show_tab("Healing")
        
        # Thread de update
        self._start_update_thread()
        
        # Fechar
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_styles(self):
        """Configura estilos ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Progress bar HP
        style.configure("HP.Horizontal.TProgressbar",
                       troughcolor=self.colors['bg_dark'],
                       background=self.colors['hp_color'],
                       bordercolor=self.colors['border'],
                       lightcolor=self.colors['hp_color'],
                       darkcolor=self.colors['hp_color'])
        
        # Progress bar MP
        style.configure("MP.Horizontal.TProgressbar",
                       troughcolor=self.colors['bg_dark'],
                       background=self.colors['mp_color'],
                       bordercolor=self.colors['border'],
                       lightcolor=self.colors['mp_color'],
                       darkcolor=self.colors['mp_color'])
    
    def _create_title_bar(self):
        """Barra de titulo moderna"""
        title_bar = tk.Frame(self.root, bg=self.colors['bg_dark'], height=32)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)
        
        # Icone
        icon_label = tk.Label(
            title_bar,
            text="🎮",
            bg=self.colors['bg_dark'],
            fg=self.colors['accent'],
            font=('Segoe UI Emoji', 12)
        )
        icon_label.pack(side=tk.LEFT, padx=8)
        
        # Titulo
        self.title_label = tk.Label(
            title_bar,
            text="Baiak Bot Premium  •  Startup  •  0 ms  •  0 exp/hour",
            bg=self.colors['bg_dark'],
            fg=self.colors['text'],
            font=('Segoe UI', 9)
        )
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        # Botao fechar
        close_btn = tk.Button(
            title_bar,
            text="✕",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 10),
            width=3,
            relief=tk.FLAT,
            activebackground=self.colors['btn_red'],
            activeforeground='white',
            command=self._on_close
        )
        close_btn.pack(side=tk.RIGHT, padx=5, pady=3)
        
        # Minimizar
        min_btn = tk.Button(
            title_bar,
            text="─",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 10),
            width=3,
            relief=tk.FLAT,
            activebackground=self.colors['btn_normal'],
            command=lambda: self.root.iconify()
        )
        min_btn.pack(side=tk.RIGHT, pady=3)
        
        # Drag
        title_bar.bind('<Button-1>', self._start_drag)
        title_bar.bind('<B1-Motion>', self._drag)
        self.title_label.bind('<Button-1>', self._start_drag)
        self.title_label.bind('<B1-Motion>', self._drag)
    
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
    
    def _drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")
    
    def _create_menu_grid(self):
        """Grid de botoes estilo ElfBot"""
        menu_frame = tk.Frame(self.root, bg=self.colors['bg_gradient_top'])
        menu_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        self.menu_buttons = {}
        
        # Linha 1: Funcionalidades principais
        row1 = tk.Frame(menu_frame, bg=self.colors['bg_gradient_top'])
        row1.pack(fill=tk.X, pady=2)
        
        buttons_row1 = [
            ("💚", "Healing"),
            ("⚔️", "Aimbot"),
            ("📋", "Lists"),
            ("📊", "HUD"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
        ]
        
        for icon, name in buttons_row1:
            self._create_menu_button(row1, icon, name)
        
        # Linha 2
        row2 = tk.Frame(menu_frame, bg=self.colors['bg_gradient_top'])
        row2.pack(fill=tk.X, pady=2)
        
        buttons_row2 = [
            ("🎁", "Extras"),
            ("⌨️", "Hotkeys"),
            ("⚡", "Shortkeys"),
            ("🔄", "Reconnect"),
            ("💾", "Save"),
            ("⚙️", "Custom"),
        ]
        
        for icon, name in buttons_row2:
            self._create_menu_button(row2, icon, name, width=8)
        
        # Linha 3
        row3 = tk.Frame(menu_frame, bg=self.colors['bg_gradient_top'])
        row3.pack(fill=tk.X, pady=2)
        
        buttons_row3 = [
            ("🤖", "Cavebot"),
            ("🧭", "Navigation"),
            ("🔗", "Links"),
            ("👁️", "Spy"),
            ("📂", "Load"),
            ("❓", "Help"),
        ]
        
        for icon, name in buttons_row3:
            self._create_menu_button(row3, icon, name, width=8)
        
        # Linha 4
        row4 = tk.Frame(menu_frame, bg=self.colors['bg_gradient_top'])
        row4.pack(fill=tk.X, pady=2)
        
        buttons_row4 = [
            ("🎯", "Targeting"),
            ("🔍", "Scanner"),
            ("💡", "Light"),
            ("📝", "Config"),
        ]
        
        for icon, name in buttons_row4:
            self._create_menu_button(row4, icon, name, width=12)
    
    def _create_menu_button(self, parent, icon, name, width=5):
        """Cria botao do menu"""
        btn_frame = tk.Frame(parent, bg=self.colors['bg_gradient_top'])
        btn_frame.pack(side=tk.LEFT, padx=1)
        
        btn = tk.Button(
            btn_frame,
            text=f"{icon}",
            font=('Segoe UI Emoji', 9),
            bg=self.colors['btn_normal'],
            fg=self.colors['text'],
            activebackground=self.colors['btn_active'],
            activeforeground='white',
            width=width,
            height=1,
            relief=tk.FLAT,
            cursor='hand2',
            command=lambda n=name: self._show_tab(n)
        )
        btn.pack()
        
        # Hover effects
        btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.colors['btn_hover']))
        btn.bind('<Leave>', lambda e, b=btn: self._update_btn_color(b, name))
        
        self.menu_buttons[name] = btn
    
    def _update_btn_color(self, btn, name):
        """Atualiza cor do botao"""
        if name == self.current_tab:
            btn.configure(bg=self.colors['btn_active'])
        else:
            btn.configure(bg=self.colors['btn_normal'])
    
    def _create_main_content(self):
        """Area principal de conteudo"""
        self.content_frame = tk.Frame(self.root, bg=self.colors['bg_panel'], 
                                      highlightbackground=self.colors['border'],
                                      highlightthickness=1)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
    
    def _create_status_bar(self):
        """Barra de status inferior"""
        status_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=60)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(4, 8))
        status_frame.pack_propagate(False)
        
        # HP
        hp_frame = tk.Frame(status_frame, bg=self.colors['bg_dark'])
        hp_frame.pack(fill=tk.X, padx=10, pady=3)
        
        tk.Label(hp_frame, text="❤️ HP", bg=self.colors['bg_dark'], 
                fg=self.colors['hp_color'], font=('Segoe UI', 9, 'bold'),
                width=6).pack(side=tk.LEFT)
        
        self.hp_bar = ttk.Progressbar(hp_frame, length=180, mode='determinate',
                                      style="HP.Horizontal.TProgressbar")
        self.hp_bar.pack(side=tk.LEFT, padx=5)
        self.hp_bar['value'] = 100
        
        self.hp_label = tk.Label(hp_frame, text="100%", bg=self.colors['bg_dark'],
                                fg=self.colors['text'], font=('Segoe UI', 9, 'bold'),
                                width=6)
        self.hp_label.pack(side=tk.LEFT)
        
        # Botoes de controle
        self.bot_btn = tk.Button(
            hp_frame,
            text="▶ START",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['btn_green'],
            fg='white',
            width=10,
            relief=tk.FLAT,
            cursor='hand2',
            command=self._toggle_bot
        )
        self.bot_btn.pack(side=tk.RIGHT, padx=5)
        
        self.connect_btn = tk.Button(
            hp_frame,
            text="🔌 Connect",
            font=('Segoe UI', 8),
            bg=self.colors['btn_normal'],
            fg=self.colors['text'],
            width=10,
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_connect
        )
        self.connect_btn.pack(side=tk.RIGHT, padx=5)
        
        # MP
        mp_frame = tk.Frame(status_frame, bg=self.colors['bg_dark'])
        mp_frame.pack(fill=tk.X, padx=10, pady=3)
        
        tk.Label(mp_frame, text="🔵 MP", bg=self.colors['bg_dark'], 
                fg=self.colors['mp_color'], font=('Segoe UI', 9, 'bold'),
                width=6).pack(side=tk.LEFT)
        
        self.mp_bar = ttk.Progressbar(mp_frame, length=180, mode='determinate',
                                      style="MP.Horizontal.TProgressbar")
        self.mp_bar.pack(side=tk.LEFT, padx=5)
        self.mp_bar['value'] = 100
        
        self.mp_label = tk.Label(mp_frame, text="100%", bg=self.colors['bg_dark'],
                                fg=self.colors['text'], font=('Segoe UI', 9, 'bold'),
                                width=6)
        self.mp_label.pack(side=tk.LEFT)
        
        # Status
        self.status_label = tk.Label(mp_frame, text="⚪ Disconnected", 
                                    bg=self.colors['bg_dark'],
                                    fg=self.colors['text_dim'], 
                                    font=('Segoe UI', 8))
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def _show_tab(self, tab_name):
        """Mostra uma aba"""
        # Atualiza botoes
        for name, btn in self.menu_buttons.items():
            if name == tab_name:
                btn.configure(bg=self.colors['btn_active'])
            else:
                btn.configure(bg=self.colors['btn_normal'])
        
        # Limpa conteudo
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.current_tab = tab_name
        
        # Cria conteudo
        if tab_name == "Healing":
            self._create_healing_tab()
        elif tab_name == "Scanner":
            self._open_scanner()
        elif tab_name == "Config":
            self._create_config_tab()
        else:
            self._create_placeholder_tab(tab_name)
    
    def _create_healing_tab(self):
        """Aba de Healing estilo ElfBot"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titulo
        title_frame = tk.Frame(frame, bg=self.colors['bg_panel'])
        title_frame.pack(fill=tk.X)
        
        tk.Label(title_frame, text="💚 Auto-Healing", bg=self.colors['bg_panel'],
                fg=self.colors['accent'], font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        
        # Toggle
        self.healing_toggle_var = tk.BooleanVar(value=False)
        self.healing_toggle = tk.Checkbutton(
            title_frame,
            text="Enable",
            variable=self.healing_toggle_var,
            bg=self.colors['bg_panel'],
            fg=self.colors['text'],
            selectcolor=self.colors['bg_dark'],
            activebackground=self.colors['bg_panel'],
            font=('Segoe UI', 9),
            cursor='hand2',
            command=self._toggle_healing
        )
        self.healing_toggle.pack(side=tk.RIGHT)
        
        # Separador
        tk.Frame(frame, bg=self.colors['border'], height=1).pack(fill=tk.X, pady=8)
        
        # Grid de healing - estilo ElfBot
        self.heal_entries = {}
        
        # Spell Hi (HP Alto)
        self._create_heal_row(frame, "Spell Hi", "exura vita", 90, 0, "F1")
        
        # Spell Lo (HP Baixo)
        self._create_heal_row(frame, "Spell Lo", "exura gran", 70, 0, "F2")
        
        # UH Rune
        self._create_heal_row(frame, "UH Rune", "uh rune", 50, 0, "F3", is_rune=True)
        
        # Separador
        tk.Frame(frame, bg=self.colors['border'], height=1).pack(fill=tk.X, pady=8)
        
        # HP Potion
        self._create_heal_row(frame, "HP Potion", "ultimate health", 60, 0, "F4")
        
        # MP Potion
        self._create_heal_row(frame, "MP Potion", "great mana", 0, 50, "F5", is_mana=True)
        
        # Separador
        tk.Frame(frame, bg=self.colors['border'], height=1).pack(fill=tk.X, pady=8)
        
        # Opcoes
        opt_frame = tk.Frame(frame, bg=self.colors['bg_panel'])
        opt_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(opt_frame, text="⏱️ Delay:", bg=self.colors['bg_panel'],
                fg=self.colors['text'], font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        self.delay_var = tk.StringVar(value="100")
        delay_entry = tk.Entry(opt_frame, textvariable=self.delay_var, width=6,
                              font=('Segoe UI', 9), bg=self.colors['bg_input'],
                              fg=self.colors['text'], insertbackground='white',
                              relief=tk.FLAT)
        delay_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(opt_frame, text="ms", bg=self.colors['bg_panel'],
                fg=self.colors['text_dim'], font=('Segoe UI', 8)).pack(side=tk.LEFT)
    
    def _create_heal_row(self, parent, label, default_spell, hp_val, mana_val, hotkey, is_rune=False, is_mana=False):
        """Cria linha de healing estilo ElfBot"""
        row = tk.Frame(parent, bg=self.colors['bg_panel'])
        row.pack(fill=tk.X, pady=4)
        
        # Checkbox + Label
        var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(
            row,
            text=label,
            variable=var,
            bg=self.colors['bg_panel'],
            fg=self.colors['text'],
            selectcolor=self.colors['bg_dark'],
            activebackground=self.colors['bg_panel'],
            font=('Segoe UI', 9),
            width=10,
            anchor='w'
        )
        cb.pack(side=tk.LEFT)
        
        # Icone da spell (atualiza automaticamente)
        icon_label = tk.Label(row, text=get_spell_icon(default_spell), 
                             bg=self.colors['bg_panel'],
                             font=('Segoe UI Emoji', 14))
        icon_label.pack(side=tk.LEFT, padx=5)
        
        # Entry da spell
        spell_var = tk.StringVar(value=default_spell)
        spell_entry = tk.Entry(row, textvariable=spell_var, width=15,
                              font=('Segoe UI', 9), bg=self.colors['bg_input'],
                              fg=self.colors['text'], insertbackground='white',
                              relief=tk.FLAT)
        spell_entry.pack(side=tk.LEFT, padx=2)
        
        # Atualiza icone quando digita
        def update_icon(*args):
            icon_label.configure(text=get_spell_icon(spell_var.get()))
        spell_var.trace('w', update_icon)
        
        # Health threshold
        tk.Label(row, text="HP ≤", bg=self.colors['bg_panel'],
                fg=self.colors['hp_color'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(10, 2))
        
        hp_var = tk.StringVar(value=str(hp_val))
        hp_entry = tk.Entry(row, textvariable=hp_var, width=4,
                           font=('Segoe UI', 9), bg=self.colors['bg_input'],
                           fg=self.colors['text'], insertbackground='white',
                           relief=tk.FLAT, justify='center')
        hp_entry.pack(side=tk.LEFT)
        
        # Mana threshold
        tk.Label(row, text="MP ≤", bg=self.colors['bg_panel'],
                fg=self.colors['mp_color'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(10, 2))
        
        mana_var = tk.StringVar(value=str(mana_val))
        mana_entry = tk.Entry(row, textvariable=mana_var, width=4,
                             font=('Segoe UI', 9), bg=self.colors['bg_input'],
                             fg=self.colors['text'], insertbackground='white',
                             relief=tk.FLAT, justify='center')
        mana_entry.pack(side=tk.LEFT)
        
        # Hotkey
        tk.Label(row, text="Key:", bg=self.colors['bg_panel'],
                fg=self.colors['gold'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(10, 2))
        
        hotkey_var = tk.StringVar(value=hotkey)
        hotkey_entry = tk.Entry(row, textvariable=hotkey_var, width=4,
                               font=('Segoe UI', 9), bg=self.colors['bg_input'],
                               fg=self.colors['gold'], insertbackground='white',
                               relief=tk.FLAT, justify='center')
        hotkey_entry.pack(side=tk.LEFT)
        
        # Salva referencias
        self.heal_entries[label] = {
            'enabled': var,
            'spell': spell_var,
            'hp': hp_var,
            'mana': mana_var,
            'hotkey': hotkey_var,
            'icon': icon_label,
            'is_mana': is_mana
        }
    
    def _create_config_tab(self):
        """Aba de configuracoes"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="⚙️ Configurações", bg=self.colors['bg_panel'],
                fg=self.colors['accent'], font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W)
        
        tk.Frame(frame, bg=self.colors['border'], height=1).pack(fill=tk.X, pady=8)
        
        # Status
        info_frame = tk.Frame(frame, bg=self.colors['bg_input'], relief=tk.FLAT)
        info_frame.pack(fill=tk.X, pady=10, ipady=10)
        
        tk.Label(info_frame, text="Status:", bg=self.colors['bg_input'],
                fg=self.colors['text'], font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=10)
        
        self.config_status = tk.Label(info_frame, text="⚪ Não conectado", 
                                     bg=self.colors['bg_input'],
                                     fg=self.colors['text_dim'], font=('Segoe UI', 10, 'bold'))
        self.config_status.pack(side=tk.LEFT)
        
        # Botoes
        btn_frame = tk.Frame(frame, bg=self.colors['bg_panel'])
        btn_frame.pack(fill=tk.X, pady=15)
        
        tk.Button(btn_frame, text="🔌 Reconectar", font=('Segoe UI', 9),
                 bg=self.colors['btn_normal'], fg=self.colors['text'],
                 relief=tk.FLAT, cursor='hand2', padx=15, pady=5,
                 command=self._on_connect).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🔍 Scanner de Offsets", font=('Segoe UI', 9),
                 bg=self.colors['btn_normal'], fg=self.colors['text'],
                 relief=tk.FLAT, cursor='hand2', padx=15, pady=5,
                 command=self._open_scanner).pack(side=tk.LEFT, padx=5)
    
    def _create_placeholder_tab(self, name):
        """Aba placeholder"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="🚧", bg=self.colors['bg_panel'],
                font=('Segoe UI Emoji', 48)).pack(pady=20)
        
        tk.Label(frame, text=f"{name}", bg=self.colors['bg_panel'],
                fg=self.colors['accent'], font=('Segoe UI', 16, 'bold')).pack()
        
        tk.Label(frame, text="Em desenvolvimento...", bg=self.colors['bg_panel'],
                fg=self.colors['text_dim'], font=('Segoe UI', 10)).pack(pady=5)
    
    def _toggle_bot(self):
        """Liga/desliga bot"""
        self.bot_enabled = not self.bot_enabled
        
        if self.bot_enabled:
            self.bot_btn.configure(text="⏹ STOP", bg=self.colors['btn_red'])
            self.title_label.configure(text="Baiak Bot Premium  •  Running  •  0 ms")
            
            if self.healing:
                self._apply_healing_config()
                self.healing.start_loop(interval=0.050)
        else:
            self.bot_btn.configure(text="▶ START", bg=self.colors['btn_green'])
            self.title_label.configure(text="Baiak Bot Premium  •  Stopped")
            
            if self.healing:
                self.healing.stop_loop()
    
    def _toggle_healing(self):
        """Toggle healing"""
        if self.healing:
            self.healing.toggle()
    
    def _apply_healing_config(self):
        """Aplica configuracao de healing"""
        if not self.healing:
            return
        
        slot = 0
        for label, data in self.heal_entries.items():
            if slot >= 3:
                break
            
            enabled = data['enabled'].get()
            hotkey = data['hotkey'].get()
            
            try:
                if data['is_mana']:
                    # Para MP, usa o valor de mana
                    threshold = int(data['mana'].get()) if data['mana'].get() else 0
                else:
                    threshold = int(data['hp'].get()) if data['hp'].get() else 0
            except:
                threshold = 80
            
            if threshold > 0 and enabled:
                self.healing.configure_slot(slot, enabled=True, hotkey=hotkey, hp_threshold=threshold)
                slot += 1
    
    def _on_connect(self):
        """Conecta ao Tibia"""
        if self.memory.connect():
            self.healing = HealingModuleV2(self.memory)
            self.healing.find_tibia_window()
            
            self.status_label.configure(text="🟢 Connected", fg=self.colors['btn_green'])
            self.connect_btn.configure(text="🔌 Reconnect")
            
            if hasattr(self, 'config_status'):
                self.config_status.configure(text="🟢 Conectado!", fg=self.colors['btn_green'])
            
            if self.memory.has_offsets():
                self.title_label.configure(text="Baiak Bot Premium  •  Connected")
            else:
                self.title_label.configure(text="Baiak Bot Premium  •  No Offsets!")
        else:
            self.status_label.configure(text="🔴 Error", fg=self.colors['btn_red'])
    
    def _open_scanner(self):
        """Abre scanner"""
        import subprocess
        scanner_path = os.path.join(os.path.dirname(__file__), "..", "memory", "scanner_advanced.py")
        try:
            subprocess.Popen([sys.executable, scanner_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        except:
            pass
    
    def _update_loop(self):
        """Loop de update"""
        while self.running:
            try:
                if self.memory and self.memory.is_connected() and self.memory.has_offsets():
                    hp_pct = self.memory.get_player_hp_percent()
                    mp_pct = self.memory.get_player_mp_percent()
                    
                    self.hp_bar['value'] = hp_pct
                    self.hp_label.configure(text=f"{hp_pct}%")
                    
                    self.mp_bar['value'] = mp_pct
                    self.mp_label.configure(text=f"{mp_pct}%")
            except:
                pass
            
            time.sleep(0.1)
    
    def _start_update_thread(self):
        """Inicia thread"""
        thread = threading.Thread(target=self._update_loop, daemon=True)
        thread.start()
    
    def _on_close(self):
        """Fecha"""
        self.running = False
        self.bot_enabled = False
        
        if self.healing:
            self.healing.stop_loop()
        
        if self.memory:
            self.memory.disconnect()
        
        self.root.destroy()
    
    def run(self):
        """Inicia"""
        self.root.mainloop()


def main():
    app = ModernBotWindow()
    app.run()


if __name__ == "__main__":
    main()
