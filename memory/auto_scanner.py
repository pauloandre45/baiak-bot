# -*- coding: utf-8 -*-
"""
Auto Scanner v2 - Encontra HP/MP automaticamente
Usa validação por estrutura conhecida para encontrar endereços.

Offsets confirmados para Tibia 15.11 (BaiakZika):
- HP_MAX = HP + 0x8
- MP     = HP + 0x620
- MP_MAX = HP + 0x628
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


class AutoScanner:
    """
    Scanner automático que encontra HP/MP do jogador.
    
    Estratégia principal:
    1. Usa valores conhecidos de HP/MP do jogador para scan inicial
    2. Valida estrutura usando offsets conhecidos
    3. Cache de endereços para reutilização
    
    Estratégia de fallback:
    - Scan automático com validação rigorosa
    """
    
    def __init__(self, process_name="client.exe"):
        self.process_name = process_name
        self.pm = None
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "offsets_cache.json")
        
        # Offsets CONFIRMADOS da estrutura do player (Tibia 15.11)
        # HP_MAX = HP + 8
        # MP = HP + 0x620 (1568 bytes)
        # MP_MAX = HP + 0x628 (1576 bytes)
        self.OFFSET_HP_MAX = 0x8
        self.OFFSET_MP = 0x620
        self.OFFSET_MP_MAX = 0x628
    
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
    
    def _get_memory_regions(self, heap_only=True):
        """
        Obtém regiões de memória válidas.
        
        heap_only: Se True, foca em regiões de heap (muito mais rápido)
        """
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
            
            # Pula se base é None
            if base is None or size is None or size == 0:
                address += 0x10000  # Pula 64KB
                continue
            
            # Filtros para acelerar o scan
            if heap_only:
                # Foca em heaps: regiões grandes em endereços altos
                # Heaps do Tibia geralmente estão acima de 0x100000000
                if base < 0x100000000:
                    address = base + size
                    continue
                
                # Ignora regiões muito pequenas (< 64KB)
                if size < 0x10000:
                    address = base + size
                    continue
                
                # Ignora regiões muito grandes (> 100MB) - provavelmente não são dados do player
                if size > 100 * 1024 * 1024:
                    address = base + size
                    continue
            
            if (mbi.State == MEM_COMMIT and 
                mbi.Protect in [PAGE_READWRITE, PAGE_READONLY, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE] and
                size < 100 * 1024 * 1024):
                regions.append((base, size))
            
            address = base + size
        
        return regions
    
    def _validate_player_struct(self, hp_addr, expected_hp=None, expected_mp=None):
        """
        Valida se o endereço é realmente o HP do jogador
        verificando a estrutura completa.
        
        expected_hp/expected_mp: valores esperados para validação mais precisa
        """
        try:
            hp = self.pm.read_int(hp_addr)
            hp_max = self.pm.read_int(hp_addr + self.OFFSET_HP_MAX)
            mp = self.pm.read_int(hp_addr + self.OFFSET_MP)
            mp_max = self.pm.read_int(hp_addr + self.OFFSET_MP_MAX)
            
            # Se temos valores esperados, verifica correspondência EXATA
            if expected_hp is not None and hp != expected_hp:
                return False
            if expected_mp is not None and mp != expected_mp:
                return False
            
            # ===============================================
            # VALIDAÇÕES RIGOROSAS
            # ===============================================
            
            # 1. HP deve ser positivo e razoável (personagens têm 50-500k HP)
            if hp <= 0 or hp > 500000:
                return False
            
            # 2. HP_MAX deve ser positivo e razoável
            if hp_max <= 0 or hp_max > 500000:
                return False
            
            # 3. HP <= HP_MAX (não pode ter mais HP que o máximo)
            if hp > hp_max:
                return False
            
            # 4. HP_MAX deve ser pelo menos 100 (mínimo level 8+)
            # Personagens de Tibia não têm menos que ~150 HP
            if hp_max < 100:
                return False
            
            # 5. MP não pode ser negativo
            if mp < 0:
                return False
            
            # 6. MP_MAX não pode ser negativo e deve ser razoável
            if mp_max < 0 or mp_max > 500000:
                return False
            
            # 7. MP <= MP_MAX
            if mp_max > 0 and mp > mp_max:
                return False
            
            # 8. HP% deve estar entre 1% e 100%
            hp_percent = (hp / hp_max) * 100
            if hp_percent < 1 or hp_percent > 100:
                return False
            
            # 9. IMPORTANTE: Personagens de Tibia SEMPRE têm mana
            # Mesmo knights level baixo têm pelo menos 50-100 MP_MAX
            # MP_MAX = 0 é definitivamente falso positivo
            if mp_max == 0:
                return False
            
            # 10. MP_MAX deve ser pelo menos 30 (mínimo para qualquer personagem)
            if mp_max < 30:
                return False
            
            # 11. HP e HP_MAX devem ter proporção razoável
            if hp_max > 0 and hp > 0:
                ratio = hp_max / hp
                if ratio > 50:  # HP_MAX não pode ser 50x maior que HP atual
                    return False
            
            # 12. Verifica que o endereço não está em região baixa da memória
            # Endereços do player geralmente estão em regiões heap (altos)
            if hp_addr < 0x100000000:  # 4GB - muito baixo para heap
                return False
            
            return True
            
        except Exception as e:
            return False
    
    def _scan_for_hp_candidates(self, min_hp=50, max_hp=500000, expected_hp=None, expected_mp=None):
        """
        Procura por candidatos a HP na memória.
        
        Se expected_hp/expected_mp forem fornecidos, filtra apenas candidatos
        que correspondem exatamente a esses valores.
        """
        print("[AUTO] Escaneando memória...")
        
        # Se temos HP esperado, usamos ele como filtro
        if expected_hp is not None:
            min_hp = expected_hp
            max_hp = expected_hp
        
        candidates = []
        regions = self._get_memory_regions()
        total_regions = len(regions)
        
        for idx, (base, size) in enumerate(regions):
            if idx % 50 == 0:
                print(f"[AUTO] Região {idx+1}/{total_regions}...", end="\r")
            
            try:
                data = self.pm.read_bytes(base, size)
                
                # Procura por inteiros de 4 bytes
                for offset in range(0, len(data) - 4, 4):
                    value = struct.unpack('<i', data[offset:offset+4])[0]
                    
                    # Filtra valores plausíveis de HP
                    if min_hp <= value <= max_hp:
                        addr = base + offset
                        
                        # Verifica estrutura completa
                        if self._validate_player_struct(addr, expected_hp, expected_mp):
                            candidates.append(addr)
                            
            except:
                continue
        
        print(f"[AUTO] Scan completo - {len(candidates)} candidatos encontrados")
        return candidates
    
    def _verify_candidate(self, addr, wait_time=2.0):
        """
        Verifica se um candidato é realmente o HP
        monitorando mudanças por alguns segundos
        """
        try:
            readings = []
            start = time.time()
            
            while time.time() - start < wait_time:
                hp = self.pm.read_int(addr)
                hp_max = self.pm.read_int(addr + self.OFFSET_HP_MAX)
                
                # Verifica consistência
                if hp <= 0 or hp_max <= 0 or hp > hp_max:
                    return False
                
                readings.append((hp, hp_max))
                time.sleep(0.1)
            
            # Verifica se HP_MAX permaneceu constante
            hp_maxes = [r[1] for r in readings]
            if len(set(hp_maxes)) > 2:  # HP_MAX não deve mudar muito
                return False
            
            return True
            
        except:
            return False
    
    def find_player_addresses(self, quick=True, hp_value=None, mp_value=None):
        """
        Encontra os endereços do jogador automaticamente.
        
        Args:
            quick: Se True, para no primeiro candidato válido
                   Se False, verifica todos e retorna o melhor
            hp_value: Valor atual do HP do jogador (para scan preciso)
            mp_value: Valor atual do MP do jogador (para validação extra)
        
        Retorna: dict com hp, hp_max, mp, mp_max ou None
        """
        if not self.pm:
            if not self.connect():
                return None
        
        print("[AUTO] Procurando endereços do jogador...")
        if hp_value:
            print(f"[AUTO] Buscando HP = {hp_value}")
        if mp_value:
            print(f"[AUTO] Validando MP = {mp_value}")
        
        candidates = self._scan_for_hp_candidates(
            expected_hp=hp_value, 
            expected_mp=mp_value
        )
        print(f"[AUTO] Encontrados {len(candidates)} candidatos")
        
        if not candidates:
            print("[AUTO] Nenhum candidato encontrado")
            return None
        
        # Se temos valores esperados, já validamos durante o scan
        # então podemos confiar mais nos resultados
        if hp_value is not None:
            # Com HP específico, geralmente temos poucos candidatos
            # Verifica cada um para confirmar
            for addr in candidates[:20]:
                try:
                    hp = self.pm.read_int(addr)
                    hp_max = self.pm.read_int(addr + self.OFFSET_HP_MAX)
                    mp = self.pm.read_int(addr + self.OFFSET_MP)
                    mp_max = self.pm.read_int(addr + self.OFFSET_MP_MAX)
                    
                    # Dupla verificação
                    if hp == hp_value:
                        if mp_value is None or mp == mp_value:
                            print(f"[AUTO] ✓ Encontrado!")
                            print(f"       HP: {hp}/{hp_max} @ {hex(addr)}")
                            print(f"       MP: {mp}/{mp_max} @ {hex(addr + self.OFFSET_MP)}")
                            
                            return {
                                "hp": addr,
                                "hp_max": addr + self.OFFSET_HP_MAX,
                                "mp": addr + self.OFFSET_MP,
                                "mp_max": addr + self.OFFSET_MP_MAX
                            }
                except:
                    continue
        else:
            # Sem valores específicos, usa método original
            for addr in candidates[:100]:
                if self._verify_candidate(addr, wait_time=0.5 if quick else 2.0):
                    hp = self.pm.read_int(addr)
                    hp_max = self.pm.read_int(addr + self.OFFSET_HP_MAX)
                    mp = self.pm.read_int(addr + self.OFFSET_MP)
                    mp_max = self.pm.read_int(addr + self.OFFSET_MP_MAX)
                    
                    print(f"[AUTO] ✓ Encontrado!")
                    print(f"       HP: {hp}/{hp_max} @ {hex(addr)}")
                    print(f"       MP: {mp}/{mp_max} @ {hex(addr + self.OFFSET_MP)}")
                    
                    return {
                        "hp": addr,
                        "hp_max": addr + self.OFFSET_HP_MAX,
                        "mp": addr + self.OFFSET_MP,
                        "mp_max": addr + self.OFFSET_MP_MAX
                    }
        
        print("[AUTO] Não foi possível encontrar endereços válidos")
        return None
    
    def save_offsets(self, offsets):
        """Salva offsets no cache"""
        try:
            data = {k: hex(v) for k, v in offsets.items()}
            # Salva também os offsets relativos
            data["offset_hp_max"] = self.OFFSET_HP_MAX
            data["offset_mp"] = self.OFFSET_MP
            data["offset_mp_max"] = self.OFFSET_MP_MAX
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[AUTO] Offsets salvos em {self.cache_file}")
            return True
        except Exception as e:
            print(f"[AUTO] Erro ao salvar: {e}")
            return False
    
    def load_cache(self):
        """
        Carrega offsets do cache.
        Retorna dict ou None se não existir/inválido.
        """
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            # Converte hex strings para int
            offsets = {}
            for key in ["hp", "hp_max", "mp", "mp_max"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, str):
                        offsets[key] = int(val, 16)
                    else:
                        offsets[key] = val
                else:
                    return None
            
            return offsets
        except Exception as e:
            print(f"[AUTO] Erro ao carregar cache: {e}")
            return None
    
    def validate_cache(self, offsets):
        """
        Verifica se os offsets do cache ainda são válidos.
        Retorna True se válido.
        """
        if not self.pm:
            if not self.connect():
                return False
        
        try:
            hp_addr = offsets["hp"]
            return self._validate_player_struct(hp_addr)
        except:
            return False
    
    def get_valid_offsets(self, hp_value=None, mp_value=None):
        """
        Retorna offsets válidos - do cache ou faz novo scan.
        
        Este é o método principal para uso em bots:
        1. Tenta carregar do cache
        2. Valida se ainda funciona
        3. Se não, faz novo scan
        
        Args:
            hp_value: HP atual (para scan preciso se necessário)
            mp_value: MP atual (para validação)
        
        Returns:
            dict com hp, hp_max, mp, mp_max ou None
        """
        # Tenta cache primeiro
        cached = self.load_cache()
        if cached:
            print("[AUTO] Cache encontrado, validando...")
            if self.validate_cache(cached):
                print("[AUTO] Cache válido!")
                return cached
            else:
                print("[AUTO] Cache inválido, fazendo novo scan...")
        
        # Faz novo scan
        return self.auto_find_and_save(hp_value, mp_value)
    
    def auto_find_and_save(self, hp_value=None, mp_value=None):
        """
        Encontra endereços automaticamente e salva no cache.
        
        Args:
            hp_value: Valor atual do HP (opcional, mas recomendado)
            mp_value: Valor atual do MP (opcional)
        """
        offsets = self.find_player_addresses(
            quick=True,
            hp_value=hp_value,
            mp_value=mp_value
        )
        
        if offsets:
            self.save_offsets(offsets)
            return offsets
        
        return None


def main():
    """Teste do auto scanner com modo interativo"""
    print("=" * 50)
    print("  AUTO SCANNER v2 - Tibia Memory")
    print("  Offsets: HP_MAX=+0x8, MP=+0x620, MP_MAX=+0x628")
    print("=" * 50)
    
    scanner = AutoScanner()
    
    if not scanner.connect():
        print("[ERRO] Não foi possível conectar ao Tibia")
        input("Pressione ENTER...")
        return
    
    print("\nModo de scan:")
    print("1. Automático (pode demorar e ter falsos positivos)")
    print("2. Interativo (você informa HP/MP atual)")
    
    choice = input("\nEscolha [1/2]: ").strip()
    
    hp_value = None
    mp_value = None
    
    if choice == "2":
        print("\n[INFO] Olhe seu HP/MP no jogo e informe:")
        try:
            hp_input = input("HP atual (ex: 3320): ").strip()
            hp_value = int(hp_input) if hp_input else None
            
            mp_input = input("MP atual (ex: 17710): ").strip()
            mp_value = int(mp_input) if mp_input else None
        except ValueError:
            print("[AVISO] Valores inválidos, usando modo automático")
    
    print()
    offsets = scanner.find_player_addresses(
        quick=True,
        hp_value=hp_value,
        mp_value=mp_value
    )
    
    if offsets:
        scanner.save_offsets(offsets)
        print()
        print("=" * 50)
        print("  ✓ SUCESSO!")
        print("=" * 50)
        print(f"  HP:     {hex(offsets['hp'])}")
        print(f"  HP_MAX: {hex(offsets['hp_max'])}")
        print(f"  MP:     {hex(offsets['mp'])}")
        print(f"  MP_MAX: {hex(offsets['mp_max'])}")
    else:
        print()
        print("[ERRO] Não foi possível encontrar os endereços")
        print("       Verifique se você está logado no jogo")
        if hp_value is None:
            print("       Tente usar o modo interativo (opção 2)")
    
    scanner.disconnect()
    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()
