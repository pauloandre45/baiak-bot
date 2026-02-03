# -*- coding: utf-8 -*-
"""
Janela principal do Bot - Interface Grafica
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time


class BotWindow:
    """
    Janela principal do Bot para Tibia 15.11
    """
    
    def __init__(self, memory_reader, screen_reader, healing_module):
        self.memory = memory_reader
        self.screen = screen_reader
        self.healing = healing_module
        
        # Estado
        self.bot_enabled = False
        self.running = True
        self.bot_thread = None
        
        # Cria janela
        self.root = tk.Tk()
        self.root.title("Baiak Bot - Tibia 15.11")
        self.root.geometry("420x520")
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a2e')
        
        # Estilo
        self._setup_styles()
        
        # Widgets
        self._create_widgets()
        
        # Inicia thread de atualizacao
        self._start_update_thread()
        
        # Evento de fechar
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_styles(self):
        """
        Configura estilos visuais
        """
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cores
        self.colors = {
            'bg': '#1a1a2e',
            'bg_light': '#16213e',
            'accent': '#0f3460',
            'green': '#00ff88',
            'red': '#ff4757',
            'yellow': '#ffa502',
            'white': '#ffffff',
            'gray': '#888888'
        }
        
        # Configura estilos
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['white'])
        style.configure('TButton', padding=5)
        style.configure('Green.TButton', foreground=self.colors['green'])
        style.configure('Red.TButton', foreground=self.colors['red'])
    
    def _create_widgets(self):
        """
        Cria todos os widgets da interface
        """
        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ============================================
        # HEADER - Status de conexao
        # ============================================
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_light'], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Titulo
        title = tk.Label(header_frame, text="BAIAK BOT", 
                        font=('Arial', 16, 'bold'),
                        bg=self.colors['bg_light'], fg=self.colors['green'])
        title.pack(side=tk.LEFT, padx=15, pady=15)
        
        # Status de conexao
        self.status_label = tk.Label(header_frame, text="DESCONECTADO",
                                     font=('Arial', 10, 'bold'),
                                     bg=self.colors['bg_light'], fg=self.colors['red'])
        self.status_label.pack(side=tk.RIGHT, padx=15, pady=15)
        
        # Botao conectar
        self.connect_btn = tk.Button(header_frame, text="Conectar",
                                     command=self._on_connect,
                                     bg=self.colors['accent'], fg=self.colors['white'],
                                     font=('Arial', 9), width=10)
        self.connect_btn.pack(side=tk.RIGHT, padx=5, pady=15)
        
        # ============================================
        # INFO DO PLAYER
        # ============================================
        info_frame = tk.Frame(main_frame, bg=self.colors['bg_light'])
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # HP Bar
        hp_frame = tk.Frame(info_frame, bg=self.colors['bg_light'])
        hp_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(hp_frame, text="HP:", font=('Arial', 10, 'bold'),
                bg=self.colors['bg_light'], fg=self.colors['white']).pack(side=tk.LEFT)
        
        self.hp_label = tk.Label(hp_frame, text="HP: ---%",
                                font=('Arial', 10),
                                bg=self.colors['bg_light'], fg=self.colors['red'])
        self.hp_label.pack(side=tk.LEFT, padx=10)
        
        # Botao para configurar barra HP
        self.config_hp_btn = tk.Button(hp_frame, text="Configurar",
                                       command=self._config_hp_bar,
                                       bg=self.colors['accent'], fg=self.colors['white'],
                                       font=('Arial', 8), width=10)
        self.config_hp_btn.pack(side=tk.RIGHT, padx=5)
        
        # HP Progress bar
        self.hp_bar = ttk.Progressbar(hp_frame, length=150, mode='determinate')
        self.hp_bar.pack(side=tk.RIGHT, padx=5)
        self.hp_bar['value'] = 100
        
        # MP Bar
        mp_frame = tk.Frame(info_frame, bg=self.colors['bg_light'])
        mp_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(mp_frame, text="MP:", font=('Arial', 10, 'bold'),
                bg=self.colors['bg_light'], fg=self.colors['white']).pack(side=tk.LEFT)
        
        self.mp_label = tk.Label(mp_frame, text="MP: ---%",
                                font=('Arial', 10),
                                bg=self.colors['bg_light'], fg='#3366ff')
        self.mp_label.pack(side=tk.LEFT, padx=10)
        
        # Botao para configurar barra MP
        self.config_mp_btn = tk.Button(mp_frame, text="Configurar",
                                       command=self._config_mp_bar,
                                       bg=self.colors['accent'], fg=self.colors['white'],
                                       font=('Arial', 8), width=10)
        self.config_mp_btn.pack(side=tk.RIGHT, padx=5)
        
        # MP Progress bar
        self.mp_bar = ttk.Progressbar(mp_frame, length=150, mode='determinate')
        self.mp_bar.pack(side=tk.RIGHT, padx=5)
        self.mp_bar['value'] = 100
        
        # MP Progress bar
        self.mp_bar = ttk.Progressbar(mp_frame, length=200, mode='determinate')
        self.mp_bar.pack(side=tk.RIGHT, padx=5)
        self.mp_bar['value'] = 100
        
        # ============================================
        # BOTAO BOT ON/OFF
        # ============================================
        bot_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        bot_frame.pack(fill=tk.X, pady=10)
        
        self.bot_btn = tk.Button(bot_frame, text="BOT: OFF",
                                command=self._toggle_bot,
                                bg=self.colors['red'], fg=self.colors['white'],
                                font=('Arial', 14, 'bold'),
                                width=20, height=2)
        self.bot_btn.pack()
        
        # ============================================
        # SECAO HEALING
        # ============================================
        healing_frame = tk.LabelFrame(main_frame, text=" HEALING ",
                                      bg=self.colors['bg_light'], fg=self.colors['green'],
                                      font=('Arial', 11, 'bold'))
        healing_frame.pack(fill=tk.X, pady=10)
        
        # Header do healing
        heal_header = tk.Frame(healing_frame, bg=self.colors['bg_light'])
        heal_header.pack(fill=tk.X, padx=10, pady=5)
        
        self.healing_btn = tk.Button(heal_header, text="OFF",
                                    command=self._toggle_healing,
                                    bg=self.colors['red'], fg=self.colors['white'],
                                    font=('Arial', 10, 'bold'), width=6)
        self.healing_btn.pack(side=tk.LEFT)
        
        tk.Label(heal_header, text="Auto Healing",
                bg=self.colors['bg_light'], fg=self.colors['white'],
                font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        
        # Slots de healing
        self.slot_frames = []
        self.slot_widgets = []
        
        for i in range(3):
            self._create_healing_slot(healing_frame, i)
        
        # ============================================
        # LOG/STATUS
        # ============================================
        log_frame = tk.LabelFrame(main_frame, text=" LOG ",
                                 bg=self.colors['bg_light'], fg=self.colors['yellow'],
                                 font=('Arial', 10, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=6, 
                               bg='#0d0d0d', fg=self.colors['gray'],
                               font=('Consolas', 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log inicial
        self._log("Bot iniciado. Clique em 'Conectar' para detectar o Tibia.")
    
    def _create_healing_slot(self, parent, index):
        """
        Cria um slot de healing
        """
        slot = self.healing.get_slot_config(index)
        
        frame = tk.Frame(parent, bg=self.colors['bg_light'])
        frame.pack(fill=tk.X, padx=10, pady=3)
        
        widgets = {}
        
        # Checkbox ON/OFF
        var = tk.BooleanVar(value=slot.enabled if slot else False)
        widgets['enabled_var'] = var
        
        cb = tk.Checkbutton(frame, text=f"Slot {index+1}",
                          variable=var,
                          command=lambda i=index: self._on_slot_toggle(i),
                          bg=self.colors['bg_light'], fg=self.colors['white'],
                          selectcolor=self.colors['accent'],
                          activebackground=self.colors['bg_light'],
                          font=('Arial', 9))
        cb.pack(side=tk.LEFT)
        widgets['checkbox'] = cb
        
        # Tipo (Potion/Spell)
        type_var = tk.StringVar(value=slot.slot_type if slot else "potion")
        widgets['type_var'] = type_var
        
        type_combo = ttk.Combobox(frame, textvariable=type_var, 
                                 values=["potion", "spell"],
                                 width=7, state='readonly')
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', lambda e, i=index: self._on_slot_type_change(i))
        widgets['type_combo'] = type_combo
        
        # Hotkey
        tk.Label(frame, text="Key:", bg=self.colors['bg_light'], 
                fg=self.colors['white'], font=('Arial', 8)).pack(side=tk.LEFT, padx=(10, 2))
        
        hotkey_var = tk.StringVar(value=slot.hotkey if slot else "F1")
        widgets['hotkey_var'] = hotkey_var
        
        hotkey_entry = tk.Entry(frame, textvariable=hotkey_var, width=5,
                               bg=self.colors['accent'], fg=self.colors['white'],
                               font=('Arial', 9))
        hotkey_entry.pack(side=tk.LEFT)
        hotkey_entry.bind('<FocusOut>', lambda e, i=index: self._on_slot_hotkey_change(i))
        widgets['hotkey_entry'] = hotkey_entry
        
        # HP %
        tk.Label(frame, text="HP%:", bg=self.colors['bg_light'],
                fg=self.colors['white'], font=('Arial', 8)).pack(side=tk.LEFT, padx=(10, 2))
        
        hp_var = tk.IntVar(value=slot.hp_percent if slot else 80)
        widgets['hp_var'] = hp_var
        
        hp_spin = tk.Spinbox(frame, from_=1, to=100, textvariable=hp_var,
                            width=4, bg=self.colors['accent'], fg=self.colors['white'],
                            font=('Arial', 9),
                            command=lambda i=index: self._on_slot_hp_change(i))
        hp_spin.pack(side=tk.LEFT)
        hp_spin.bind('<FocusOut>', lambda e, i=index: self._on_slot_hp_change(i))
        widgets['hp_spin'] = hp_spin
        
        self.slot_frames.append(frame)
        self.slot_widgets.append(widgets)
    
    def _toggle_bot(self):
        """
        Liga/desliga o bot
        """
        self.bot_enabled = not self.bot_enabled
        
        if self.bot_enabled:
            self.bot_btn.configure(text="BOT: ON", bg=self.colors['green'])
            self._log("Bot LIGADO")
        else:
            self.bot_btn.configure(text="BOT: OFF", bg=self.colors['red'])
            self._log("Bot DESLIGADO")
    
    def _toggle_healing(self):
        """
        Liga/desliga o modulo de healing
        """
        self.healing.toggle()
        
        if self.healing.enabled:
            self.healing_btn.configure(text="ON", bg=self.colors['green'])
            self._log("Healing LIGADO")
        else:
            self.healing_btn.configure(text="OFF", bg=self.colors['red'])
            self._log("Healing DESLIGADO")
    
    def _on_slot_toggle(self, index):
        """
        Toggle de um slot de healing
        """
        widgets = self.slot_widgets[index]
        enabled = widgets['enabled_var'].get()
        self.healing.configure_slot(index, enabled=enabled)
        
        status = "ON" if enabled else "OFF"
        self._log(f"Healing Slot {index+1}: {status}")
    
    def _on_slot_type_change(self, index):
        """
        Mudanca de tipo de um slot
        """
        widgets = self.slot_widgets[index]
        slot_type = widgets['type_var'].get()
        self.healing.configure_slot(index, slot_type=slot_type)
    
    def _on_slot_hotkey_change(self, index):
        """
        Mudanca de hotkey de um slot
        """
        widgets = self.slot_widgets[index]
        hotkey = widgets['hotkey_var'].get()
        self.healing.configure_slot(index, hotkey=hotkey)
    
    def _on_slot_hp_change(self, index):
        """
        Mudanca de HP% de um slot
        """
        widgets = self.slot_widgets[index]
        try:
            hp_percent = widgets['hp_var'].get()
            self.healing.configure_slot(index, hp_percent=hp_percent)
        except:
            pass
    
    def _on_connect(self):
        """
        Tenta conectar ao Tibia
        """
        self._log("Procurando cliente Tibia...")
        
        # Tenta conectar via screen reader (preferido)
        if self.screen.find_tibia_window():
            self.status_label.configure(text="CONECTADO", fg=self.colors['green'])
            self.connect_btn.configure(text="Reconectar")
            self._log("Conectado! Agora configure as barras HP/MP")
            self._log("Clique em 'Configurar' ao lado de HP")
            return
        
        # Fallback para memory reader
        if self.memory.connect():
            self.status_label.configure(text="CONECTADO", fg=self.colors['green'])
            self.connect_btn.configure(text="Reconectar")
            self._log("Conectado ao Tibia (memoria)!")
        else:
            self.status_label.configure(text="ERRO", fg=self.colors['red'])
            self._log("ERRO: Nao foi possivel conectar ao Tibia")
            self._log("Certifique-se que o jogo esta aberto")
    
    def _config_hp_bar(self):
        """
        Inicia configuracao da barra de HP
        """
        self._log("=== CONFIGURAR BARRA HP ===")
        self._log("1. Posicione o mouse no INICIO da barra HP")
        self._log("2. Pressione ENTER")
        
        self.config_hp_btn.configure(text="Esperando...", bg=self.colors['yellow'])
        self.root.bind('<Return>', self._capture_hp_start)
    
    def _capture_hp_start(self, event):
        """
        Captura posicao inicial da barra HP
        """
        pos = self.screen.get_mouse_position()
        self._hp_start_pos = pos
        self._log(f"Inicio HP: {pos}")
        self._log("Agora posicione no FIM da barra HP")
        self._log("Pressione ENTER novamente")
        
        self.root.unbind('<Return>')
        self.root.bind('<Return>', self._capture_hp_end)
    
    def _capture_hp_end(self, event):
        """
        Captura posicao final da barra HP
        """
        pos = self.screen.get_mouse_position()
        self._hp_end_pos = (pos[0], self._hp_start_pos[1])  # Usa mesmo Y
        
        self.screen.set_hp_bar(self._hp_start_pos, self._hp_end_pos)
        
        self._log(f"Fim HP: {self._hp_end_pos}")
        self._log("Barra HP configurada!")
        
        # Debug - mostra cores nos cantos da barra
        c1 = self.screen.get_pixel_color(self._hp_start_pos[0], self._hp_start_pos[1])
        c2 = self.screen.get_pixel_color(self._hp_end_pos[0], self._hp_end_pos[1])
        self._log(f"Cor inicio: RGB{c1}")
        self._log(f"Cor fim: RGB{c2}")
        
        self.config_hp_btn.configure(text="OK!", bg=self.colors['green'])
        self.root.unbind('<Return>')
        
        # Reseta apos 2 segundos
        self.root.after(2000, lambda: self.config_hp_btn.configure(
            text="Configurar", bg=self.colors['accent']))
    
    def _config_mp_bar(self):
        """
        Inicia configuracao da barra de MP
        """
        self._log("=== CONFIGURAR BARRA MP ===")
        self._log("1. Posicione o mouse no INICIO da barra MP")
        self._log("2. Pressione ENTER")
        
        self.config_mp_btn.configure(text="Esperando...", bg=self.colors['yellow'])
        self.root.bind('<Return>', self._capture_mp_start)
    
    def _capture_mp_start(self, event):
        """
        Captura posicao inicial da barra MP
        """
        pos = self.screen.get_mouse_position()
        self._mp_start_pos = pos
        self._log(f"Inicio MP: {pos}")
        self._log("Agora posicione no FIM da barra MP")
        self._log("Pressione ENTER novamente")
        
        self.root.unbind('<Return>')
        self.root.bind('<Return>', self._capture_mp_end)
    
    def _capture_mp_end(self, event):
        """
        Captura posicao final da barra MP
        """
        pos = self.screen.get_mouse_position()
        self._mp_end_pos = (pos[0], self._mp_start_pos[1])  # Usa mesmo Y
        
        self.screen.set_mp_bar(self._mp_start_pos, self._mp_end_pos)
        
        self._log(f"Fim MP: {self._mp_end_pos}")
        self._log("Barra MP configurada!")
        
        self.config_mp_btn.configure(text="OK!", bg=self.colors['green'])
        self.root.unbind('<Return>')
        
        # Reseta apos 2 segundos
        self.root.after(2000, lambda: self.config_mp_btn.configure(
            text="Configurar", bg=self.colors['accent']))
    
    def _log(self, message):
        """
        Adiciona mensagem ao log
        """
        self.log_text.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def _update_ui(self):
        """
        Atualiza a interface com dados do jogo
        """
        while self.running:
            try:
                # Verifica se screen reader esta conectado
                if self.screen and self.screen.tibia_hwnd:
                    # Usa screen reader (leitura de pixels)
                    hp_percent = self.screen.get_hp_percent()
                    mp_percent = self.screen.get_mp_percent()
                    
                    self.hp_label.configure(text=f"HP: {hp_percent}%")
                    self.hp_bar['value'] = hp_percent
                    
                    self.mp_label.configure(text=f"MP: {mp_percent}%")
                    self.mp_bar['value'] = mp_percent
                    
                    # Executa modulos se bot ligado
                    if self.bot_enabled:
                        self.healing.execute()
                
                elif self.memory.is_connected():
                    # Fallback para memory reader
                    hp = self.memory.get_player_hp()
                    hp_max = self.memory.get_player_hp_max()
                    hp_percent = self.memory.get_player_hp_percent()
                    
                    self.hp_label.configure(text=f"{hp} / {hp_max} ({hp_percent}%)")
                    self.hp_bar['value'] = hp_percent
                    
                    mp = self.memory.get_player_mp()
                    mp_max = self.memory.get_player_mp_max()
                    mp_percent = self.memory.get_player_mp_percent()
                    
                    self.mp_label.configure(text=f"{mp} / {mp_max} ({mp_percent}%)")
                    self.mp_bar['value'] = mp_percent
                    
                    if self.bot_enabled:
                        self.healing.execute()
                
            except Exception as e:
                pass
            
            time.sleep(0.1)  # 100ms
    
    def _start_update_thread(self):
        """
        Inicia thread de atualizacao
        """
        self.bot_thread = threading.Thread(target=self._update_ui, daemon=True)
        self.bot_thread.start()
    
    def _on_close(self):
        """
        Evento de fechar janela
        """
        self.running = False
        self.memory.disconnect()
        self.root.destroy()
    
    def run(self):
        """
        Inicia o loop principal da interface
        """
        self.root.mainloop()
