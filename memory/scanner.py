# -*- coding: utf-8 -*-
"""
Scanner de memoria para encontrar offsets
Utilitario para descobrir enderecos de memoria no Tibia 15.11
"""

import time

try:
    import pymem
    import pymem.process
    import pymem.pattern
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False


class MemoryScanner:
    """
    Classe para escanear memoria e encontrar offsets
    Util para desenvolvimento e atualizacao de offsets
    """
    
    def __init__(self, pm):
        """
        pm: instancia de pymem.Pymem conectada ao processo
        """
        self.pm = pm
    
    def scan_for_value(self, value, value_type="int"):
        """
        Escaneia a memoria procurando por um valor especifico
        
        value: valor a procurar
        value_type: "int", "float", "string"
        
        Retorna: lista de enderecos encontrados
        """
        if not PYMEM_AVAILABLE:
            return []
            
        results = []
        
        try:
            # Pega lista de modulos do processo
            modules = list(self.pm.list_modules())
            
            for module in modules:
                module_name = module.name.lower()
                
                # Foca apenas no modulo principal do Tibia
                if "client" not in module_name and "tibia" not in module_name:
                    continue
                
                print(f"[SCAN] Escaneando modulo: {module.name}")
                print(f"       Base: {hex(module.lpBaseOfDll)}")
                print(f"       Size: {module.SizeOfImage}")
                
                # Escaneia o modulo
                base = module.lpBaseOfDll
                size = module.SizeOfImage
                
                # Le toda a memoria do modulo
                try:
                    data = self.pm.read_bytes(base, size)
                except:
                    continue
                
                # Procura o valor
                if value_type == "int":
                    # Converte valor para bytes (little endian)
                    value_bytes = value.to_bytes(4, byteorder='little', signed=True)
                    
                    # Procura todas as ocorrencias
                    pos = 0
                    while True:
                        pos = data.find(value_bytes, pos)
                        if pos == -1:
                            break
                        results.append(base + pos)
                        pos += 1
                        
        except Exception as e:
            print(f"[ERRO] Falha no scan: {e}")
        
        return results
    
    def filter_by_change(self, addresses, old_value, new_value):
        """
        Filtra enderecos que mudaram de old_value para new_value
        Util para encontrar o endereco correto de HP/MP
        
        1. HP estava em 1000 -> addresses com valor 1000
        2. Leva dano, HP vai para 950
        3. filter_by_change filtra apenas addresses que mudaram para 950
        """
        if not PYMEM_AVAILABLE:
            return []
            
        results = []
        
        for addr in addresses:
            try:
                current = self.pm.read_int(addr)
                if current == new_value:
                    results.append(addr)
            except:
                pass
        
        return results
    
    def monitor_address(self, address, duration=10):
        """
        Monitora um endereco por X segundos e mostra as mudancas
        Util para verificar se encontramos o endereco correto
        """
        if not PYMEM_AVAILABLE:
            return
            
        print(f"[MONITOR] Monitorando {hex(address)} por {duration}s...")
        
        start_time = time.time()
        last_value = None
        
        while time.time() - start_time < duration:
            try:
                value = self.pm.read_int(address)
                if value != last_value:
                    print(f"  [{time.time()-start_time:.1f}s] Valor: {value}")
                    last_value = value
            except:
                print(f"  [ERRO] Nao foi possivel ler endereco")
                break
            time.sleep(0.1)
        
        print("[MONITOR] Fim do monitoramento")
    
    def find_hp_address(self, known_hp, known_hp_max):
        """
        Tenta encontrar o endereco de HP do player
        
        Uso:
        1. Verifique seu HP atual no jogo (ex: 1500/2000)
        2. Chame: scanner.find_hp_address(1500, 2000)
        3. Leve um pouco de dano
        4. Chame novamente com o novo HP
        5. Repita ate encontrar o endereco correto
        """
        print(f"[HP SCAN] Procurando HP = {known_hp}")
        
        hp_addresses = self.scan_for_value(known_hp, "int")
        print(f"[HP SCAN] Encontrados {len(hp_addresses)} enderecos possiveis")
        
        if len(hp_addresses) < 100:
            for addr in hp_addresses[:20]:
                print(f"  {hex(addr)}")
        
        return hp_addresses
