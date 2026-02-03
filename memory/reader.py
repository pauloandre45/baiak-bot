# -*- coding: utf-8 -*-
"""
Leitor de memoria do cliente Tibia 15.11
"""

import ctypes
from ctypes import wintypes
import time

try:
    import pymem
    import pymem.process
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False
    print("[AVISO] pymem nao instalado. Execute: pip install pymem")

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("[AVISO] pywin32 nao instalado. Execute: pip install pywin32")

from config import TIBIA_PROCESS_NAME, TIBIA_WINDOW_TITLE, OFFSETS


class TibiaMemoryReader:
    """
    Classe para ler memoria do cliente Tibia 15.11
    """
    
    def __init__(self):
        self.pm = None
        self.process_handle = None
        self.process_id = None
        self.base_address = None
        self.connected = False
        
        # Cache de valores
        self._cache = {
            "hp": 0,
            "hp_max": 100,
            "mp": 0,
            "mp_max": 100,
            "name": "",
            "level": 1,
            "last_update": 0
        }
        
    def find_tibia_window(self):
        """
        Encontra a janela do Tibia
        Retorna: (hwnd, titulo) ou (None, None)
        """
        if not WIN32_AVAILABLE:
            return None, None
            
        result = [None, None]
        
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if TIBIA_WINDOW_TITLE.lower() in title.lower():
                    result[0] = hwnd
                    result[1] = title
                    return False  # Para a enumeracao
            return True
            
        try:
            win32gui.EnumWindows(enum_callback, None)
        except:
            pass
            
        return result[0], result[1]
    
    def connect(self):
        """
        Conecta ao processo do Tibia
        Retorna: True se conectou, False caso contrario
        """
        if not PYMEM_AVAILABLE:
            print("[ERRO] pymem nao disponivel")
            return False
            
        try:
            # Primeiro tenta encontrar pela janela
            hwnd, title = self.find_tibia_window()
            
            if hwnd:
                print(f"[INFO] Janela encontrada: {title}")
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                self.process_id = pid
            
            # Conecta ao processo
            self.pm = pymem.Pymem(TIBIA_PROCESS_NAME)
            self.process_handle = self.pm.process_handle
            self.base_address = self.pm.base_address
            
            if not self.process_id:
                self.process_id = self.pm.process_id
            
            self.connected = True
            print(f"[OK] Conectado ao Tibia!")
            print(f"     PID: {self.process_id}")
            print(f"     Base Address: {hex(self.base_address)}")
            
            return True
            
        except pymem.exception.ProcessNotFound:
            print(f"[ERRO] Processo '{TIBIA_PROCESS_NAME}' nao encontrado")
            print("       Certifique-se que o Tibia esta aberto")
            self.connected = False
            return False
            
        except Exception as e:
            print(f"[ERRO] Falha ao conectar: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """
        Desconecta do processo
        """
        if self.pm:
            try:
                self.pm.close_process()
            except:
                pass
        self.pm = None
        self.connected = False
        print("[INFO] Desconectado do Tibia")
    
    def is_connected(self):
        """
        Verifica se ainda esta conectado ao processo
        """
        if not self.connected or not self.pm:
            return False
            
        try:
            # Tenta ler um byte para verificar se processo ainda existe
            self.pm.read_bytes(self.base_address, 1)
            return True
        except:
            self.connected = False
            return False
    
    def read_int(self, address):
        """
        Le um inteiro (4 bytes) do endereco
        """
        if not self.connected:
            return 0
        try:
            return self.pm.read_int(address)
        except:
            return 0
    
    def read_uint(self, address):
        """
        Le um inteiro sem sinal (4 bytes) do endereco
        """
        if not self.connected:
            return 0
        try:
            return self.pm.read_uint(address)
        except:
            return 0
    
    def read_string(self, address, length=32):
        """
        Le uma string do endereco
        """
        if not self.connected:
            return ""
        try:
            data = self.pm.read_bytes(address, length)
            # Encontra o terminador null
            null_pos = data.find(b'\x00')
            if null_pos != -1:
                data = data[:null_pos]
            return data.decode('utf-8', errors='ignore')
        except:
            return ""
    
    def read_pointer(self, base, offsets):
        """
        Le um valor seguindo uma cadeia de ponteiros
        base: endereco base
        offsets: lista de offsets para seguir
        """
        if not self.connected:
            return 0
            
        try:
            addr = self.pm.read_uint(base)
            for offset in offsets[:-1]:
                addr = self.pm.read_uint(addr + offset)
            return addr + offsets[-1]
        except:
            return 0
    
    # ============================================
    # FUNCOES DE LEITURA DO PLAYER
    # ============================================
    
    def get_player_hp(self):
        """
        Retorna HP atual do player
        """
        # TODO: Implementar quando tivermos os offsets corretos
        # Por enquanto retorna valor do cache ou simulado
        return self._cache.get("hp", 100)
    
    def get_player_hp_max(self):
        """
        Retorna HP maximo do player
        """
        return self._cache.get("hp_max", 100)
    
    def get_player_hp_percent(self):
        """
        Retorna HP em porcentagem (0-100)
        """
        hp = self.get_player_hp()
        hp_max = self.get_player_hp_max()
        if hp_max <= 0:
            return 100
        return int((hp / hp_max) * 100)
    
    def get_player_mp(self):
        """
        Retorna MP atual do player
        """
        return self._cache.get("mp", 100)
    
    def get_player_mp_max(self):
        """
        Retorna MP maximo do player
        """
        return self._cache.get("mp_max", 100)
    
    def get_player_mp_percent(self):
        """
        Retorna MP em porcentagem (0-100)
        """
        mp = self.get_player_mp()
        mp_max = self.get_player_mp_max()
        if mp_max <= 0:
            return 100
        return int((mp / mp_max) * 100)
    
    def get_player_name(self):
        """
        Retorna nome do player
        """
        return self._cache.get("name", "Unknown")
    
    def get_player_level(self):
        """
        Retorna level do player
        """
        return self._cache.get("level", 1)
    
    def update_cache(self):
        """
        Atualiza o cache com valores da memoria
        TODO: Implementar leitura real quando tivermos offsets
        """
        now = time.time()
        
        # Por enquanto, apenas simula valores para teste da interface
        # Quando tivermos os offsets, aqui leremos da memoria real
        
        self._cache["last_update"] = now
    
    # ============================================
    # FUNCOES PARA DEBUG/DESENVOLVIMENTO
    # ============================================
    
    def set_debug_values(self, hp=None, hp_max=None, mp=None, mp_max=None):
        """
        Define valores de debug para testar a interface
        """
        if hp is not None:
            self._cache["hp"] = hp
        if hp_max is not None:
            self._cache["hp_max"] = hp_max
        if mp is not None:
            self._cache["mp"] = mp
        if mp_max is not None:
            self._cache["mp_max"] = mp_max
