# -*- coding: utf-8 -*-
"""
Buscar pointer chains para o endereco do player
Bots profissionais usam: client.exe + offset -> pointer -> player struct
"""
import pymem
import struct
import ctypes
from ctypes import wintypes

pm = pymem.Pymem('client.exe')

# Endereco conhecido do player (da sessao atual)
PLAYER_ADDR = 0x1e9edc87d70

print(f'=== ANALISE DE POINTER CHAINS ===')
print(f'Endereco do Player: {hex(PLAYER_ADDR)}')

# Pegar modulo base do client.exe
base_addr = pm.base_address
print(f'Base do client.exe: {hex(base_addr)}')

# Listar todos os modulos carregados
print('\nModulos carregados:')
for module in pm.list_modules():
    if 'client' in module.name.lower() or 'qt' in module.name.lower():
        print(f'  {module.name}: {hex(module.lpBaseOfDll)} ({module.SizeOfImage/1024/1024:.1f}MB)')

# Buscar ponteiros que apontam para o endereco do player
print(f'\n=== BUSCANDO PONTEIROS PARA {hex(PLAYER_ADDR)} ===')

# Converter endereco para bytes (64-bit pointer)
target_bytes = struct.pack('<Q', PLAYER_ADDR)

MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_READONLY = 0x02
PAGE_WRITECOPY = 0x08

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

pointers = []
address = 0
mbi = MBI()

while address < 0x7FFFFFFFFFFF:
    result = ctypes.windll.kernel32.VirtualQueryEx(
        pm.process_handle, ctypes.c_void_p(address),
        ctypes.byref(mbi), ctypes.sizeof(mbi))
    if result == 0:
        break
    
    readable = mbi.Protect in [PAGE_READWRITE, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE, PAGE_READONLY, PAGE_WRITECOPY]
    
    if mbi.State == MEM_COMMIT and readable:
        if mbi.RegionSize and mbi.RegionSize < 100*1024*1024:
            try:
                data = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                pos = 0
                while True:
                    pos = data.find(target_bytes, pos)
                    if pos == -1:
                        break
                    ptr_addr = mbi.BaseAddress + pos
                    pointers.append(ptr_addr)
                    pos += 8
            except:
                pass
    
    address = (mbi.BaseAddress or 0) + (mbi.RegionSize or 0x10000)

print(f'Encontrados {len(pointers)} ponteiros para o endereco do player')

# Classificar ponteiros
for ptr in pointers[:30]:  # Primeiros 30
    rel = ptr - base_addr
    if 0 < rel < 0x10000000:  # Dentro de ~256MB do base
        print(f'  {hex(ptr)} (client.exe + {hex(rel)}) <-- POSSIVEL STATIC!')
    else:
        print(f'  {hex(ptr)}')

# Buscar ponteiros nivel 2 (ponteiros para ponteiros)
print(f'\n=== BUSCANDO PONTEIROS NIVEL 2 ===')
for ptr_addr in pointers[:10]:
    ptr_bytes = struct.pack('<Q', ptr_addr)
    level2 = []
    
    address = 0
    while address < 0x7FFFFFFFFFFF:
        result = ctypes.windll.kernel32.VirtualQueryEx(
            pm.process_handle, ctypes.c_void_p(address),
            ctypes.byref(mbi), ctypes.sizeof(mbi))
        if result == 0:
            break
        
        readable = mbi.Protect in [PAGE_READWRITE, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE, PAGE_READONLY]
        
        if mbi.State == MEM_COMMIT and readable:
            if mbi.RegionSize and mbi.RegionSize < 100*1024*1024:
                try:
                    data = pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                    pos = data.find(ptr_bytes)
                    if pos != -1:
                        level2.append(mbi.BaseAddress + pos)
                except:
                    pass
        
        address = (mbi.BaseAddress or 0) + (mbi.RegionSize or 0x10000)
    
    if level2:
        for l2 in level2[:5]:
            rel = l2 - base_addr
            if 0 < rel < 0x10000000:
                print(f'  {hex(l2)} -> {hex(ptr_addr)} -> PLAYER (client.exe + {hex(rel)})')
