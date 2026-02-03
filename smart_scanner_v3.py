# -*- coding: utf-8 -*-
"""
Scanner inteligente V3 - Usa multiplos criterios para identificar o player
Criterios:
1. HP == HP_MAX (vida cheia)
2. HP no range 150-30000
3. MP_MAX diferente de HP_MAX
4. Valor em HP+0x14 (possivel level) entre 1-2000
5. Valor em HP+0x14 deve ser DIFERENTE de HP (nao confundir HP com level)
"""
import pymem
import struct
import ctypes
import time
from ctypes import wintypes

OFFSET_HP_MAX = 0x8
OFFSET_MP = 0x620
OFFSET_MP_MAX = 0x628
OFFSET_LEVEL = 0x14  # Possivel offset do level

MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04

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

def find_player_v3(pm):
    """
    Encontra o player usando multiplos criterios
    """
    print('=== SMART SCANNER V3 ===')
    start_time = time.time()
    
    candidates = []
    address = 0x100000000
    mbi = MBI()
    regions_scanned = 0
    
    while address < 0x7FFFFFFFFFFF:
        result = ctypes.windll.kernel32.VirtualQueryEx(
            pm.process_handle, ctypes.c_void_p(address),
            ctypes.byref(mbi), ctypes.sizeof(mbi))
        if result == 0:
            break
        
        if mbi.State == MEM_COMMIT and mbi.Protect == PAGE_READWRITE:
            if mbi.RegionSize and mbi.RegionSize < 50*1024*1024:
                try:
                    data = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                    regions_scanned += 1
                    
                    # Scanear cada 8 bytes (alinhado)
                    for offset in range(0, len(data) - OFFSET_MP_MAX - 4, 8):
                        try:
                            hp = struct.unpack_from('<i', data, offset)[0]
                            
                            # Criterio 1: HP no range valido
                            if not (150 <= hp <= 30000):
                                continue
                            
                            hp_max = struct.unpack_from('<i', data, offset + OFFSET_HP_MAX)[0]
                            
                            # Criterio 2: HP == HP_MAX (vida cheia)
                            if hp != hp_max:
                                continue
                            
                            # Criterio 3: Verificar MP
                            mp = struct.unpack_from('<i', data, offset + OFFSET_MP)[0]
                            mp_max = struct.unpack_from('<i', data, offset + OFFSET_MP_MAX)[0]
                            
                            # MP_MAX deve ser diferente de HP_MAX
                            if mp_max == hp_max:
                                continue
                            
                            # MP deve estar no range valido
                            if not (100 <= mp_max <= 100000):
                                continue
                            
                            # MP deve ser > 0 (player com mana)
                            if not (1 <= mp <= mp_max):
                                continue
                            
                            # MP_MAX nao deve ser potencia de 2 (valores suspeitos de buffer)
                            if mp_max in [256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 65792]:
                                continue
                            
                            # Criterio 4: Verificar possivel level
                            level = struct.unpack_from('<i', data, offset + OFFSET_LEVEL)[0]
                            
                            # Level deve ser diferente de HP (senao pode ser falso positivo)
                            if level == hp:
                                continue
                            
                            # Level deve estar no range 1-2000
                            if not (1 <= level <= 2000):
                                continue
                            
                            addr = mbi.BaseAddress + offset
                            candidates.append({
                                'addr': addr,
                                'hp': hp,
                                'hp_max': hp_max,
                                'mp': mp,
                                'mp_max': mp_max,
                                'level': level
                            })
                        except:
                            continue
                except:
                    pass
        
        address = (mbi.BaseAddress or 0) + (mbi.RegionSize or 0x10000)
    
    elapsed = time.time() - start_time
    print(f'Regioes escaneadas: {regions_scanned}')
    print(f'Candidatos encontrados: {len(candidates)}')
    print(f'Tempo: {elapsed:.1f}s')
    
    # Remover duplicatas (mesmo HP/MP)
    seen = set()
    unique = []
    for c in candidates:
        key = (c['hp'], c['hp_max'], c['mp'], c['mp_max'], c['level'])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    
    print(f'Candidatos unicos: {len(unique)}')
    
    # Ordenar por criterios de "realidade"
    # Player real provavelmente tem:
    # - HP_MAX > level * 10 (HP cresce mais rapido que level)
    # - MP_MAX > HP_MAX (mages tem mais mana)
    def score(c):
        s = 0
        # Bonus se MP_MAX > HP_MAX (comum em mages)
        if c['mp_max'] > c['hp_max']:
            s += 1000
        # Bonus se HP_MAX > level * 5 (HP cresce mais que level)
        if c['hp_max'] > c['level'] * 5:
            s += 500
        # Bonus para HPs medios (nem muito baixo nem muito alto)
        if 1000 <= c['hp_max'] <= 10000:
            s += 300
        return s
    
    unique.sort(key=score, reverse=True)
    
    return unique

if __name__ == '__main__':
    pm = pymem.Pymem('client.exe')
    
    candidates = find_player_v3(pm)
    
    print('\n=== TOP 10 CANDIDATOS ===')
    for i, c in enumerate(candidates[:10]):
        print(f"{i+1}. HP={c['hp']}/{c['hp_max']}, MP={c['mp']}/{c['mp_max']}, Level={c['level']} @ {hex(c['addr'])}")
    
    # Verificar se o endereco correto esta na lista
    KNOWN_ADDR = 0x1e9edc87d70
    found = False
    for i, c in enumerate(candidates):
        if c['addr'] == KNOWN_ADDR:
            print(f'\n*** Endereco correto encontrado na posicao {i+1}! ***')
            found = True
            break
    
    if not found:
        print(f'\n*** ATENCAO: Endereco correto {hex(KNOWN_ADDR)} NAO encontrado! ***')
        # Verificar manualmente
        print('Verificando endereco correto manualmente...')
        hp = pm.read_int(KNOWN_ADDR)
        hp_max = pm.read_int(KNOWN_ADDR + OFFSET_HP_MAX)
        mp = pm.read_int(KNOWN_ADDR + OFFSET_MP)
        mp_max = pm.read_int(KNOWN_ADDR + OFFSET_MP_MAX)
        level = pm.read_int(KNOWN_ADDR + OFFSET_LEVEL)
        print(f'  HP={hp}/{hp_max}, MP={mp}/{mp_max}, Level={level}')
