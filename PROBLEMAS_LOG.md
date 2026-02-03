# 🐛 Log de Problemas e Soluções

## Problemas Encontrados Durante o Desenvolvimento

---

## ❌ PROBLEMA 1: Interface com Ícones PNG Não Funciona

### Data: 03/02/2026

### Descrição
Após criar a interface `main_ultimate.py` com ícones PNG reais do Tibia (pasta `store\store\64`), a interface apresentou problemas graves.

### Sintomas
1. Botões do menu aparecem cortados (só mostram números 1-4)
2. Ícones não aparecem nos botões
3. Layout completamente quebrado
4. Bot não funciona após as mudanças

### Screenshot
```
Antes (funcionava):
[💚 Healing] [⚔️ Attack] [📋 Lists] [📊 HUD] [1] [2] [3] [4]

Depois (quebrado):
[    ] [    ] [    ] [    ] [1] [2] [3] [4]
       ^-- Botões sem conteúdo
```

### Causa Provável
- Problema com `compound=tk.LEFT` nos botões do tkinter
- Conflito entre `image` e `text` no mesmo botão
- Tamanho dos ícones (64x64) muito grande para botões

### Arquivo Afetado
`gui/main_window_icons.py`

### Solução Temporária
Usar a versão antiga que funciona: `python main_v2.py`

### TODO
- [ ] Investigar problema com compound no tkinter
- [ ] Testar com ícones menores (32x32)
- [ ] Considerar usar Canvas ao invés de Button

---

## ❌ PROBLEMA 2: Emojis Não Renderizam no Windows

### Data: 03/02/2026

### Descrição
A interface `main_premium.py` usa emojis (💚, ⚔️, 🔥, etc.) mas eles não aparecem corretamente no Windows.

### Sintomas
1. Emojis aparecem como quadrados (□)
2. Alguns emojis aparecem como símbolos estranhos
3. Fonte "Segoe UI Emoji" não resolve

### Código Problemático
```python
SPELL_ICONS = {
    "exura": "💚",      # <- Não renderiza
    "exori": "⚔️",      # <- Não renderiza
    "uh": "❤️",         # <- Não renderiza
}

btn = tk.Button(text="💚 Healing")  # <- Emoji não aparece
```

### Causa
- tkinter no Windows tem suporte limitado a emojis
- Depende da fonte do sistema
- Python 3.14 pode ter mudanças no suporte a Unicode

### Arquivo Afetado
`gui/main_window_modern.py`

### Solução Temporária
Usar imagens PNG ao invés de emojis (mas essa solução também tem problemas - ver PROBLEMA 1)

---

## ❌ PROBLEMA 3: Terminal Não Muda de Diretório

### Data: 03/02/2026

### Descrição
Comandos `cd` no PowerShell do VS Code não funcionam como esperado.

### Sintomas
```powershell
PS> cd e:\projetos\projeto\novo_bot; python main_v2.py
Erro: arquivo não encontrado 'e:\projetos\projeto\main_v2.py'
```

### Causa
- O terminal do VS Code mantém contexto anterior
- `cd` não afeta o próximo comando na mesma linha às vezes

### Solução
Usar `Set-Location` ou caminho absoluto:
```powershell
Set-Location e:\projetos\projeto\novo_bot; python main_v2.py
# ou
python e:\projetos\projeto\novo_bot\main_v2.py
```

---

## ✅ PROBLEMA 4: Bot Roubava Foco da Janela (RESOLVIDO)

### Data: 03/02/2026

### Descrição
Quando o bot enviava teclas para curar, a janela do Tibia era trazida para frente, atrapalhando o usuário.

### Causa
Uso de `SendInput` ou `keybd_event` que requerem foco da janela.

### Solução
Usar `PostMessage` da Win32 API:

```python
# ANTES (roubava foco):
import pyautogui
pyautogui.press('F1')

# DEPOIS (funciona em background):
import win32api
import win32con

def send_key_background(hwnd, key):
    vk_code = get_vk_code(key)
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, 0)
```

### Arquivo Corrigido
`modules/healing_v2.py`

### Status
✅ RESOLVIDO

---

## ✅ PROBLEMA 5: Endereços Mudam ao Reiniciar Tibia (RESOLVIDO)

### Data: 03/02/2026

### Descrição
Após reiniciar o Tibia, os endereços de HP/MP não funcionam mais.

### Causa
ASLR (Address Space Layout Randomization) do Windows randomiza os endereços a cada execução.

### Solução
1. Criado `scanner_advanced.py` para encontrar novos endereços
2. Cache salvo em `offsets_cache.json`
3. Documentação de como usar o scanner

### Status
✅ RESOLVIDO (com workaround - precisa escanear novamente)

---

## 📊 Resumo de Status

| Problema | Status | Solução |
|----------|--------|---------|
| Interface com ícones PNG | ❌ Não resolvido | Usar main_v2.py |
| Emojis não renderizam | ❌ Não resolvido | Usar main_v2.py |
| Terminal cd | ⚠️ Workaround | Usar Set-Location |
| Bot roubava foco | ✅ Resolvido | PostMessage |
| Endereços mudam | ✅ Resolvido | Scanner |

---

## 🔧 Versões que Funcionam

Para evitar os problemas acima, use estas versões:

```bash
# Versão estável e funcional:
python main_v2.py

# Versão ElfBot (também funciona):
python main_elf.py
```

**NÃO USE:**
- `main_premium.py` (emojis bugados)
- `main_ultimate.py` (ícones quebrados)

---

*Log de problemas atualizado em: 03/02/2026*
