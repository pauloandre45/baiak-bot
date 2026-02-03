# -*- coding: utf-8 -*-
"""
Buscar ponteiros que apontam para PERTO do endereco do player
O ponteiro pode apontar para o inicio de uma estrutura maior
"""
import pymem
import struct
import ctypes
from ctypes import wintypes

pm = pymem.Pymem('client.exe')

PLAYER_ADDR = 0x1e9edc87d70
base_addr = pm.base_address

print(f'Player: {hex(PLAYER_ADDR)}')
print(f'Base: {hex(base_addr)}')

# Calcular possiveis enderecos base (antes do HP)
# Se HP esta no offset X da struct, o base seria PLAYER_ADDR - X
possible_bases = []
for offset in [0, 0x8, 0x10, 0x18, 0x20, 0x30, 0x40, 0x50, 0x60, 0x80, 0x100, 0x200, 0x400, 0x620, 0x800, 0x1000]:
    possible_bases.append(PLAYER_ADDR - offset)

print(f'\nPossiveis bases da struct player:')
for pb in possible_bases[:10]:
    print(f'  {hex(pb)} (offset -{hex(PLAYER_ADDR - pb)})')

MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02

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

# Buscar ponteiros para cada possivel base
print(f'\n=== BUSCANDO PONTEIROS ===')

for target in possible_bases:
    target_bytes = struct.pack('<Q', target)
    pointers = []
    
    address = base_addr  # Comecar do modulo client.exe
    mbi = MBI()
    
    # Buscar apenas no modulo client.exe e areas estaticas
    while address < base_addr + 0x10000000:  # ~256MB
        result = ctypes.windll.kernel32.VirtualQueryEx(
            pm.process_handle, ctypes.c_void_p(address),
            ctypes.byref(mbi), ctypes.sizeof(mbi))
        if result == 0:
            break
        
        if mbi.State == MEM_COMMIT:
            if mbi.RegionSize and mbi.RegionSize < 50*1024*1024:
                try:
                    data = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                    pos = 0
                    while True:
                        pos = data.find(target_bytes, pos)
                        if pos == -1:
                            break
                        ptr_addr = mbi.BaseAddress + pos
                        rel = ptr_addr - base_addr
                        if 0 < rel < 0x2000000:  # Dentro do modulo
                            pointers.append((ptr_addr, rel))
                        pos += 8
                except:
                    pass
        
        address = (mbi.BaseAddress or 0) + (mbi.RegionSize or 0x10000)
    
    if pointers:
        offset = PLAYER_ADDR - target
        print(f'\nPonteiros para {hex(target)} (HP offset seria {hex(offset)}):')
        for ptr, rel in pointers[:5]:
            print(f'  client.exe + {hex(rel)} -> {hex(target)}')

# Buscar no HEAP tambem
print(f'\n=== BUSCANDO NO HEAP ===')

for target in possible_bases[:5]:
    target_bytes = struct.pack('<Q', target)
    pointers = []
    
    address = 0x100000000  # Heap
    mbi = MBI()
    
    while address < 0x300000000:
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
                        pos = data.find(target_bytes, pos)
                        if pos == -1:
                            break
                        pointers.append(mbi.BaseAddress + pos)
                        pos += 8
                except:
                    pass
        
        address = (mbi.BaseAddress or 0) + (mbi.RegionSize or 0x10000)
    
    if pointers:
        offset = PLAYER_ADDR - target
        print(f'\nPonteiros heap para {hex(target)} (HP offset={hex(offset)}):')
        for ptr in pointers[:10]:
            print(f'  {hex(ptr)}')
