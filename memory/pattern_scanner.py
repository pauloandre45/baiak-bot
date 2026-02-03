# -*- coding: utf-8 -*-
"""
Pattern Scanner - Busca padrões de bytes na memória
Similar ao que bots profissionais como ZeroBot usam.

Em vez de procurar valores específicos, procura PADRÕES que identificam
estruturas do jogo. Esses padrões não mudam entre sessões.
"""

import ctypes
from ctypes import wintypes
import struct
import json
import os
import time

try:
    import pymem
    import pymem.process
    import pymem.pattern
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


class PatternScanner:
    """
    Scanner baseado em padrões de bytes.
    
    A ideia é:
    1. Encontrar uma estrutura conhecida (HP/MP) UMA vez usando valores
    2. Ler os bytes ao redor dessa estrutura
    3. Criar um "padrão" que identifica essa estrutura
    4. Usar o padrão para encontrar a estrutura novamente
    
    Isso funciona porque a ESTRUTURA do código não muda,
    apenas os ENDEREÇOS mudam devido ao ASLR.
    """
    
    # Offsets conhecidos da estrutura do player (Tibia 15.11)
    OFFSET_HP_MAX = 0x8
    OFFSET_MP = 0x620
    OFFSET_MP_MAX = 0x628
    
    def __init__(self, process_name="client.exe"):
        self.process_name = process_name
        self.pm = None
        self.pattern_file = os.path.join(os.path.dirname(__file__), "..", "player_pattern.json")
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "offsets_cache.json")
    
    def connect(self):
        """Conecta ao processo"""
        if not PYMEM_AVAILABLE:
            return False
        try:
            self.pm = pymem.Pymem(self.process_name)
            return True
        except:
            return False
    
    def disconnect(self):
        """Desconecta"""
        if self.pm:
            try:
                self.pm.close_process()
            except:
                pass
        self.pm = None
    
    def _get_memory_regions(self):
        """Obtém regiões de memória válidas (apenas heap)"""
        regions = []
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
            
            # Filtra para heap (endereços altos, tamanho razoável)
            if base >= 0x100000000 and 0x10000 <= size <= 100 * 1024 * 1024:
                if (mbi.State == MEM_COMMIT and 
                    mbi.Protect in [PAGE_READWRITE, PAGE_READONLY]):
                    regions.append((base, size))
            
            address = base + size
        
        return regions
    
    def create_pattern_from_address(self, hp_addr, pattern_size=32):
        """
        Cria um padrão a partir de um endereço conhecido de HP.
        
        IMPORTANTE: Usa bytes ENTRE HP_MAX e MP que são mais estáveis
        (não contêm ponteiros que mudam a cada execução)
        """
        try:
            # Lê a estrutura entre HP_MAX e MP
            # Offset 0x10 até 0x620 (MP) - pega uma amostra do meio
            # Bytes no offset 0x280-0x2A0 parecem ter dados estáveis
            
            # Vamos usar múltiplas amostras da estrutura
            samples = []
            
            # Amostra 1: Bytes após HP_MAX (offset 0x10-0x30)
            sample1_offset = 0x10
            sample1 = self.pm.read_bytes(hp_addr + sample1_offset, 16)
            samples.append(("after_hp_max", sample1_offset, sample1))
            
            # Amostra 2: Bytes no meio da estrutura (offset 0x280-0x290)
            # Esta região geralmente contém flags e valores pequenos
            sample2_offset = 0x280
            sample2 = self.pm.read_bytes(hp_addr + sample2_offset, 16)
            samples.append(("mid_struct", sample2_offset, sample2))
            
            # Amostra 3: Bytes antes do MP (offset 0x600-0x610)
            sample3_offset = 0x600
            sample3 = self.pm.read_bytes(hp_addr + sample3_offset, 16)
            samples.append(("before_mp", sample3_offset, sample3))
            
            # Salva informações
            hp = self.pm.read_int(hp_addr)
            hp_max = self.pm.read_int(hp_addr + self.OFFSET_HP_MAX)
            mp = self.pm.read_int(hp_addr + self.OFFSET_MP)
            mp_max = self.pm.read_int(hp_addr + self.OFFSET_MP_MAX)
            
            pattern_data = {
                "version": 2,
                "samples": [
                    {"name": name, "offset": offset, "bytes": list(data)}
                    for name, offset, data in samples
                ],
                "verified_values": {
                    "hp": hp,
                    "hp_max": hp_max,
                    "mp": mp,
                    "mp_max": mp_max
                },
                "structure_offsets": {
                    "hp_max": self.OFFSET_HP_MAX,
                    "mp": self.OFFSET_MP,
                    "mp_max": self.OFFSET_MP_MAX
                }
            }
            
            return pattern_data
            
        except Exception as e:
            print(f"[PATTERN] Erro ao criar padrão: {e}")
            return None
    
    def save_pattern(self, pattern_data):
        """Salva padrão para uso futuro"""
        try:
            with open(self.pattern_file, 'w') as f:
                json.dump(pattern_data, f, indent=2)
            print(f"[PATTERN] Padrão salvo em {self.pattern_file}")
            return True
        except Exception as e:
            print(f"[PATTERN] Erro ao salvar: {e}")
            return False
    
    def load_pattern(self):
        """Carrega padrão salvo"""
        try:
            if not os.path.exists(self.pattern_file):
                return None
            with open(self.pattern_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def find_by_pattern(self, pattern_data):
        """
        Encontra a estrutura do player usando o padrão salvo.
        
        Versão 2: Usa amostras internas da estrutura (mais estável)
        """
        if not pattern_data:
            return None
        
        # Verifica versão do padrão
        version = pattern_data.get("version", 1)
        
        if version == 1:
            # Padrão antigo (prefixo) - menos confiável
            return self._find_by_prefix_pattern(pattern_data)
        
        # Versão 2: Usa amostras internas
        samples = pattern_data.get("samples", [])
        if not samples:
            return None
        
        print(f"[PATTERN] Buscando com {len(samples)} amostras...")
        
        regions = self._get_memory_regions()
        candidates = []
        
        # Usa a primeira amostra para busca inicial
        first_sample = samples[0]
        search_bytes = bytes(first_sample["bytes"])
        search_offset = first_sample["offset"]
        
        for base, size in regions:
            try:
                data = self.pm.read_bytes(base, size)
                
                pos = 0
                while True:
                    pos = data.find(search_bytes, pos)
                    if pos == -1:
                        break
                    
                    # Calcula HP addr (sample está em hp_addr + offset)
                    hp_addr = base + pos - search_offset
                    
                    # Verifica outras amostras
                    all_match = True
                    for sample in samples[1:]:
                        try:
                            expected = bytes(sample["bytes"])
                            actual = self.pm.read_bytes(hp_addr + sample["offset"], len(expected))
                            if actual != expected:
                                all_match = False
                                break
                        except:
                            all_match = False
                            break
                    
                    if all_match:
                        # Valida estrutura
                        if self._validate_structure(hp_addr):
                            candidates.append(hp_addr)
                    
                    pos += 1
                    
            except:
                continue
        
        print(f"[PATTERN] Encontrados {len(candidates)} candidatos")
        
        if candidates:
            hp_addr = candidates[0]
            return {
                "hp": hp_addr,
                "hp_max": hp_addr + self.OFFSET_HP_MAX,
                "mp": hp_addr + self.OFFSET_MP,
                "mp_max": hp_addr + self.OFFSET_MP_MAX
            }
        
        return None
    
    def _find_by_prefix_pattern(self, pattern_data):
        """Busca usando padrão de prefixo (versão 1, menos confiável)"""
        prefix_bytes = bytes(pattern_data.get("prefix_bytes", []))
        prefix_size = pattern_data.get("prefix_size", 64)
        hp_offset = pattern_data.get("hp_offset_from_prefix", prefix_size)
        
        if not prefix_bytes:
            return None
        
        print(f"[PATTERN] Buscando padrão de {len(prefix_bytes)} bytes (v1)...")
        
        regions = self._get_memory_regions()
        candidates = []
        
        for base, size in regions:
            try:
                data = self.pm.read_bytes(base, size)
                
                pos = 0
                while True:
                    pos = data.find(prefix_bytes, pos)
                    if pos == -1:
                        break
                    
                    hp_addr = base + pos + hp_offset
                    
                    if self._validate_structure(hp_addr):
                        candidates.append(hp_addr)
                    
                    pos += 1
                    
            except:
                continue
        
        print(f"[PATTERN] Encontrados {len(candidates)} candidatos")
        
        if candidates:
            hp_addr = candidates[0]
            return {
                "hp": hp_addr,
                "hp_max": hp_addr + self.OFFSET_HP_MAX,
                "mp": hp_addr + self.OFFSET_MP,
                "mp_max": hp_addr + self.OFFSET_MP_MAX
            }
        
        return None
    
    def _validate_structure(self, hp_addr):
        """Valida se o endereço contém estrutura válida de player"""
        try:
            hp = self.pm.read_int(hp_addr)
            hp_max = self.pm.read_int(hp_addr + self.OFFSET_HP_MAX)
            mp = self.pm.read_int(hp_addr + self.OFFSET_MP)
            mp_max = self.pm.read_int(hp_addr + self.OFFSET_MP_MAX)
            
            # Validações
            if hp <= 0 or hp > 500000:
                return False
            if hp_max < 100 or hp_max > 500000:
                return False
            if hp > hp_max:
                return False
            if mp < 0 or mp_max < 30:
                return False
            if mp_max > 0 and mp > mp_max:
                return False
            if mp_max > 500000:
                return False
            
            return True
        except:
            return False
    
    def find_with_values(self, hp_value, mp_value=None):
        """
        Encontra a estrutura usando valores conhecidos de HP/MP.
        
        Este método é mais lento mas mais preciso.
        Use para criar o padrão inicial.
        """
        print(f"[PATTERN] Buscando HP={hp_value}" + (f", MP={mp_value}" if mp_value else ""))
        
        regions = self._get_memory_regions()
        print(f"[PATTERN] {len(regions)} regiões de memória")
        
        candidates = []
        scanned = 0
        
        for base, size in regions:
            try:
                data = self.pm.read_bytes(base, size)
                scanned += 1
                
                if scanned % 50 == 0:
                    print(f"[PATTERN] Escaneado {scanned}/{len(regions)} regiões...", end="\r")
                
                # Procura HP na região
                hp_bytes = struct.pack('<i', hp_value)
                pos = 0
                
                while True:
                    pos = data.find(hp_bytes, pos)
                    if pos == -1:
                        break
                    
                    hp_addr = base + pos
                    
                    # Valida estrutura
                    try:
                        hp = self.pm.read_int(hp_addr)
                        hp_max = self.pm.read_int(hp_addr + self.OFFSET_HP_MAX)
                        mp = self.pm.read_int(hp_addr + self.OFFSET_MP)
                        mp_max = self.pm.read_int(hp_addr + self.OFFSET_MP_MAX)
                        
                        # Verifica valores
                        if hp == hp_value:
                            if hp <= hp_max and hp_max < 500000:
                                if mp_value is None or mp == mp_value:
                                    if mp <= mp_max and mp_max > 0:
                                        candidates.append({
                                            "addr": hp_addr,
                                            "hp": hp,
                                            "hp_max": hp_max,
                                            "mp": mp,
                                            "mp_max": mp_max
                                        })
                    except:
                        pass
                    
                    pos += 4
                    
            except:
                continue
        
        print()
        print(f"[PATTERN] Encontrados {len(candidates)} candidatos")
        
        if candidates:
            # Mostra candidatos
            for i, c in enumerate(candidates[:5]):
                print(f"  [{i}] HP={c['hp']}/{c['hp_max']}, MP={c['mp']}/{c['mp_max']} @ {hex(c['addr'])}")
            
            # Retorna o primeiro
            best = candidates[0]
            return {
                "hp": best["addr"],
                "hp_max": best["addr"] + self.OFFSET_HP_MAX,
                "mp": best["addr"] + self.OFFSET_MP,
                "mp_max": best["addr"] + self.OFFSET_MP_MAX
            }
        
        return None
    
    def auto_find(self, hp_value=None, mp_value=None):
        """
        Método principal: tenta encontrar automaticamente.
        
        1. Se tem padrão salvo, usa pattern matching (rápido)
        2. Se tem valores de HP/MP, usa scan por valores
        3. Se não tem nada, precisa de valores do usuário
        """
        # Tenta cache primeiro
        cached = self._load_cache()
        if cached and self._validate_cache(cached):
            print("[PATTERN] ✓ Cache válido!")
            return cached
        
        # Tenta padrão
        pattern = self.load_pattern()
        if pattern:
            print("[PATTERN] Tentando pattern matching...")
            offsets = self.find_by_pattern(pattern)
            if offsets:
                self._save_cache(offsets)
                return offsets
        
        # Tenta com valores
        if hp_value:
            print("[PATTERN] Usando valores fornecidos...")
            offsets = self.find_with_values(hp_value, mp_value)
            if offsets:
                # Cria novo padrão para uso futuro
                pattern_data = self.create_pattern_from_address(offsets["hp"])
                if pattern_data:
                    self.save_pattern(pattern_data)
                
                self._save_cache(offsets)
                return offsets
        
        print("[PATTERN] Não foi possível encontrar automaticamente")
        print("         Forneça HP/MP atual para criar novo padrão")
        return None
    
    def _load_cache(self):
        """Carrega cache de offsets"""
        try:
            if not os.path.exists(self.cache_file):
                return None
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            return {k: int(v, 16) if isinstance(v, str) else v 
                    for k, v in data.items() if k in ["hp", "hp_max", "mp", "mp_max"]}
        except:
            return None
    
    def _validate_cache(self, cached):
        """Valida cache"""
        try:
            return self._validate_structure(cached["hp"])
        except:
            return False
    
    def _save_cache(self, offsets):
        """Salva cache"""
        try:
            data = {k: hex(v) for k, v in offsets.items()}
            data["offset_hp_max"] = self.OFFSET_HP_MAX
            data["offset_mp"] = self.OFFSET_MP
            data["offset_mp_max"] = self.OFFSET_MP_MAX
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[PATTERN] Cache salvo")
        except:
            pass


def main():
    """Teste interativo do Pattern Scanner"""
    print("=" * 50)
    print("  PATTERN SCANNER - Tibia Memory")
    print("  Baseado em técnicas de bots profissionais")
    print("=" * 50)
    
    scanner = PatternScanner()
    
    if not scanner.connect():
        print("[ERRO] Não foi possível conectar ao client.exe")
        input("Pressione ENTER...")
        return
    
    print()
    print("Opções:")
    print("1. Busca automática (usa cache/padrão)")
    print("2. Busca com valores de HP/MP")
    print("3. Criar novo padrão")
    
    choice = input("\nEscolha [1/2/3]: ").strip()
    
    offsets = None
    
    if choice == "1":
        offsets = scanner.auto_find()
        
    elif choice == "2":
        try:
            hp = int(input("HP atual: ").strip())
            mp_input = input("MP atual (Enter para pular): ").strip()
            mp = int(mp_input) if mp_input else None
            offsets = scanner.auto_find(hp, mp)
        except ValueError:
            print("[ERRO] Valores inválidos")
            
    elif choice == "3":
        # Primeiro encontra com valores
        try:
            hp = int(input("HP atual: ").strip())
            mp_input = input("MP atual (Enter para pular): ").strip()
            mp = int(mp_input) if mp_input else None
            
            offsets = scanner.find_with_values(hp, mp)
            if offsets:
                print()
                print("Criando padrão...")
                pattern = scanner.create_pattern_from_address(offsets["hp"])
                if pattern:
                    scanner.save_pattern(pattern)
                    print("✓ Padrão criado com sucesso!")
        except ValueError:
            print("[ERRO] Valores inválidos")
    
    if offsets:
        print()
        print("=" * 50)
        print("  ✓ ENCONTRADO!")
        print("=" * 50)
        
        hp = scanner.pm.read_int(offsets["hp"])
        hp_max = scanner.pm.read_int(offsets["hp_max"])
        mp = scanner.pm.read_int(offsets["mp"])
        mp_max = scanner.pm.read_int(offsets["mp_max"])
        
        print(f"  HP: {hp}/{hp_max} ({int(hp/hp_max*100)}%)")
        print(f"  MP: {mp}/{mp_max} ({int(mp/mp_max*100)}%)")
        print()
        print(f"  Endereços:")
        print(f"  HP:     {hex(offsets['hp'])}")
        print(f"  HP_MAX: {hex(offsets['hp_max'])}")
        print(f"  MP:     {hex(offsets['mp'])}")
        print(f"  MP_MAX: {hex(offsets['mp_max'])}")
    
    scanner.disconnect()
    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()
