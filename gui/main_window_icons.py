# -*- coding: utf-8 -*-
"""
Baiak Bot - Interface Premium com Ícones Reais do Tibia
Visual estilo ZeroBot/ElfBot com ícones PNG da store
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.reader_v2 import TibiaMemoryReader
from modules.healing_v2 import HealingModuleV2


# Caminho dos ícones
ICONS_PATH = r"E:\projetos\projeto\store\store\64"

# Mapeamento de spells/itens para ícones PNG
SPELL_TO_ICON = {
    # Healing Spells - usa icone de poção como referência visual
    "exura": "Intense_Healing_Rune.png",
    "exura gran": "Intense_Healing_Rune.png",
    "exura vita": "Ultimate_Healing_Rune.png",
    "exura gran mas res": "Ultimate_Healing_Rune.png",
    "exura sio": "Ultimate_Healing_Rune.png",
    
    # Runes
    "uh": "Ultimate_Healing_Rune.png",
    "uh rune": "Ultimate_Healing_Rune.png",
    "ih": "Intense_Healing_Rune.png",
    "ih rune": "Intense_Healing_Rune.png",
    "sd": "Sudden_Death_Rune.png",
    "sudden death": "Sudden_Death_Rune.png",
    "gfb": "Great_Fireball_Rune.png",
    "great fireball": "Great_Fireball_Rune.png",
    "avalanche": "Avalanche_Rune.png",
    "thunderstorm": "Thunderstorm_Rune.png",
    "stone shower": "Stone_Shower_Rune.png",
    "icicle": "Icicle_Rune.png",
    "fireball": "Fireball_Rune.png",
    "explosion": "Explosion_Rune.png",
    "magic wall": "Magic_Wall_Rune.png",
    "wild growth": "Wild_Growth_Rune.png",
    "paralyse": "Paralyse_Rune.png",
    "soulfire": "Soulfire_Rune.png",
    "energy bomb": "Energy_Bomb_Rune.png",
    "fire bomb": "Fire_Bomb_Rune.png",
    "poison bomb": "Poison_Bomb_Rune.png",
    "energy wall": "Energy_Wall_Rune.png",
    "fire wall": "Fire_Wall_Rune.png",
    "poison wall": "Poison_Wall_Rune.png",
    "energy field": "Energy_Field_Rune.png",
    "fire field": "Fire_Field_Rune.png",
    "chameleon": "Chameleon_Rune.png",
    "convince": "Convince_Creature_Rune.png",
    "cure poison": "Cure_Poison_Rune.png",
    "disintegrate": "Disintegrate_Rune.png",
    "animate dead": "Animate_Dead_Rune.png",
    
    # Health Potions
    "hp": "Health_Potion.png",
    "health": "Health_Potion.png",
    "health potion": "Health_Potion.png",
    "great health": "Great_Health_Potion.png",
    "ghp": "Great_Health_Potion.png",
    "strong health": "Strong_Health_Potion.png",
    "shp": "Strong_Health_Potion.png",
    "ultimate health": "Ultimate_Health_Potion.png",
    "uhp": "Ultimate_Health_Potion.png",
    "supreme health": "Supreme_Health_Potion.png",
    "sup health": "Supreme_Health_Potion.png",
    
    # Mana Potions
    "mp": "Mana_Potion.png",
    "mana": "Mana_Potion.png",
    "mana potion": "Mana_Potion.png",
    "great mana": "Great_Mana_Potion.png",
    "gmp": "Great_Mana_Potion.png",
    "strong mana": "Strong_Mana_Potion.png",
    "smp": "Strong_Mana_Potion.png",
    "ultimate mana": "Ultimate_Mana_Potion.png",
    "ump": "Ultimate_Mana_Potion.png",
    
    # Spirit Potions
    "great spirit": "Great_Spirit_Potion.png",
    "gsp": "Great_Spirit_Potion.png",
    "ultimate spirit": "Ultimate_Spirit_Potion.png",
    "usp": "Ultimate_Spirit_Potion.png",
}

# Ícones do menu
MENU_ICONS = {
    "Healing": "Category_Potions.png",
    "Runes": "Category_Runes.png",
    "Attack": "Sudden_Death_Rune.png",
    "Targeting": "Outfit_Assassin_Male.png",
    "Cavebot": "Outfit_Cave_Explorer_Male.png",
    "Tools": "Toolbox.png",
    "Config": "Imbuing_Shrine.png",
    "Scanner": "Reward_Shrine.png",
    "Save": "Chest_of_Abundance.png",
    "Load": "Pirate_Treasure_Chest.png",
    "Help": "Flying_Book.png",
}


class IconManager:
    """Gerencia carregamento de ícones"""
    
    def __init__(self, icons_path, size=32):
        self.icons_path = icons_path
        self.size = size
        self.cache = {}
        self.default_icon = None
    
    def get_icon(self, filename, size=None):
        """Carrega e retorna um ícone"""
        if size is None:
            size = self.size
        
        cache_key = f"{filename}_{size}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        filepath = os.path.join(self.icons_path, filename)
        
        try:
            if os.path.exists(filepath):
                img = Image.open(filepath)
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.cache[cache_key] = photo
                return photo
        except Exception as e:
            print(f"Erro ao carregar {filename}: {e}")
        
        return self._get_default_icon(size)
    
    def _get_default_icon(self, size):
        """Retorna ícone padrão"""
        cache_key = f"default_{size}"
        if cache_key not in self.cache:
            # Cria um ícone padrão colorido
            img = Image.new('RGBA', (size, size), (100, 100, 150, 200))
            photo = ImageTk.PhotoImage(img)
            self.cache[cache_key] = photo
        return self.cache[cache_key]
    
    def get_spell_icon(self, spell_name, size=None):
        """Retorna ícone baseado no nome da spell"""
        name = spell_name.lower().strip()
        
        # Busca correspondência
        for key, icon_file in SPELL_TO_ICON.items():
            if key in name or name in key:
                return self.get_icon(icon_file, size)
        
        # Tenta encontrar por palavras-chave
        if "health" in name or "hp" in name:
            return self.get_icon("Health_Potion.png", size)
        elif "mana" in name or "mp" in name:
            return self.get_icon("Mana_Potion.png", size)
        elif "spirit" in name:
            return self.get_icon("Great_Spirit_Potion.png", size)
        elif "rune" in name or "uh" in name:
            return self.get_icon("Ultimate_Healing_Rune.png", size)
        
        return self._get_default_icon(size or self.size)


class BotWindowWithIcons:
    """Interface Premium com ícones reais do Tibia"""
    
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
        self.root.geometry("620x620")
        self.root.resizable(False, False)
        
        # Cores
        self.colors = {
            'bg': '#1a1a2e',
            'bg_dark': '#0f0f1a',
            'bg_panel': '#1f1f3a',
            'bg_input': '#2a2a4a',
            'btn': '#3a3a5a',
            'btn_hover': '#4a4a7a',
            'btn_active': '#6366f1',
            'text': '#e2e8f0',
            'text_dim': '#94a3b8',
            'accent': '#818cf8',
            'hp': '#ef4444',
            'mp': '#3b82f6',
            'green': '#10b981',
            'red': '#ef4444',
            'gold': '#fbbf24',
            'border': '#4a4a6a',
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Gerenciador de ícones
        self.icons = IconManager(ICONS_PATH, size=32)
        
        # Estilo
        self._setup_styles()
        
        # Interface - IMPORTANTE: status_bar ANTES do content_area
        # para que fique fixo na parte de baixo
        self._create_title_bar()
        self._create_menu_grid()
        self._create_status_bar()  # Criar ANTES para ficar embaixo
        self._create_content_area()
        
        # Aba inicial
        self._show_tab("Healing")
        
        # Thread
        self._start_update_thread()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_styles(self):
        """Configura estilos"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("HP.Horizontal.TProgressbar",
                       troughcolor=self.colors['bg_dark'],
                       background=self.colors['hp'],
                       bordercolor=self.colors['border'])
        
        style.configure("MP.Horizontal.TProgressbar",
                       troughcolor=self.colors['bg_dark'],
                       background=self.colors['mp'],
                       bordercolor=self.colors['border'])
    
    def _create_title_bar(self):
        """Barra de título"""
        title_bar = tk.Frame(self.root, bg=self.colors['bg_dark'], height=35)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)
        
        # Ícone
        try:
            icon = self.icons.get_icon("Category_Potions.png", 24)
            icon_label = tk.Label(title_bar, image=icon, bg=self.colors['bg_dark'])
            icon_label.image = icon
            icon_label.pack(side=tk.LEFT, padx=8)
        except:
            pass
        
        # Título
        self.title_label = tk.Label(
            title_bar,
            text="Baiak Bot Premium  •  Startup  •  0 ms  •  0 exp/hour",
            bg=self.colors['bg_dark'],
            fg=self.colors['text'],
            font=('Segoe UI', 10)
        )
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        # Botões
        close_btn = tk.Button(
            title_bar, text="✕",
            bg=self.colors['bg_dark'], fg=self.colors['text_dim'],
            font=('Segoe UI', 11), width=3, relief=tk.FLAT,
            activebackground=self.colors['red'],
            command=self._on_close
        )
        close_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        min_btn = tk.Button(
            title_bar, text="─",
            bg=self.colors['bg_dark'], fg=self.colors['text_dim'],
            font=('Segoe UI', 11), width=3, relief=tk.FLAT,
            command=lambda: self.root.iconify()
        )
        min_btn.pack(side=tk.RIGHT, pady=5)
        
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
        """Grid de menu com ícones"""
        menu_frame = tk.Frame(self.root, bg=self.colors['bg'])
        menu_frame.pack(fill=tk.X, padx=8, pady=8)
        
        self.menu_buttons = {}
        
        # Linha 1
        row1 = tk.Frame(menu_frame, bg=self.colors['bg'])
        row1.pack(fill=tk.X, pady=2)
        
        menu_items_1 = [
            ("Healing", "Category_Potions.png"),
            ("Attack", "Sudden_Death_Rune.png"),
            ("Runes", "Category_Runes.png"),
            ("Targeting", "Outfit_Assassin_Male.png"),
            ("1", None),
            ("2", None),
            ("3", None),
            ("4", None),
        ]
        
        for name, icon_file in menu_items_1:
            self._create_menu_button(row1, name, icon_file)
        
        # Linha 2
        row2 = tk.Frame(menu_frame, bg=self.colors['bg'])
        row2.pack(fill=tk.X, pady=2)
        
        menu_items_2 = [
            ("Tools", "Toolbox.png"),
            ("Cavebot", "Outfit_Cave_Explorer_Male.png"),
            ("Config", "Imbuing_Shrine.png"),
            ("Scanner", "Reward_Shrine.png"),
            ("Save", "Chest_of_Abundance.png"),
            ("Load", "Pirate_Treasure_Chest.png"),
            ("Help", "Flying_Book.png"),
        ]
        
        for name, icon_file in menu_items_2:
            self._create_menu_button(row2, name, icon_file, width=60)
    
    def _create_menu_button(self, parent, name, icon_file, width=50):
        """Cria botão do menu com ícone"""
        btn_frame = tk.Frame(parent, bg=self.colors['bg'])
        btn_frame.pack(side=tk.LEFT, padx=2)
        
        # Se tem ícone, usa frame com ícone em cima e texto embaixo
        if icon_file:
            btn = tk.Button(
                btn_frame,
                text=name,
                font=('Segoe UI', 8),
                bg=self.colors['btn'],
                fg=self.colors['text'],
                activebackground=self.colors['btn_active'],
                relief=tk.FLAT,
                cursor='hand2',
                compound=tk.TOP,
                padx=8,
                pady=4,
                command=lambda n=name: self._show_tab(n)
            )
            try:
                icon = self.icons.get_icon(icon_file, 40)
                btn.configure(image=icon)
                btn.image = icon
            except:
                pass
        else:
            btn = tk.Button(
                btn_frame,
                text=name,
                font=('Segoe UI', 9),
                bg=self.colors['btn'],
                fg=self.colors['text'],
                activebackground=self.colors['btn_active'],
                width=4,
                height=2,
                relief=tk.FLAT,
                cursor='hand2',
                command=lambda n=name: self._show_tab(n)
            )
        
        btn.pack()
        
        # Hover
        btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.colors['btn_hover']))
        btn.bind('<Leave>', lambda e, b=btn, n=name: self._update_btn_color(b, n))
        
        self.menu_buttons[name] = btn
    
    def _update_btn_color(self, btn, name):
        if name == self.current_tab:
            btn.configure(bg=self.colors['btn_active'])
        else:
            btn.configure(bg=self.colors['btn'])
    
    def _create_content_area(self):
        """Área de conteúdo"""
        self.content_frame = tk.Frame(
            self.root, 
            bg=self.colors['bg_panel'],
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
    
    def _create_status_bar(self):
        """Barra de status"""
        status_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=70)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(4, 8))
        status_frame.pack_propagate(False)
        
        # HP
        hp_frame = tk.Frame(status_frame, bg=self.colors['bg_dark'])
        hp_frame.pack(fill=tk.X, padx=10, pady=4)
        
        # Ícone HP
        try:
            hp_icon = self.icons.get_icon("Health_Potion.png", 20)
            hp_icon_label = tk.Label(hp_frame, image=hp_icon, bg=self.colors['bg_dark'])
            hp_icon_label.image = hp_icon
            hp_icon_label.pack(side=tk.LEFT, padx=(0, 5))
        except:
            pass
        
        tk.Label(hp_frame, text="HP", bg=self.colors['bg_dark'],
                fg=self.colors['hp'], font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        
        self.hp_bar = ttk.Progressbar(hp_frame, length=200, mode='determinate',
                                      style="HP.Horizontal.TProgressbar")
        self.hp_bar.pack(side=tk.LEFT, padx=8)
        self.hp_bar['value'] = 100
        
        self.hp_label = tk.Label(hp_frame, text="100%", bg=self.colors['bg_dark'],
                                fg=self.colors['text'], font=('Segoe UI', 9, 'bold'))
        self.hp_label.pack(side=tk.LEFT)
        
        # Botões
        self.bot_btn = tk.Button(
            hp_frame, text="▶ START",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['green'], fg='white',
            width=10, relief=tk.FLAT, cursor='hand2',
            command=self._toggle_bot
        )
        self.bot_btn.pack(side=tk.RIGHT, padx=5)
        
        self.connect_btn = tk.Button(
            hp_frame, text="Connect",
            font=('Segoe UI', 8),
            bg=self.colors['btn'], fg=self.colors['text'],
            width=10, relief=tk.FLAT, cursor='hand2',
            command=self._on_connect
        )
        self.connect_btn.pack(side=tk.RIGHT, padx=5)
        
        # MP
        mp_frame = tk.Frame(status_frame, bg=self.colors['bg_dark'])
        mp_frame.pack(fill=tk.X, padx=10, pady=4)
        
        # Ícone MP
        try:
            mp_icon = self.icons.get_icon("Mana_Potion.png", 20)
            mp_icon_label = tk.Label(mp_frame, image=mp_icon, bg=self.colors['bg_dark'])
            mp_icon_label.image = mp_icon
            mp_icon_label.pack(side=tk.LEFT, padx=(0, 5))
        except:
            pass
        
        tk.Label(mp_frame, text="MP", bg=self.colors['bg_dark'],
                fg=self.colors['mp'], font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        
        self.mp_bar = ttk.Progressbar(mp_frame, length=200, mode='determinate',
                                      style="MP.Horizontal.TProgressbar")
        self.mp_bar.pack(side=tk.LEFT, padx=8)
        self.mp_bar['value'] = 100
        
        self.mp_label = tk.Label(mp_frame, text="100%", bg=self.colors['bg_dark'],
                                fg=self.colors['text'], font=('Segoe UI', 9, 'bold'))
        self.mp_label.pack(side=tk.LEFT)
        
        # Status
        self.status_label = tk.Label(mp_frame, text="● Disconnected",
                                    bg=self.colors['bg_dark'],
                                    fg=self.colors['text_dim'], font=('Segoe UI', 8))
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def _show_tab(self, tab_name):
        """Mostra aba"""
        # Atualiza botões
        for name, btn in self.menu_buttons.items():
            if name == tab_name:
                btn.configure(bg=self.colors['btn_active'])
            else:
                btn.configure(bg=self.colors['btn'])
        
        # Limpa
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.current_tab = tab_name
        
        # Conteúdo
        if tab_name == "Healing":
            self._create_healing_tab()
        elif tab_name == "Scanner":
            self._open_scanner()
        elif tab_name == "Config":
            self._create_config_tab()
        else:
            self._create_placeholder(tab_name)
    
    def _create_healing_tab(self):
        """Aba de Healing com ícones reais"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Título com ícone
        title_frame = tk.Frame(frame, bg=self.colors['bg_panel'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        try:
            title_icon = self.icons.get_icon("Category_Potions.png", 28)
            icon_label = tk.Label(title_frame, image=title_icon, bg=self.colors['bg_panel'])
            icon_label.image = title_icon
            icon_label.pack(side=tk.LEFT, padx=(0, 8))
        except:
            pass
        
        tk.Label(title_frame, text="Auto-Healing", bg=self.colors['bg_panel'],
                fg=self.colors['accent'], font=('Segoe UI', 14, 'bold')).pack(side=tk.LEFT)
        
        # Toggle
        self.healing_var = tk.BooleanVar(value=False)
        self.healing_cb = tk.Checkbutton(
            title_frame, text="Enable",
            variable=self.healing_var,
            bg=self.colors['bg_panel'], fg=self.colors['text'],
            selectcolor=self.colors['bg_dark'],
            font=('Segoe UI', 10),
            command=self._toggle_healing
        )
        self.healing_cb.pack(side=tk.RIGHT)
        
        # Separador
        tk.Frame(frame, bg=self.colors['border'], height=1).pack(fill=tk.X, pady=10)
        
        # Heal entries
        self.heal_entries = {}
        
        # Spell Hi
        self._create_heal_row(frame, "Spell Hi", "exura vita", 90, 0, "F1")
        
        # Spell Lo
        self._create_heal_row(frame, "Spell Lo", "exura gran", 70, 0, "F2")
        
        # UH Rune
        self._create_heal_row(frame, "UH Rune", "uh rune", 50, 0, "F3")
        
        # Separador
        tk.Frame(frame, bg=self.colors['border'], height=1).pack(fill=tk.X, pady=10)
        
        # HP Potion
        self._create_heal_row(frame, "HP Potion", "ultimate health", 60, 0, "F4")
        
        # MP Potion
        self._create_heal_row(frame, "MP Potion", "great mana", 0, 50, "F5", is_mana=True)
        
        # Delay
        delay_frame = tk.Frame(frame, bg=self.colors['bg_panel'])
        delay_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(delay_frame, text="Delay:", bg=self.colors['bg_panel'],
                fg=self.colors['text'], font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        self.delay_var = tk.StringVar(value="100")
        delay_entry = tk.Entry(delay_frame, textvariable=self.delay_var, width=6,
                              font=('Segoe UI', 9), bg=self.colors['bg_input'],
                              fg=self.colors['text'], relief=tk.FLAT,
                              insertbackground='white')
        delay_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(delay_frame, text="ms", bg=self.colors['bg_panel'],
                fg=self.colors['text_dim'], font=('Segoe UI', 8)).pack(side=tk.LEFT)
    
    def _create_heal_row(self, parent, label, default_spell, hp_val, mana_val, hotkey, is_mana=False):
        """Cria linha de healing com ícone PNG"""
        row = tk.Frame(parent, bg=self.colors['bg_panel'])
        row.pack(fill=tk.X, pady=5)
        
        widgets = {}
        
        # Checkbox
        var = tk.BooleanVar(value=False)
        widgets['enabled'] = var
        
        cb = tk.Checkbutton(
            row, text=label, variable=var,
            bg=self.colors['bg_panel'], fg=self.colors['text'],
            selectcolor=self.colors['bg_dark'],
            font=('Segoe UI', 9), width=10, anchor='w'
        )
        cb.pack(side=tk.LEFT)
        
        # Ícone (Label que será atualizado)
        icon_label = tk.Label(row, bg=self.colors['bg_panel'])
        icon_label.pack(side=tk.LEFT, padx=5)
        widgets['icon_label'] = icon_label
        
        # Atualiza ícone inicial
        self._update_row_icon(icon_label, default_spell)
        
        # Entry spell
        spell_var = tk.StringVar(value=default_spell)
        widgets['spell'] = spell_var
        
        spell_entry = tk.Entry(row, textvariable=spell_var, width=15,
                              font=('Segoe UI', 9), bg=self.colors['bg_input'],
                              fg=self.colors['text'], relief=tk.FLAT,
                              insertbackground='white')
        spell_entry.pack(side=tk.LEFT, padx=3)
        
        # Atualiza ícone quando digita
        def on_spell_change(*args):
            self._update_row_icon(icon_label, spell_var.get())
        spell_var.trace('w', on_spell_change)
        
        # HP
        tk.Label(row, text="HP ≤", bg=self.colors['bg_panel'],
                fg=self.colors['hp'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(15, 3))
        
        hp_var = tk.StringVar(value=str(hp_val))
        widgets['hp'] = hp_var
        
        hp_entry = tk.Entry(row, textvariable=hp_var, width=4,
                           font=('Segoe UI', 9), bg=self.colors['bg_input'],
                           fg=self.colors['hp'], relief=tk.FLAT,
                           insertbackground='white', justify='center')
        hp_entry.pack(side=tk.LEFT)
        
        # MP
        tk.Label(row, text="MP ≤", bg=self.colors['bg_panel'],
                fg=self.colors['mp'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(10, 3))
        
        mana_var = tk.StringVar(value=str(mana_val))
        widgets['mana'] = mana_var
        
        mana_entry = tk.Entry(row, textvariable=mana_var, width=4,
                             font=('Segoe UI', 9), bg=self.colors['bg_input'],
                             fg=self.colors['mp'], relief=tk.FLAT,
                             insertbackground='white', justify='center')
        mana_entry.pack(side=tk.LEFT)
        
        # Hotkey
        tk.Label(row, text="Key:", bg=self.colors['bg_panel'],
                fg=self.colors['gold'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(10, 3))
        
        hotkey_var = tk.StringVar(value=hotkey)
        widgets['hotkey'] = hotkey_var
        widgets['is_mana'] = is_mana
        
        hotkey_entry = tk.Entry(row, textvariable=hotkey_var, width=4,
                               font=('Segoe UI', 9), bg=self.colors['bg_input'],
                               fg=self.colors['gold'], relief=tk.FLAT,
                               insertbackground='white', justify='center')
        hotkey_entry.pack(side=tk.LEFT)
        
        self.heal_entries[label] = widgets
    
    def _update_row_icon(self, icon_label, spell_name):
        """Atualiza ícone da linha"""
        try:
            icon = self.icons.get_spell_icon(spell_name, 40)
            icon_label.configure(image=icon)
            icon_label.image = icon
        except Exception as e:
            print(f"Erro ao atualizar ícone: {e}")
    
    def _create_config_tab(self):
        """Aba de config"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(frame, text="⚙️ Configurações", bg=self.colors['bg_panel'],
                fg=self.colors['accent'], font=('Segoe UI', 14, 'bold')).pack(anchor=tk.W)
        
        tk.Frame(frame, bg=self.colors['border'], height=1).pack(fill=tk.X, pady=10)
        
        # Status
        status_frame = tk.Frame(frame, bg=self.colors['bg_input'])
        status_frame.pack(fill=tk.X, pady=10, ipady=10)
        
        tk.Label(status_frame, text="Status:", bg=self.colors['bg_input'],
                fg=self.colors['text'], font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=10)
        
        self.config_status = tk.Label(status_frame, text="● Não conectado",
                                     bg=self.colors['bg_input'],
                                     fg=self.colors['text_dim'], font=('Segoe UI', 10, 'bold'))
        self.config_status.pack(side=tk.LEFT)
        
        # Botões
        btn_frame = tk.Frame(frame, bg=self.colors['bg_panel'])
        btn_frame.pack(fill=tk.X, pady=15)
        
        tk.Button(btn_frame, text="Reconectar", font=('Segoe UI', 9),
                 bg=self.colors['btn'], fg=self.colors['text'],
                 relief=tk.FLAT, padx=15, pady=5,
                 command=self._on_connect).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Scanner de Offsets", font=('Segoe UI', 9),
                 bg=self.colors['btn'], fg=self.colors['text'],
                 relief=tk.FLAT, padx=15, pady=5,
                 command=self._open_scanner).pack(side=tk.LEFT, padx=5)
    
    def _create_placeholder(self, name):
        """Placeholder"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="🚧", bg=self.colors['bg_panel'],
                font=('Segoe UI', 48)).pack(pady=30)
        
        tk.Label(frame, text=name, bg=self.colors['bg_panel'],
                fg=self.colors['accent'], font=('Segoe UI', 16, 'bold')).pack()
        
        tk.Label(frame, text="Em desenvolvimento...", bg=self.colors['bg_panel'],
                fg=self.colors['text_dim'], font=('Segoe UI', 10)).pack(pady=5)
    
    def _toggle_bot(self):
        """Liga/desliga bot"""
        self.bot_enabled = not self.bot_enabled
        
        if self.bot_enabled:
            self.bot_btn.configure(text="⏹ STOP", bg=self.colors['red'])
            self.title_label.configure(text="Baiak Bot Premium  •  Running")
            
            if self.healing:
                self._apply_healing_config()
                self.healing.start_loop(interval=0.050)
        else:
            self.bot_btn.configure(text="▶ START", bg=self.colors['green'])
            self.title_label.configure(text="Baiak Bot Premium  •  Stopped")
            
            if self.healing:
                self.healing.stop_loop()
    
    def _toggle_healing(self):
        """Toggle healing"""
        if self.healing:
            self.healing.toggle()
    
    def _apply_healing_config(self):
        """Aplica config healing"""
        if not self.healing:
            return
        
        slot = 0
        for label, data in self.heal_entries.items():
            if slot >= 3:
                break
            
            enabled = data['enabled'].get()
            hotkey = data['hotkey'].get()
            
            try:
                if data.get('is_mana'):
                    threshold = int(data['mana'].get()) if data['mana'].get() else 0
                else:
                    threshold = int(data['hp'].get()) if data['hp'].get() else 0
            except:
                threshold = 80
            
            if threshold > 0 and enabled:
                self.healing.configure_slot(slot, enabled=True, hotkey=hotkey, hp_threshold=threshold)
                slot += 1
    
    def _on_connect(self):
        """Conecta"""
        if self.memory.connect():
            self.healing = HealingModuleV2(self.memory)
            self.healing.find_tibia_window()
            
            self.status_label.configure(text="● Connected", fg=self.colors['green'])
            self.connect_btn.configure(text="Reconnect")
            
            if hasattr(self, 'config_status'):
                self.config_status.configure(text="● Conectado!", fg=self.colors['green'])
            
            if self.memory.has_offsets():
                self.title_label.configure(text="Baiak Bot Premium  •  Connected")
            else:
                self.title_label.configure(text="Baiak Bot Premium  •  No Offsets!")
        else:
            self.status_label.configure(text="● Error", fg=self.colors['red'])
    
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
    # Verifica se Pillow está instalado
    try:
        from PIL import Image, ImageTk
    except ImportError:
        print("=" * 50)
        print("ERRO: Pillow não está instalado!")
        print("Execute: pip install Pillow")
        print("=" * 50)
        input("Pressione ENTER para sair...")
        return
    
    print("=" * 50)
    print("  🎮 BAIAK BOT - Premium Edition")
    print("  Com ícones reais do Tibia!")
    print("=" * 50)
    
    app = BotWindowWithIcons()
    app.run()


if __name__ == "__main__":
    main()
