# -*- coding: utf-8 -*-
"""
Analisar a estrutura completa do player para encontrar dados unicos
que possamos usar para identificar automaticamente
"""
import pymem
import struct

pm = pymem.Pymem('client.exe')

PLAYER_ADDR = 0x1e9edc87d70

print('=== ANALISE DA ESTRUTURA DO PLAYER ===')
print(f'Endereco HP: {hex(PLAYER_ADDR)}')

# Ler 4KB ao redor do HP
# Comecar 1KB antes e ir ate 3KB depois
START = PLAYER_ADDR - 0x400  # 1KB antes
SIZE = 0x1000  # 4KB total

data = pm.read_bytes(START, SIZE)

print(f'\nLendo de {hex(START)} ate {hex(START + SIZE)}')
print(f'HP esta no offset 0x400 deste dump\n')

# Analisar como inteiros de 4 bytes (signed)
print('=== VALORES INT32 (possiveis stats) ===')
for offset in range(0, SIZE, 4):
    val = struct.unpack_from('<i', data, offset)[0]
    real_addr = START + offset
    rel_to_hp = offset - 0x400  # Relativo ao HP
    
    # Filtrar valores interessantes
    if 100 <= val <= 50000:  # Range de HP/MP/Level/etc
        prefix = ''
        if rel_to_hp == 0:
            prefix = ' <-- HP'
        elif rel_to_hp == 8:
            prefix = ' <-- HP_MAX'
        elif rel_to_hp == 0x620:
            prefix = ' <-- MP'
        elif rel_to_hp == 0x628:
            prefix = ' <-- MP_MAX'
        
        if prefix or (val > 500 and val < 30000):
            print(f'  HP+{hex(rel_to_hp):>6}: {val:>8}{prefix}')

# Verificar bytes especificos
print('\n=== BYTES INTERESSANTES ===')

# Ler HP, HP_MAX, MP, MP_MAX conhecidos
hp = pm.read_int(PLAYER_ADDR)
hp_max = pm.read_int(PLAYER_ADDR + 0x8)
mp = pm.read_int(PLAYER_ADDR + 0x620)
mp_max = pm.read_int(PLAYER_ADDR + 0x628)
print(f'HP: {hp}/{hp_max}')
print(f'MP: {mp}/{mp_max}')

# Verificar se tem strings (nome do personagem?)
print('\n=== BUSCANDO STRINGS ===')
for offset in range(0, SIZE - 32, 8):
    # Verificar se parece string ASCII
    chunk = data[offset:offset+32]
    try:
        # Tentar decodificar como ASCII
        text = ''
        for b in chunk:
            if 32 <= b <= 126:  # Printable ASCII
                text += chr(b)
            elif b == 0:
                break
            else:
                text = ''
                break
        
        if len(text) >= 4:  # String de pelo menos 4 chars
            real_addr = START + offset
            rel_to_hp = offset - 0x400
            print(f'  HP+{hex(rel_to_hp):>6}: "{text}"')
    except:
        pass

# Analisar como ponteiros de 64 bits
print('\n=== PONTEIROS (64-bit) ===')
for offset in range(0, SIZE - 8, 8):
    val = struct.unpack_from('<Q', data, offset)[0]
    real_addr = START + offset
    rel_to_hp = offset - 0x400
    
    # Ponteiros validos tipicamente comecam com 0x7ff ou 0x000001
    if (0x7ff000000000 <= val <= 0x7fffffffffff) or (0x100000000 <= val <= 0x400000000):
        print(f'  HP+{hex(rel_to_hp):>6}: {hex(val)}')

# Buscar valor unico (Level? Experience? Soul?)
print('\n=== VALORES UNICOS ===')
# O level do personagem seria um bom identificador
# Tipicamente 1-2000 em servers custom
for offset in range(0, 0x200, 4):  # Primeiros 512 bytes apos HP
    rel = offset
    addr = PLAYER_ADDR + offset
    try:
        val = pm.read_int(addr)
        if 1 <= val <= 2000:  # Possivel level
            print(f'  HP+{hex(rel)}: {val} (possivel level?)')
    except:
        pass
