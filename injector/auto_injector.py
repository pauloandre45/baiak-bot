# -*- coding: utf-8 -*-
"""
Auto Injector - Injeta DLL automaticamente no client.exe
e le HP/MP via shared memory

Este arquivo substitui o memory reader tradicional
"""

import os
import sys
import time
import struct
import ctypes
import ctypes.wintypes as wintypes
from pathlib import Path

# Constantes Windows
PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04
PAGE_EXECUTE_READWRITE = 0x40
INFINITE = 0xFFFFFFFF

# Shared memory
SHARED_MEMORY_NAME = "BaiakBotSharedMemory"
SHARED_FILE_NAME = "baiak_bot_data.bin"


class AutoInjector:
    """
    Injeta DLL no Tibia e le dados automaticamente
    """
    
    def __init__(self):
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        self.pid = None
        self.dll_path = None
        self.injected = False
        self.shared_handle = None
        self.shared_data = None
        
        # Dados do player
        self._hp = 0
        self._hp_max = 0
        self._mp = 0
        self._mp_max = 0
        self._last_read = 0
        
        # Caminho da DLL
        self.dll_path = self._find_dll()
        
    def _find_dll(self):
        """
        Encontra a DLL BaiakBot
        """
        possible_paths = [
            Path(__file__).parent / "BaiakBot.dll",
            Path(__file__).parent / "baiak_bot.dll",
            Path(__file__).parent.parent / "BaiakBot.dll",
            Path(__file__).parent.parent / "dll" / "BaiakBot.dll",
            Path.cwd() / "BaiakBot.dll",
        ]
        
        for p in possible_paths:
            if p.exists():
                return str(p.absolute())
        
        return None
    
    def find_tibia(self):
        """
        Encontra processo do Tibia
        """
        try:
            import pymem
            pm = pymem.Pymem('client.exe')
            self.pid = pm.process_id
            print(f"[INJECTOR] Tibia encontrado - PID: {self.pid}")
            return True
        except Exception as e:
            # Tenta outro metodo
            pass
        
        # Metodo alternativo usando tasklist
        import subprocess
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq client.exe', '/FO', 'CSV'], 
                                    capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].replace('"', '').split(',')
                self.pid = int(parts[1])
                print(f"[INJECTOR] Tibia encontrado - PID: {self.pid}")
                return True
        except:
            pass
        
        return False
    
    def inject_dll(self):
        """
        Injeta a DLL no processo do Tibia
        """
        if not self.dll_path:
            print("[INJECTOR] ERRO: DLL nao encontrada!")
            print("[INJECTOR] Coloque 'BaiakBot.dll' na pasta do bot")
            return False
        
        if not os.path.exists(self.dll_path):
            print(f"[INJECTOR] ERRO: DLL nao existe: {self.dll_path}")
            return False
        
        if not self.pid:
            if not self.find_tibia():
                print("[INJECTOR] ERRO: Tibia nao encontrado!")
                return False
        
        print(f"[INJECTOR] Injetando DLL: {self.dll_path}")
        
        dll_path_bytes = self.dll_path.encode('utf-8') + b'\x00'
        dll_path_len = len(dll_path_bytes)
        
        # Abre processo
        h_process = self.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, self.pid)
        if not h_process:
            error = ctypes.get_last_error()
            print(f"[INJECTOR] ERRO ao abrir processo: {error}")
            if error == 5:
                print("[INJECTOR] Execute como Administrador!")
            return False
        
        try:
            # Aloca memoria para o path da DLL
            remote_mem = self.kernel32.VirtualAllocEx(
                h_process, None, dll_path_len,
                MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE
            )
            
            if not remote_mem:
                print(f"[INJECTOR] ERRO ao alocar memoria: {ctypes.get_last_error()}")
                return False
            
            # Escreve path da DLL na memoria do processo
            written = ctypes.c_size_t(0)
            success = self.kernel32.WriteProcessMemory(
                h_process, remote_mem, dll_path_bytes,
                dll_path_len, ctypes.byref(written)
            )
            
            if not success:
                print(f"[INJECTOR] ERRO ao escrever memoria: {ctypes.get_last_error()}")
                return False
            
            # Obtem endereco de LoadLibraryA
            h_kernel32 = self.kernel32.GetModuleHandleW("kernel32.dll")
            load_library = self.kernel32.GetProcAddress(h_kernel32, b"LoadLibraryA")
            
            if not load_library:
                print("[INJECTOR] ERRO: LoadLibraryA nao encontrada")
                return False
            
            # Cria thread remota para carregar a DLL
            thread_id = ctypes.c_ulong(0)
            h_thread = self.kernel32.CreateRemoteThread(
                h_process, None, 0, load_library,
                remote_mem, 0, ctypes.byref(thread_id)
            )
            
            if not h_thread:
                print(f"[INJECTOR] ERRO ao criar thread: {ctypes.get_last_error()}")
                return False
            
            # Aguarda thread terminar
            self.kernel32.WaitForSingleObject(h_thread, 5000)
            
            # Verifica se DLL foi carregada
            exit_code = ctypes.c_ulong(0)
            self.kernel32.GetExitCodeThread(h_thread, ctypes.byref(exit_code))
            
            self.kernel32.CloseHandle(h_thread)
            
            # Libera memoria alocada
            self.kernel32.VirtualFreeEx(h_process, remote_mem, 0, MEM_RELEASE)
            
            if exit_code.value == 0:
                print("[INJECTOR] AVISO: DLL pode nao ter sido carregada")
                # Continua mesmo assim, pode funcionar
            
            self.injected = True
            print("[INJECTOR] DLL injetada com sucesso!")
            return True
            
        finally:
            self.kernel32.CloseHandle(h_process)
    
    def connect_shared_memory(self):
        """
        Conecta ao shared memory criado pela DLL
        """
        try:
            import mmap
            self.shared_data = mmap.mmap(-1, 32, SHARED_MEMORY_NAME, access=mmap.ACCESS_READ)
            print("[INJECTOR] Conectado ao shared memory")
            return True
        except Exception as e:
            # Shared memory ainda nao existe
            return False
    
    def read_from_file(self):
        """
        Le dados do arquivo (fallback)
        """
        temp_path = Path(os.environ.get('TEMP', '.')) / SHARED_FILE_NAME
        
        if not temp_path.exists():
            return False
        
        try:
            with open(temp_path, 'rb') as f:
                data = f.read(32)
            
            if len(data) >= 24:
                self._hp, self._hp_max, self._mp, self._mp_max = struct.unpack('<IIII', data[:16])
                return True
        except:
            pass
        
        return False
    
    def update(self):
        """
        Atualiza dados do player
        """
        now = time.time()
        if now - self._last_read < 0.05:  # 50ms
            return
        self._last_read = now
        
        # Tenta shared memory primeiro
        if self.shared_data:
            try:
                self.shared_data.seek(0)
                data = self.shared_data.read(32)
                if len(data) >= 16:
                    self._hp, self._hp_max, self._mp, self._mp_max = struct.unpack('<IIII', data[:16])
                    return
            except:
                self.shared_data = None
        
        # Tenta reconectar
        if not self.shared_data:
            self.connect_shared_memory()
        
        # Fallback para arquivo
        self.read_from_file()
    
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
        """
        Verifica se esta conectado e recebendo dados
        """
        self.update()
        return self._hp_max > 0 or self._mp_max > 0
    
    def auto_connect(self):
        """
        Conecta automaticamente - encontra Tibia, injeta DLL, conecta shared memory
        """
        print("[INJECTOR] Iniciando conexao automatica...")
        
        # 1. Encontra Tibia
        if not self.find_tibia():
            print("[INJECTOR] Tibia nao encontrado. Abra o jogo primeiro!")
            return False
        
        # 2. Verifica se ja esta conectado (DLL ja injetada de antes)
        if self.connect_shared_memory() or self.read_from_file():
            if self.is_connected():
                print("[INJECTOR] Ja conectado (DLL previamente injetada)")
                return True
        
        # 3. Injeta DLL
        if not self.injected:
            if not self.inject_dll():
                return False
        
        # 4. Aguarda DLL inicializar e conecta
        print("[INJECTOR] Aguardando DLL inicializar...")
        for i in range(30):  # 15 segundos max
            time.sleep(0.5)
            if self.connect_shared_memory() or self.read_from_file():
                if self.is_connected():
                    print("[INJECTOR] Conectado com sucesso!")
                    print(f"[INJECTOR] HP: {self.hp}/{self.hp_max} | MP: {self.mp}/{self.mp_max}")
                    return True
            print(f"[INJECTOR] Aguardando... ({i+1}/30)")
        
        print("[INJECTOR] Timeout aguardando DLL")
        return False


# Teste
if __name__ == "__main__":
    print("=" * 50)
    print("BAIAK BOT - AUTO INJECTOR")
    print("=" * 50)
    print()
    
    injector = AutoInjector()
    
    if not injector.dll_path:
        print("ERRO: BaiakBot.dll nao encontrada!")
        print()
        print("Voce precisa compilar a DLL primeiro.")
        print("Ou coloque 'BaiakBot.dll' na pasta do bot.")
        sys.exit(1)
    
    print(f"DLL encontrada: {injector.dll_path}")
    print()
    
    if injector.auto_connect():
        print()
        print("Monitorando HP/MP... (Ctrl+C para sair)")
        print()
        
        try:
            while True:
                print(f"\rHP: {injector.hp:>5}/{injector.hp_max:<5} ({injector.hp_percent:>3}%) | "
                      f"MP: {injector.mp:>5}/{injector.mp_max:<5} ({injector.mp_percent:>3}%)", end='')
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nFinalizado!")
    else:
        print("Falha ao conectar!")
        sys.exit(1)
