# -*- coding: utf-8 -*-
"""
Baiak Bot - Interface estilo ElfBot
Compacta e organizada com abas
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


class BotWindowElfStyle:
    """
    Interface estilo ElfBot - compacta com abas
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
        self.root.title("Baiak Bot - Startup")
        self.root.geometry("480x320")
        self.root.resizable(False, False)
        self.root.configure(bg='#2b2b2b')
        
        # Remove borda padrao e cria custom
        self.root.overrideredirect(False)
        
        # Cores estilo ElfBot
        self.colors = {
            'bg': '#2b2b2b',
            'bg_dark': '#1e1e1e',
            'bg_light': '#3c3c3c',
            'btn': '#d4d4d4',
            'btn_hover': '#e8e8e8',
            'btn_active': '#90EE90',
            'text': '#000000',
            'text_light': '#ffffff',
            'accent': '#4a9eff',
            'red': '#ff6b6b',
            'green': '#90EE90',
            'title_bar': '#1e1e1e',
        }
        
        # Cria interface
        self._create_title_bar()
        self._create_menu_buttons()
        self._create_content_area()
        self._create_status_bar()
        
        # Mostra aba inicial
        self._show_tab("Healing")
        
        # Thread de update
        self._start_update_thread()
        
        # Fechar
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_title_bar(self):
        """
        Barra de titulo customizada
        """
        title_bar = tk.Frame(self.root, bg=self.colors['title_bar'], height=25)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)
        
        # Titulo
        self.title_label = tk.Label(
            title_bar, 
            text="Baiak Bot - Startup - 0 ms - 0 exp/hour",
            bg=self.colors['title_bar'],
            fg=self.colors['text_light'],
            font=('Segoe UI', 9)
        )
        self.title_label.pack(side=tk.LEFT, padx=10)
        
        # Botao fechar
        close_btn = tk.Button(
            title_bar,
            text="X",
            bg=self.colors['red'],
            fg='white',
            font=('Segoe UI', 8, 'bold'),
            width=3,
            relief=tk.FLAT,
            command=self._on_close
        )
        close_btn.pack(side=tk.RIGHT, padx=2, pady=2)
        
        # Drag window
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
    
    def _create_menu_buttons(self):
        """
        Grid de botoes de menu estilo ElfBot
        """
        menu_frame = tk.Frame(self.root, bg=self.colors['bg'])
        menu_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Linha 1
        row1 = tk.Frame(menu_frame, bg=self.colors['bg'])
        row1.pack(fill=tk.X, pady=1)
        
        self.menu_buttons = {}
        
        # Botoes linha 1
        buttons_row1 = ["Healing", "Mana", "Attack", "Targeting", "1", "2", "3"]
        for text in buttons_row1:
            btn = tk.Button(
                row1,
                text=text,
                font=('Segoe UI', 8),
                bg=self.colors['btn'],
                fg=self.colors['text'],
                width=9 if len(text) > 2 else 3,
                height=1,
                relief=tk.RAISED,
                bd=1,
                command=lambda t=text: self._show_tab(t)
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.menu_buttons[text] = btn
        
        # Linha 2
        row2 = tk.Frame(menu_frame, bg=self.colors['bg'])
        row2.pack(fill=tk.X, pady=1)
        
        buttons_row2 = ["Tools", "Cavebot", "Config", "Scanner", "Save", "Load", "Help"]
        for text in buttons_row2:
            btn = tk.Button(
                row2,
                text=text,
                font=('Segoe UI', 8),
                bg=self.colors['btn'],
                fg=self.colors['text'],
                width=9 if len(text) > 2 else 3,
                height=1,
                relief=tk.RAISED,
                bd=1,
                command=lambda t=text: self._show_tab(t)
            )
            btn.pack(side=tk.LEFT, padx=1)
            self.menu_buttons[text] = btn
    
    def _create_content_area(self):
        """
        Area de conteudo (muda conforme aba selecionada)
        """
        self.content_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=200)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.content_frame.pack_propagate(False)
        
        # Frames para cada aba (criados sob demanda)
        self.tab_frames = {}
    
    def _create_status_bar(self):
        """
        Barra de status inferior
        """
        status_frame = tk.Frame(self.root, bg=self.colors['bg_light'], height=50)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        status_frame.pack_propagate(False)
        
        # HP Bar
        hp_frame = tk.Frame(status_frame, bg=self.colors['bg_light'])
        hp_frame.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(hp_frame, text="HP:", bg=self.colors['bg_light'], fg='#ff6b6b', 
                font=('Segoe UI', 8, 'bold'), width=4).pack(side=tk.LEFT)
        
        self.hp_bar = ttk.Progressbar(hp_frame, length=200, mode='determinate')
        self.hp_bar.pack(side=tk.LEFT, padx=5)
        self.hp_bar['value'] = 100
        
        self.hp_label = tk.Label(hp_frame, text="100%", bg=self.colors['bg_light'], 
                                fg=self.colors['text_light'], font=('Segoe UI', 8), width=8)
        self.hp_label.pack(side=tk.LEFT)
        
        # Botao ON/OFF
        self.bot_btn = tk.Button(
            hp_frame,
            text="OFF",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['red'],
            fg='white',
            width=6,
            command=self._toggle_bot
        )
        self.bot_btn.pack(side=tk.RIGHT, padx=10)
        
        # Conectar
        self.connect_btn = tk.Button(
            hp_frame,
            text="Connect",
            font=('Segoe UI', 8),
            bg=self.colors['btn'],
            fg=self.colors['text'],
            width=8,
            command=self._on_connect
        )
        self.connect_btn.pack(side=tk.RIGHT, padx=5)
        
        # MP Bar
        mp_frame = tk.Frame(status_frame, bg=self.colors['bg_light'])
        mp_frame.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(mp_frame, text="MP:", bg=self.colors['bg_light'], fg='#6b9fff', 
                font=('Segoe UI', 8, 'bold'), width=4).pack(side=tk.LEFT)
        
        self.mp_bar = ttk.Progressbar(mp_frame, length=200, mode='determinate')
        self.mp_bar.pack(side=tk.LEFT, padx=5)
        self.mp_bar['value'] = 100
        
        self.mp_label = tk.Label(mp_frame, text="100%", bg=self.colors['bg_light'], 
                                fg=self.colors['text_light'], font=('Segoe UI', 8), width=8)
        self.mp_label.pack(side=tk.LEFT)
        
        # Status conexao
        self.status_label = tk.Label(mp_frame, text="Disconnected", bg=self.colors['bg_light'], 
                                    fg=self.colors['red'], font=('Segoe UI', 8))
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def _show_tab(self, tab_name):
        """
        Mostra uma aba
        """
        # Atualiza botoes
        for name, btn in self.menu_buttons.items():
            if name == tab_name:
                btn.configure(bg=self.colors['btn_active'])
            else:
                btn.configure(bg=self.colors['btn'])
        
        # Limpa conteudo
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.current_tab = tab_name
        
        # Cria conteudo da aba
        if tab_name == "Healing":
            self._create_healing_tab()
        elif tab_name == "Mana":
            self._create_mana_tab()
        elif tab_name == "Attack":
            self._create_attack_tab()
        elif tab_name == "Tools":
            self._create_tools_tab()
        elif tab_name == "Config":
            self._create_config_tab()
        elif tab_name == "Scanner":
            self._open_scanner()
        else:
            self._create_coming_soon_tab(tab_name)
    
    def _create_healing_tab(self):
        """
        Aba de Healing
        """
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Titulo
        tk.Label(frame, text="Auto Healing", bg=self.colors['bg_dark'], 
                fg=self.colors['green'], font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W)
        
        tk.Label(frame, text="Cura automatica baseada em HP%", bg=self.colors['bg_dark'], 
                fg=self.colors['text_light'], font=('Segoe UI', 8)).pack(anchor=tk.W, pady=(0,10))
        
        # Toggle healing
        toggle_frame = tk.Frame(frame, bg=self.colors['bg_dark'])
        toggle_frame.pack(fill=tk.X, pady=5)
        
        self.healing_btn = tk.Button(
            toggle_frame,
            text="Healing: OFF",
            font=('Segoe UI', 9, 'bold'),
            bg=self.colors['red'],
            fg='white',
            width=15,
            command=self._toggle_healing
        )
        self.healing_btn.pack(side=tk.LEFT)
        
        # Slots
        self.slot_widgets = []
        
        for i in range(3):
            self._create_healing_slot(frame, i)
    
    def _create_healing_slot(self, parent, index):
        """
        Cria um slot de healing
        """
        slot_frame = tk.Frame(parent, bg=self.colors['bg_light'], relief=tk.GROOVE, bd=1)
        slot_frame.pack(fill=tk.X, pady=3)
        
        widgets = {}
        
        # Checkbox
        var = tk.BooleanVar(value=False)
        widgets['enabled_var'] = var
        
        cb = tk.Checkbutton(
            slot_frame,
            text=f"Slot {index+1}",
            variable=var,
            bg=self.colors['bg_light'],
            fg=self.colors['text_light'],
            selectcolor=self.colors['bg_dark'],
            activebackground=self.colors['bg_light'],
            font=('Segoe UI', 9),
            command=lambda i=index: self._on_slot_toggle(i)
        )
        cb.pack(side=tk.LEFT, padx=5)
        widgets['checkbox'] = cb
        
        # Hotkey
        tk.Label(slot_frame, text="Key:", bg=self.colors['bg_light'], 
                fg=self.colors['text_light'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(10,2))
        
        hotkey_var = tk.StringVar(value=["F1", "F2", "F3"][index])
        widgets['hotkey_var'] = hotkey_var
        
        hotkey_entry = tk.Entry(slot_frame, textvariable=hotkey_var, width=5, 
                               font=('Segoe UI', 8), bg=self.colors['bg_dark'], 
                               fg=self.colors['text_light'], insertbackground='white')
        hotkey_entry.pack(side=tk.LEFT, padx=2)
        hotkey_entry.bind('<FocusOut>', lambda e, i=index: self._on_slot_change(i))
        widgets['hotkey_entry'] = hotkey_entry
        
        # HP Threshold
        tk.Label(slot_frame, text="HP <=", bg=self.colors['bg_light'], 
                fg=self.colors['text_light'], font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(10,2))
        
        hp_var = tk.IntVar(value=[80, 60, 40][index])
        widgets['hp_var'] = hp_var
        
        hp_spin = tk.Spinbox(slot_frame, from_=1, to=100, textvariable=hp_var, width=4,
                            font=('Segoe UI', 8), bg=self.colors['bg_dark'], 
                            fg=self.colors['text_light'],
                            command=lambda i=index: self._on_slot_change(i))
        hp_spin.pack(side=tk.LEFT, padx=2)
        widgets['hp_spin'] = hp_spin
        
        tk.Label(slot_frame, text="%", bg=self.colors['bg_light'], 
                fg=self.colors['text_light'], font=('Segoe UI', 8)).pack(side=tk.LEFT)
        
        self.slot_widgets.append(widgets)
    
    def _create_mana_tab(self):
        """
        Aba de Mana (em breve)
        """
        self._create_coming_soon_tab("Mana", "Auto Mana - Em desenvolvimento")
    
    def _create_attack_tab(self):
        """
        Aba de Attack (em breve)
        """
        self._create_coming_soon_tab("Attack", "Auto Attack - Em desenvolvimento")
    
    def _create_tools_tab(self):
        """
        Aba de Tools (em breve)
        """
        self._create_coming_soon_tab("Tools", "Buffs automaticos - Em desenvolvimento")
    
    def _create_config_tab(self):
        """
        Aba de configuracoes
        """
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(frame, text="Configuracoes", bg=self.colors['bg_dark'], 
                fg=self.colors['accent'], font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W)
        
        # Info
        info_frame = tk.Frame(frame, bg=self.colors['bg_light'], relief=tk.GROOVE, bd=1)
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(info_frame, text="Status: ", bg=self.colors['bg_light'], 
                fg=self.colors['text_light'], font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.config_status = tk.Label(info_frame, text="Nao conectado", bg=self.colors['bg_light'], 
                                     fg=self.colors['red'], font=('Segoe UI', 9, 'bold'))
        self.config_status.pack(side=tk.LEFT)
        
        # Botoes
        btn_frame = tk.Frame(frame, bg=self.colors['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(btn_frame, text="Reconectar", font=('Segoe UI', 9), 
                 bg=self.colors['btn'], fg=self.colors['text'],
                 command=self._on_connect).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Scanner de Offsets", font=('Segoe UI', 9), 
                 bg=self.colors['btn'], fg=self.colors['text'],
                 command=self._open_scanner).pack(side=tk.LEFT, padx=5)
    
    def _create_coming_soon_tab(self, name, message=None):
        """
        Aba placeholder
        """
        frame = tk.Frame(self.content_frame, bg=self.colors['bg_dark'])
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=name, bg=self.colors['bg_dark'], 
                fg=self.colors['accent'], font=('Segoe UI', 14, 'bold')).pack(pady=30)
        
        msg = message or f"Modulo {name} - Em desenvolvimento"
        tk.Label(frame, text=msg, bg=self.colors['bg_dark'], 
                fg=self.colors['text_light'], font=('Segoe UI', 10)).pack()
        
        tk.Label(frame, text="Em breve!", bg=self.colors['bg_dark'], 
                fg=self.colors['green'], font=('Segoe UI', 9)).pack(pady=10)
    
    def _toggle_bot(self):
        """
        Liga/desliga bot
        """
        self.bot_enabled = not self.bot_enabled
        
        if self.bot_enabled:
            self.bot_btn.configure(text="ON", bg=self.colors['green'], fg='black')
            self.title_label.configure(text="Baiak Bot - Running")
            
            if self.healing:
                self.healing.start_loop(interval=0.050)
        else:
            self.bot_btn.configure(text="OFF", bg=self.colors['red'], fg='white')
            self.title_label.configure(text="Baiak Bot - Stopped")
            
            if self.healing:
                self.healing.stop_loop()
    
    def _toggle_healing(self):
        """
        Liga/desliga healing
        """
        if not self.healing:
            return
        
        enabled = self.healing.toggle()
        
        if enabled:
            self.healing_btn.configure(text="Healing: ON", bg=self.colors['green'], fg='black')
        else:
            self.healing_btn.configure(text="Healing: OFF", bg=self.colors['red'], fg='white')
    
    def _on_slot_toggle(self, index):
        """
        Toggle slot
        """
        if not self.healing:
            return
        
        widgets = self.slot_widgets[index]
        enabled = widgets['enabled_var'].get()
        self.healing.configure_slot(index, enabled=enabled)
    
    def _on_slot_change(self, index):
        """
        Mudanca no slot
        """
        if not self.healing:
            return
        
        widgets = self.slot_widgets[index]
        hotkey = widgets['hotkey_var'].get()
        
        try:
            hp = widgets['hp_var'].get()
        except:
            hp = 80
        
        self.healing.configure_slot(index, hotkey=hotkey, hp_threshold=hp)
    
    def _on_connect(self):
        """
        Conecta ao Tibia
        """
        if self.memory.connect():
            self.healing = HealingModuleV2(self.memory)
            self.healing.find_tibia_window()
            self.healing.on_heal(self._on_heal_executed)
            
            self.status_label.configure(text="Connected", fg=self.colors['green'])
            self.connect_btn.configure(text="Reconnect")
            
            if hasattr(self, 'config_status'):
                self.config_status.configure(text="Conectado!", fg=self.colors['green'])
            
            if self.memory.has_offsets():
                self.title_label.configure(text="Baiak Bot - Connected")
            else:
                self.title_label.configure(text="Baiak Bot - No Offsets!")
        else:
            self.status_label.configure(text="Error!", fg=self.colors['red'])
    
    def _on_heal_executed(self, slot_index, hp_percent, threshold):
        """
        Callback de cura
        """
        pass  # Pode adicionar log ou efeito visual
    
    def _open_scanner(self):
        """
        Abre scanner
        """
        import subprocess
        scanner_path = os.path.join(os.path.dirname(__file__), "..", "memory", "scanner_advanced.py")
        try:
            subprocess.Popen([sys.executable, scanner_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        except:
            pass
    
    def _update_loop(self):
        """
        Loop de update
        """
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
        """
        Inicia thread
        """
        thread = threading.Thread(target=self._update_loop, daemon=True)
        thread.start()
    
    def _on_close(self):
        """
        Fecha
        """
        self.running = False
        self.bot_enabled = False
        
        if self.healing:
            self.healing.stop_loop()
        
        if self.memory:
            self.memory.disconnect()
        
        self.root.destroy()
    
    def run(self):
        """
        Inicia
        """
        self.root.mainloop()


def main():
    app = BotWindowElfStyle()
    app.run()


if __name__ == "__main__":
    main()
