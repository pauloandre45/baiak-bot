# 🎮 BAIAK BOT - Documentação Completa

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Sistema de Leitura de Memória](#sistema-de-leitura-de-memória)
4. [Como Encontramos os Endereços de HP/MP](#como-encontramos-os-endereços-de-hpmp)
5. [Sistema de Healing](#sistema-de-healing)
6. [Interface Gráfica](#interface-gráfica)
7. [Problemas Conhecidos](#problemas-conhecidos)
8. [Arquivos do Projeto](#arquivos-do-projeto)
9. [Como Usar](#como-usar)
10. [Histórico de Desenvolvimento](#histórico-de-desenvolvimento)

---

## 🎯 Visão Geral

**Baiak Bot** é um bot externo para Tibia 15.11 que funciona através de **leitura direta de memória** do processo do cliente. Diferente de bots baseados em leitura de tela (OCR), este bot:

- ✅ Funciona **em background** (não precisa da janela do Tibia em foco)
- ✅ Leitura **instantânea** de HP/MP (sem delay de OCR)
- ✅ Envia teclas **sem roubar foco** da janela (usando PostMessage)
- ✅ Funciona mesmo com Tibia **minimizado**

### Tecnologias Utilizadas

- **Python 3.8+**
- **pymem** - Leitura de memória do processo
- **pywin32** - Envio de teclas via PostMessage (background)
- **tkinter** - Interface gráfica
- **Pillow** - Carregamento de ícones PNG

### Cliente Suportado

- **Tibia 15.11** (client.exe)
- Servidor: localhost (Baiak)

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      BAIAK BOT                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   GUI        │    │   Memory     │    │   Healing    │   │
│  │   (tkinter)  │◄──►│   Reader     │◄──►│   Module     │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│         │                   │                   │            │
│         │                   ▼                   ▼            │
│         │            ┌──────────────┐    ┌──────────────┐   │
│         │            │  client.exe  │    │  PostMessage │   │
│         │            │  (Tibia)     │    │  (Win32 API) │   │
│         │            └──────────────┘    └──────────────┘   │
│         │                   │                   │            │
│         ▼                   ▼                   ▼            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              offsets_cache.json                       │   │
│  │  (Armazena endereços de memória encontrados)          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧠 Sistema de Leitura de Memória

### Como Funciona

O bot usa a biblioteca **pymem** para:

1. **Conectar ao processo** `client.exe` (Tibia)
2. **Ler valores** diretamente da RAM do processo
3. **Calcular porcentagens** de HP/MP

### Código Principal (memory/reader_v2.py)

```python
import pymem
import json

class TibiaMemoryReader:
    def __init__(self):
        self.pm = None
        self.process_name = "client.exe"
        self.offsets = {}  # Carregado do cache
    
    def connect(self):
        """Conecta ao processo do Tibia"""
        self.pm = pymem.Pymem(self.process_name)
        self.load_offsets()  # Carrega do offsets_cache.json
        return True
    
    def read_int(self, address):
        """Lê um valor inteiro de 4 bytes"""
        return self.pm.read_int(address)
    
    def get_player_hp(self):
        """Retorna HP atual"""
        return self.read_int(self.offsets['HP'])
    
    def get_player_hp_max(self):
        """Retorna HP máximo"""
        return self.read_int(self.offsets['HP_MAX'])
    
    def get_player_hp_percent(self):
        """Retorna HP em porcentagem"""
        hp = self.get_player_hp()
        hp_max = self.get_player_hp_max()
        if hp_max > 0:
            return int((hp / hp_max) * 100)
        return 100
```

### Arquivo de Cache (offsets_cache.json)

Os endereços encontrados são salvos para não precisar escanear toda vez:

```json
{
    "HP": "0x201cd3272f0",
    "HP_MAX": "0x201cd3272f8",
    "MP": "0x201cd327910",
    "MP_MAX": "0x201cd327918",
    "found_at": "2026-02-03T...",
    "process_name": "client.exe"
}
```

**IMPORTANTE**: Os endereços mudam a cada vez que o Tibia é reiniciado!

---

## 🔍 Como Encontramos os Endereços de HP/MP

### O Processo de Descoberta

Este foi o processo mais complexo do desenvolvimento. Usamos um **scanner interativo** que:

1. **Escaneia toda a memória** do processo procurando o valor atual de HP
2. **Filtra os resultados** quando o HP muda
3. **Repete** até sobrar apenas o endereço correto

### Passo a Passo Detalhado

#### Passo 1: Primeira Varredura

```
Seu HP atual: 185
Escaneando memória...
Encontrados: 847.293 endereços com valor 185
```

O scanner procura **todos** os endereços que contêm o valor 185.

#### Passo 2: Mudança de HP

O jogador toma dano ou se cura, mudando o HP para outro valor (ex: 150).

#### Passo 3: Segunda Varredura (Filtro)

```
Seu HP atual: 150
Filtrando endereços...
Restaram: 12 endereços
```

Dos 847.293 endereços, apenas 12 mudaram de 185 para 150.

#### Passo 4: Repetir até Encontrar

Após 3-5 iterações, geralmente sobra **1 único endereço** - o correto!

### Código do Scanner (memory/scanner_advanced.py)

```python
def scan_for_value(pm, value):
    """Escaneia toda memória procurando um valor"""
    addresses = []
    
    # Obtém regiões de memória do processo
    for region in get_memory_regions(pm.process_handle):
        try:
            # Lê bloco de memória
            data = pm.read_bytes(region.BaseAddress, region.RegionSize)
            
            # Procura o valor (como int32)
            value_bytes = struct.pack('<i', value)
            
            offset = 0
            while True:
                pos = data.find(value_bytes, offset)
                if pos == -1:
                    break
                
                addresses.append(region.BaseAddress + pos)
                offset = pos + 1
                
        except:
            continue
    
    return addresses

def filter_addresses(pm, addresses, new_value):
    """Filtra endereços que mudaram para novo valor"""
    valid = []
    
    for addr in addresses:
        try:
            current = pm.read_int(addr)
            if current == new_value:
                valid.append(addr)
        except:
            continue
    
    return valid
```

### Descoberta do HP_MAX

Uma vez encontrado o HP, descobrimos que o **HP_MAX está 8 bytes depois**:

```
HP:     0x201cd3272f0  (valor: 185)
HP_MAX: 0x201cd3272f8  (valor: 185)  <- HP + 8 bytes
```

### Descoberta do MP

O mesmo processo foi repetido para MP, resultando em:

```
MP:     0x201cd327910  (valor: 35)
MP_MAX: 0x201cd327918  (valor: 35)   <- MP + 8 bytes
```

### Estrutura de Memória Descoberta

```
Offset    Campo
───────────────────
+0x00     HP atual
+0x08     HP máximo
...
+0x620    MP atual      (HP + 0x620)
+0x628    MP máximo     (HP + 0x628)
```

---

## 💊 Sistema de Healing

### Como Funciona

1. **Loop contínuo** (50ms de intervalo)
2. **Lê HP/MP** da memória
3. **Verifica thresholds** configurados
4. **Envia tecla** se necessário (via PostMessage)

### Código Principal (modules/healing_v2.py)

```python
class HealingModuleV2:
    def __init__(self, memory_reader):
        self.memory = memory_reader
        self.tibia_hwnd = None  # Handle da janela do Tibia
        self.slots = [
            {'enabled': False, 'hotkey': 'F1', 'hp_threshold': 80},
            {'enabled': False, 'hotkey': 'F2', 'hp_threshold': 60},
            {'enabled': False, 'hotkey': 'F3', 'hp_threshold': 40},
        ]
    
    def check_and_heal(self):
        """Verifica HP e cura se necessário"""
        hp_percent = self.memory.get_player_hp_percent()
        
        for slot in self.slots:
            if not slot['enabled']:
                continue
            
            if hp_percent <= slot['hp_threshold']:
                self.send_key(slot['hotkey'])
                break  # Só uma cura por ciclo
    
    def send_key(self, key):
        """Envia tecla via PostMessage (background)"""
        vk_code = self.get_vk_code(key)
        
        # PostMessage não rouba foco!
        win32api.PostMessage(self.tibia_hwnd, WM_KEYDOWN, vk_code, 0)
        time.sleep(0.05)
        win32api.PostMessage(self.tibia_hwnd, WM_KEYUP, vk_code, 0)
```

### Por que PostMessage?

| Método | Rouba Foco? | Funciona em Background? |
|--------|-------------|------------------------|
| `SendInput` | ✅ Sim | ❌ Não |
| `keybd_event` | ✅ Sim | ❌ Não |
| `PostMessage` | ❌ Não | ✅ Sim |

**PostMessage** envia a mensagem diretamente para a janela do Tibia, sem precisar que ela esteja em foco!

---

## 🎨 Interface Gráfica

### Versões Criadas

| Versão | Arquivo | Status |
|--------|---------|--------|
| v1 | `main_v2.py` | ✅ Funciona |
| ElfBot Style | `main_elf.py` | ✅ Funciona |
| Premium (emojis) | `main_premium.py` | ⚠️ Emojis não renderizam bem |
| Ultimate (ícones PNG) | `main_ultimate.py` | ❌ **NÃO FUNCIONA** |

### Interface que Funciona (main_v2.py)

```
┌─────────────────────────────────────────┐
│ Baiak Bot v2 - Memory Reader            │
├─────────────────────────────────────────┤
│ Status: ● Connected                     │
│                                         │
│ HP: ████████████░░░ 85%                │
│ MP: ██████████████░ 92%                │
├─────────────────────────────────────────┤
│ [Slot 1] [✓] F1  HP <= 80%             │
│ [Slot 2] [ ] F2  HP <= 60%             │
│ [Slot 3] [ ] F3  HP <= 40%             │
├─────────────────────────────────────────┤
│ [Connect]  [Start Bot]  [Scanner]      │
└─────────────────────────────────────────┘
```

### Interface com Ícones (NÃO FUNCIONA)

A versão `main_ultimate.py` usa ícones PNG da pasta `store\store\64`:

- ✅ Ícones carregam corretamente
- ✅ Interface renderiza
- ❌ **Botões do menu não aparecem** (só números 1-4)
- ❌ **Bot não funciona** após o novo layout

---

## ⚠️ Problemas Conhecidos

### 1. Interface Ultimate com Ícones PNG - NÃO FUNCIONA

**Sintomas:**
- Botões do menu não renderizam (aparecem cortados)
- Apenas números 1-4 aparecem no menu
- Layout quebrado

**Causa provável:**
- Problema com `compound=tk.LEFT` nos botões
- Ícones muito grandes para os botões
- Conflito entre imagem e texto no tkinter

**Arquivo afetado:** `gui/main_window_icons.py`

### 2. Emojis não Renderizam (Windows)

**Sintomas:**
- Emojis aparecem como quadrados ou símbolos estranhos
- Fonte "Segoe UI Emoji" não funciona corretamente

**Arquivo afetado:** `gui/main_window_modern.py`

### 3. Endereços Mudam ao Reiniciar Tibia

**Sintomas:**
- Bot para de ler HP/MP após reiniciar o Tibia
- Valores mostram 0% ou valores errados

**Solução:**
- Rodar o Scanner novamente (`scanner_advanced.py`)
- Novos endereços serão salvos no `offsets_cache.json`

### 4. Terminal não Muda de Diretório

**Sintomas:**
- Comandos `cd` não funcionam corretamente no PowerShell do VS Code
- Arquivo não encontrado ao rodar

**Solução:**
- Usar caminho absoluto: `python e:\projetos\projeto\novo_bot\main_v2.py`
- Ou abrir novo terminal no diretório correto

---

## 📁 Arquivos do Projeto

### Estrutura

```
novo_bot/
├── main_v2.py              # ✅ FUNCIONA - Entrada principal (interface simples)
├── main_elf.py             # ✅ FUNCIONA - Estilo ElfBot
├── main_premium.py         # ⚠️ Emojis bugados no Windows
├── main_ultimate.py        # ✅ FUNCIONA - Interface com ícones PNG
├── config.py               # Configurações
├── requirements.txt        # Dependências
├── offsets_cache.json      # Cache de endereços de memória
├── README.md               # Readme do GitHub
│
├── gui/
│   ├── main_window_v2.py       # ✅ Interface funcional simples
│   ├── main_window_elf.py      # ✅ Interface ElfBot
│   ├── main_window_modern.py   # ⚠️ Interface com emojis
│   └── main_window_icons.py    # ✅ Interface Premium com ícones PNG
│
├── memory/
│   ├── reader_v2.py            # ✅ Leitor de memória
│   └── scanner_advanced.py     # ✅ Scanner de endereços
│
├── modules/
│   └── healing_v2.py           # ✅ Módulo de healing
│
└── screen/                 # (Não usado - era para OCR)
```

### Dependências (requirements.txt)

```
pymem>=1.13.0
pywin32>=306
Pillow>=10.0.0
```

---

## 🚀 Como Usar

### Primeira Vez (Encontrar Endereços)

1. **Abrir Tibia** e logar com personagem

2. **Rodar o Scanner:**
   ```bash
   cd e:\projetos\projeto\novo_bot
   python memory/scanner_advanced.py
   ```

3. **Seguir instruções** do scanner:
   - Digitar HP atual
   - Tomar dano ou curar
   - Digitar novo HP
   - Repetir até encontrar

4. **Endereços salvos** em `offsets_cache.json`

### Uso Normal

1. **Abrir Tibia** e logar

2. **Rodar o Bot:**
   ```bash
   cd e:\projetos\projeto\novo_bot
   python main_v2.py
   ```

3. **Clicar "Connect"** para conectar ao Tibia

4. **Configurar slots** de healing

5. **Clicar "Start"** para iniciar

---

## 📜 Histórico de Desenvolvimento

### Sessão 1 - Início
- Criado sistema de leitura de memória
- Abandonada abordagem de OCR (muito lenta)

### Sessão 2 - Scanner de Memória
- Criado scanner interativo para encontrar endereços
- Descobertos endereços de HP/MP
- Estrutura: HP+8 = HP_MAX, HP+0x620 = MP

### Sessão 3 - Sistema de Healing
- Implementado módulo de healing
- Problema: bot roubava foco da janela

### Sessão 4 - PostMessage (Background)
- Substituído SendInput por PostMessage
- Bot agora funciona sem roubar foco!

### Sessão 5 - GitHub
- Criado repositório: https://github.com/pauloandre45/baiak-bot
- Código publicado

### Sessão 6 - Nova Interface (PROBLEMAS)
- Tentativa de criar interface estilo ElfBot
- Versão com emojis: emojis não renderizam bem
- Versão com ícones PNG: **QUEBROU** - botões não aparecem
- **VERSÃO FUNCIONAL:** `main_v2.py` (interface simples)

### Sessão 7 - Correção Interface Premium (03/02/2026)
**Problemas identificados:**
1. Botões do menu apareciam sem ícones (só retângulos vazios)
2. Ícones dos spells muito pequenos (20-24px)
3. Barra inferior com Connect/START não aparecia

**Correções aplicadas em `gui/main_window_icons.py`:**
1. Aumentou tamanho da janela de 550x480 para 620x620
2. Ícones do menu aumentados de 28px para 40px
3. Botões do menu agora mostram ícone em cima + texto embaixo (`compound=tk.TOP`)
4. Ícones das spells aumentados de 32px para 40px
5. Ordem de criação dos widgets corrigida: `_create_status_bar()` agora é criado ANTES de `_create_content_area()` para ficar fixo na parte inferior

**Resultado:** Interface Premium (`main_ultimate.py`) agora funciona corretamente!

### Sessão 8 - Smart Scanner V3 (03/02/2026)
**GRANDE AVANÇO:** Criamos o Smart Scanner V3 que encontra o player **AUTOMATICAMENTE** sem precisar de input do usuário!

**Problema anterior:**
- Pattern Scanner falhava após reiniciar o cliente (bytes mudavam)
- Usuário precisava digitar HP/MP manualmente (ruim para distribuição)

**Solução Smart Scanner V3:**
- Busca estruturas onde HP == HP_MAX (vida cheia)
- Valida MP no offset +0x620 (não pode ser 0 ou potência de 2)
- Verifica campo de Level no offset +0x14
- Aplica scoring para ranquear o melhor candidato

**Critérios de validação:**
1. HP no range 150-30000
2. HP == HP_MAX (vida cheia - comum ao abrir o bot)
3. MP_MAX diferente de HP_MAX
4. MP > 0 e não é potência de 2 (256, 512, 1024, etc.)
5. Level entre 1-2000 e diferente de HP

**Resultado:** Encontra o player correto em ~15 segundos sem NENHUM input!

**Interface com barra de progresso:**
- Popup estilo download mostrando progresso
- Barra colorida (azul → verde)
- Porcentagem e tempo em tempo real
- Tela de sucesso ao encontrar

---

## 🤖 Smart Scanner V3 - Detalhes Técnicos

### Por que é automático?

O scanner V3 usa **heurísticas** para identificar o player:

```python
# Critérios principais:
1. HP == HP_MAX          → Player com vida cheia (comum)
2. MP em range válido    → Elimina buffers/falsos positivos
3. Level no offset +0x14 → Confirma estrutura do player
4. Scoring inteligente   → MP_MAX > HP_MAX ganha pontos (mages)
```

### Estrutura de Memória do Player (Tibia 15.11 BaiakZika)

```
Offset    Campo         Tamanho
────────────────────────────────
+0x00     HP            4 bytes (int32)
+0x08     HP_MAX        4 bytes (int32)
+0x14     Level(?)      4 bytes (int32)
...
+0x620    MP            4 bytes (int32)
+0x628    MP_MAX        4 bytes (int32)
```

### Velocidade do Scanner

| Situação | Tempo |
|----------|-------|
| Primeira vez (sem cache) | ~13-15 segundos |
| Com cache válido | **Instantâneo** |
| Após reiniciar Tibia | ~13-15 segundos |

### O que NÃO afeta a velocidade:
- ❌ Level do personagem
- ❌ Quantidade de HP/MP
- ❌ Primeira vez vs. veterano

### O que AFETA a velocidade:
- ✅ Velocidade do processador (CPU)
- ✅ Quantidade de RAM alocada pelo Tibia

---

## 🔧 Offsets Confirmados (Tibia 15.11 BaiakZika)

```
HP      = endereço base
HP_MAX  = HP + 0x8
MP      = HP + 0x620
MP_MAX  = HP + 0x628
Level   = HP + 0x14 (possível)
```

**IMPORTANTE:** Os endereços base mudam a cada reinício do Tibia (ASLR).
O scanner encontra automaticamente o novo endereço.

---

## 📊 Comparação com Outros Bots

### Métodos de leitura de HP/MP:

| Método | ZeroBot | WindBot | Nosso Bot |
|--------|---------|---------|-----------|
| Leitura de Memória | ✅ | ✅ | ✅ |
| Leitura de Pixels | ✅ backup | ? | ❌ |
| Precisa Status Bar | Talvez | Sim | **NÃO** |
| Auto-detecta player | ✅ | ✅ | ✅ |

### Vantagens do nosso bot:
- ✅ **100% automático** - não pede HP/MP do usuário
- ✅ **Funciona sem Status Bar** visível
- ✅ **Leitura instantânea** (não depende de FPS)
- ✅ **Funciona em background** (janela minimizada)

---

## 📞 Próximos Passos

1. [x] ~~**CORRIGIR** interface com ícones PNG~~ ✅ FEITO!
2. [x] ~~**Smart Scanner automático**~~ ✅ FEITO!
3. [x] ~~**Barra de progresso no Connect**~~ ✅ FEITO!
4. [ ] Adicionar módulo de Attack
5. [ ] Salvar/Carregar configurações
6. [ ] Adicionar mais spells ao mapeamento de ícones
7. [ ] Testar em outros servidores/versões

---

## 🔗 Links

- **GitHub:** https://github.com/pauloandre45/baiak-bot
- **Ícones:** `E:\projetos\projeto\store\store\64\`

---

*Documentação criada em: 03/02/2026*
*Última atualização: 03/02/2026 - Smart Scanner V3 + Barra de Progresso*
