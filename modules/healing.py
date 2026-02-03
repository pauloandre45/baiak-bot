# -*- coding: utf-8 -*-
"""
Modulo de Healing - Auto cura baseado em HP%
"""

import time
import ctypes
from ctypes import wintypes

try:
    import win32gui
    import win32api
    import win32con
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from config import HEALING_CONFIG, TIMERS


# Estruturas para SendInput
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

# Mapeamento de teclas para virtual key codes e scan codes
VK_CODES = {
    'F1': (0x70, 0x3B), 'F2': (0x71, 0x3C), 'F3': (0x72, 0x3D), 'F4': (0x73, 0x3E),
    'F5': (0x74, 0x3F), 'F6': (0x75, 0x40), 'F7': (0x76, 0x41), 'F8': (0x77, 0x42),
    'F9': (0x78, 0x43), 'F10': (0x79, 0x44), 'F11': (0x7A, 0x57), 'F12': (0x7B, 0x58),
    '1': (0x31, 0x02), '2': (0x32, 0x03), '3': (0x33, 0x04), '4': (0x34, 0x05),
    '5': (0x35, 0x06), '6': (0x36, 0x07), '7': (0x37, 0x08), '8': (0x38, 0x09),
    '9': (0x39, 0x0A), '0': (0x30, 0x0B),
}


class HealingModule:
    """
    Modulo de cura automatica
    - 3 slots configuraveis
    - Suporta potions (via hotkey) ou spells (via hotkey)
    - Ativa quando HP% <= threshold configurado
    """
    
    def __init__(self, memory_reader, screen_reader=None):
        """
        memory_reader: instancia de TibiaMemoryReader
        screen_reader: instancia de ScreenReader (opcional, mas recomendado)
        """
        self.memory = memory_reader
        self.screen = screen_reader
        self.enabled = False
        self.last_heal_time = 0
        self.cooldown = TIMERS["healing_cooldown"] / 1000.0  # Converte para segundos
        
        # Handle da janela do Tibia
        self.tibia_hwnd = None
        
        # Configuracao dos slots
        self.slots = []
        self._load_config()
    
    def _load_config(self):
        """
        Carrega configuracao dos slots
        """
        self.enabled = HEALING_CONFIG.get("enabled", False)
        
        self.slots = []
        for slot_cfg in HEALING_CONFIG.get("slots", []):
            slot = HealingSlot(
                enabled=slot_cfg.get("enabled", False),
                slot_type=slot_cfg.get("type", "potion"),
                item_name=slot_cfg.get("item_name", ""),
                spell_words=slot_cfg.get("spell_words", ""),
                hp_percent=slot_cfg.get("hp_percent", 80),
                hotkey=slot_cfg.get("hotkey", "F1")
            )
            self.slots.append(slot)
    
    def set_enabled(self, enabled):
        """
        Liga/desliga o modulo
        """
        self.enabled = enabled
        status = "LIGADO" if enabled else "DESLIGADO"
        print(f"[HEALING] {status}")
    
    def toggle(self):
        """
        Alterna estado do modulo
        """
        self.set_enabled(not self.enabled)
    
    def configure_slot(self, index, enabled=None, slot_type=None, 
                       item_name=None, spell_words=None, hp_percent=None, hotkey=None):
        """
        Configura um slot especifico
        
        index: 0, 1 ou 2
        """
        if index < 0 or index >= len(self.slots):
            return False
            
        slot = self.slots[index]
        
        if enabled is not None:
            slot.enabled = enabled
        if slot_type is not None:
            slot.slot_type = slot_type
        if item_name is not None:
            slot.item_name = item_name
        if spell_words is not None:
            slot.spell_words = spell_words
        if hp_percent is not None:
            slot.hp_percent = max(1, min(100, hp_percent))
        if hotkey is not None:
            slot.hotkey = hotkey
            
        return True
    
    def get_slot_config(self, index):
        """
        Retorna configuracao de um slot
        """
        if index < 0 or index >= len(self.slots):
            return None
        return self.slots[index]
    
    def execute(self):
        """
        Executa a logica de healing
        Deve ser chamado no loop principal
        
        Retorna: True se executou uma cura, False caso contrario
        """
        if not self.enabled:
            return False
        
        # Verifica cooldown
        now = time.time()
        if now - self.last_heal_time < self.cooldown:
            return False
        
        # Obtem HP atual - prefere screen reader se disponivel
        if self.screen:
            hp_percent = self.screen.get_hp_percent()
        else:
            hp_percent = self.memory.get_player_hp_percent()
        
        # Protecao: se HP = 0%, provavelmente a leitura falhou
        # Nao cura para evitar spam
        if hp_percent <= 0:
            return False
        
        # Verifica cada slot (em ordem de prioridade)
        for i, slot in enumerate(self.slots):
            if not slot.enabled:
                continue
            
            # Verifica se HP esta abaixo do threshold
            if hp_percent <= slot.hp_percent:
                # Executa a cura (pressiona hotkey)
                success = self._execute_heal(slot)
                
                if success:
                    self.last_heal_time = now
                    print(f"[HEALING] Slot {i+1} ativado! HP: {hp_percent}% (threshold: {slot.hp_percent}%)")
                    return True
        
        return False
    
    def _execute_heal(self, slot):
        """
        Executa a acao de cura (pressiona a hotkey)
        Funciona mesmo com Tibia em background
        """
        try:
            key = slot.hotkey.upper()
            key_info = VK_CODES.get(key)
            
            if not key_info:
                print(f"[HEALING] Tecla nao suportada: {key}")
                return False
            
            vk_code, scan_code = key_info
            
            # Metodo 1: Traz janela do Tibia para frente e envia tecla
            if WIN32_AVAILABLE and self.screen and self.screen.tibia_hwnd:
                hwnd = self.screen.tibia_hwnd
                
                # Salva janela atual em foco
                current_hwnd = win32gui.GetForegroundWindow()
                
                # Ativa janela do Tibia brevemente
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.01)
                except:
                    pass
                
                # Envia tecla usando SendInput (funciona melhor com jogos)
                self._send_key(vk_code, scan_code)
                
                # Restaura janela anterior (opcional - comente se preferir ficar no Tibia)
                # time.sleep(0.05)
                # try:
                #     win32gui.SetForegroundWindow(current_hwnd)
                # except:
                #     pass
                
                return True
            
            # Fallback: SendInput sem mudar foco
            self._send_key(vk_code, scan_code)
            return True
            
        except Exception as e:
            print(f"[HEALING] Erro ao pressionar hotkey: {e}")
            return False
    
    def _send_key(self, vk_code, scan_code):
        """
        Envia tecla usando SendInput (simula hardware)
        """
        # Key down
        inputs = INPUT()
        inputs.type = INPUT_KEYBOARD
        inputs.ki.wVk = vk_code
        inputs.ki.wScan = scan_code
        inputs.ki.dwFlags = 0
        inputs.ki.time = 0
        inputs.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
        
        ctypes.windll.user32.SendInput(1, ctypes.byref(inputs), ctypes.sizeof(inputs))
        
        time.sleep(0.02)
        
        # Key up
        inputs.ki.dwFlags = KEYEVENTF_KEYUP
        ctypes.windll.user32.SendInput(1, ctypes.byref(inputs), ctypes.sizeof(inputs))
    
    def get_status(self):
        """
        Retorna status formatado do modulo
        """
        status = "ON" if self.enabled else "OFF"
        hp_percent = self.memory.get_player_hp_percent()
        
        lines = [
            f"Healing: {status}",
            f"HP: {hp_percent}%",
            ""
        ]
        
        for i, slot in enumerate(self.slots):
            slot_status = "ON" if slot.enabled else "OFF"
            
            if slot.slot_type == "potion":
                desc = slot.item_name or "Nenhuma"
            else:
                desc = slot.spell_words or "Nenhuma"
            
            lines.append(f"Slot {i+1}: [{slot_status}] {desc} @ {slot.hp_percent}% ({slot.hotkey})")
        
        return "\n".join(lines)


class HealingSlot:
    """
    Representa um slot de healing
    """
    
    def __init__(self, enabled=False, slot_type="potion", item_name="", 
                 spell_words="", hp_percent=80, hotkey="F1"):
        self.enabled = enabled
        self.slot_type = slot_type      # "potion" ou "spell"
        self.item_name = item_name      # Nome da potion
        self.spell_words = spell_words  # Palavras da spell
        self.hp_percent = hp_percent    # Threshold de HP%
        self.hotkey = hotkey            # Hotkey a pressionar
    
    def to_dict(self):
        """
        Converte para dicionario (para salvar config)
        """
        return {
            "enabled": self.enabled,
            "type": self.slot_type,
            "item_name": self.item_name,
            "spell_words": self.spell_words,
            "hp_percent": self.hp_percent,
            "hotkey": self.hotkey
        }
