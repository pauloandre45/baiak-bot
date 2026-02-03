# -*- coding: utf-8 -*-
"""
Pointer Scanner - Encontra ponteiros estáticos para HP/MP
Este é o método usado por bots profissionais como ZeroBot, WindBot

A ideia é:
1. Encontrar o endereço dinâmico do HP (muda a cada reinício)
2. Procurar por ponteiros que apontam PARA esse endereço
3. Encontrar um ponteiro em uma região ESTÁTICA (não muda)
4. Salvar: base_module + offset = ponteiro -> HP
"""

import ctypes
from ctypes import wintypes
import struct
import time
import json
import os

try:
    import pymem
    import pymem.process
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False

# Windows API
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40


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


class PointerScanner:
    """
    Scanner de ponteiros para encontrar estruturas estáticas
    """
    
    def __init__(self, process_name="client.exe"):
        self.process_name = process_name
        self.pm = None
        self.base_address = None
        self.module_size = None
        
    def connect(self):
        """Conecta ao processo"""
        if not PYMEM_AVAILABLE:
            print("[ERRO] pymem não instalado")
            return False
        
        try:
            self.pm = pymem.Pymem(self.process_name)
            self.base_address = self.pm.base_address
            
            # Obtém tamanho do módulo principal
            for module in self.pm.list_modules():
                if module.name.lower() == self.process_name.lower():
                    self.module_size = module.SizeOfImage
                    break
            
            print(f"[POINTER] Conectado ao {self.process_name}")
            print(f"          Base: {hex(self.base_address)}")
            print(f"          Size: {self.module_size} bytes")
            
            return True
        except Exception as e:
            print(f"[ERRO] {e}")
            return False
    
    def scan_for_pointers(self, target_address, max_offset=0x2000):
        """
        Procura por ponteiros que apontam para target_address
        
        Retorna lista de (endereço_do_ponteiro, offset)
        onde: *(endereço_do_ponteiro) + offset = target_address
        """
        print(f"[POINTER] Procurando ponteiros para {hex(target_address)}...")
        
        pointers = []
        
        # Procura em toda a memória por valores que podem ser ponteiros
        address = 0
        mbi = MEMORY_BASIC_INFORMATION()
        mbi_size = ctypes.sizeof(mbi)
        
        VirtualQueryEx = ctypes.windll.kernel32.VirtualQueryEx
        
        while address < 0x7FFFFFFFFFFF:
            result = VirtualQueryEx(
                self.pm.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                mbi_size
            )
            
            if result == 0:
                break
            
            base = mbi.BaseAddress
            size = mbi.RegionSize
            
            if base is None or size is None or size == 0:
                address += 0x10000
                continue
            
            if (mbi.State == MEM_COMMIT and 
                mbi.Protect in [PAGE_READWRITE, PAGE_READONLY, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE] and
                size < 50 * 1024 * 1024):
                
                try:
                    data = self.pm.read_bytes(base, size)
                    
                    # Procura por ponteiros (8 bytes em 64-bit)
                    for offset in range(0, len(data) - 8, 8):
                        ptr_value = struct.unpack('<Q', data[offset:offset+8])[0]
                        
                        # Verifica se o ponteiro aponta para perto do target
                        diff = target_address - ptr_value
                        
                        if 0 <= diff < max_offset:
                            ptr_addr = base + offset
                            pointers.append((ptr_addr, diff))
                            
                except:
                    pass
            
            address = base + size
        
        print(f"[POINTER] Encontrados {len(pointers)} ponteiros")
        return pointers
    
    def find_static_pointers(self, target_address):
        """
        Encontra ponteiros ESTÁTICOS (dentro do módulo do jogo)
        que apontam para o target_address
        
        Ponteiros estáticos = base_module + offset fixo
        """
        pointers = self.scan_for_pointers(target_address)
        
        static_pointers = []
        
        for ptr_addr, offset in pointers:
            # Verifica se o ponteiro está dentro do módulo principal
            if self.base_address <= ptr_addr < self.base_address + self.module_size:
                relative_addr = ptr_addr - self.base_address
                static_pointers.append({
                    "absolute": ptr_addr,
                    "relative": relative_addr,
                    "offset_to_hp": offset
                })
        
        print(f"[POINTER] Encontrados {len(static_pointers)} ponteiros ESTÁTICOS")
        
        for p in static_pointers[:10]:  # Mostra os primeiros 10
            print(f"          Base+{hex(p['relative'])} -> +{hex(p['offset_to_hp'])} -> HP")
        
        return static_pointers
    
    def find_pointer_chain(self, hp_address, max_depth=3):
        """
        Encontra uma cadeia de ponteiros até o HP
        
        Exemplo: base_module + offset1 -> ptr1 + offset2 -> ptr2 + offset3 -> HP
        """
        print(f"[POINTER] Procurando cadeia de ponteiros para {hex(hp_address)}...")
        print(f"          Profundidade máxima: {max_depth}")
        
        chains = []
        
        # Nível 1: Ponteiros diretos para HP
        level1 = self.scan_for_pointers(hp_address, max_offset=0x1000)
        
        for ptr_addr, offset in level1:
            # Verifica se está no módulo principal (estático)
            if self.base_address <= ptr_addr < self.base_address + self.module_size:
                relative = ptr_addr - self.base_address
                chains.append({
                    "type": "direct",
                    "base_offset": relative,
                    "offsets": [offset],
                    "test_addr": ptr_addr
                })
        
        if chains:
            print(f"[POINTER] Encontradas {len(chains)} cadeias de nível 1")
            return chains
        
        if max_depth < 2:
            return chains
        
        # Nível 2: Ponteiro -> Ponteiro -> HP
        print("[POINTER] Procurando cadeias de nível 2...")
        
        for ptr_addr, offset1 in level1[:100]:  # Limita para não demorar
            level2 = self.scan_for_pointers(ptr_addr, max_offset=0x100)
            
            for ptr2_addr, offset2 in level2:
                if self.base_address <= ptr2_addr < self.base_address + self.module_size:
                    relative = ptr2_addr - self.base_address
                    chains.append({
                        "type": "level2",
                        "base_offset": relative,
                        "offsets": [offset2, offset1],
                        "test_addr": ptr2_addr
                    })
        
        print(f"[POINTER] Encontradas {len(chains)} cadeias totais")
        return chains
    
    def verify_pointer_chain(self, chain):
        """
        Verifica se uma cadeia de ponteiros está funcionando
        """
        try:
            # Lê o primeiro ponteiro
            ptr = self.pm.read_longlong(self.base_address + chain["base_offset"])
            
            # Segue a cadeia
            for offset in chain["offsets"][:-1]:
                ptr = self.pm.read_longlong(ptr + offset)
            
            # O último offset aponta para o valor
            final_addr = ptr + chain["offsets"][-1]
            value = self.pm.read_int(final_addr)
            
            return value, final_addr
            
        except Exception as e:
            return None, None
    
    def test_static_pointer(self, base_offset, hp_offset):
        """
        Testa se um ponteiro estático funciona
        
        base_offset: offset relativo ao módulo base
        hp_offset: offset do ponteiro para o HP
        """
        try:
            # Lê o ponteiro base
            ptr_addr = self.base_address + base_offset
            ptr_value = self.pm.read_longlong(ptr_addr)
            
            # Lê HP
            hp_addr = ptr_value + hp_offset
            hp = self.pm.read_int(hp_addr)
            hp_max = self.pm.read_int(hp_addr + 8)
            
            return {
                "hp": hp,
                "hp_max": hp_max,
                "hp_addr": hp_addr,
                "valid": 0 < hp <= hp_max <= 500000
            }
        except:
            return None


def interactive_pointer_scan():
    """
    Scanner interativo de ponteiros
    """
    print("=" * 60)
    print("  POINTER SCANNER - Encontra estruturas estáticas")
    print("=" * 60)
    print()
    print("Este scanner encontra ponteiros que NÃO mudam entre")
    print("reinicializações do Tibia.")
    print()
    
    scanner = PointerScanner()
    
    if not scanner.connect():
        input("Pressione ENTER para sair...")
        return
    
    print()
    print("Primeiro, precisamos do endereço ATUAL do HP.")
    print("Se você já rodou o scanner_advanced.py, os offsets")
    print("devem estar salvos no offsets_cache.json")
    print()
    
    # Tenta carregar do cache
    cache_file = os.path.join(os.path.dirname(__file__), "..", "offsets_cache.json")
    hp_address = None
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            if 'hp' in data:
                hp_address = int(data['hp'], 16)
                
                # Verifica se ainda é válido
                try:
                    hp = scanner.pm.read_int(hp_address)
                    hp_max = scanner.pm.read_int(hp_address + 8)
                    if 0 < hp <= hp_max <= 500000:
                        print(f"[OK] HP encontrado no cache: {hp}/{hp_max} @ {hex(hp_address)}")
                    else:
                        print(f"[AVISO] Endereço do cache inválido")
                        hp_address = None
                except:
                    hp_address = None
        except:
            pass
    
    if not hp_address:
        print()
        addr_str = input("Digite o endereço do HP (ex: 0x201cd3272f0): ").strip()
        try:
            hp_address = int(addr_str, 16)
        except:
            print("Endereço inválido!")
            return
    
    print()
    print("-" * 60)
    print("Procurando ponteiros estáticos...")
    print("-" * 60)
    print()
    
    # Busca ponteiros estáticos
    static_pointers = scanner.find_static_pointers(hp_address)
    
    if static_pointers:
        print()
        print("=" * 60)
        print("  PONTEIROS ESTÁTICOS ENCONTRADOS!")
        print("=" * 60)
        print()
        print("Estes são os offsets que funcionam independente de reinício:")
        print()
        
        for i, p in enumerate(static_pointers[:5]):
            print(f"  [{i+1}] client.exe + {hex(p['relative'])}")
            print(f"      -> +{hex(p['offset_to_hp'])} = HP")
            print()
        
        # Salva o primeiro
        if static_pointers:
            best = static_pointers[0]
            save_data = {
                "type": "static_pointer",
                "base_offset": hex(best['relative']),
                "hp_offset": hex(best['offset_to_hp']),
                "hp_max_offset": hex(best['offset_to_hp'] + 8),
                "mp_offset": hex(best['offset_to_hp'] + 0x620),
                "mp_max_offset": hex(best['offset_to_hp'] + 0x628),
            }
            
            pointer_file = os.path.join(os.path.dirname(__file__), "..", "pointer_config.json")
            with open(pointer_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print(f"[SALVO] Configuração salva em pointer_config.json")
    else:
        print()
        print("Nenhum ponteiro estático direto encontrado.")
        print("Tentando busca de cadeia de ponteiros...")
        
        chains = scanner.find_pointer_chain(hp_address, max_depth=2)
        
        if chains:
            print()
            for chain in chains[:3]:
                print(f"  Tipo: {chain['type']}")
                print(f"  Base: client.exe + {hex(chain['base_offset'])}")
                print(f"  Offsets: {[hex(o) for o in chain['offsets']]}")
                print()
    
    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    interactive_pointer_scan()
