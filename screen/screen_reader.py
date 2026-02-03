# -*- coding: utf-8 -*-
"""
Leitor de tela - Le HP/MP das barras do Tibia por cor de pixel
"""

import time

try:
    import win32gui
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("[AVISO] pywin32 nao instalado")


class ScreenReader:
    """
    Le HP e MP do Tibia atraves das barras na tela
    """
    
    def __init__(self):
        self.tibia_hwnd = None
        self.window_rect = None
        
        # Posicao das barras (absoluta na tela, definida pelo usuario)
        self.hp_bar_start = None  # (x, y) do inicio da barra HP
        self.hp_bar_end = None    # (x, y) do fim da barra HP
        self.mp_bar_start = None  # (x, y) do inicio da barra MP
        self.mp_bar_end = None    # (x, y) do fim da barra MP
        
        # Cache
        self._hp_percent = 100
        self._mp_percent = 100
        self._last_update = 0
        self._update_interval = 0.03  # 30ms - mais rapido
        
        # Modo de configuracao
        self.config_mode = None  # 'hp_start', 'hp_end', 'mp_start', 'mp_end'
    
    def find_tibia_window(self):
        """
        Encontra a janela do Tibia
        """
        if not WIN32_AVAILABLE:
            return False
            
        def enum_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Tibia" in title and "Baiak Bot" not in title:
                    results.append((hwnd, title))
            return True
        
        results = []
        try:
            win32gui.EnumWindows(enum_callback, results)
        except:
            pass
        
        if results:
            self.tibia_hwnd = results[0][0]
            print(f"[SCREEN] Janela encontrada: {results[0][1]}")
            self.get_window_rect()
            return True
        
        return False
    
    def get_window_rect(self):
        """
        Obtem retangulo da janela do Tibia
        """
        if not self.tibia_hwnd:
            return None
            
        try:
            rect = win32gui.GetWindowRect(self.tibia_hwnd)
            self.window_rect = rect
            return rect
        except:
            return None
    
    def get_pixel_color(self, x, y):
        """
        Obtem cor de um pixel na tela
        """
        if not WIN32_AVAILABLE:
            return (0, 0, 0)
            
        try:
            hdc = win32gui.GetDC(0)
            color = win32gui.GetPixel(hdc, x, y)
            win32gui.ReleaseDC(0, hdc)
            
            r = color & 0xFF
            g = (color >> 8) & 0xFF
            b = (color >> 16) & 0xFF
            
            return (r, g, b)
        except:
            return (0, 0, 0)
    
    def get_mouse_position(self):
        """
        Retorna posicao atual do mouse
        """
        try:
            return win32api.GetCursorPos()
        except:
            return (0, 0)
    
    def is_hp_color(self, color):
        """
        Verifica se a cor e de barra de HP
        HP: vermelho, laranja, amarelo, verde
        """
        r, g, b = color
        
        # Ignora preto/cinza escuro (fundo vazio da barra)
        if r < 50 and g < 50 and b < 50:
            return False
        
        # Vermelho (HP baixo): R alto, G e B baixos
        if r > 100 and g < 100 and b < 100:
            return True
        
        # Laranja: R alto, G medio
        if r > 150 and g > 50 and g < 150 and b < 100:
            return True
        
        # Amarelo: R e G altos
        if r > 150 and g > 150 and b < 100:
            return True
        
        # Verde (HP cheio): G alto
        if g > 100 and r < 150 and b < 100:
            return True
        
        return False
    
    def is_mp_color(self, color):
        """
        Verifica se a cor e de barra de MP
        MP: azul/roxo
        """
        r, g, b = color
        
        # Ignora preto/cinza escuro
        if r < 50 and g < 50 and b < 50:
            return False
        
        # Azul: B alto
        if b > 100:
            return True
        
        # Roxo: R e B altos
        if r > 80 and b > 80 and g < 100:
            return True
        
        return False
    
    def calculate_bar_percent(self, start_pos, end_pos, bar_type='hp'):
        """
        Calcula porcentagem da barra
        """
        if not start_pos or not end_pos:
            return 100
        
        x1, y = start_pos
        x2, _ = end_pos
        
        bar_width = x2 - x1
        if bar_width <= 0:
            return 100
        
        # Amostra mais pontos para precisao
        samples = 30
        step = bar_width / samples
        last_filled = 0
        
        # Debug - mostra primeira e ultima cor
        first_color = self.get_pixel_color(x1, y)
        last_color = self.get_pixel_color(x2, y)
        
        for i in range(samples):
            x = int(x1 + (i * step))
            color = self.get_pixel_color(x, y)
            
            # Usa detector especifico para cada tipo de barra
            if bar_type == 'hp':
                is_filled = self.is_hp_color(color)
            else:
                is_filled = self.is_mp_color(color)
            
            if is_filled:
                last_filled = i + 1
        
        percent = int((last_filled / samples) * 100)
        return max(0, min(100, percent))
    
    def update(self):
        """
        Atualiza leitura de HP e MP
        """
        now = time.time()
        if now - self._last_update < self._update_interval:
            return
            
        self._last_update = now
        
        # Le HP se configurado
        if self.hp_bar_start and self.hp_bar_end:
            self._hp_percent = self.calculate_bar_percent(
                self.hp_bar_start, self.hp_bar_end, 'hp'
            )
        
        # Le MP se configurado
        if self.mp_bar_start and self.mp_bar_end:
            self._mp_percent = self.calculate_bar_percent(
                self.mp_bar_start, self.mp_bar_end, 'mp'
            )
    
    def get_hp_percent(self):
        """
        Retorna HP em porcentagem
        """
        self.update()
        return self._hp_percent
    
    def get_mp_percent(self):
        """
        Retorna MP em porcentagem
        """
        self.update()
        return self._mp_percent
    
    def is_configured(self):
        """
        Verifica se as barras estao configuradas
        """
        return (self.hp_bar_start is not None and 
                self.hp_bar_end is not None)
    
    def set_hp_bar(self, start_pos, end_pos):
        """
        Define posicao da barra de HP
        """
        self.hp_bar_start = start_pos
        self.hp_bar_end = end_pos
        print(f"[SCREEN] HP Bar: {start_pos} -> {end_pos}")
    
    def set_mp_bar(self, start_pos, end_pos):
        """
        Define posicao da barra de MP
        """
        self.mp_bar_start = start_pos
        self.mp_bar_end = end_pos
        print(f"[SCREEN] MP Bar: {start_pos} -> {end_pos}")
