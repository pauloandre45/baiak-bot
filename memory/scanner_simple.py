# -*- coding: utf-8 -*-
"""
Scanner Simples - Encontra HP/MP de forma fácil
"""

import ctypes
from ctypes import wintypes
import struct
import json
import os

try:
    import pymem
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False

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


def scan_value(pm, value):
    """Procura um valor int32 na memória"""
    results = []
    search_bytes = struct.pack("<i", value)
    
    address = 0
    mbi = MEMORY_BASIC_INFORMATION()
    VirtualQueryEx = ctypes.windll.kernel32.VirtualQueryEx
    
    while address < 0x7FFFFFFFFFFF:
        result = VirtualQueryEx(
            pm.process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(mbi),
            ctypes.sizeof(mbi)
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
            size < 100 * 1024 * 1024):
            
            try:
                data = pm.read_bytes(base, size)
                pos = 0
                while True:
                    pos = data.find(search_bytes, pos)
                    if pos == -1:
                        break
                    results.append(base + pos)
                    pos += 1
            except:
                pass
        
        address = base + size
    
    return results


def filter_value(pm, addresses, new_value):
    """Filtra endereços que têm o novo valor"""
    valid = []
    for addr in addresses:
        try:
            if pm.read_int(addr) == new_value:
                valid.append(addr)
        except:
            pass
    return valid


def validate_hp_structure(pm, addr):
    """Verifica se um endereço tem estrutura válida de HP"""
    try:
        hp = pm.read_int(addr)
        hp_max = pm.read_int(addr + 8)
        mp = pm.read_int(addr + 0x620)
        mp_max = pm.read_int(addr + 0x628)
        
        # Validações
        if hp <= 0 or hp > 500000:
            return False
        if hp_max <= 0 or hp_max > 500000:
            return False
        if hp > hp_max:
            return False
        if mp < 0 or mp_max < 0:
            return False
        if mp_max > 0 and mp > mp_max:
            return False
            
        return True
    except:
        return False


def main():
    print("=" * 50)
    print("  SCANNER SIMPLES - Tibia")
    print("=" * 50)
    print()
    
    if not PYMEM_AVAILABLE:
        print("ERRO: pymem não instalado")
        print("Execute: pip install pymem")
        input("ENTER para sair...")
        return
    
    try:
        pm = pymem.Pymem("client.exe")
        print(f"Conectado ao Tibia (PID: {pm.process_id})")
    except:
        print("ERRO: Tibia não encontrado!")
        print("Abra o Tibia e logue no jogo antes de executar.")
        input("ENTER para sair...")
        return
    
    print()
    hp1 = input("Digite seu HP ATUAL: ").strip()
    
    if not hp1.isdigit():
        print("HP inválido!")
        input("ENTER para sair...")
        return
    
    hp1 = int(hp1)
    
    print()
    print("Escaneando... (pode demorar alguns segundos)")
    results = scan_value(pm, hp1)
    print(f"Encontrados {len(results)} endereços")
    
    if len(results) == 0:
        print("Nenhum endereço encontrado!")
        input("ENTER para sair...")
        return
    
    print()
    print("Agora LEVE DANO (ataque um monstro) ou CURE-SE")
    hp2 = input("Digite seu NOVO HP: ").strip()
    
    if not hp2.isdigit():
        print("HP inválido!")
        input("ENTER para sair...")
        return
    
    hp2 = int(hp2)
    
    print()
    print("Filtrando...")
    results = filter_value(pm, results, hp2)
    print(f"Restaram {len(results)} endereços")
    
    # Se ainda tiver muitos, pede mais uma vez
    while len(results) > 5:
        print()
        print("Ainda muitos resultados. Mude HP novamente.")
        hp3 = input("Digite seu NOVO HP (ou ENTER para continuar): ").strip()
        
        if not hp3:
            break
        
        if hp3.isdigit():
            results = filter_value(pm, results, int(hp3))
            print(f"Restaram {len(results)} endereços")
    
    if len(results) == 0:
        print("Nenhum endereço encontrado!")
        input("ENTER para sair...")
        return
    
    # Encontra o endereço correto validando a estrutura
    print()
    print("Validando estrutura de memória...")
    
    hp_addr = None
    for addr in results:
        if validate_hp_structure(pm, addr):
            hp_addr = addr
            break
    
    # Se não encontrou com validação, usa o primeiro
    if not hp_addr and results:
        hp_addr = results[0]
        print("(usando primeiro resultado)")
    
    if hp_addr:
        hp = pm.read_int(hp_addr)
        hp_max = pm.read_int(hp_addr + 8)
        mp = pm.read_int(hp_addr + 0x620)
        mp_max = pm.read_int(hp_addr + 0x628)
        
        print()
        print("=" * 50)
        print("  ✓ ENCONTRADO!")
        print("=" * 50)
        print()
        print(f"  HP:     {hp}/{hp_max}  @  {hex(hp_addr)}")
        print(f"  MP:     {mp}/{mp_max}  @  {hex(hp_addr + 0x620)}")
        print()
        
        # Salva
        cache_file = os.path.join(os.path.dirname(__file__), "..", "offsets_cache.json")
        data = {
            "hp": hex(hp_addr),
            "hp_max": hex(hp_addr + 8),
            "mp": hex(hp_addr + 0x620),
            "mp_max": hex(hp_addr + 0x628)
        }
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Salvo em: {cache_file}")
        print()
        print("Agora você pode usar o bot!")
    else:
        print("Não foi possível encontrar o endereço correto.")
    
    input("\nENTER para sair...")


if __name__ == "__main__":
    main()
