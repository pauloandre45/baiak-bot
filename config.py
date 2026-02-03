# -*- coding: utf-8 -*-
"""
Configuracoes do Bot para Tibia 15.11
"""

# Nome do processo do Tibia
TIBIA_PROCESS_NAME = "client.exe"

# Nome da janela do Tibia (parcial)
TIBIA_WINDOW_TITLE = "Tibia"

# Versao do cliente suportada
TIBIA_VERSION = "15.11"

# ============================================
# OFFSETS DE MEMORIA - TIBIA 15.11
# IMPORTANTE: Estes offsets precisam ser
# atualizados para cada versao do cliente
# ============================================

# Base addresses (precisam ser encontrados)
# Estes sao valores de exemplo - precisamos descobrir os reais
OFFSETS = {
    # Player Info
    "player_base": 0x0,          # Base do player (precisa descobrir)
    "player_hp": 0x0,            # Offset para HP atual
    "player_hp_max": 0x0,        # Offset para HP maximo
    "player_mp": 0x0,            # Offset para MP atual
    "player_mp_max": 0x0,        # Offset para MP maximo
    "player_name": 0x0,          # Offset para nome do player
    "player_level": 0x0,         # Offset para level
    
    # Status
    "is_connected": 0x0,         # Se esta conectado ao jogo
}

# ============================================
# CONFIGURACOES DE HEALING
# ============================================

HEALING_CONFIG = {
    "enabled": False,
    "slots": [
        {
            "enabled": False,
            "type": "potion",      # "potion" ou "spell"
            "item_name": "Supreme Health Potion",
            "spell_words": "",
            "hp_percent": 80,
            "hotkey": "F1",
        },
        {
            "enabled": False,
            "type": "spell",
            "item_name": "",
            "spell_words": "exura vita",
            "hp_percent": 70,
            "hotkey": "F5",
        },
        {
            "enabled": False,
            "type": "potion",
            "item_name": "Health Potion",
            "hp_percent": 50,
            "hotkey": "F2",
        },
    ]
}

# ============================================
# HOTKEYS PADRAO (podem ser reconfiguradas)
# ============================================

HOTKEYS = {
    "toggle_bot": "F12",         # Liga/desliga o bot
    "toggle_healing": "F11",      # Liga/desliga healing
}

# ============================================
# TIMERS (em milissegundos)
# ============================================

TIMERS = {
    "main_loop": 50,             # Loop principal (50ms - mais rapido)
    "healing_cooldown": 150,     # Cooldown minimo entre curas (150ms)
    "memory_read": 30,           # Intervalo de leitura de memoria
}
