# -*- coding: utf-8 -*-
"""
Teste de scan focado no HP exato
"""
import pymem
import struct
import time
import ctypes
from ctypes import wintypes

pm = pymem.Pymem('client.exe')

# Valores conhecidos do seu char
TARGET_HP = 3320
TARGET_MP_MAX = 18900

OFFSET_HP_MAX = 0x8
OFFSET_MP = 0x620
OFFSET_MP_MAX = 0x628

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

print(f'Buscando HP={TARGET_HP}...')
start = time.time()

address = 0x100000000  # Comeca no heap
mbi = MBI()
hp_bytes = struct.pack('<i', TARGET_HP)
addresses = []

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
                pos = 0
                while True:
                    pos = data.find(hp_bytes, pos)
                    if pos == -1:
                        break
                    addresses.append(mbi.BaseAddress + pos)
                    pos += 4
            except:
                pass
    
    address = (mbi.BaseAddress or 0) + (mbi.RegionSize or 0x10000)

print(f'Encontrados {len(addresses)} enderecos com HP={TARGET_HP}')

# Valida cada um
valid = []
for addr in addresses:
    try:
        hp = pm.read_int(addr)
        hp_max = pm.read_int(addr + OFFSET_HP_MAX)
        mp = pm.read_int(addr + OFFSET_MP)
        mp_max = pm.read_int(addr + OFFSET_MP_MAX)
        
        if hp == hp_max == TARGET_HP:
            if mp_max > 100 and mp >= 0 and mp <= mp_max:
                valid.append({
                    'addr': addr,
                    'hp': hp,
                    'hp_max': hp_max,
                    'mp': mp,
                    'mp_max': mp_max
                })
    except:
        pass

print(f'{len(valid)} validos')
for v in valid:
    marker = ' <-- CORRETO!' if v['mp_max'] == TARGET_MP_MAX else ''
    print(f"  HP={v['hp']}/{v['hp_max']}, MP={v['mp']}/{v['mp_max']} @ {hex(v['addr'])}{marker}")

print(f'Tempo: {time.time()-start:.1f}s')
