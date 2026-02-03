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
        self.selected_class = "Knight"  # Classe selecionada
        self.healing_var = None  # Será criado depois com tk.BooleanVar
        
        # Spells por classe (5 classes: Knight, Paladin, Sorcerer, Druid, Monk)
        self.class_spells = {
            "Knight": [
                ("Exura", "exura", "Light Healing"),
                ("Exura Gran", "exura gran", "Intense Healing"),
                ("Exura Gran Ico", "exura gran ico", "Intense Wound Cleansing"),
                ("Utani Hur", "utani hur", "Haste"),
                ("Utito Tempo", "utito tempo", "Blood Rage"),
                ("Exeta Res", "exeta res", "Challenge"),
                ("Exori", "exori", "Brutal Strike"),
                ("Exori Gran", "exori gran", "Fierce Berserk"),
                ("Exori Min", "exori min", "Berserk"),
                ("Exori Mas", "exori mas", "Groundshaker"),
            ],
            "Paladin": [
                ("Exura", "exura", "Light Healing"),
                ("Exura Gran", "exura gran", "Intense Healing"),
                ("Exura San", "exura san", "Divine Healing"),
                ("Utani Hur", "utani hur", "Haste"),
                ("Utani Gran Hur", "utani gran hur", "Strong Haste"),
                ("Exori Con", "exori con", "Ethereal Spear"),
                ("Exori Gran Con", "exori gran con", "Strong Ethereal Spear"),
                ("Exori San", "exori san", "Divine Missile"),
                ("Exevo Mas San", "exevo mas san", "Divine Caldera"),
                ("San Shake", "utito tempo san", "Sharpshooter"),
            ],
            "Sorcerer": [
                ("Exura", "exura", "Light Healing"),
                ("Exura Vita", "exura vita", "Ultimate Healing"),
                ("Utamo Vita", "utamo vita", "Magic Shield"),
                ("Utani Hur", "utani hur", "Haste"),
                ("Utani Gran Hur", "utani gran hur", "Strong Haste"),
                ("Exori Vis", "exori vis", "Energy Strike"),
                ("Exori Mort", "exori mort", "Death Strike"),
                ("Exori Flam", "exori flam", "Flame Strike"),
                ("Exevo Gran Mas Vis", "exevo gran mas vis", "Rage of the Skies"),
                ("Exevo Gran Mas Flam", "exevo gran mas flam", "Hell's Core"),
            ],
            "Druid": [
                ("Exura", "exura", "Light Healing"),
                ("Exura Gran", "exura gran", "Intense Healing"),
                ("Exura Vita", "exura vita", "Ultimate Healing"),
                ("Exura Sio", "exura sio", "Heal Friend"),
                ("Exura Gran Mas Res", "exura gran mas res", "Mass Healing"),
                ("Utamo Vita", "utamo vita", "Magic Shield"),
                ("Utani Hur", "utani hur", "Haste"),
                ("Exori Tera", "exori tera", "Terra Strike"),
                ("Exori Frigo", "exori frigo", "Ice Strike"),
                ("Exevo Gran Mas Tera", "exevo gran mas tera", "Wrath of Nature"),
            ],
            "Monk": [
                ("Exura", "exura", "Light Healing"),
                ("Exura Gran", "exura gran", "Intense Healing"),
                ("Exura San", "exura san", "Divine Healing"),
                ("Utani Hur", "utani hur", "Haste"),
                ("Utito Tempo", "utito tempo", "Blood Rage"),
                ("Punch", "exori moe ico", "Monk Punch"),
                ("Kick", "exori moe", "Monk Kick"),
                ("Combo", "exori gran moe", "Monk Combo"),
                ("Dodge", "utamo moe", "Monk Dodge"),
                ("Chi Wave", "exevo mas moe", "Chi Wave"),
            ],
        }
        
        self.class_colors = {
            "Knight": "#ef4444",
            "Paladin": "#22c55e", 
            "Sorcerer": "#3b82f6",
            "Druid": "#a855f7",
            "Monk": "#f59e0b",
        }
        
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
        """Aba de Healing estilo ZeroBot"""
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === HEADER: Colunas da tabela ===
        header_frame = tk.Frame(frame, bg=self.colors['bg_dark'])
        header_frame.pack(fill=tk.X)
        
        # Colunas: Active | Icon | Spell/Item | Value | Condition
        tk.Label(header_frame, text="Ac.", bg=self.colors['bg_dark'],
                fg=self.colors['text_dim'], font=('Segoe UI', 8, 'bold'),
                width=3).pack(side=tk.LEFT, padx=2)
        tk.Label(header_frame, text="", bg=self.colors['bg_dark'],
                width=4).pack(side=tk.LEFT)  # Ícone
        tk.Label(header_frame, text="Spell / Item", bg=self.colors['bg_dark'],
                fg=self.colors['text_dim'], font=('Segoe UI', 8, 'bold'),
                width=15, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="Value", bg=self.colors['bg_dark'],
                fg=self.colors['text_dim'], font=('Segoe UI', 8, 'bold'),
                width=6).pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="Condition", bg=self.colors['bg_dark'],
                fg=self.colors['text_dim'], font=('Segoe UI', 8, 'bold'),
                width=18, anchor='w').pack(side=tk.LEFT, padx=5)
        
        # === LISTA DE CURAS ===
        self.healing_list_frame = tk.Frame(frame, bg=self.colors['bg_panel'])
        self.healing_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Lista de curas (dados)
        self.healing_entries = []
        
        # Curas padrão
        default_heals = [
            {"enabled": True, "spell": "exura med ico", "item_id": "", "hp_percent": True, "condition": ">=", "value": 0, "and_value": 0, "hotkey": "F1"},
            {"enabled": True, "spell": "", "item_id": "23375", "hp_percent": True, "condition": "<=", "value": 100, "and_value": 0, "hotkey": "F2"},
            {"enabled": True, "spell": "", "item_id": "23373", "hp_percent": True, "condition": "<=", "value": 100, "and_value": 0, "hotkey": "F3"},
        ]
        
        for heal_data in default_heals:
            self._add_healing_entry(heal_data)
        
        # === BOTÕES INFERIORES ===
        btn_frame = tk.Frame(frame, bg=self.colors['bg_panel'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        # Botão Adicionar
        add_btn = tk.Button(
            btn_frame, text="+ Add",
            font=('Segoe UI', 9),
            bg=self.colors['btn'], fg=self.colors['text'],
            relief=tk.FLAT, cursor='hand2', padx=15,
            command=self._add_new_healing
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Enable Healing checkbox
        self.healing_var = tk.BooleanVar(value=False)
        enable_cb = tk.Checkbutton(
            btn_frame, text="Enable Healing",
            variable=self.healing_var,
            bg=self.colors['bg_panel'], fg=self.colors['text'],
            selectcolor=self.colors['bg_dark'],
            font=('Segoe UI', 9),
            command=self._toggle_healing
        )
        enable_cb.pack(side=tk.LEFT, padx=20)
        
        # Hotkey label
        tk.Label(btn_frame, text="Set Key", bg=self.colors['bg_panel'],
                fg=self.colors['text_dim'], font=('Segoe UI', 8)).pack(side=tk.RIGHT, padx=5)
    
    def _add_healing_entry(self, data):
        """Adiciona uma entrada de cura na lista"""
        idx = len(self.healing_entries)
        
        row = tk.Frame(self.healing_list_frame, bg=self.colors['bg_input'])
        row.pack(fill=tk.X, pady=1)
        
        entry_data = {"frame": row, "data": data}
        
        # Checkbox ativo
        var = tk.BooleanVar(value=data.get('enabled', False))
        entry_data['enabled_var'] = var
        
        cb = tk.Checkbutton(
            row, variable=var,
            bg=self.colors['bg_input'],
            selectcolor=self.colors['bg_dark'],
            activebackground=self.colors['bg_input']
        )
        cb.pack(side=tk.LEFT, padx=5)
        
        # Ícone verde se ativo
        status_label = tk.Label(row, text="✓" if data.get('enabled') else "",
                               bg=self.colors['bg_input'],
                               fg=self.colors['green'] if data.get('enabled') else self.colors['text_dim'],
                               font=('Segoe UI', 10, 'bold'), width=2)
        status_label.pack(side=tk.LEFT)
        entry_data['status_label'] = status_label
        
        # Ícone da spell/item
        icon_label = tk.Label(row, bg=self.colors['bg_input'])
        icon_label.pack(side=tk.LEFT, padx=5)
        
        spell_or_item = data.get('spell') or data.get('item_id', '')
        self._update_row_icon(icon_label, spell_or_item)
        entry_data['icon_label'] = icon_label
        
        # Nome da spell/item
        display_text = data.get('spell') if data.get('spell') else f"Item {data.get('item_id', '')}"
        name_label = tk.Label(row, text=display_text[:15], bg=self.colors['bg_input'],
                             fg=self.colors['text'], font=('Segoe UI', 9),
                             width=15, anchor='w')
        name_label.pack(side=tk.LEFT, padx=5)
        entry_data['name_label'] = name_label
        
        # Value
        value_label = tk.Label(row, text=str(data.get('value', 0)), bg=self.colors['bg_input'],
                              fg=self.colors['gold'], font=('Segoe UI', 9, 'bold'),
                              width=6)
        value_label.pack(side=tk.LEFT, padx=5)
        entry_data['value_label'] = value_label
        
        # Condition
        cond_type = "HP" if data.get('hp_percent') else "MP"
        cond_op = data.get('condition', '<=')
        cond_val = data.get('value', 0)
        cond_text = f"{cond_type} {cond_op} {cond_val}%"
        
        if data.get('and_value', 0) > 0:
            cond_text += f" A..."
        
        cond_label = tk.Label(row, text=cond_text, bg=self.colors['bg_input'],
                             fg=self.colors['text_dim'], font=('Segoe UI', 8),
                             width=18, anchor='w')
        cond_label.pack(side=tk.LEFT, padx=5)
        entry_data['cond_label'] = cond_label
        
        # Botão editar (clique na linha)
        row.bind('<Double-Button-1>', lambda e, i=idx: self._open_edit_healing(i))
        name_label.bind('<Double-Button-1>', lambda e, i=idx: self._open_edit_healing(i))
        
        # Botão deletar
        del_btn = tk.Button(
            row, text="✕",
            font=('Segoe UI', 8),
            bg=self.colors['bg_input'], fg=self.colors['red'],
            relief=tk.FLAT, cursor='hand2',
            command=lambda i=idx: self._delete_healing(i)
        )
        del_btn.pack(side=tk.RIGHT, padx=5)
        
        # Atualiza status ao mudar checkbox
        def on_check_change(*args):
            is_enabled = var.get()
            status_label.configure(
                text="✓" if is_enabled else "",
                fg=self.colors['green'] if is_enabled else self.colors['text_dim']
            )
            entry_data['data']['enabled'] = is_enabled
        
        var.trace('w', on_check_change)
        
        self.healing_entries.append(entry_data)
    
    def _add_new_healing(self):
        """Adiciona nova cura vazia"""
        new_data = {
            "enabled": False,
            "spell": "",
            "item_id": "",
            "hp_percent": True,
            "condition": "<=",
            "value": 80,
            "and_value": 0,
            "hotkey": "F1"
        }
        self._add_healing_entry(new_data)
        # Abre editor
        self._open_edit_healing(len(self.healing_entries) - 1)
    
    def _delete_healing(self, idx):
        """Deleta uma entrada de cura"""
        if idx < len(self.healing_entries):
            entry = self.healing_entries[idx]
            entry['frame'].destroy()
            self.healing_entries.pop(idx)
            
            # Reindexar eventos
            for i, entry in enumerate(self.healing_entries):
                entry['frame'].bind('<Double-Button-1>', lambda e, i=i: self._open_edit_healing(i))
    
    def _open_edit_healing(self, idx):
        """Abre popup de edição de cura (estilo ZeroBot)"""
        if idx >= len(self.healing_entries):
            return
        
        entry = self.healing_entries[idx]
        data = entry['data']
        
        # Cria popup
        popup = tk.Toplevel(self.root)
        popup.title("Edit Healing")
        popup.geometry("320x380")
        popup.configure(bg=self.colors['bg_dark'])
        popup.resizable(False, False)
        
        # Centraliza
        x = self.root.winfo_x() + 150
        y = self.root.winfo_y() + 100
        popup.geometry(f"+{x}+{y}")
        
        # === WHEN (HP% ou MP%) ===
        when_frame = tk.Frame(popup, bg=self.colors['bg_dark'])
        when_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(when_frame, text="When:", bg=self.colors['bg_dark'],
                fg=self.colors['text'], font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        when_var = tk.StringVar(value="HP%" if data.get('hp_percent', True) else "MP%")
        
        hp_rb = tk.Radiobutton(when_frame, text="HP%", variable=when_var, value="HP%",
                              bg=self.colors['bg_dark'], fg=self.colors['text'],
                              selectcolor=self.colors['bg_input'],
                              font=('Segoe UI', 9))
        hp_rb.pack(side=tk.LEFT, padx=10)
        
        mp_rb = tk.Radiobutton(when_frame, text="MP%", variable=when_var, value="MP%",
                              bg=self.colors['bg_dark'], fg=self.colors['text'],
                              selectcolor=self.colors['bg_input'],
                              font=('Segoe UI', 9))
        mp_rb.pack(side=tk.LEFT)
        
        # === IS (condição) ===
        is_frame = tk.Frame(popup, bg=self.colors['bg_dark'])
        is_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(is_frame, text="Is:", bg=self.colors['bg_dark'],
                fg=self.colors['text'], font=('Segoe UI', 9), width=6, anchor='w').pack(side=tk.LEFT)
        
        cond_var = tk.StringVar(value=data.get('condition', '<='))
        cond_combo = ttk.Combobox(is_frame, textvariable=cond_var, values=[">=", "<=", "=="],
                                  width=5, state='readonly')
        cond_combo.pack(side=tk.LEFT, padx=5)
        
        value_var = tk.StringVar(value=str(data.get('value', 80)))
        value_entry = tk.Entry(is_frame, textvariable=value_var, width=5,
                              font=('Segoe UI', 9), bg=self.colors['bg_input'],
                              fg=self.colors['text'], relief=tk.FLAT)
        value_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(is_frame, text="And <=", bg=self.colors['bg_dark'],
                fg=self.colors['text_dim'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=5)
        
        and_var = tk.StringVar(value=str(data.get('and_value', 100)))
        and_entry = tk.Entry(is_frame, textvariable=and_var, width=5,
                            font=('Segoe UI', 9), bg=self.colors['bg_input'],
                            fg=self.colors['text'], relief=tk.FLAT)
        and_entry.pack(side=tk.LEFT, padx=5)
        
        # === SPELL ===
        spell_frame = tk.Frame(popup, bg=self.colors['bg_dark'])
        spell_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(spell_frame, text="Spell:", bg=self.colors['bg_dark'],
                fg=self.colors['text'], font=('Segoe UI', 9), width=6, anchor='w').pack(side=tk.LEFT)
        
        spell_var = tk.StringVar(value=data.get('spell', ''))
        spell_entry = tk.Entry(spell_frame, textvariable=spell_var, width=18,
                              font=('Segoe UI', 9), bg=self.colors['bg_input'],
                              fg=self.colors['text'], relief=tk.FLAT)
        spell_entry.pack(side=tk.LEFT, padx=5)
        
        # Botão para escolher spell da classe
        spell_btn = tk.Button(
            spell_frame, text="...",
            font=('Segoe UI', 8, 'bold'),
            bg=self.colors['btn'], fg=self.colors['accent'],
            relief=tk.FLAT, cursor='hand2',
            command=lambda: self._open_spell_picker_popup(spell_var, popup)
        )
        spell_btn.pack(side=tk.LEFT, padx=5)
        
        # === ITEM ===
        item_frame = tk.Frame(popup, bg=self.colors['bg_dark'])
        item_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(item_frame, text="Item:", bg=self.colors['bg_dark'],
                fg=self.colors['text'], font=('Segoe UI', 9), width=6, anchor='w').pack(side=tk.LEFT)
        
        item_var = tk.StringVar(value=data.get('item_id', ''))
        item_entry = tk.Entry(item_frame, textvariable=item_var, width=10,
                             font=('Segoe UI', 9), bg=self.colors['bg_input'],
                             fg=self.colors['text'], relief=tk.FLAT)
        item_entry.pack(side=tk.LEFT, padx=5)
        
        # Ícone do item (preview)
        item_icon = tk.Label(item_frame, bg=self.colors['bg_dark'])
        item_icon.pack(side=tk.LEFT, padx=10)
        
        # Botão info
        tk.Button(item_frame, text="ⓘ", font=('Segoe UI', 8),
                 bg=self.colors['bg_dark'], fg=self.colors['accent'],
                 relief=tk.FLAT).pack(side=tk.LEFT)
        
        # === MANA ===
        mana_frame = tk.Frame(popup, bg=self.colors['bg_dark'])
        mana_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(mana_frame, text="Mana:", bg=self.colors['bg_dark'],
                fg=self.colors['text'], font=('Segoe UI', 9), width=6, anchor='w').pack(side=tk.LEFT)
        
        mana_var = tk.StringVar(value=str(data.get('mana_cost', 0)))
        mana_entry = tk.Entry(mana_frame, textvariable=mana_var, width=8,
                             font=('Segoe UI', 9), bg=self.colors['bg_input'],
                             fg=self.colors['text'], relief=tk.FLAT)
        mana_entry.pack(side=tk.LEFT, padx=5)
        
        # === HOTKEY ===
        hotkey_frame = tk.Frame(popup, bg=self.colors['bg_dark'])
        hotkey_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(hotkey_frame, text="Hotkey:", bg=self.colors['bg_dark'],
                fg=self.colors['text'], font=('Segoe UI', 9), width=6, anchor='w').pack(side=tk.LEFT)
        
        hotkey_var = tk.StringVar(value=data.get('hotkey', 'F1'))
        hotkey_entry = tk.Entry(hotkey_frame, textvariable=hotkey_var, width=6,
                               font=('Segoe UI', 9), bg=self.colors['bg_input'],
                               fg=self.colors['gold'], relief=tk.FLAT)
        hotkey_entry.pack(side=tk.LEFT, padx=5)
        
        # === CONDITIONS ===
        cond_frame = tk.LabelFrame(popup, text="Conditions", bg=self.colors['bg_dark'],
                                   fg=self.colors['text_dim'], font=('Segoe UI', 8))
        cond_frame.pack(fill=tk.X, padx=15, pady=10)
        
        drunk_var = tk.BooleanVar(value=data.get('drunk', False))
        tk.Checkbutton(cond_frame, text="Drunk", variable=drunk_var,
                      bg=self.colors['bg_dark'], fg=self.colors['text'],
                      selectcolor=self.colors['bg_input'],
                      font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=5)
        
        rooted_var = tk.BooleanVar(value=data.get('rooted', False))
        tk.Checkbutton(cond_frame, text="Rooted", variable=rooted_var,
                      bg=self.colors['bg_dark'], fg=self.colors['text'],
                      selectcolor=self.colors['bg_input'],
                      font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=5)
        
        feared_var = tk.BooleanVar(value=data.get('feared', False))
        tk.Checkbutton(cond_frame, text="Feared", variable=feared_var,
                      bg=self.colors['bg_dark'], fg=self.colors['text'],
                      selectcolor=self.colors['bg_input'],
                      font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=5)
        
        no_target_var = tk.BooleanVar(value=data.get('no_target', False))
        tk.Checkbutton(cond_frame, text="Don't Cast If Targeting", variable=no_target_var,
                      bg=self.colors['bg_dark'], fg=self.colors['text'],
                      selectcolor=self.colors['bg_input'],
                      font=('Segoe UI', 8)).pack(fill=tk.X, padx=5, pady=5)
        
        # === BOTÕES ===
        btn_frame = tk.Frame(popup, bg=self.colors['bg_dark'])
        btn_frame.pack(fill=tk.X, padx=15, pady=15)
        
        def save_and_close():
            # Salva dados
            data['hp_percent'] = when_var.get() == "HP%"
            data['condition'] = cond_var.get()
            data['value'] = int(value_var.get()) if value_var.get().isdigit() else 80
            data['and_value'] = int(and_var.get()) if and_var.get().isdigit() else 100
            data['spell'] = spell_var.get()
            data['item_id'] = item_var.get()
            data['mana_cost'] = int(mana_var.get()) if mana_var.get().isdigit() else 0
            data['hotkey'] = hotkey_var.get()
            data['drunk'] = drunk_var.get()
            data['rooted'] = rooted_var.get()
            data['feared'] = feared_var.get()
            data['no_target'] = no_target_var.get()
            
            # Atualiza display
            self._update_healing_entry_display(idx)
            popup.destroy()
        
        tk.Button(btn_frame, text="Cancel", font=('Segoe UI', 9),
                 bg=self.colors['btn'], fg=self.colors['text'],
                 relief=tk.FLAT, padx=20, cursor='hand2',
                 command=popup.destroy).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Edit", font=('Segoe UI', 9, 'bold'),
                 bg=self.colors['green'], fg='white',
                 relief=tk.FLAT, padx=20, cursor='hand2',
                 command=save_and_close).pack(side=tk.LEFT, padx=5)
        
        popup.transient(self.root)
        popup.grab_set()
    
    def _update_healing_entry_display(self, idx):
        """Atualiza o display de uma entrada de cura"""
        if idx >= len(self.healing_entries):
            return
        
        entry = self.healing_entries[idx]
        data = entry['data']
        
        # Atualiza nome
        display_text = data.get('spell') if data.get('spell') else f"Item {data.get('item_id', '')}"
        entry['name_label'].configure(text=display_text[:15])
        
        # Atualiza ícone
        spell_or_item = data.get('spell') or data.get('item_id', '')
        self._update_row_icon(entry['icon_label'], spell_or_item)
        
        # Atualiza valor
        entry['value_label'].configure(text=str(data.get('value', 0)))
        
        # Atualiza condição
        cond_type = "HP" if data.get('hp_percent') else "MP"
        cond_op = data.get('condition', '<=')
        cond_val = data.get('value', 0)
        cond_text = f"{cond_type} {cond_op} {cond_val}%"
        
        if data.get('and_value', 0) > 0 and data.get('and_value') != 100:
            cond_text += f" A..."
        
        entry['cond_label'].configure(text=cond_text)
    
    def _open_spell_picker_popup(self, spell_var, parent_popup):
        """Abre popup de seleção de spell"""
        picker = tk.Toplevel(parent_popup)
        picker.title(f"Spells - {self.selected_class}")
        picker.geometry("280x350")
        picker.configure(bg=self.colors['bg_dark'])
        
        x = parent_popup.winfo_x() + 50
        y = parent_popup.winfo_y() + 20
        picker.geometry(f"+{x}+{y}")
        
        # Seletor de classe
        class_frame = tk.Frame(picker, bg=self.colors['bg_dark'])
        class_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for class_name in ["Knight", "Paladin", "Sorcerer", "Druid", "Monk"]:
            color = self.class_colors[class_name]
            is_sel = class_name == self.selected_class
            btn = tk.Button(
                class_frame, text=class_name[:2],
                font=('Segoe UI', 7, 'bold'),
                bg=color if is_sel else self.colors['btn'],
                fg='white' if is_sel else self.colors['text'],
                relief=tk.FLAT, width=3,
                command=lambda c=class_name, p=picker, sv=spell_var: self._refresh_spell_picker(c, p, sv)
            )
            btn.pack(side=tk.LEFT, padx=1)
        
        # Lista de spells
        self._create_spell_list(picker, spell_var)
        
        picker.transient(parent_popup)
        picker.grab_set()
    
    def _refresh_spell_picker(self, class_name, picker, spell_var):
        """Atualiza a lista de spells ao mudar classe"""
        self.selected_class = class_name
        
        # Remove lista antiga
        for widget in picker.winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_y() > 50:
                widget.destroy()
        
        self._create_spell_list(picker, spell_var)
    
    def _create_spell_list(self, picker, spell_var):
        """Cria lista de spells no picker"""
        list_frame = tk.Frame(picker, bg=self.colors['bg_dark'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(list_frame, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['bg_dark'])
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        spells = self.class_spells.get(self.selected_class, [])
        color = self.class_colors[self.selected_class]
        
        for spell_name, spell_words, desc in spells:
            row = tk.Frame(scrollable, bg=self.colors['bg_input'])
            row.pack(fill=tk.X, pady=1, padx=2)
            
            # Ícone
            icon_lbl = tk.Label(row, bg=self.colors['bg_input'])
            icon_lbl.pack(side=tk.LEFT, padx=5, pady=3)
            self._update_row_icon(icon_lbl, spell_words)
            
            # Info
            tk.Label(row, text=spell_words, bg=self.colors['bg_input'],
                    fg=self.colors['text'], font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
            
            # Botão selecionar
            def select(sw=spell_words, p=picker):
                spell_var.set(sw)
                p.destroy()
            
            tk.Button(row, text="✓", font=('Segoe UI', 9, 'bold'),
                     bg=color, fg='white', relief=tk.FLAT, width=2,
                     cursor='hand2', command=select).pack(side=tk.RIGHT, padx=5, pady=3)
    
    def _select_class(self, class_name):
        """Seleciona a classe do personagem"""
        self.selected_class = class_name
        
        # Atualiza botões se existirem
        if hasattr(self, 'class_buttons_healing'):
            for name, btn in self.class_buttons_healing.items():
                color = self.class_colors[name]
                if name == class_name:
                    btn.configure(bg=color, fg='white')
                else:
                    btn.configure(bg=self.colors['btn'], fg=self.colors['text'])
    
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
                self.healing.set_enabled(True)  # ATIVA o módulo de healing
                self.healing.start_loop(interval=0.050)
                if self.healing_var:
                    self.healing_var.set(True)  # Atualiza checkbox
        else:
            self.bot_btn.configure(text="▶ START", bg=self.colors['green'])
            self.title_label.configure(text="Baiak Bot Premium  •  Stopped")
            
            if self.healing:
                self.healing.set_enabled(False)  # DESATIVA o módulo
                self.healing.stop_loop()
                if self.healing_var:
                    self.healing_var.set(False)  # Atualiza checkbox
    
    def _toggle_healing(self):
        """Toggle healing"""
        if self.healing and self.healing_var:
            enabled = self.healing_var.get()
            self.healing.set_enabled(enabled)
            print(f"[GUI] Healing {'ATIVADO' if enabled else 'DESATIVADO'}")
    
    def _apply_healing_config(self):
        """Aplica config healing"""
        if not self.healing:
            return
        
        slot = 0
        for entry in self.healing_entries:
            if slot >= 3:
                break
            
            data = entry['data']
            enabled = entry['enabled_var'].get()
            hotkey = data.get('hotkey', 'F1')
            
            try:
                threshold = int(data.get('value', 80))
            except:
                threshold = 80
            
            if threshold > 0 and enabled:
                self.healing.configure_slot(slot, enabled=True, hotkey=hotkey, hp_threshold=threshold)
                slot += 1
    
    def _on_connect(self):
        """Conecta com barra de progresso"""
        # Desabilita o botão durante a conexão
        self.connect_btn.configure(state='disabled', text="Conectando...")
        self.status_label.configure(text="● Conectando...", fg=self.colors['gold'])
        self.root.update()
        
        # Conecta ao processo primeiro (sem auto-scan)
        try:
            if not self.memory.pm:
                import pymem
                self.memory.pm = pymem.Pymem("client.exe")
                self.memory.pid = self.memory.pm.process_id
                self.memory.base_address = self.memory.pm.base_address
                self.memory.connected = True
            
            # Tenta carregar cache
            self.memory._load_offsets()
            
            # Verifica se offsets são válidos
            if self.memory._verify_offsets():
                # Cache válido, conecta direto
                self.healing = HealingModuleV2(self.memory)
                self.healing.find_tibia_window()
                self._on_connect_success()
            else:
                # Precisa escanear - mostra popup com barra de progresso
                self._show_auto_scan_popup()
                
        except Exception as e:
            print(f"[CONNECT] Erro: {e}")
            self._on_connect_failed()
    
    def _on_connect_success(self):
        """Chamado quando conexão bem sucedida"""
        self.connect_btn.configure(state='normal', text="Reconnect")
        
        if self.memory.has_offsets():
            hp = self.memory.get_player_hp_percent()
            mp = self.memory.get_player_mp_percent()
            
            if hp > 0 and hp <= 100:
                self.status_label.configure(text="● Connected", fg=self.colors['green'])
                self.title_label.configure(text="Baiak Bot Premium  •  Connected")
                
                if hasattr(self, 'config_status'):
                    self.config_status.configure(text="● Conectado!", fg=self.colors['green'])
            else:
                self.status_label.configure(text="● Offsets inválidos", fg=self.colors['gold'])
                self.title_label.configure(text="Baiak Bot Premium  •  Precisa escanear")
                self._show_auto_scan_popup()
        else:
            self.status_label.configure(text="● Sem offsets", fg=self.colors['gold'])
            self.title_label.configure(text="Baiak Bot Premium  •  Precisa escanear")
            self._show_auto_scan_popup()
    
    def _on_connect_failed(self):
        """Chamado quando conexão falha"""
        self.connect_btn.configure(state='normal', text="Connect")
        self.status_label.configure(text="● Tibia não encontrado", fg=self.colors['red'])
    
    def _show_auto_scan_popup(self):
        """Mostra popup de scan automático com barra de progresso estilo download"""
        popup = tk.Toplevel(self.root)
        popup.title("Auto Scanner")
        popup.geometry("450x280")
        popup.configure(bg='#1a1a2e')
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.overrideredirect(False)
        
        # Centraliza na tela
        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 225
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 140
        popup.geometry(f"+{x}+{y}")
        
        # Frame principal com borda
        main_frame = tk.Frame(popup, bg='#1a1a2e', highlightbackground='#4a90d9', highlightthickness=2)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Ícone animado (emoji)
        icon_label = tk.Label(main_frame, text="🔍", 
                             bg='#1a1a2e', fg='white',
                             font=('Segoe UI Emoji', 32))
        icon_label.pack(pady=(20, 10))
        
        # Título
        title_label = tk.Label(main_frame, text="Detectando Player Automaticamente", 
                              bg='#1a1a2e', fg='#4a90d9',
                              font=('Segoe UI', 14, 'bold'))
        title_label.pack(pady=(0, 5))
        
        # Subtítulo
        subtitle = tk.Label(main_frame, text="Escaneando memória do Tibia...",
                           bg='#1a1a2e', fg='#888888',
                           font=('Segoe UI', 9))
        subtitle.pack(pady=(0, 15))
        
        # Frame da barra de progresso customizada
        bar_frame = tk.Frame(main_frame, bg='#0d0d1a', height=30)
        bar_frame.pack(fill=tk.X, padx=30, pady=5)
        bar_frame.pack_propagate(False)
        
        # Barra de fundo
        bar_bg = tk.Frame(bar_frame, bg='#2d2d44', height=24)
        bar_bg.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Barra de progresso (vai crescer)
        progress_bar = tk.Frame(bar_bg, bg='#4a90d9', width=0, height=18)
        progress_bar.place(x=3, y=3, height=18)
        
        # Porcentagem no centro da barra
        pct_label = tk.Label(bar_bg, text="0%", 
                            bg='#2d2d44', fg='white',
                            font=('Segoe UI', 10, 'bold'))
        pct_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Status detalhado
        status_label = tk.Label(main_frame, text="Iniciando...",
                               bg='#1a1a2e', fg='#aaaaaa',
                               font=('Segoe UI', 9))
        status_label.pack(pady=(10, 5))
        
        # Info de tempo
        time_label = tk.Label(main_frame, text="Tempo estimado: ~15 segundos",
                             bg='#1a1a2e', fg='#666666',
                             font=('Segoe UI', 8))
        time_label.pack(pady=(0, 15))
        
        # Variáveis para animação
        bar_width = [0]
        max_width = 384  # Largura máxima da barra
        
        def update_progress(pct, msg):
            """Callback para atualizar progresso"""
            try:
                # Atualiza barra
                new_width = int((pct / 100) * max_width)
                bar_width[0] = new_width
                progress_bar.configure(width=new_width)
                progress_bar.place(x=3, y=3, width=new_width, height=18)
                
                # Atualiza porcentagem
                pct_label.configure(text=f"{int(pct)}%")
                
                # Muda cor da barra conforme progresso
                if pct < 30:
                    progress_bar.configure(bg='#4a90d9')  # Azul
                elif pct < 70:
                    progress_bar.configure(bg='#5ba0e9')  # Azul claro
                else:
                    progress_bar.configure(bg='#6bc96b')  # Verde
                
                # Atualiza cor do texto da porcentagem baseado no progresso
                if new_width > max_width / 2:
                    pct_label.configure(bg='#4a90d9' if pct < 70 else '#6bc96b', fg='white')
                else:
                    pct_label.configure(bg='#2d2d44', fg='white')
                
                # Atualiza status
                status_label.configure(text=msg)
                
                popup.update()
            except:
                pass
        
        def scan_thread():
            """Executa scan em thread separada"""
            import time as t
            start_time = t.time()
            
            try:
                from memory.smart_scanner import SmartScanner
                
                scanner = SmartScanner()
                scanner.pm = self.memory.pm
                
                # Callback que também atualiza tempo
                def progress_with_time(pct, msg):
                    elapsed = t.time() - start_time
                    self.root.after(0, lambda: time_label.configure(
                        text=f"Tempo: {elapsed:.1f}s"
                    ))
                    self.root.after(0, lambda p=pct, m=msg: update_progress(p, m))
                
                result = scanner.find_player_auto(progress_callback=progress_with_time)
                
                if result:
                    # Atualiza endereços no memory reader
                    self.memory._addresses["hp"] = result["addr"]
                    self.memory._addresses["hp_max"] = result["addr"] + 0x8
                    self.memory._addresses["mp"] = result["addr"] + 0x620
                    self.memory._addresses["mp_max"] = result["addr"] + 0x628
                    
                    # Salva cache
                    scanner.save_to_cache(result["addr"])
                    
                    # Mostra sucesso por 1 segundo
                    self.root.after(0, lambda: self._show_scan_success(popup, result, t.time() - start_time))
                else:
                    self.root.after(0, lambda: self._scan_failed(popup))
                    
            except Exception as e:
                print(f"[SCAN] Erro: {e}")
                self.root.after(0, lambda: self._scan_failed(popup))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def _show_scan_success(self, popup, result, elapsed):
        """Mostra tela de sucesso antes de fechar"""
        # Limpa popup
        for widget in popup.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = tk.Frame(popup, bg='#1a1a2e', highlightbackground='#6bc96b', highlightthickness=2)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Ícone de sucesso
        tk.Label(main_frame, text="✅", 
                bg='#1a1a2e', fg='white',
                font=('Segoe UI Emoji', 40)).pack(pady=(30, 10))
        
        # Título
        tk.Label(main_frame, text="Player Detectado!", 
                bg='#1a1a2e', fg='#6bc96b',
                font=('Segoe UI', 16, 'bold')).pack(pady=(0, 10))
        
        # Info
        tk.Label(main_frame, text=f"HP: {result['hp']}/{result['hp_max']}  •  MP: {result['mp']}/{result['mp_max']}", 
                bg='#1a1a2e', fg='white',
                font=('Segoe UI', 11)).pack(pady=5)
        
        tk.Label(main_frame, text=f"Tempo: {elapsed:.1f} segundos", 
                bg='#1a1a2e', fg='#888888',
                font=('Segoe UI', 9)).pack(pady=(5, 20))
        
        # Fecha após 1.5 segundos
        popup.after(1500, lambda: self._scan_complete(popup, result))
    
    def _scan_complete(self, popup, result):
        """Chamado quando scan termina com sucesso"""
        try:
            popup.destroy()
        except:
            pass
        
        # Configura healing após scan bem sucedido
        self.healing = HealingModuleV2(self.memory)
        self.healing.find_tibia_window()
        
        self.connect_btn.configure(state='normal', text="Reconnect")
        self.status_label.configure(text="● Connected", fg=self.colors['green'])
        self.title_label.configure(text="Baiak Bot Premium  •  Connected")
        
        if hasattr(self, 'config_status'):
            self.config_status.configure(text="● Conectado!", fg=self.colors['green'])
    
    def _scan_failed(self, popup):
        """Chamado quando scan falha"""
        try:
            popup.destroy()
        except:
            pass
        
        self.connect_btn.configure(state='normal', text="Connect")
        self.status_label.configure(text="● Scan falhou", fg=self.colors['red'])
        self.title_label.configure(text="Baiak Bot Premium  •  Erro")
    
    def _open_scanner(self):
        """Abre scanner simples em uma nova janela"""
        import subprocess
        scanner_path = os.path.join(os.path.dirname(__file__), "..", "memory", "scanner_simple.py")
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
