# 🔧 Guia Técnico - Scanner de Memória

## Como o Scanner Funciona

Este documento explica em detalhes como encontrar os endereços de HP/MP no cliente do Tibia.

---

## Conceito Básico

O Tibia armazena os dados do jogador na memória RAM. Cada variável (HP, MP, Level, etc.) tem um **endereço de memória** onde o valor está armazenado.

**Problema:** O endereço muda toda vez que o Tibia é reiniciado (ASLR - Address Space Layout Randomization).

**Solução:** Escanear a memória procurando o valor atual e filtrar até encontrar o endereço correto.

---

## Passo a Passo do Scanner

### 1. Conectar ao Processo

```python
import pymem

pm = pymem.Pymem("client.exe")
print(f"Conectado! PID: {pm.process_id}")
```

### 2. Obter Regiões de Memória

```python
import ctypes
from ctypes import wintypes

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

def get_memory_regions(process_handle):
    """Obtém todas as regiões de memória do processo"""
    regions = []
    address = 0
    
    while address < 0x7FFFFFFFFFFF:  # Limite de memória 64-bit
        mbi = MEMORY_BASIC_INFORMATION()
        result = ctypes.windll.kernel32.VirtualQueryEx(
            process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(mbi),
            ctypes.sizeof(mbi)
        )
        
        if result == 0:
            break
        
        # Apenas regiões committed e readable
        MEM_COMMIT = 0x1000
        PAGE_READABLE = 0x02 | 0x04 | 0x20 | 0x40  # READ, READWRITE, EXECUTE_READ, EXECUTE_READWRITE
        
        if mbi.State == MEM_COMMIT and (mbi.Protect & PAGE_READABLE):
            regions.append(mbi)
        
        address += mbi.RegionSize
    
    return regions
```

### 3. Primeira Varredura

```python
import struct

def scan_for_int32(pm, target_value):
    """Escaneia toda memória procurando um int32"""
    found_addresses = []
    target_bytes = struct.pack('<i', target_value)  # Little-endian int32
    
    regions = get_memory_regions(pm.process_handle)
    
    for region in regions:
        try:
            # Lê toda a região
            data = pm.read_bytes(region.BaseAddress, region.RegionSize)
            
            # Procura o padrão
            offset = 0
            while True:
                pos = data.find(target_bytes, offset)
                if pos == -1:
                    break
                
                address = region.BaseAddress + pos
                found_addresses.append(address)
                offset = pos + 1
                
        except Exception:
            continue  # Região inacessível
    
    return found_addresses

# Exemplo: HP = 185
addresses = scan_for_int32(pm, 185)
print(f"Encontrados {len(addresses)} endereços com valor 185")
# Resultado típico: 500.000+ endereços
```

### 4. Filtrar Endereços

```python
def filter_addresses(pm, addresses, new_value):
    """Mantém apenas endereços que mudaram para novo valor"""
    valid = []
    
    for addr in addresses:
        try:
            current = pm.read_int(addr)
            if current == new_value:
                valid.append(addr)
        except:
            continue
    
    return valid

# HP mudou de 185 para 150
filtered = filter_addresses(pm, addresses, 150)
print(f"Restaram {len(filtered)} endereços")
# Resultado típico: 10-50 endereços
```

### 5. Repetir até Encontrar

```python
def find_hp_address(pm):
    """Processo interativo para encontrar HP"""
    
    # Primeira varredura
    hp = int(input("Digite seu HP atual: "))
    addresses = scan_for_int32(pm, hp)
    print(f"Encontrados: {len(addresses)}")
    
    while len(addresses) > 1:
        input("Mude seu HP (tome dano ou cure) e pressione ENTER...")
        
        new_hp = int(input("Digite seu HP atual: "))
        addresses = filter_addresses(pm, addresses, new_hp)
        print(f"Restaram: {len(addresses)}")
    
    if len(addresses) == 1:
        print(f"ENCONTRADO! HP está em: {hex(addresses[0])}")
        return addresses[0]
    else:
        print("Não foi possível encontrar. Tente novamente.")
        return None
```

---

## Descoberta do HP_MAX

Após encontrar o HP, verificamos os endereços próximos:

```python
def find_hp_max(pm, hp_address):
    """HP_MAX geralmente está logo após HP"""
    
    # Testa offsets comuns
    for offset in [4, 8, 12, 16]:
        try:
            value = pm.read_int(hp_address + offset)
            print(f"HP + {offset}: {value}")
        except:
            pass

# Resultado descoberto:
# HP + 0: 185 (HP atual)
# HP + 4: 0
# HP + 8: 185 (HP máximo!) ← ENCONTRADO!
```

**Conclusão:** HP_MAX = HP + 8 bytes

---

## Descoberta do MP

Repetimos o processo para MP e descobrimos:

```python
# Endereços encontrados:
HP_ADDRESS = 0x201cd3272f0
MP_ADDRESS = 0x201cd327910

# Diferença:
offset = MP_ADDRESS - HP_ADDRESS
print(f"Offset HP -> MP: {hex(offset)}")  # 0x620 (1568 bytes)
```

**Estrutura completa:**

```
Offset do HP    Campo
──────────────────────────
+0x000          HP atual
+0x008          HP máximo
...
+0x620          MP atual
+0x628          MP máximo
```

---

## Código Completo do Scanner

O arquivo `memory/scanner_advanced.py` contém a implementação completa com:

- Interface interativa no terminal
- Salvamento automático em `offsets_cache.json`
- Detecção automática de HP_MAX e MP_MAX
- Tratamento de erros

### Uso:

```bash
python memory/scanner_advanced.py
```

### Output esperado:

```
================================================
   SCANNER DE MEMÓRIA - Tibia 15.11
================================================

[1] Conectando ao client.exe...
✓ Conectado! PID: 23332

[2] ENCONTRAR HP
Digite seu HP atual: 185
Escaneando memória... (pode demorar)
✓ Encontrados 523847 endereços

Mude seu HP e pressione ENTER...
Digite seu HP atual: 150
Filtrando...
✓ Restaram 23 endereços

Mude seu HP e pressione ENTER...
Digite seu HP atual: 175
Filtrando...
✓ Restaram 1 endereço

★ HP ENCONTRADO: 0x201cd3272f0
★ HP_MAX (HP+8): 0x201cd3272f8

[3] ENCONTRAR MP
...

[4] SALVANDO
✓ Offsets salvos em offsets_cache.json
```

---

## Dicas Importantes

### 1. ASLR
Os endereços mudam a cada reinício do Tibia. Sempre rode o scanner novamente após reiniciar.

### 2. Valores Comuns
Valores como 100, 0, 1 aparecem em milhões de endereços. Prefira valores "únicos" como 185, 347, etc.

### 3. Regiões de Memória
Nem todas as regiões são acessíveis. O scanner ignora regiões protegidas automaticamente.

### 4. Performance
A primeira varredura pode demorar 10-30 segundos dependendo do uso de memória do Tibia.

### 5. Validação
Sempre valide o endereço encontrado mudando o HP novamente e verificando se o valor lido está correto.

---

*Documentação técnica do Scanner de Memória*
*Criada em: 03/02/2026*
