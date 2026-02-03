# 🎮 Baiak Bot - Tibia 15.11

Bot externo para Tibia 15.11 usando leitura de memória direta.
Funciona mesmo com o Tibia minimizado!

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Funcionalidades

- ✅ **Auto Healing** - Cura automática baseada em HP%
- ✅ **Leitura de Memória** - Instantâneo, sem delay de pixels
- ✅ **Background Mode** - Funciona com Tibia minimizado
- ✅ **3 Slots de Cura** - Configure múltiplas hotkeys
- ✅ **Interface Gráfica** - Fácil de usar

## 📸 Screenshot

```
┌─────────────────────────────────────────┐
│           BAIAK BOT v2                  │
├─────────────────────────────────────────┤
│  HP: 88,665 / 96,755 (91%)  ████████░░  │
│  MP: 40,617 / 96,660 (42%)  ████░░░░░░  │
├─────────────────────────────────────────┤
│           [ BOT: ON ]                   │
├─────────────────────────────────────────┤
│  AUTO HEALING                           │
│  [ON] Slot 1: F1 @ HP <= 80%            │
│  [ON] Slot 2: F2 @ HP <= 60%            │
│  [OFF] Slot 3: F3 @ HP <= 40%           │
└─────────────────────────────────────────┘
```

## 🚀 Instalação

### Requisitos
- Python 3.8 ou superior
- Windows 10/11
- Tibia Client 15.11

### Passos

1. **Clone o repositório**
```bash
git clone https://github.com/SEU_USUARIO/baiak-bot.git
cd baiak-bot
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Execute o bot**
```bash
python main_v2.py
```

## ⚙️ Configuração Inicial

Na primeira execução, você precisa configurar os endereços de memória:

1. Abra o Tibia e entre no jogo
2. Execute o bot e clique em **"Conectar"**
3. Se HP/MP não aparecerem, clique em **"Configurar Offsets"**
4. Siga o wizard para encontrar os endereços

> ⚠️ **Nota:** Os endereços podem mudar quando o Tibia reinicia. Se isso acontecer, execute o scanner novamente.

## 📖 Como Usar

1. **Abra o Tibia** e entre no jogo
2. **Execute o bot** (`python main_v2.py`)
3. Clique em **"Conectar"**
4. **Configure os slots de healing:**
   - Marque a checkbox para ativar
   - Defina a hotkey (F1, F2, etc)
   - Defina o HP% para ativar a cura
5. Clique em **"BOT: ON"**

### Exemplo de Configuração

| Slot | Hotkey | HP% | Descrição |
|------|--------|-----|-----------|
| 1 | F1 | 80% | Supreme Health Potion |
| 2 | F5 | 70% | Exura Vita |
| 3 | F2 | 40% | Emergência |

## 🔧 Estrutura do Projeto

```
baiak-bot/
├── main_v2.py              # Arquivo principal
├── config.py               # Configurações
├── requirements.txt        # Dependências
├── offsets_cache.json      # Endereços de memória (gerado)
│
├── gui/
│   └── main_window_v2.py   # Interface gráfica
│
├── memory/
│   ├── reader_v2.py        # Leitor de memória
│   └── scanner_advanced.py # Scanner de offsets
│
└── modules/
    └── healing_v2.py       # Módulo de auto healing
```

## 🛠️ Tecnologias

- **pymem** - Leitura de memória de processos
- **pywin32** - API Windows (PostMessage, FindWindow)
- **tkinter** - Interface gráfica

## ⚠️ Aviso Legal

Este bot foi desenvolvido para uso em **servidores privados** (OTServ).
O uso em servidores oficiais pode resultar em banimento.

**Use por sua conta e risco.**

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer um Fork
2. Criar uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

## 📋 Roadmap

- [ ] Módulo de Auto Mana
- [ ] Módulo de Auto Attack
- [ ] Módulo de Buffs (Haste, Utamo)
- [ ] CaveBot básico
- [ ] Salvar/Carregar perfis
- [ ] Hotkeys globais

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

Desenvolvido para o projeto **Crystal Server (Baiak)**

---

⭐ Se este projeto te ajudou, deixe uma estrela!
