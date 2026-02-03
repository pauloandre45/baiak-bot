# -*- coding: utf-8 -*-
"""
Scanner Avancado de Memoria para Tibia 15.11
Encontra automaticamente os offsets de HP, MP, etc
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
    print("[AVISO] pymem nao instalado. Execute: pip install pymem")


# Windows API constants
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
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


class AdvancedScanner:
    """
    Scanner avancado para encontrar valores na memoria do Tibia
    """
    
    def __init__(self, process_name="client.exe"):
        self.process_name = process_name
        self.pm = None
        self.pid = None
        self.handle = None
        
        # Cache de resultados
        self._scan_results = []
        self._found_offsets = {}
        
        # Arquivo de cache
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "offsets_cache.json")
    
    def connect(self):
        """
        Conecta ao processo do Tibia
        """
        if not PYMEM_AVAILABLE:
            print("[ERRO] pymem nao disponivel")
            return False
        
        try:
            self.pm = pymem.Pymem(self.process_name)
            self.pid = self.pm.process_id
            self.handle = self.pm.process_handle
            
            print(f"[SCANNER] Conectado ao Tibia!")
            print(f"          PID: {self.pid}")
            print(f"          Base: {hex(self.pm.base_address)}")
            
            return True
            
        except pymem.exception.ProcessNotFound:
            print(f"[ERRO] Processo '{self.process_name}' nao encontrado")
            return False
        except Exception as e:
            print(f"[ERRO] {e}")
            return False
    
    def disconnect(self):
        """
        Desconecta do processo
        """
        if self.pm:
            try:
                self.pm.close_process()
            except:
                pass
        self.pm = None
    
    def scan_all_memory(self, value, value_type="int4"):
        """
        Escaneia TODA a memoria do processo procurando um valor
        
        value_type: 
            "int4" = inteiro 4 bytes
            "int2" = inteiro 2 bytes
            "float" = float 4 bytes
        
        Retorna lista de enderecos
        """
        if not self.pm:
            print("[ERRO] Nao conectado")
            return []
        
        print(f"[SCAN] Procurando valor {value} (tipo: {value_type})...")
        
        results = []
        
        # Converte valor para bytes
        if value_type == "int4":
            search_bytes = struct.pack("<i", int(value))
        elif value_type == "int2":
            search_bytes = struct.pack("<h", int(value))
        elif value_type == "float":
            search_bytes = struct.pack("<f", float(value))
        else:
            print(f"[ERRO] Tipo desconhecido: {value_type}")
            return []
        
        # Enumera regioes de memoria
        address = 0
        mbi = MEMORY_BASIC_INFORMATION()
        mbi_size = ctypes.sizeof(mbi)
        
        VirtualQueryEx = ctypes.windll.kernel32.VirtualQueryEx
        ReadProcessMemory = ctypes.windll.kernel32.ReadProcessMemory
        
        regions_scanned = 0
        bytes_scanned = 0
        
        while True:
            # Consulta informacoes da regiao
            result = VirtualQueryEx(
                self.handle,
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                mbi_size
            )
            
            if result == 0:
                break
            
            # Pula para proxima regiao
            next_address = mbi.BaseAddress + mbi.RegionSize
            
            # Verifica se a regiao e valida para leitura
            if (mbi.State == MEM_COMMIT and 
                mbi.Protect in [PAGE_READWRITE, PAGE_READONLY, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE] and
                mbi.RegionSize < 100 * 1024 * 1024):  # Max 100MB por regiao
                
                try:
                    # Le a regiao de memoria
                    data = self.pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                    bytes_scanned += len(data)
                    regions_scanned += 1
                    
                    # Procura o valor
                    pos = 0
                    while True:
                        pos = data.find(search_bytes, pos)
                        if pos == -1:
                            break
                        
                        addr = mbi.BaseAddress + pos
                        results.append(addr)
                        pos += 1
                        
                except Exception:
                    pass
            
            address = next_address
            
            # Evita loop infinito
            if address > 0x7FFFFFFF:
                break
        
        print(f"[SCAN] Escaneados {regions_scanned} regioes, {bytes_scanned / 1024 / 1024:.1f} MB")
        print(f"[SCAN] Encontrados {len(results)} enderecos")
        
        self._scan_results = results
        return results
    
    def filter_changed(self, new_value, value_type="int4"):
        """
        Filtra resultados do scan anterior, mantendo apenas
        os que mudaram para o novo valor
        """
        if not self._scan_results:
            print("[ERRO] Faca um scan primeiro")
            return []
        
        print(f"[FILTER] Filtrando {len(self._scan_results)} enderecos para valor {new_value}...")
        
        results = []
        
        for addr in self._scan_results:
            try:
                if value_type == "int4":
                    current = self.pm.read_int(addr)
                elif value_type == "int2":
                    current = self.pm.read_short(addr)
                elif value_type == "float":
                    current = self.pm.read_float(addr)
                else:
                    continue
                
                if current == new_value:
                    results.append(addr)
                    
            except:
                pass
        
        print(f"[FILTER] Restaram {len(results)} enderecos")
        
        self._scan_results = results
        return results
    
    def filter_unchanged(self):
        """
        Filtra resultados, mantendo apenas os que NAO mudaram
        Util para encontrar valores maximos (HP Max, MP Max)
        """
        if not self._scan_results:
            print("[ERRO] Faca um scan primeiro")
            return []
        
        print(f"[FILTER] Filtrando enderecos inalterados...")
        
        # Salva valores atuais
        addr_values = {}
        for addr in self._scan_results:
            try:
                addr_values[addr] = self.pm.read_int(addr)
            except:
                pass
        
        print(f"[FILTER] Aguarde 2 segundos e NAO mude seu HP/MP...")
        time.sleep(2)
        
        # Verifica quais nao mudaram
        results = []
        for addr, old_value in addr_values.items():
            try:
                new_value = self.pm.read_int(addr)
                if new_value == old_value:
                    results.append(addr)
            except:
                pass
        
        print(f"[FILTER] Restaram {len(results)} enderecos")
        
        self._scan_results = results
        return results
    
    def monitor_addresses(self, count=10, duration=10):
        """
        Monitora os primeiros N enderecos encontrados
        """
        if not self._scan_results:
            print("[ERRO] Nenhum endereco para monitorar")
            return
        
        addresses = self._scan_results[:count]
        
        print(f"[MONITOR] Monitorando {len(addresses)} enderecos por {duration}s...")
        print(f"          Faca algo que mude HP/MP para identificar o correto")
        print()
        
        # Valores iniciais
        last_values = {}
        for addr in addresses:
            try:
                last_values[addr] = self.pm.read_int(addr)
            except:
                last_values[addr] = 0
        
        start = time.time()
        
        while time.time() - start < duration:
            for addr in addresses:
                try:
                    value = self.pm.read_int(addr)
                    if value != last_values[addr]:
                        print(f"  {hex(addr)}: {last_values[addr]} -> {value}")
                        last_values[addr] = value
                except:
                    pass
            
            time.sleep(0.1)
        
        print()
        print("[MONITOR] Fim")
    
    def mark_as_hp(self, address):
        """
        Marca um endereco como sendo o HP
        """
        self._found_offsets["hp"] = address
        print(f"[OK] HP marcado: {hex(address)}")
        self._save_cache()
    
    def mark_as_hp_max(self, address):
        """
        Marca um endereco como sendo o HP Max
        """
        self._found_offsets["hp_max"] = address
        print(f"[OK] HP Max marcado: {hex(address)}")
        self._save_cache()
    
    def mark_as_mp(self, address):
        """
        Marca um endereco como sendo o MP
        """
        self._found_offsets["mp"] = address
        print(f"[OK] MP marcado: {hex(address)}")
        self._save_cache()
    
    def mark_as_mp_max(self, address):
        """
        Marca um endereco como sendo o MP Max
        """
        self._found_offsets["mp_max"] = address
        print(f"[OK] MP Max marcado: {hex(address)}")
        self._save_cache()
    
    def _save_cache(self):
        """
        Salva offsets encontrados em arquivo
        """
        try:
            with open(self.cache_file, 'w') as f:
                # Converte addresses para string hex
                data = {k: hex(v) for k, v in self._found_offsets.items()}
                json.dump(data, f, indent=2)
            print(f"[CACHE] Salvo em {self.cache_file}")
        except Exception as e:
            print(f"[ERRO] Falha ao salvar cache: {e}")
    
    def load_cache(self):
        """
        Carrega offsets do cache
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    # Converte hex strings para int
                    self._found_offsets = {k: int(v, 16) for k, v in data.items()}
                print(f"[CACHE] Carregado: {self._found_offsets}")
                return True
        except Exception as e:
            print(f"[ERRO] Falha ao carregar cache: {e}")
        return False
    
    def get_offsets(self):
        """
        Retorna offsets encontrados
        """
        return self._found_offsets.copy()
    
    def test_offsets(self, duration=5):
        """
        Testa se os offsets salvos estao funcionando
        """
        if not self._found_offsets:
            print("[ERRO] Nenhum offset encontrado. Execute o wizard primeiro.")
            return False
        
        print(f"[TEST] Testando offsets por {duration}s...")
        print()
        
        start = time.time()
        
        while time.time() - start < duration:
            line = ""
            
            if "hp" in self._found_offsets:
                try:
                    hp = self.pm.read_int(self._found_offsets["hp"])
                    line += f"HP: {hp}"
                except:
                    line += "HP: ERRO"
            
            if "hp_max" in self._found_offsets:
                try:
                    hp_max = self.pm.read_int(self._found_offsets["hp_max"])
                    line += f"/{hp_max}"
                except:
                    line += "/ERRO"
            
            if "mp" in self._found_offsets:
                try:
                    mp = self.pm.read_int(self._found_offsets["mp"])
                    line += f"  |  MP: {mp}"
                except:
                    line += "  |  MP: ERRO"
            
            if "mp_max" in self._found_offsets:
                try:
                    mp_max = self.pm.read_int(self._found_offsets["mp_max"])
                    line += f"/{mp_max}"
                except:
                    line += "/ERRO"
            
            print(f"\r{line}          ", end="", flush=True)
            time.sleep(0.2)
        
        print()
        print()
        print("[TEST] Fim do teste")
        return True


def run_wizard():
    """
    Wizard interativo para encontrar offsets
    """
    print("=" * 60)
    print("  WIZARD DE BUSCA DE OFFSETS - Tibia 15.11")
    print("=" * 60)
    print()
    print("Este wizard vai ajudar a encontrar os enderecos de memoria")
    print("do HP e MP do seu personagem.")
    print()
    print("IMPORTANTE: Tenha o Tibia aberto e logado no jogo!")
    print()
    
    input("Pressione ENTER para continuar...")
    print()
    
    # Conecta ao Tibia
    scanner = AdvancedScanner()
    
    if not scanner.connect():
        print()
        print("ERRO: Nao foi possivel conectar ao Tibia.")
        print("Verifique se o jogo esta aberto e tente novamente.")
        return None
    
    print()
    print("-" * 60)
    print("PASSO 1: Encontrar HP")
    print("-" * 60)
    print()
    
    hp_atual = input("Digite seu HP ATUAL (ex: 1500): ").strip()
    
    if not hp_atual.isdigit():
        print("HP invalido!")
        return None
    
    hp_atual = int(hp_atual)
    
    print()
    print("Escaneando memoria...")
    scanner.scan_all_memory(hp_atual)
    
    if len(scanner._scan_results) == 0:
        print("Nenhum endereco encontrado. Verifique se o HP esta correto.")
        return None
    
    print()
    print("Agora, LEVE UM POUCO DE DANO no jogo (ataque um monstro)")
    print("e digite seu NOVO HP:")
    print()
    
    hp_novo = input("Digite seu HP NOVO (apos levar dano): ").strip()
    
    if not hp_novo.isdigit():
        print("HP invalido!")
        return None
    
    hp_novo = int(hp_novo)
    
    print()
    scanner.filter_changed(hp_novo)
    
    if len(scanner._scan_results) == 0:
        print("Nenhum endereco encontrado apos filtro.")
        return None
    
    if len(scanner._scan_results) > 10:
        print()
        print("Ainda temos muitos enderecos. Leve mais dano e digite o novo HP:")
        
        hp_novo2 = input("HP NOVO: ").strip()
        
        if hp_novo2.isdigit():
            scanner.filter_changed(int(hp_novo2))
    
    if len(scanner._scan_results) <= 20:
        print()
        print("Monitorando enderecos... Leve dano ou cure para ver qual muda:")
        scanner.monitor_addresses(count=10, duration=10)
        
        print()
        addr_str = input("Digite o endereco correto de HP (ex: 0x12345678): ").strip()
        
        if addr_str:
            try:
                addr = int(addr_str, 16)
                scanner.mark_as_hp(addr)
            except:
                print("Endereco invalido")
    
    # HP Max
    print()
    print("-" * 60)
    print("PASSO 2: Encontrar HP Max")
    print("-" * 60)
    print()
    
    hp_max = input("Digite seu HP MAXIMO (ex: 2000): ").strip()
    
    if hp_max.isdigit():
        hp_max = int(hp_max)
        scanner.scan_all_memory(hp_max)
        scanner.filter_unchanged()
        
        if len(scanner._scan_results) > 0 and len(scanner._scan_results) <= 50:
            print()
            print("Enderecos possiveis para HP Max:")
            for addr in scanner._scan_results[:10]:
                print(f"  {hex(addr)}")
            
            print()
            addr_str = input("Digite o endereco de HP Max (ou ENTER para pular): ").strip()
            
            if addr_str:
                try:
                    addr = int(addr_str, 16)
                    scanner.mark_as_hp_max(addr)
                except:
                    pass
    
    # MP
    print()
    print("-" * 60)
    print("PASSO 3: Encontrar MP")
    print("-" * 60)
    print()
    
    mp_atual = input("Digite seu MP ATUAL: ").strip()
    
    if mp_atual.isdigit():
        mp_atual = int(mp_atual)
        scanner.scan_all_memory(mp_atual)
        
        print()
        print("Use uma spell ou potion de mana e digite o NOVO MP:")
        
        mp_novo = input("MP NOVO: ").strip()
        
        if mp_novo.isdigit():
            scanner.filter_changed(int(mp_novo))
            
            if len(scanner._scan_results) <= 20:
                scanner.monitor_addresses(count=10, duration=10)
                
                print()
                addr_str = input("Digite o endereco correto de MP: ").strip()
                
                if addr_str:
                    try:
                        addr = int(addr_str, 16)
                        scanner.mark_as_mp(addr)
                    except:
                        pass
    
    # MP Max
    print()
    print("-" * 60)
    print("PASSO 4: Encontrar MP Max")
    print("-" * 60)
    print()
    
    mp_max = input("Digite seu MP MAXIMO (ou ENTER para pular): ").strip()
    
    if mp_max.isdigit():
        mp_max = int(mp_max)
        scanner.scan_all_memory(mp_max)
        scanner.filter_unchanged()
        
        if len(scanner._scan_results) > 0 and len(scanner._scan_results) <= 50:
            for addr in scanner._scan_results[:10]:
                print(f"  {hex(addr)}")
            
            addr_str = input("Digite o endereco de MP Max: ").strip()
            
            if addr_str:
                try:
                    addr = int(addr_str, 16)
                    scanner.mark_as_mp_max(addr)
                except:
                    pass
    
    # Teste final
    print()
    print("-" * 60)
    print("TESTE FINAL")
    print("-" * 60)
    print()
    
    scanner.test_offsets(duration=10)
    
    print()
    print("=" * 60)
    print("  WIZARD CONCLUIDO!")
    print("=" * 60)
    print()
    print("Offsets salvos em:", scanner.cache_file)
    print("Offsets encontrados:", scanner.get_offsets())
    print()
    
    return scanner.get_offsets()


if __name__ == "__main__":
    run_wizard()
