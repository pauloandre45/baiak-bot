# -*- coding: utf-8 -*-
"""
Smart Memory Reader v2 - Encontra HP/MP automaticamente
Usa tecnica de comparacao de valores para encontrar enderecos reais

COMO FUNCIONA:
1. Escaneia memoria por valor de HP atual
2. Pede para usuario tomar dano ou curar
3. Compara quais enderecos mudaram
4. Encontra estrutura completa (HP, HP_MAX, MP, MP_MAX)
5. Cacheia para proximas sessoes

OFFSETS CONHECIDOS (Tibia 15.11):
- HP_MAX = HP + 0x8
- MP = HP + 0x620
- MP_MAX = HP + 0x628
"""

import os
import sys
import time
import json
import ctypes
from ctypes import wintypes
from pathlib import Path

try:
    import pymem
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False


class SmartReaderV2:
    """
    Leitor de memoria que encontra HP/MP automaticamente
    """
    
    # Offsets conhecidos (Tibia 15.11 BaiakZika)
    OFFSET_HP_MAX = 0x8
    OFFSET_MP = 0x620
    OFFSET_MP_MAX = 0x628
    
    CACHE_FILE = "offsets_cache.json"
    
    def __init__(self):
        self.pm = None
        self.hp_address = 0
        self.offsets = {}
        
        self._hp = 0
        self._hp_max = 0
        self._mp = 0
        self._mp_max = 0
        self._last_read = 0
        self._connected = False
        
        self.cache_path = Path(__file__).parent.parent / self.CACHE_FILE
        self._load_cache()
    
    def _load_cache(self):
        """Carrega offsets do cache"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r') as f:
                    self.offsets = json.load(f)
                print(f"[SMART] Cache carregado")
            except:
                self.offsets = {}
    
    def _save_cache(self):
        """Salva offsets no cache"""
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(self.offsets, f, indent=2)
        except:
            pass
    
    def connect(self, process_name='client.exe'):
        """Conecta ao processo do Tibia"""
        if not PYMEM_AVAILABLE:
            return False
        
        try:
            self.pm = pymem.Pymem(process_name)
            print(f"[SMART] Conectado ao Tibia - PID: {self.pm.process_id}")
            
            # Tenta usar cache
            if self._try_cached_offsets():
                return True
            
            return True
        except Exception as e:
            print(f"[SMART] Erro ao conectar: {e}")
            return False
    
    def _try_cached_offsets(self):
        """Tenta usar offsets do cache"""
        if not self.offsets:
            return False
        
        try:
            hp_addr = int(self.offsets.get('hp', '0'), 16)
            if hp_addr == 0:
                return False
            
            # Verifica se estrutura ainda e valida
            hp = self.pm.read_int(hp_addr)
            hp_max = self.pm.read_int(hp_addr + self.OFFSET_HP_MAX)
            mp = self.pm.read_int(hp_addr + self.OFFSET_MP)
            mp_max = self.pm.read_int(hp_addr + self.OFFSET_MP_MAX)
            
            # Validacao
            if hp <= 0 or hp > 100000:
                return False
            if hp_max <= 0 or hp_max > 100000:
                return False
            if hp > hp_max:
                return False
            if mp < 0 or mp > 500000:
                return False
            if mp_max <= 0 or mp_max > 500000:
                return False
            if mp > mp_max:
                return False
            
            self.hp_address = hp_addr
            self._connected = True
            print(f"[SMART] Cache valido! HP: {hp}/{hp_max} MP: {mp}/{mp_max}")
            return True
            
        except:
            return False
    
    def scan_for_value(self, value):
        """Escaneia memoria por um valor especifico"""
        if not self.pm:
            return []
        
        kernel32 = ctypes.WinDLL('kernel32')
        
        class MBI(ctypes.Structure):
            _fields_ = [
                ('BaseAddress', ctypes.c_void_p),
                ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wintypes.DWORD),
                ('RegionSize', ctypes.c_size_t),
                ('State', wintypes.DWORD),
                ('Protect', wintypes.DWORD),
                ('Type', wintypes.DWORD),
            ]
        
        addresses = []
        address = 0x10000
        max_addr = 0x7FFFFFFFFFFF
        mbi = MBI()
        value_bytes = value.to_bytes(4, 'little', signed=True)
        
        while address < max_addr:
            result = kernel32.VirtualQueryEx(
                self.pm.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                ctypes.sizeof(mbi)
            )
            
            if result == 0:
                break
            
            base = mbi.BaseAddress if mbi.BaseAddress else address
            size = mbi.RegionSize if mbi.RegionSize else 0x1000
            
            if mbi.State == 0x1000 and size > 0x1000:
                if mbi.Protect in [0x04, 0x02, 0x40, 0x20]:
                    try:
                        data = self.pm.read_bytes(base, min(size, 0x200000))
                        pos = 0
                        while True:
                            idx = data.find(value_bytes, pos)
                            if idx == -1:
                                break
                            addresses.append(base + idx)
                            pos = idx + 4
                    except:
                        pass
            
            next_addr = base + size
            address = next_addr if next_addr > address else address + 0x1000
        
        return addresses
    
    def find_player_structure(self, hp_value, hp_max_value, mp_value, mp_max_value):
        """
        Encontra estrutura do player buscando HP e MP
        """
        print(f"[SMART] Buscando HP={hp_value} e MP={mp_value}...")
        
        hp_addrs = self.scan_for_value(hp_value)
        mp_addrs = self.scan_for_value(mp_value)
        
        print(f"[SMART] Encontrados: {len(hp_addrs)} HP, {len(mp_addrs)} MP")
        
        # Procura estrutura onde HP e MP estao nos offsets corretos
        for hp_addr in hp_addrs:
            try:
                # Verifica HP_MAX
                hp_max = self.pm.read_int(hp_addr + self.OFFSET_HP_MAX)
                if hp_max != hp_max_value:
                    continue
                
                # Verifica MP
                mp = self.pm.read_int(hp_addr + self.OFFSET_MP)
                if mp != mp_value:
                    continue
                
                # Verifica MP_MAX
                mp_max = self.pm.read_int(hp_addr + self.OFFSET_MP_MAX)
                if mp_max != mp_max_value:
                    continue
                
                # ENCONTRADO!
                self.hp_address = hp_addr
                self.offsets = {
                    'hp': hex(hp_addr),
                    'hp_max': hex(hp_addr + self.OFFSET_HP_MAX),
                    'mp': hex(hp_addr + self.OFFSET_MP),
                    'mp_max': hex(hp_addr + self.OFFSET_MP_MAX),
                    'offset_hp_max': self.OFFSET_HP_MAX,
                    'offset_mp': self.OFFSET_MP,
                    'offset_mp_max': self.OFFSET_MP_MAX
                }
                self._save_cache()
                self._connected = True
                
                print(f"[SMART] Estrutura encontrada @ {hex(hp_addr)}")
                return True
                
            except:
                continue
        
        return False
    
    def auto_scan_interactive(self):
        """
        Scan interativo - pede valores ao usuario
        """
        print()
        print("=== SCAN AUTOMATICO ===")
        print()
        print("Digite os valores mostrados no jogo:")
        print()
        
        try:
            hp = int(input("HP atual: "))
            hp_max = int(input("HP maximo: "))
            mp = int(input("MP atual: "))
            mp_max = int(input("MP maximo: "))
            
            if self.find_player_structure(hp, hp_max, mp, mp_max):
                print()
                print("SUCESSO! Enderecos encontrados e salvos.")
                return True
            else:
                print()
                print("Estrutura nao encontrada. Verifique os valores.")
                return False
                
        except ValueError:
            print("Valores invalidos!")
            return False
    
    def update(self):
        """Atualiza valores de HP/MP"""
        now = time.time()
        if now - self._last_read < 0.03:
            return
        self._last_read = now
        
        if not self.hp_address or not self.pm:
            return
        
        try:
            self._hp = self.pm.read_int(self.hp_address)
            self._hp_max = self.pm.read_int(self.hp_address + self.OFFSET_HP_MAX)
            self._mp = self.pm.read_int(self.hp_address + self.OFFSET_MP)
            self._mp_max = self.pm.read_int(self.hp_address + self.OFFSET_MP_MAX)
            
            # Valida dados
            if self._hp <= 0 or self._hp > self._hp_max or self._hp_max > 100000:
                self._connected = False
            else:
                self._connected = True
                
        except:
            self._connected = False
    
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
        self.update()
        return self._connected


# Teste
if __name__ == "__main__":
    print("=" * 50)
    print("SMART MEMORY READER V2")
    print("=" * 50)
    print()
    
    reader = SmartReaderV2()
    
    if not reader.connect():
        print("Falha ao conectar ao Tibia!")
        sys.exit(1)
    
    if not reader.is_connected():
        print("Cache invalido ou nao existe.")
        print()
        if not reader.auto_scan_interactive():
            sys.exit(1)
    
    print()
    print("Monitorando HP/MP... (Ctrl+C para sair)")
    print()
    
    try:
        while True:
            if reader.is_connected():
                print(f"\rHP: {reader.hp:>5}/{reader.hp_max:<5} ({reader.hp_percent:>3}%) | "
                      f"MP: {reader.mp:>5}/{reader.mp_max:<5} ({reader.mp_percent:>3}%)", end='')
            else:
                print("\rDesconectado - enderecos invalidos", end='')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nFinalizado!")
