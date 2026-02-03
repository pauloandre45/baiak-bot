# -*- coding: utf-8 -*-
"""
Smart Memory Reader - Le HP/MP automaticamente sem DLL
Escaneia uma vez, cacheia, e re-escaneia quando necessario

SOLUCAO 100% PYTHON - NAO PRECISA DE DLL
"""

import os
import sys
import time
import json
import threading
from pathlib import Path

try:
    import pymem
    import pymem.process
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False
    print("[AVISO] pymem nao instalado!")


class SmartMemoryReader:
    """
    Leitor de memoria inteligente que:
    1. Escaneia automaticamente ao conectar
    2. Cacheia enderecos para rapida reconexao
    3. Re-escaneia automaticamente se dados ficarem invalidos
    4. Funciona em background sem travar a UI
    """
    
    # Estrutura do player (offsets relativos ao HP)
    OFFSET_HP_MAX = 0x8
    OFFSET_MP = 0x620
    OFFSET_MP_MAX = 0x628
    
    # Arquivo de cache
    CACHE_FILE = "player_cache.json"
    
    def __init__(self, callback=None):
        """
        callback: funcao chamada quando encontrar player (opcional)
        """
        self.pm = None
        self.base_address = 0
        self.hp_address = 0
        
        self._hp = 0
        self._hp_max = 0
        self._mp = 0
        self._mp_max = 0
        self._last_read = 0
        self._connected = False
        self._scanning = False
        self._last_valid_check = 0
        
        self.callback = callback
        self.scan_thread = None
        self.cache_path = Path(__file__).parent.parent / self.CACHE_FILE
        
        # Carrega cache se existir
        self._load_cache()
    
    def _load_cache(self):
        """
        Carrega enderecos do cache
        """
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r') as f:
                    data = json.load(f)
                    # Cache inclui PID para saber se e o mesmo processo
                    self._cached_hp_addr = data.get('hp_address', 0)
                    self._cached_pid = data.get('pid', 0)
                    print(f"[SMART] Cache carregado: HP @ {hex(self._cached_hp_addr)}")
            except:
                self._cached_hp_addr = 0
                self._cached_pid = 0
        else:
            self._cached_hp_addr = 0
            self._cached_pid = 0
    
    def _save_cache(self):
        """
        Salva enderecos no cache
        """
        try:
            data = {
                'hp_address': self.hp_address,
                'pid': self.pm.process_id if self.pm else 0,
                'timestamp': time.time()
            }
            with open(self.cache_path, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def connect(self, process_name='client.exe'):
        """
        Conecta ao processo do Tibia
        """
        if not PYMEM_AVAILABLE:
            print("[SMART] ERRO: pymem nao disponivel!")
            return False
        
        try:
            self.pm = pymem.Pymem(process_name)
            self.base_address = self.pm.base_address
            print(f"[SMART] Conectado ao Tibia - PID: {self.pm.process_id}")
            
            # Se PID e o mesmo do cache, tenta usar endereco cacheado
            if self._cached_pid == self.pm.process_id and self._cached_hp_addr:
                print("[SMART] Mesmo processo, tentando cache...")
                if self._try_cached_address():
                    self._connected = True
                    return True
            
            # Novo processo ou cache invalido - precisa escanear
            print("[SMART] Iniciando scan automatico...")
            self._start_background_scan()
            
            return True
            
        except Exception as e:
            print(f"[SMART] Erro ao conectar: {e}")
            return False
    
    def _try_cached_address(self):
        """
        Tenta usar endereco do cache
        """
        if not self._cached_hp_addr:
            return False
        
        if self._validate_player_structure(self._cached_hp_addr):
            self.hp_address = self._cached_hp_addr
            self._read_values()
            print(f"[SMART] Cache valido! HP: {self._hp}/{self._hp_max}")
            return True
        
        print("[SMART] Cache invalido")
        return False
    
    def _validate_player_structure(self, addr):
        """
        Valida se o endereco aponta para estrutura de player valida
        """
        try:
            hp = self.pm.read_int(addr)
            hp_max = self.pm.read_int(addr + self.OFFSET_HP_MAX)
            mp = self.pm.read_int(addr + self.OFFSET_MP)
            mp_max = self.pm.read_int(addr + self.OFFSET_MP_MAX)
            
            # Validacoes
            if hp <= 0 or hp > 100000:
                return False
            if hp_max <= 0 or hp_max > 100000:
                return False
            if hp > hp_max:
                return False
            if mp < 0 or mp > 500000:
                return False
            if mp_max < 0 or mp_max > 500000:
                return False
            if mp_max > 0 and mp > mp_max:
                return False
            
            return True
        except:
            return False
    
    def _start_background_scan(self):
        """
        Inicia scan em background
        """
        if self._scanning:
            return
        
        self._scanning = True
        self.scan_thread = threading.Thread(target=self._background_scan, daemon=True)
        self.scan_thread.start()
    
    def _background_scan(self):
        """
        Escaneia memoria em background
        """
        print("[SMART] Escaneando memoria (isso pode levar alguns segundos)...")
        
        start_time = time.time()
        found = False
        
        try:
            import ctypes
            from ctypes import wintypes
            
            # Usa VirtualQueryEx para listar regioes
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            
            class MEMORY_BASIC_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("BaseAddress", ctypes.c_void_p),
                    ("AllocationBase", ctypes.c_void_p),
                    ("AllocationProtect", wintypes.DWORD),
                    ("RegionSize", ctypes.c_size_t),
                    ("State", wintypes.DWORD),
                    ("Protect", wintypes.DWORD),
                    ("Type", wintypes.DWORD),
                ]
            
            MEM_COMMIT = 0x1000
            PAGE_READWRITE = 0x04
            PAGE_READONLY = 0x02
            
            regions = []
            address = 0x10000  # Comeca apos primeiras paginas
            max_address = 0x7FFFFFFFFFFF  # 64-bit
            
            mbi = MEMORY_BASIC_INFORMATION()
            
            while address < max_address:
                result = kernel32.VirtualQueryEx(
                    self.pm.process_handle,
                    ctypes.c_void_p(address),
                    ctypes.byref(mbi),
                    ctypes.sizeof(mbi)
                )
                
                if result == 0:
                    break
                
                base_addr = mbi.BaseAddress if mbi.BaseAddress else address
                region_size = mbi.RegionSize if mbi.RegionSize else 0x1000
                
                if mbi.State == MEM_COMMIT and region_size > 0x1000:
                    if mbi.Protect in [PAGE_READWRITE, PAGE_READONLY, 0x40, 0x20, 0x04, 0x02]:
                        regions.append({
                            'base': base_addr,
                            'size': region_size
                        })
                
                # Avanca para proxima regiao
                next_addr = base_addr + region_size
                if next_addr <= address:
                    address += 0x1000
                else:
                    address = next_addr
            
            total_regions = len(regions)
            checked = 0
            
            print(f"[SMART] Encontradas {total_regions} regioes para escanear")
            
            for region in regions:
                base = region['base']
                size = region['size']
                
                if not base or size < 0x1000:
                    continue
                
                # Escaneia esta regiao
                if self._scan_region(base, size):
                    found = True
                    break
                
                checked += 1
                if checked % 100 == 0:
                    elapsed = time.time() - start_time
                    print(f"[SMART] Progresso: {checked}/{total_regions} regioes ({elapsed:.1f}s)...")
        
        except Exception as e:
            print(f"[SMART] Erro no scan: {e}")
            import traceback
            traceback.print_exc()
        
        elapsed = time.time() - start_time
        
        if found:
            print(f"[SMART] Player encontrado em {elapsed:.1f}s!")
            print(f"[SMART] HP: {self._hp}/{self._hp_max} | MP: {self._mp}/{self._mp_max}")
            self._connected = True
            self._save_cache()
            
            if self.callback:
                self.callback(True)
        else:
            print(f"[SMART] Player nao encontrado ({elapsed:.1f}s)")
            print("[SMART] Dica: Entre no jogo com um personagem primeiro!")
        
        self._scanning = False
    
    def _scan_region(self, base, size):
        """
        Escaneia uma regiao de memoria
        """
        try:
            # Le regiao em chunks
            chunk_size = 0x10000  # 64KB
            
            for offset in range(0, size - 0x700, chunk_size):
                try:
                    addr = base + offset
                    data = self.pm.read_bytes(addr, min(chunk_size, size - offset))
                    
                    # Procura padroes de HP validos
                    for i in range(0, len(data) - 0x630, 4):
                        # Le potenciais valores
                        hp = int.from_bytes(data[i:i+4], 'little', signed=True)
                        
                        # Filtro rapido
                        if hp <= 0 or hp > 50000:
                            continue
                        
                        # Valida estrutura completa
                        check_addr = addr + i
                        if self._validate_player_structure(check_addr):
                            self.hp_address = check_addr
                            self._read_values()
                            return True
                            
                except:
                    continue
        except:
            pass
        
        return False
    
    def _read_values(self):
        """
        Le valores de HP/MP
        """
        if not self.hp_address or not self.pm:
            return
        
        try:
            self._hp = self.pm.read_int(self.hp_address)
            self._hp_max = self.pm.read_int(self.hp_address + self.OFFSET_HP_MAX)
            self._mp = self.pm.read_int(self.hp_address + self.OFFSET_MP)
            self._mp_max = self.pm.read_int(self.hp_address + self.OFFSET_MP_MAX)
        except:
            pass
    
    def update(self):
        """
        Atualiza valores (chamado automaticamente pelos getters)
        """
        now = time.time()
        
        # Rate limit
        if now - self._last_read < 0.03:  # 30ms
            return
        self._last_read = now
        
        if not self.hp_address or not self.pm:
            return
        
        # Le valores
        self._read_values()
        
        # Verifica validade periodicamente (a cada 5 segundos)
        if now - self._last_valid_check > 5:
            self._last_valid_check = now
            
            if not self._validate_player_structure(self.hp_address):
                print("[SMART] Estrutura invalidada, re-escaneando...")
                self._connected = False
                self.hp_address = 0
                self._start_background_scan()
    
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
        return self._connected and self.hp_address > 0
    
    def is_scanning(self):
        return self._scanning
    
    def wait_for_connection(self, timeout=30):
        """
        Aguarda ate conectar ou timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.is_connected():
                return True
            if not self._scanning:
                return False
            time.sleep(0.5)
        return False


# Teste
if __name__ == "__main__":
    print("=" * 50)
    print("SMART MEMORY READER - 100% PYTHON")
    print("=" * 50)
    print()
    
    reader = SmartMemoryReader()
    
    if not reader.connect():
        print("Falha ao conectar!")
        print("Certifique-se que o Tibia esta aberto.")
        sys.exit(1)
    
    print()
    print("Aguardando scan completar...")
    
    if reader.wait_for_connection(60):
        print()
        print("Conectado! Monitorando... (Ctrl+C para sair)")
        print()
        
        try:
            while True:
                if reader.is_connected():
                    print(f"\rHP: {reader.hp:>5}/{reader.hp_max:<5} ({reader.hp_percent:>3}%) | "
                          f"MP: {reader.mp:>5}/{reader.mp_max:<5} ({reader.mp_percent:>3}%)", end='')
                elif reader.is_scanning():
                    print("\rEscaneando...", end='')
                else:
                    print("\rDesconectado", end='')
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nFinalizado!")
    else:
        print("Timeout - player nao encontrado")
        print("Entre no jogo com um personagem primeiro!")
