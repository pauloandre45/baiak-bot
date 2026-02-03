# -*- coding: utf-8 -*-
"""
Memory Reader para Tibia 15.11
Le HP, MP e outros dados diretamente da memoria do cliente

Este reader usa enderecos ABSOLUTOS encontrados pelo scanner.
Os enderecos podem mudar a cada reinicio do jogo!
"""

import json
import os
import time

try:
    import pymem
    import pymem.process
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False
    print("[AVISO] pymem nao instalado. Execute: pip install pymem")

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class TibiaMemoryReader:
    """
    Le dados da memoria do cliente Tibia 15.11
    
    IMPORTANTE: Os enderecos de memoria sao ABSOLUTOS e podem
    mudar toda vez que o jogo reinicia. Use o scanner para
    encontrar os enderecos novos.
    """
    
    def __init__(self, process_name="client.exe"):
        self.process_name = process_name
        self.pm = None
        self.connected = False
        self.pid = None
        self.base_address = None
        
        # Enderecos absolutos (encontrados pelo scanner)
        self._addresses = {
            "hp": None,
            "hp_max": None,
            "mp": None,
            "mp_max": None,
            "name": None,
            "level": None,
        }
        
        # Cache para reduzir leituras
        self._cache = {
            "hp": 0,
            "hp_max": 100,
            "mp": 0,
            "mp_max": 100,
            "name": "",
            "level": 1,
            "last_update": 0
        }
        
        self._cache_interval = 0.030  # 30ms - bem rapido
        
        # Arquivo de cache de offsets
        self._offsets_file = os.path.join(os.path.dirname(__file__), "..", "offsets_cache.json")
    
    def find_tibia_window(self):
        """
        Encontra a janela do Tibia e retorna (hwnd, titulo)
        """
        if not WIN32_AVAILABLE:
            return None, None
        
        result = [None, None]
        
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Tibia" in title and "Bot" not in title:
                    result[0] = hwnd
                    result[1] = title
                    return False
            return True
        
        try:
            win32gui.EnumWindows(callback, None)
        except:
            pass
        
        return result[0], result[1]
    
    def connect(self):
        """
        Conecta ao processo do Tibia
        """
        if not PYMEM_AVAILABLE:
            print("[ERRO] pymem nao disponivel")
            return False
        
        try:
            # Tenta encontrar o processo
            self.pm = pymem.Pymem(self.process_name)
            self.pid = self.pm.process_id
            self.base_address = self.pm.base_address
            self.connected = True
            
            print(f"[MEMORY] Conectado ao Tibia!")
            print(f"         PID: {self.pid}")
            print(f"         Base: {hex(self.base_address)}")
            
            # Tenta carregar offsets salvos
            self._load_offsets()
            
            # Verifica se os offsets são válidos
            if not self._verify_offsets():
                print("[MEMORY] Offsets inválidos, executando auto-scanner...")
                self._auto_find_offsets()
            
            return True
            
        except pymem.exception.ProcessNotFound:
            print(f"[ERRO] Processo '{self.process_name}' nao encontrado")
            print("       Verifique se o Tibia esta aberto")
            return False
        except Exception as e:
            print(f"[ERRO] Falha ao conectar: {e}")
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
        self.connected = False
        print("[MEMORY] Desconectado")
    
    def is_connected(self):
        """
        Verifica se ainda esta conectado
        """
        if not self.connected or not self.pm:
            return False
        
        try:
            # Tenta ler um byte para verificar
            self.pm.read_bytes(self.base_address, 1)
            return True
        except:
            self.connected = False
            return False
    
    def _load_offsets(self):
        """
        Carrega enderecos do arquivo de cache
        Suporta formato antigo (hp, hp_max, mp, mp_max) e novo (hp_addr)
        """
        # Offsets conhecidos do Tibia 15.11 BaiakZika
        OFFSET_HP_MAX = 0x8
        OFFSET_MP = 0x620
        OFFSET_MP_MAX = 0x628
        
        try:
            if os.path.exists(self._offsets_file):
                with open(self._offsets_file, 'r') as f:
                    data = json.load(f)
                
                # Novo formato (Smart Scanner V3): hp_addr
                if "hp_addr" in data:
                    hp_addr = data["hp_addr"]
                    if isinstance(hp_addr, str):
                        hp_addr = int(hp_addr, 16)
                    
                    self._addresses["hp"] = hp_addr
                    self._addresses["hp_max"] = hp_addr + OFFSET_HP_MAX
                    self._addresses["mp"] = hp_addr + OFFSET_MP
                    self._addresses["mp_max"] = hp_addr + OFFSET_MP_MAX
                    
                    print(f"[MEMORY] Offsets carregados (V3):")
                    print(f"         HP: {hex(hp_addr)}")
                    return True
                
                # Formato antigo: hp, hp_max, mp, mp_max separados
                for key, value in data.items():
                    if key in self._addresses:
                        self._addresses[key] = int(value, 16) if isinstance(value, str) else value
                
                if self._addresses["hp"]:
                    print(f"[MEMORY] Offsets carregados:")
                    for k, v in self._addresses.items():
                        if v:
                            print(f"         {k}: {hex(v)}")
                    return True
                
        except Exception as e:
            print(f"[AVISO] Nao foi possivel carregar offsets: {e}")
        
        return False
    
    def _verify_offsets(self):
        """
        Verifica se os offsets salvos ainda são válidos
        """
        if not self._addresses["hp"] or not self._addresses["hp_max"]:
            return False
        
        try:
            hp = self.pm.read_int(self._addresses["hp"])
            hp_max = self.pm.read_int(self._addresses["hp_max"])
            
            # Verifica se os valores fazem sentido
            if hp <= 0 or hp_max <= 0:
                return False
            if hp > hp_max:
                return False
            if hp_max > 1000000:  # Valor muito alto
                return False
            
            print(f"[MEMORY] Offsets validados: HP={hp}/{hp_max}")
            return True
            
        except Exception as e:
            print(f"[MEMORY] Offsets inválidos: {e}")
            return False
    
    def _auto_find_offsets(self, hp_value=None, mp_value=None):
        """
        Usa o Smart Scanner V3 para encontrar os offsets automaticamente.
        
        Ordem de prioridade:
        1. Smart Scanner V3 (totalmente automático, ~15s)
        2. Pattern Scanner (fallback se V3 falhar)
        
        Args:
            hp_value: Não usado (V3 é automático)
            mp_value: Não usado (V3 é automático)
        """
        # Tenta Smart Scanner V3 primeiro (totalmente automático)
        try:
            from memory.smart_scanner import SmartScanner
            
            scanner = SmartScanner(self.process_name)
            scanner.pm = self.pm  # Reutiliza a conexão
            
            print("[MEMORY] Tentando Smart Scanner V3 (automático)...")
            result = scanner.find_player_auto()
            
            if result:
                self._addresses["hp"] = result["addr"]
                self._addresses["hp_max"] = result["addr"] + scanner.OFFSET_HP_MAX
                self._addresses["mp"] = result["addr"] + scanner.OFFSET_MP
                self._addresses["mp_max"] = result["addr"] + scanner.OFFSET_MP_MAX
                
                # Salva no cache
                self._save_offsets()
                
                print(f"[MEMORY] ✓ Player encontrado automaticamente!")
                print(f"         HP={result['hp']}/{result['hp_max']}, MP={result['mp']}/{result['mp_max']}")
                return True
                
        except Exception as e:
            print(f"[MEMORY] Smart Scanner V3 falhou: {e}")
        
        # Fallback para Pattern Scanner
        try:
            from memory.pattern_scanner import PatternScanner
            
            scanner = PatternScanner(self.process_name)
            scanner.pm = self.pm  # Reutiliza a conexão
            
            print("[MEMORY] Tentando Pattern Scanner...")
            offsets = scanner.auto_find(hp_value, mp_value)
            
            if offsets:
                self._addresses["hp"] = offsets["hp"]
                self._addresses["hp_max"] = offsets["hp_max"]
                self._addresses["mp"] = offsets["mp"]
                self._addresses["mp_max"] = offsets["mp_max"]
                
                print("[MEMORY] ✓ Offsets encontrados via Pattern Scanner!")
                return True
                
        except Exception as e:
            print(f"[MEMORY] Pattern Scanner falhou: {e}")
        
        print("[MEMORY] ✗ Não foi possível encontrar offsets automaticamente")
        return False
    
    def _save_offsets(self):
        """Salva os endereços encontrados no cache"""
        try:
            data = {
                "hp_addr": self._addresses["hp"],
                "last_scan": time.time()
            }
            with open(self._offsets_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
    
    def set_address(self, key, address):
        """
        Define um endereco manualmente
        
        key: "hp", "hp_max", "mp", "mp_max", "name", "level"
        address: endereco absoluto (int)
        """
        if key in self._addresses:
            self._addresses[key] = address
            print(f"[MEMORY] {key} = {hex(address)}")
    
    def scan_with_values(self, hp_value, mp_value=None):
        """
        Faz um scan precisão usando os valores atuais do jogador.
        
        Use este método quando o scan automático falhar.
        Olhe seu HP/MP no jogo e passe os valores.
        
        Args:
            hp_value: HP atual do personagem
            mp_value: MP atual do personagem (opcional)
        
        Returns:
            True se encontrou, False caso contrário
        """
        if not self.connected:
            print("[MEMORY] Não está conectado!")
            return False
        
        return self._auto_find_offsets(hp_value, mp_value)
    
    def has_offsets(self):
        """
        Verifica se os offsets essenciais estao configurados
        """
        return self._addresses["hp"] is not None and self._addresses["hp_max"] is not None
    
    def _update_cache(self):
        """
        Atualiza o cache de valores
        """
        now = time.time()
        
        if now - self._cache["last_update"] < self._cache_interval:
            return
        
        self._cache["last_update"] = now
        
        if not self.connected:
            return
        
        # Le HP
        if self._addresses["hp"]:
            try:
                self._cache["hp"] = self.pm.read_int(self._addresses["hp"])
            except:
                pass
        
        # Le HP Max
        if self._addresses["hp_max"]:
            try:
                self._cache["hp_max"] = self.pm.read_int(self._addresses["hp_max"])
            except:
                pass
        
        # Le MP
        if self._addresses["mp"]:
            try:
                self._cache["mp"] = self.pm.read_int(self._addresses["mp"])
            except:
                pass
        
        # Le MP Max
        if self._addresses["mp_max"]:
            try:
                self._cache["mp_max"] = self.pm.read_int(self._addresses["mp_max"])
            except:
                pass
    
    # ============================================
    # GETTERS
    # ============================================
    
    def get_player_hp(self):
        """
        Retorna HP atual
        """
        self._update_cache()
        return self._cache["hp"]
    
    def get_player_hp_max(self):
        """
        Retorna HP maximo
        """
        self._update_cache()
        return self._cache["hp_max"]
    
    def get_player_hp_percent(self):
        """
        Retorna HP em porcentagem (0-100)
        """
        self._update_cache()
        
        hp = self._cache["hp"]
        hp_max = self._cache["hp_max"]
        
        if hp_max <= 0:
            return 100
        
        percent = int((hp / hp_max) * 100)
        return max(0, min(100, percent))
    
    def get_player_mp(self):
        """
        Retorna MP atual
        """
        self._update_cache()
        return self._cache["mp"]
    
    def get_player_mp_max(self):
        """
        Retorna MP maximo
        """
        self._update_cache()
        return self._cache["mp_max"]
    
    def get_player_mp_percent(self):
        """
        Retorna MP em porcentagem (0-100)
        """
        self._update_cache()
        
        mp = self._cache["mp"]
        mp_max = self._cache["mp_max"]
        
        if mp_max <= 0:
            return 100
        
        percent = int((mp / mp_max) * 100)
        return max(0, min(100, percent))
    
    def get_player_name(self):
        """
        Retorna nome do jogador
        """
        return self._cache["name"]
    
    def get_player_level(self):
        """
        Retorna level do jogador
        """
        return self._cache["level"]


# Teste rapido
if __name__ == "__main__":
    print("Teste do Memory Reader")
    print()
    
    reader = TibiaMemoryReader()
    
    if reader.connect():
        print()
        
        if reader.has_offsets():
            print("Lendo valores por 10 segundos...")
            print()
            
            for i in range(50):
                hp = reader.get_player_hp()
                hp_max = reader.get_player_hp_max()
                hp_pct = reader.get_player_hp_percent()
                mp = reader.get_player_mp()
                mp_max = reader.get_player_mp_max()
                mp_pct = reader.get_player_mp_percent()
                
                print(f"\rHP: {hp}/{hp_max} ({hp_pct}%)  |  MP: {mp}/{mp_max} ({mp_pct}%)     ", end="")
                
                time.sleep(0.2)
            
            print()
        else:
            print()
            print("OFFSETS NAO CONFIGURADOS!")
            print()
            print("Execute o scanner primeiro:")
            print("  python -m memory.scanner_advanced")
        
        reader.disconnect()
