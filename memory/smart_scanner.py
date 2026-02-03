# -*- coding: utf-8 -*-
"""
Smart Scanner V3 - Encontra HP/MP automaticamente sem input do usuário

Estratégia:
1. Procura estruturas onde HP == HP_MAX (vida cheia)
2. Verifica se MP está em range válido (não 0, não potência de 2)
3. Verifica campo de level no offset +0x14
4. Aplica scoring para ranquear o melhor candidato
"""

import ctypes
from ctypes import wintypes
import struct
import time
import json
import os

try:
    import pymem
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False

MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('BaseAddress', ctypes.c_void_p),
        ('AllocationBase', ctypes.c_void_p),
        ('AllocationProtect', wintypes.DWORD),
        ('RegionSize', ctypes.c_size_t),
        ('State', wintypes.DWORD),
        ('Protect', wintypes.DWORD),
        ('Type', wintypes.DWORD),
    ]


class SmartScanner:
    """
    Scanner inteligente V3 que encontra HP/MP sem precisar de input do usuário.
    
    Funciona procurando por estruturas válidas de player onde:
    - HP == HP_MAX (vida cheia) - comum quando abre o bot
    - MP > 0 e em range válido (não potência de 2)
    - Level no offset +0x14 entre 1-2000 e diferente de HP
    - Offsets conhecidos: HP_MAX = +0x8, MP = +0x620, MP_MAX = +0x628
    """
    
    # Offsets confirmados para Tibia 15.11 BaiakZika
    OFFSET_HP_MAX = 0x8
    OFFSET_MP = 0x620
    OFFSET_MP_MAX = 0x628
    OFFSET_LEVEL = 0x14  # Possível offset do level
    
    # Valores suspeitos de MP_MAX (potências de 2 = buffers, não mana real)
    SUSPICIOUS_MP_VALUES = {256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 65792}
    
    def __init__(self, process_name="client.exe"):
        self.process_name = process_name
        self.pm = None
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "offsets_cache.json")
    
    def connect(self):
        if not PYMEM_AVAILABLE:
            return False
        try:
            self.pm = pymem.Pymem(self.process_name)
            return True
        except:
            return False
    
    def disconnect(self):
        if self.pm:
            try:
                self.pm.close_process()
            except:
                pass
        self.pm = None
    
    def _get_heap_regions(self):
        """Obtém regiões de heap (onde ficam os dados do player)"""
        regions = []
        address = 0
        mbi = MEMORY_BASIC_INFORMATION()
        
        while address < 0x7FFFFFFFFFFF:
            result = ctypes.windll.kernel32.VirtualQueryEx(
                self.pm.process_handle,
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                ctypes.sizeof(mbi)
            )
            
            if result == 0:
                break
            
            base = mbi.BaseAddress
            size = mbi.RegionSize
            
            if base and size:
                # Filtra para heap: endereços altos, tamanho razoável, read/write
                if base >= 0x100000000:  # Acima de 4GB = heap
                    if mbi.State == MEM_COMMIT and mbi.Protect == PAGE_READWRITE:
                        if 0x10000 <= size <= 50 * 1024 * 1024:
                            regions.append((base, size))
            
            address = (base or 0) + (size or 0x10000)
        
        return regions
    
    def _score_candidate(self, c):
        """
        Calcula score para ranquear candidatos.
        Quanto maior o score, mais provável de ser o player real.
        """
        score = 0
        
        # Bonus se MP_MAX > HP_MAX (comum em mages)
        if c['mp_max'] > c['hp_max']:
            score += 1000
        
        # Bonus se HP_MAX > level * 5 (HP cresce mais que level)
        if c['hp_max'] > c['level'] * 5:
            score += 500
        
        # Bonus para HPs médios (nem muito baixo nem muito alto)
        if 1000 <= c['hp_max'] <= 10000:
            score += 300
        
        # Bonus se MP está parcialmente cheio (não exatamente no máximo)
        if c['mp'] < c['mp_max']:
            score += 200
        
        return score
    
    def find_player_auto(self, progress_callback=None):
        """
        Encontra o player automaticamente procurando por HP == HP_MAX.
        
        Args:
            progress_callback: função(percent, message) para reportar progresso
        
        Returns:
            dict com addr, hp, hp_max, mp, mp_max ou None
        """
        if not self.pm:
            if not self.connect():
                return None
        
        def report(pct, msg):
            if progress_callback:
                progress_callback(pct, msg)
            else:
                print(f"[SMART] {msg}")
        
        report(0, "Iniciando busca automática...")
        start = time.time()
        
        regions = self._get_heap_regions()
        report(5, f"{len(regions)} regiões de heap para escanear")
        
        candidates = []
        total = len(regions)
        
        for i, (base, size) in enumerate(regions):
            if total > 0:
                pct = 5 + int(85 * i / total)
                if i % 50 == 0:
                    report(pct, f"Escaneando região {i}/{total}...")
            
            try:
                data = self.pm.read_bytes(base, size)
                
                # Procura estruturas válidas (alinhado em 8 bytes)
                for offset in range(0, len(data) - self.OFFSET_MP_MAX - 4, 8):
                    # Criterio 1: HP no range válido (150-30000)
                    hp = struct.unpack_from('<i', data, offset)[0]
                    if not (150 <= hp <= 30000):
                        continue
                    
                    # Criterio 2: HP == HP_MAX (vida cheia)
                    hp_max = struct.unpack_from('<i', data, offset + self.OFFSET_HP_MAX)[0]
                    if hp != hp_max:
                        continue
                    
                    # Criterio 3: MP válido
                    mp = struct.unpack_from('<i', data, offset + self.OFFSET_MP)[0]
                    mp_max = struct.unpack_from('<i', data, offset + self.OFFSET_MP_MAX)[0]
                    
                    # MP_MAX deve ser diferente de HP_MAX
                    if mp_max == hp_max:
                        continue
                    
                    # MP_MAX deve estar no range válido
                    if not (100 <= mp_max <= 100000):
                        continue
                    
                    # MP deve ser > 0 (player com mana)
                    if not (1 <= mp <= mp_max):
                        continue
                    
                    # MP_MAX não deve ser potência de 2 (valores suspeitos de buffer)
                    if mp_max in self.SUSPICIOUS_MP_VALUES:
                        continue
                    
                    # Criterio 4: Level válido
                    level = struct.unpack_from('<i', data, offset + self.OFFSET_LEVEL)[0]
                    
                    # Level deve ser diferente de HP (senão pode ser falso positivo)
                    if level == hp:
                        continue
                    
                    # Level deve estar no range 1-2000
                    if not (1 <= level <= 2000):
                        continue
                    
                    addr = base + offset
                    candidates.append({
                        'addr': addr,
                        'hp': hp,
                        'hp_max': hp_max,
                        'mp': mp,
                        'mp_max': mp_max,
                        'level': level
                    })
            except Exception:
                continue
        
        elapsed = time.time() - start
        report(95, f"{len(candidates)} candidatos encontrados em {elapsed:.1f}s")
        
        if not candidates:
            report(100, "Nenhum player encontrado")
            return None
        
        # Remover duplicatas
        seen = set()
        unique = []
        for c in candidates:
            key = (c['hp'], c['hp_max'], c['mp'], c['mp_max'], c['level'])
            if key not in seen:
                seen.add(key)
                unique.append(c)
        
        # Ordenar por score
        unique.sort(key=self._score_candidate, reverse=True)
        
        best = unique[0]
        report(100, f"Player encontrado: HP={best['hp']}/{best['hp_max']}, MP={best['mp']}/{best['mp_max']}")
        
        return best
    
    def validate_address(self, addr):
        """
        Valida se um endereço ainda contém dados válidos de HP/MP.
        Usado para verificar cache.
        
        Returns:
            dict com hp, hp_max, mp, mp_max se válido, None caso contrário
        """
        if not self.pm:
            if not self.connect():
                return None
        
        try:
            hp = self.pm.read_int(addr)
            hp_max = self.pm.read_int(addr + self.OFFSET_HP_MAX)
            mp = self.pm.read_int(addr + self.OFFSET_MP)
            mp_max = self.pm.read_int(addr + self.OFFSET_MP_MAX)
            
            # Validações básicas
            if not (1 <= hp <= hp_max <= 50000):
                return None
            if not (0 <= mp <= mp_max <= 200000):
                return None
            
            return {
                'addr': addr,
                'hp': hp,
                'hp_max': hp_max,
                'mp': mp,
                'mp_max': mp_max
            }
        except:
            return None
    
    def load_from_cache(self):
        """
        Tenta carregar endereço do cache e valida.
        
        Returns:
            dict com dados do player se cache válido, None caso contrário
        """
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            addr = cache.get('hp_addr')
            if not addr:
                return None
            
            # Valida se ainda funciona
            result = self.validate_address(addr)
            if result:
                print(f"[CACHE] Endereço válido: HP={result['hp']}/{result['hp_max']}")
                return result
            else:
                print("[CACHE] Endereço inválido, precisa re-escanear")
                return None
        except:
            return None
    
    def save_to_cache(self, addr):
        """Salva endereço no cache"""
        try:
            cache = {}
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
            
            cache['hp_addr'] = addr
            cache['last_scan'] = time.time()
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
        except:
            pass
    
    def find_player(self, progress_callback=None):
        """
        Método principal: tenta cache primeiro, depois faz scan automático.
        
        Returns:
            dict com addr, hp, hp_max, mp, mp_max ou None
        """
        # Tenta cache primeiro
        cached = self.load_from_cache()
        if cached:
            return cached
        
        # Faz scan automático
        result = self.find_player_auto(progress_callback)
        
        if result:
            # Salva no cache
            self.save_to_cache(result['addr'])
        
        return result


# Função helper para uso direto
def auto_find_player(process_name="client.exe"):
    """
    Helper function para encontrar o player automaticamente.
    
    Returns:
        dict com addr, hp, hp_max, mp, mp_max ou None
    """
    scanner = SmartScanner(process_name)
    return scanner.find_player()


if __name__ == '__main__':
    # Teste
    scanner = SmartScanner()
    if scanner.connect():
        result = scanner.find_player()
        if result:
            print(f"\n=== RESULTADO ===")
            print(f"Endereço: {hex(result['addr'])}")
            print(f"HP: {result['hp']}/{result['hp_max']}")
            print(f"MP: {result['mp']}/{result['mp_max']}")
        else:
            print("Player não encontrado!")
        scanner.disconnect()
    else:
        print("Não foi possível conectar ao client.exe")
