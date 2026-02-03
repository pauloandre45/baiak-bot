# -*- coding: utf-8 -*-
"""
Bot Bridge - Injeta DLL no client.exe e le dados via shared memory/arquivo
Solucao automatica que nao requer scan manual
"""

import os
import sys
import time
import json
import ctypes
import struct
import mmap
from pathlib import Path

# Constantes Windows
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_READWRITE = 0x04
PAGE_EXECUTE_READWRITE = 0x40


class BotBridge:
    """
    Bridge entre o bot Python e o client.exe via DLL injetada
    """
    
    # Nome do arquivo de dados compartilhados
    SHARED_FILE = "baiak_bot_data.bin"
    SHARED_MEMORY_NAME = "BaiakBotSharedMemory"
    
    def __init__(self):
        self.data_path = Path(os.environ.get('TEMP', '.')) / self.SHARED_FILE
        self.shared_mem = None
        self._hp = 0
        self._hp_max = 0
        self._mp = 0
        self._mp_max = 0
        self._last_update = 0
        self._connected = False
        
    def connect(self):
        """
        Conecta ao shared memory ou arquivo de dados
        """
        # Tenta shared memory primeiro
        try:
            self.shared_mem = mmap.mmap(-1, 64, self.SHARED_MEMORY_NAME, access=mmap.ACCESS_READ)
            self._connected = True
            print(f"[BRIDGE] Conectado via Shared Memory")
            return True
        except:
            pass
        
        # Tenta arquivo
        if self.data_path.exists():
            self._connected = True
            print(f"[BRIDGE] Conectado via arquivo: {self.data_path}")
            return True
            
        print(f"[BRIDGE] Aguardando dados do cliente...")
        return False
    
    def update(self):
        """
        Atualiza dados do player
        """
        now = time.time()
        if now - self._last_update < 0.05:  # 50ms
            return
        self._last_update = now
        
        data = None
        
        # Le de shared memory
        if self.shared_mem:
            try:
                self.shared_mem.seek(0)
                data = self.shared_mem.read(32)
            except:
                self.shared_mem = None
        
        # Le de arquivo
        if not data and self.data_path.exists():
            try:
                with open(self.data_path, 'rb') as f:
                    data = f.read(32)
            except:
                pass
        
        # Parse dos dados: HP(4) + HP_MAX(4) + MP(4) + MP_MAX(4) + TIMESTAMP(8)
        if data and len(data) >= 24:
            try:
                self._hp, self._hp_max, self._mp, self._mp_max = struct.unpack('<IIII', data[:16])
                self._connected = True
            except:
                pass
    
    @property
    def hp(self):
        self.update()
        return self._hp
    
    @property
    def hp_max(self):
        self.update()
        return self._hp_max
    
    @property
    def mp(self):
        self.update()
        return self._mp
    
    @property
    def mp_max(self):
        self.update()
        return self._mp_max
    
    @property
    def hp_percent(self):
        self.update()
        if self._hp_max <= 0:
            return 100
        return int((self._hp / self._hp_max) * 100)
    
    @property
    def mp_percent(self):
        self.update()
        if self._mp_max <= 0:
            return 100
        return int((self._mp / self._mp_max) * 100)
    
    def is_connected(self):
        return self._connected and (self._hp_max > 0 or self._mp_max > 0)


class DLLInjector:
    """
    Injeta DLL no processo do Tibia
    """
    
    def __init__(self):
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        
    def get_process_id(self, process_name):
        """
        Encontra PID do processo
        """
        import pymem
        try:
            pm = pymem.Pymem(process_name)
            return pm.process_id
        except:
            return None
    
    def inject_dll(self, pid, dll_path):
        """
        Injeta DLL no processo
        """
        if not os.path.exists(dll_path):
            print(f"[INJECTOR] DLL nao encontrada: {dll_path}")
            return False
        
        dll_path_bytes = dll_path.encode('utf-8') + b'\x00'
        dll_path_len = len(dll_path_bytes)
        
        # Abre processo
        h_process = self.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not h_process:
            print(f"[INJECTOR] Falha ao abrir processo: {ctypes.get_last_error()}")
            return False
        
        try:
            # Aloca memoria no processo alvo
            remote_mem = self.kernel32.VirtualAllocEx(
                h_process, None, dll_path_len, 
                MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE
            )
            if not remote_mem:
                print(f"[INJECTOR] Falha ao alocar memoria: {ctypes.get_last_error()}")
                return False
            
            # Escreve caminho da DLL
            written = ctypes.c_size_t(0)
            self.kernel32.WriteProcessMemory(
                h_process, remote_mem, dll_path_bytes, 
                dll_path_len, ctypes.byref(written)
            )
            
            # Obtem endereco de LoadLibraryA
            h_kernel32 = self.kernel32.GetModuleHandleW("kernel32.dll")
            load_library_addr = self.kernel32.GetProcAddress(h_kernel32, b"LoadLibraryA")
            
            # Cria thread remota para carregar a DLL
            thread_id = ctypes.c_ulong(0)
            h_thread = self.kernel32.CreateRemoteThread(
                h_process, None, 0, load_library_addr, 
                remote_mem, 0, ctypes.byref(thread_id)
            )
            
            if h_thread:
                self.kernel32.WaitForSingleObject(h_thread, 5000)
                self.kernel32.CloseHandle(h_thread)
                print(f"[INJECTOR] DLL injetada com sucesso!")
                return True
            else:
                print(f"[INJECTOR] Falha ao criar thread: {ctypes.get_last_error()}")
                return False
                
        finally:
            self.kernel32.CloseHandle(h_process)
        
        return False


def test_bridge():
    """
    Testa a bridge
    """
    print("=== TESTE BOT BRIDGE ===\n")
    
    bridge = BotBridge()
    
    print("Aguardando conexao com o cliente...")
    print("(A DLL precisa estar injetada no client.exe)")
    print()
    
    for i in range(100):
        if bridge.connect():
            break
        time.sleep(0.5)
    
    if not bridge.is_connected():
        print("Nao conectado. Verifique se a DLL esta injetada.")
        return
    
    print("Conectado! Lendo dados...\n")
    
    while True:
        print(f"\rHP: {bridge.hp}/{bridge.hp_max} ({bridge.hp_percent}%) | "
              f"MP: {bridge.mp}/{bridge.mp_max} ({bridge.mp_percent}%)", end='')
        time.sleep(0.1)


if __name__ == "__main__":
    test_bridge()
