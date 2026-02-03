# -*- coding: utf-8 -*-
"""
Modulo de Healing v2 - Usa leitura de memoria direta
Funciona mesmo com Tibia minimizado!
"""

import time
import ctypes
from ctypes import wintypes
import threading

try:
    import win32gui
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


# Estruturas para SendInput (envio de teclas)
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("ki", KEYBDINPUT),
        ("padding", ctypes.c_ubyte * 8)
    ]


# Constantes
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Virtual Key Codes e Scan Codes
VK_CODES = {
    'F1': (0x70, 0x3B), 'F2': (0x71, 0x3C), 'F3': (0x72, 0x3D), 'F4': (0x73, 0x3E),
    'F5': (0x74, 0x3F), 'F6': (0x75, 0x40), 'F7': (0x76, 0x41), 'F8': (0x77, 0x42),
    'F9': (0x78, 0x43), 'F10': (0x79, 0x44), 'F11': (0x7A, 0x57), 'F12': (0x7B, 0x58),
    '1': (0x31, 0x02), '2': (0x32, 0x03), '3': (0x33, 0x04), '4': (0x34, 0x05),
    '5': (0x35, 0x06), '6': (0x36, 0x07), '7': (0x37, 0x08), '8': (0x38, 0x09),
    '9': (0x39, 0x0A), '0': (0x30, 0x0B),
    'A': (0x41, 0x1E), 'B': (0x42, 0x30), 'C': (0x43, 0x2E), 'D': (0x44, 0x20),
    'E': (0x45, 0x12), 'F': (0x46, 0x21), 'G': (0x47, 0x22), 'H': (0x48, 0x23),
    'I': (0x49, 0x17), 'J': (0x4A, 0x24), 'K': (0x4B, 0x25), 'L': (0x4C, 0x26),
    'Q': (0x51, 0x10), 'R': (0x52, 0x13), 'T': (0x54, 0x14), 'Z': (0x5A, 0x2C),
}


class HealingSlot:
    """
    Representa um slot de cura configuravel
    """
    
    def __init__(self, enabled=False, hotkey="F1", hp_threshold=80):
        self.enabled = enabled
        self.hotkey = hotkey.upper()
        self.hp_threshold = hp_threshold  # Cura quando HP% <= threshold
    
    def to_dict(self):
        return {
            "enabled": self.enabled,
            "hotkey": self.hotkey,
            "hp_threshold": self.hp_threshold
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            enabled=data.get("enabled", False),
            hotkey=data.get("hotkey", "F1"),
            hp_threshold=data.get("hp_threshold", 80)
        )


class HealingModuleV2:
    """
    Modulo de cura automatica usando leitura de memoria
    
    Funciona assim:
    1. Le HP% da memoria do Tibia (instantaneo!)
    2. Se HP% <= threshold, pressiona a hotkey
    3. Repete a cada ~50ms
    
    Vantagens:
    - Instantaneo (sem delay de pixels)
    - Funciona com Tibia minimizado
    - Preciso (valores exatos)
    """
    
    def __init__(self, memory_reader):
        """
        memory_reader: instancia de TibiaMemoryReader conectada
        """
        self.memory = memory_reader
        self.enabled = False
        self.running = False
        
        # Cooldown entre acoes (evita spam)
        self.cooldown = 0.15  # 150ms
        self.last_action_time = 0
        
        # Slots de cura (3 slots)
        self.slots = [
            HealingSlot(enabled=False, hotkey="F1", hp_threshold=80),
            HealingSlot(enabled=False, hotkey="F2", hp_threshold=60),
            HealingSlot(enabled=False, hotkey="F3", hp_threshold=40),
        ]
        
        # Handle da janela Tibia (para enviar teclas)
        self.tibia_hwnd = None
        
        # Thread de execucao
        self._thread = None
        
        # Callbacks
        self._on_heal_callback = None
    
    def set_enabled(self, enabled):
        """
        Liga/desliga o modulo
        """
        self.enabled = enabled
        print(f"[HEALING] {'LIGADO' if enabled else 'DESLIGADO'}")
    
    def toggle(self):
        """
        Alterna estado
        """
        self.set_enabled(not self.enabled)
        return self.enabled
    
    def configure_slot(self, index, enabled=None, hotkey=None, hp_threshold=None):
        """
        Configura um slot de cura
        
        index: 0, 1 ou 2
        """
        if index < 0 or index >= len(self.slots):
            return False
        
        slot = self.slots[index]
        
        if enabled is not None:
            slot.enabled = enabled
        if hotkey is not None:
            slot.hotkey = hotkey.upper()
        if hp_threshold is not None:
            slot.hp_threshold = max(1, min(100, hp_threshold))
        
        return True
    
    def get_slot(self, index):
        """
        Retorna um slot
        """
        if 0 <= index < len(self.slots):
            return self.slots[index]
        return None
    
    def find_tibia_window(self):
        """
        Encontra a janela do Tibia
        """
        if not WIN32_AVAILABLE:
            return False
        
        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Tibia" in title and "Bot" not in title:
                    results.append(hwnd)
                    return False
            return True
        
        results = []
        try:
            win32gui.EnumWindows(callback, results)
        except:
            pass
        
        if results:
            self.tibia_hwnd = results[0]
            return True
        
        return False
    
    def execute_once(self):
        """
        Executa uma verificacao/cura
        Chamado pelo loop principal
        
        Retorna: True se curou, False se nao
        """
        if not self.enabled:
            return False
        
        # Verifica cooldown
        now = time.time()
        if now - self.last_action_time < self.cooldown:
            return False
        
        # Verifica se memoria esta funcionando
        if not self.memory or not self.memory.is_connected():
            return False
        
        if not self.memory.has_offsets():
            return False
        
        # Le HP%
        hp_percent = self.memory.get_player_hp_percent()
        
        # Protecao: HP 0 ou 100 pode ser erro de leitura
        if hp_percent <= 0:
            return False
        
        # Verifica slots (em ordem de prioridade - menor HP% primeiro)
        # Ordena por threshold decrescente (cura mais urgente primeiro)
        sorted_slots = sorted(
            [(i, s) for i, s in enumerate(self.slots) if s.enabled],
            key=lambda x: x[1].hp_threshold,
            reverse=True
        )
        
        for index, slot in sorted_slots:
            if hp_percent <= slot.hp_threshold:
                # Executa cura
                success = self._press_hotkey(slot.hotkey)
                
                if success:
                    self.last_action_time = now
                    
                    # Callback
                    if self._on_heal_callback:
                        self._on_heal_callback(index, hp_percent, slot.hp_threshold)
                    
                    return True
        
        return False
    
    def _press_hotkey(self, hotkey):
        """
        Pressiona uma hotkey no Tibia SEM tirar o foco da janela atual
        Usa PostMessage para enviar diretamente para a janela do Tibia
        """
        key = hotkey.upper()
        
        if key not in VK_CODES:
            print(f"[HEALING] Hotkey invalida: {key}")
            return False
        
        vk_code, scan_code = VK_CODES[key]
        
        try:
            # Metodo 1: PostMessage - envia tecla sem mudar foco (PREFERIDO)
            if self.tibia_hwnd and WIN32_AVAILABLE:
                return self._send_key_background(vk_code, scan_code)
            
            # Fallback: SendInput (precisa de foco)
            self._send_key_foreground(vk_code, scan_code)
            return True
            
        except Exception as e:
            print(f"[HEALING] Erro ao pressionar {key}: {e}")
            return False
    
    def _send_key_background(self, vk_code, scan_code):
        """
        Envia tecla para o Tibia em BACKGROUND usando PostMessage
        NAO muda o foco - voce pode usar outros programas!
        """
        # Constantes do Windows
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101
        
        # lParam contém scan code e flags
        # Bits 16-23: scan code
        # Bit 30: previous key state (0 for keydown)
        # Bit 31: transition state (0 for keydown, 1 for keyup)
        
        lparam_down = (scan_code << 16) | 1
        lparam_up = (scan_code << 16) | 1 | (1 << 30) | (1 << 31)
        
        try:
            # Key down
            win32api.PostMessage(self.tibia_hwnd, WM_KEYDOWN, vk_code, lparam_down)
            time.sleep(0.015)
            
            # Key up
            win32api.PostMessage(self.tibia_hwnd, WM_KEYUP, vk_code, lparam_up)
            
            return True
        except Exception as e:
            print(f"[HEALING] PostMessage falhou: {e}")
            # Fallback para SendInput
            return self._send_key_foreground(vk_code, scan_code)
    
    def _send_key_foreground(self, vk_code, scan_code):
        """
        Envia tecla usando SendInput (precisa de foco)
        Usado como fallback se PostMessage falhar
        """
        # Key down
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.ki.wVk = vk_code
        inp.ki.wScan = scan_code
        inp.ki.dwFlags = 0
        inp.ki.time = 0
        inp.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
        
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
        
        time.sleep(0.015)
        
        # Key up
        inp.ki.dwFlags = KEYEVENTF_KEYUP
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    
    def start_loop(self, interval=0.050):
        """
        Inicia loop de execucao em thread separada
        
        interval: tempo entre verificacoes em segundos (50ms padrao)
        """
        if self._thread and self._thread.is_alive():
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._loop, args=(interval,), daemon=True)
        self._thread.start()
        print(f"[HEALING] Loop iniciado (intervalo: {interval*1000:.0f}ms)")
    
    def stop_loop(self):
        """
        Para o loop de execucao
        """
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        print("[HEALING] Loop parado")
    
    def _loop(self, interval):
        """
        Loop interno de execucao
        """
        while self.running:
            try:
                self.execute_once()
            except Exception as e:
                print(f"[HEALING] Erro no loop: {e}")
            
            time.sleep(interval)
    
    def on_heal(self, callback):
        """
        Define callback chamado quando cura
        callback(slot_index, hp_percent, threshold)
        """
        self._on_heal_callback = callback
    
    def get_status(self):
        """
        Retorna status formatado
        """
        lines = [
            f"Healing: {'ON' if self.enabled else 'OFF'}",
            ""
        ]
        
        for i, slot in enumerate(self.slots):
            status = "ON" if slot.enabled else "OFF"
            lines.append(f"  Slot {i+1}: [{status}] {slot.hotkey} @ HP <= {slot.hp_threshold}%")
        
        return "\n".join(lines)
