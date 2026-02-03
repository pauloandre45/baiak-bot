# -*- coding: utf-8 -*-
"""
Baiak Bot v2 - Interface Principal
Usa leitura de memoria direta (instantaneo!)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
import os

# Adiciona path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.reader_v2 import TibiaMemoryReader
from modules.healing_v2 import HealingModuleV2


class BotWindowV2:
    """
    Interface grafica do Bot v2
    """
    
    def __init__(self):
        # Componentes
        self.memory = TibiaMemoryReader()
        self.healing = None  # Criado apos conectar
        
        # Estado
        self.bot_enabled = False
        self.running = True
        self._update_thread = None
        
        # Janela
        self.root = tk.Tk()
        self.root.title("Baiak Bot v2 - Memory Reader")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a2e')
        
        # Cores
        self.colors = {
            'bg': '#1a1a2e',
            'bg_light': '#16213e',
            'accent': '#0f3460',
            'green': '#00ff88',
            'red': '#ff4757',
            'yellow': '#ffa502',
            'white': '#ffffff',
            'gray': '#888888',
            'blue': '#3366ff'
        }
        
        # Cria interface
        self._create_widgets()
        
        # Inicia thread de update
        self._start_update_thread()
        
        # Evento de fechar
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_widgets(self):
        """
        Cria todos os widgets
        """
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ============================================
        # HEADER
        # ============================================
        header = tk.Frame(main, bg=self.colors['bg_light'], height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)
        
        tk.Label(header, text="BAIAK BOT v2", 
                font=('Arial', 16, 'bold'),
                bg=self.colors['bg_light'], 
                fg=self.colors['green']).pack(side=tk.LEFT, padx=15, pady=15)
        
        # Status
        self.status_label = tk.Label(header, text="DESCONECTADO",
                                    font=('Arial', 10, 'bold'),
                                    bg=self.colors['bg_light'], 
                                    fg=self.colors['red'])
        self.status_label.pack(side=tk.RIGHT, padx=15)
        
        # Botao conectar
        self.connect_btn = tk.Button(header, text="Conectar",
                                    command=self._on_connect,
                                    bg=self.colors['accent'], 
                                    fg=self.colors['white'],
                                    font=('Arial', 9), width=10)
        self.connect_btn.pack(side=tk.RIGHT, padx=5, pady=15)
        
        # ============================================
        # INFO DO PLAYER
        # ============================================
        info = tk.Frame(main, bg=self.colors['bg_light'])
        info.pack(fill=tk.X, pady=(0, 10))
        
        # HP
        hp_frame = tk.Frame(info, bg=self.colors['bg_light'])
        hp_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(hp_frame, text="HP:", font=('Arial', 11, 'bold'),
                bg=self.colors['bg_light'], fg=self.colors['red']).pack(side=tk.LEFT)
        
        self.hp_label = tk.Label(hp_frame, text="--- / --- (---%)",
                                font=('Arial', 11),
                                bg=self.colors['bg_light'], 
                                fg=self.colors['white'])
        self.hp_label.pack(side=tk.LEFT, padx=10)
        
        self.hp_bar = ttk.Progressbar(hp_frame, length=180, mode='determinate')
        self.hp_bar.pack(side=tk.RIGHT, padx=5)
        self.hp_bar['value'] = 100
        
        # MP
        mp_frame = tk.Frame(info, bg=self.colors['bg_light'])
        mp_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(mp_frame, text="MP:", font=('Arial', 11, 'bold'),
                bg=self.colors['bg_light'], fg=self.colors['blue']).pack(side=tk.LEFT)
        
        self.mp_label = tk.Label(mp_frame, text="--- / --- (---%)",
                                font=('Arial', 11),
                                bg=self.colors['bg_light'], 
                                fg=self.colors['white'])
        self.mp_label.pack(side=tk.LEFT, padx=10)
        
        self.mp_bar = ttk.Progressbar(mp_frame, length=180, mode='determinate')
        self.mp_bar.pack(side=tk.RIGHT, padx=5)
        self.mp_bar['value'] = 100
        
        # ============================================
        # BOTAO BOT ON/OFF
        # ============================================
        bot_frame = tk.Frame(main, bg=self.colors['bg'])
        bot_frame.pack(fill=tk.X, pady=10)
        
        self.bot_btn = tk.Button(bot_frame, text="BOT: OFF",
                                command=self._toggle_bot,
                                bg=self.colors['red'], 
                                fg=self.colors['white'],
                                font=('Arial', 14, 'bold'),
                                width=20, height=2,
                                state=tk.DISABLED)  # Desabilitado ate conectar
        self.bot_btn.pack()
        
        # ============================================
        # HEALING
        # ============================================
        healing_frame = tk.LabelFrame(main, text=" AUTO HEALING ",
                                     bg=self.colors['bg_light'], 
                                     fg=self.colors['green'],
                                     font=('Arial', 11, 'bold'))
        healing_frame.pack(fill=tk.X, pady=10)
        
        # Header
        heal_header = tk.Frame(healing_frame, bg=self.colors['bg_light'])
        heal_header.pack(fill=tk.X, padx=10, pady=5)
        
        self.healing_btn = tk.Button(heal_header, text="OFF",
                                    command=self._toggle_healing,
                                    bg=self.colors['red'], 
                                    fg=self.colors['white'],
                                    font=('Arial', 10, 'bold'), 
                                    width=6,
                                    state=tk.DISABLED)
        self.healing_btn.pack(side=tk.LEFT)
        
        tk.Label(heal_header, text="Cura automatica por HP%",
                bg=self.colors['bg_light'], fg=self.colors['white'],
                font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        
        # Slots
        self.slot_widgets = []
        
        for i in range(3):
            self._create_slot_widget(healing_frame, i)
        
        # ============================================
        # CONFIGURACAO
        # ============================================
        config_frame = tk.LabelFrame(main, text=" CONFIGURACAO ",
                                    bg=self.colors['bg_light'], 
                                    fg=self.colors['yellow'],
                                    font=('Arial', 10, 'bold'))
        config_frame.pack(fill=tk.X, pady=10)
        
        # Botao para abrir scanner
        scanner_btn = tk.Button(config_frame, 
                               text="Configurar Offsets (Scanner)",
                               command=self._open_scanner,
                               bg=self.colors['accent'], 
                               fg=self.colors['white'],
                               font=('Arial', 9))
        scanner_btn.pack(pady=10)
        
        tk.Label(config_frame, 
                text="Se HP/MP nao estao atualizando, execute o Scanner\npara encontrar os enderecos de memoria corretos.",
                bg=self.colors['bg_light'], fg=self.colors['gray'],
                font=('Arial', 8), justify=tk.CENTER).pack(pady=(0, 10))
        
        # ============================================
        # LOG
        # ============================================
        log_frame = tk.LabelFrame(main, text=" LOG ",
                                 bg=self.colors['bg_light'], 
                                 fg=self.colors['yellow'],
                                 font=('Arial', 10, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=5,
                               bg='#0d0d0d', fg=self.colors['gray'],
                               font=('Consolas', 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Mensagem inicial
        self._log("Bot v2 iniciado - Leitura de memoria direta!")
        self._log("Clique em 'Conectar' para comecar.")
    
    def _create_slot_widget(self, parent, index):
        """
        Cria widget de um slot de healing
        """
        frame = tk.Frame(parent, bg=self.colors['bg_light'])
        frame.pack(fill=tk.X, padx=10, pady=3)
        
        widgets = {}
        
        # Checkbox
        var = tk.BooleanVar(value=False)
        widgets['enabled_var'] = var
        
        cb = tk.Checkbutton(frame, text=f"Slot {index+1}",
                           variable=var,
                           command=lambda i=index: self._on_slot_toggle(i),
                           bg=self.colors['bg_light'], 
                           fg=self.colors['white'],
                           selectcolor=self.colors['accent'],
                           activebackground=self.colors['bg_light'],
                           font=('Arial', 9),
                           state=tk.DISABLED)
        cb.pack(side=tk.LEFT)
        widgets['checkbox'] = cb
        
        # Hotkey
        tk.Label(frame, text="Hotkey:", 
                bg=self.colors['bg_light'],
                fg=self.colors['white'], 
                font=('Arial', 8)).pack(side=tk.LEFT, padx=(15, 2))
        
        hotkey_var = tk.StringVar(value=["F1", "F2", "F3"][index])
        widgets['hotkey_var'] = hotkey_var
        
        hotkey_entry = tk.Entry(frame, textvariable=hotkey_var, 
                               width=5,
                               bg=self.colors['accent'], 
                               fg=self.colors['white'],
                               font=('Arial', 9))
        hotkey_entry.pack(side=tk.LEFT)
        hotkey_entry.bind('<FocusOut>', lambda e, i=index: self._on_slot_change(i))
        widgets['hotkey_entry'] = hotkey_entry
        
        # HP Threshold
        tk.Label(frame, text="HP <=", 
                bg=self.colors['bg_light'],
                fg=self.colors['white'], 
                font=('Arial', 8)).pack(side=tk.LEFT, padx=(15, 2))
        
        hp_var = tk.IntVar(value=[80, 60, 40][index])
        widgets['hp_var'] = hp_var
        
        hp_spin = tk.Spinbox(frame, from_=1, to=100, 
                            textvariable=hp_var,
                            width=4, 
                            bg=self.colors['accent'], 
                            fg=self.colors['white'],
                            font=('Arial', 9),
                            command=lambda i=index: self._on_slot_change(i))
        hp_spin.pack(side=tk.LEFT)
        hp_spin.bind('<FocusOut>', lambda e, i=index: self._on_slot_change(i))
        widgets['hp_spin'] = hp_spin
        
        tk.Label(frame, text="%", 
                bg=self.colors['bg_light'],
                fg=self.colors['white'], 
                font=('Arial', 8)).pack(side=tk.LEFT)
        
        self.slot_widgets.append(widgets)
    
    def _on_connect(self):
        """
        Conecta ao Tibia
        """
        self._log("Procurando cliente Tibia...")
        
        if self.memory.connect():
            self.status_label.configure(text="CONECTADO", fg=self.colors['green'])
            self.connect_btn.configure(text="Reconectar")
            
            # Cria modulo de healing
            self.healing = HealingModuleV2(self.memory)
            self.healing.find_tibia_window()
            
            # Configura callback de cura
            self.healing.on_heal(self._on_heal_executed)
            
            # Habilita controles
            self.bot_btn.configure(state=tk.NORMAL)
            self.healing_btn.configure(state=tk.NORMAL)
            for widgets in self.slot_widgets:
                widgets['checkbox'].configure(state=tk.NORMAL)
            
            # Verifica offsets
            if self.memory.has_offsets():
                self._log("Conectado! Offsets carregados.")
                self._log("HP/MP serao lidos da memoria.")
            else:
                self._log("Conectado, mas OFFSETS NAO CONFIGURADOS!")
                self._log("Execute o Scanner para configurar.")
        else:
            self.status_label.configure(text="ERRO", fg=self.colors['red'])
            self._log("ERRO: Tibia nao encontrado!")
            self._log("Verifique se o jogo esta aberto.")
    
    def _toggle_bot(self):
        """
        Liga/desliga bot
        """
        self.bot_enabled = not self.bot_enabled
        
        if self.bot_enabled:
            self.bot_btn.configure(text="BOT: ON", bg=self.colors['green'])
            self._log("Bot LIGADO!")
            
            # Inicia loop de healing
            if self.healing:
                self.healing.start_loop(interval=0.050)
        else:
            self.bot_btn.configure(text="BOT: OFF", bg=self.colors['red'])
            self._log("Bot DESLIGADO")
            
            # Para loop
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
            self.healing_btn.configure(text="ON", bg=self.colors['green'])
            self._log("Healing LIGADO")
        else:
            self.healing_btn.configure(text="OFF", bg=self.colors['red'])
            self._log("Healing DESLIGADO")
    
    def _on_slot_toggle(self, index):
        """
        Toggle de slot
        """
        if not self.healing:
            return
        
        widgets = self.slot_widgets[index]
        enabled = widgets['enabled_var'].get()
        
        self.healing.configure_slot(index, enabled=enabled)
        
        status = "ON" if enabled else "OFF"
        self._log(f"Slot {index+1}: {status}")
    
    def _on_slot_change(self, index):
        """
        Mudanca de config do slot
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
    
    def _on_heal_executed(self, slot_index, hp_percent, threshold):
        """
        Callback quando cura e executada
        """
        slot = self.healing.get_slot(slot_index)
        self._log(f"CURA! Slot {slot_index+1} ({slot.hotkey}) - HP: {hp_percent}%")
    
    def _open_scanner(self):
        """
        Abre o scanner de offsets
        """
        self._log("Abrindo Scanner de Offsets...")
        
        import subprocess
        import sys
        
        scanner_path = os.path.join(os.path.dirname(__file__), "..", "memory", "scanner_advanced.py")
        
        try:
            subprocess.Popen([sys.executable, scanner_path], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            self._log("Scanner aberto em nova janela")
        except Exception as e:
            self._log(f"Erro ao abrir scanner: {e}")
    
    def _log(self, message):
        """
        Adiciona ao log
        """
        self.log_text.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _update_loop(self):
        """
        Loop de atualizacao da interface
        """
        while self.running:
            try:
                if self.memory and self.memory.is_connected() and self.memory.has_offsets():
                    # Le HP
                    hp = self.memory.get_player_hp()
                    hp_max = self.memory.get_player_hp_max()
                    hp_pct = self.memory.get_player_hp_percent()
                    
                    self.hp_label.configure(text=f"{hp} / {hp_max} ({hp_pct}%)")
                    self.hp_bar['value'] = hp_pct
                    
                    # Le MP
                    mp = self.memory.get_player_mp()
                    mp_max = self.memory.get_player_mp_max()
                    mp_pct = self.memory.get_player_mp_percent()
                    
                    self.mp_label.configure(text=f"{mp} / {mp_max} ({mp_pct}%)")
                    self.mp_bar['value'] = mp_pct
                    
            except Exception as e:
                pass
            
            time.sleep(0.1)
    
    def _start_update_thread(self):
        """
        Inicia thread de update
        """
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
    
    def _on_close(self):
        """
        Fecha aplicacao
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
        Inicia aplicacao
        """
        self.root.mainloop()


def main():
    print("=" * 50)
    print("  BAIAK BOT v2 - Memory Reader")
    print("  Tibia 15.11")
    print("=" * 50)
    print()
    
    app = BotWindowV2()
    app.run()
    
    print("\n[EXIT] Bot encerrado.")


if __name__ == "__main__":
    main()
