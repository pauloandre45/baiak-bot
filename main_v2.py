# -*- coding: utf-8 -*-
"""
Baiak Bot v2 - Bot para Tibia 15.11 usando leitura de memoria
Funciona mesmo com o Tibia minimizado!

Uso:
  python main_v2.py
  
Como funciona:
  1. Conecta ao processo do Tibia via pymem
  2. Le HP/MP diretamente da memoria (instantaneo!)
  3. Executa curas pressionando hotkeys
  
Primeiro uso:
  1. Execute o bot
  2. Clique em "Conectar"
  3. Se HP/MP nao aparecer, clique em "Configurar Offsets"
  4. Siga o wizard para encontrar os enderecos de HP/MP
  5. Apos configurar, reinicie o bot
"""

import sys
import os

# Adiciona diretorio ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window_v2 import main

if __name__ == "__main__":
    main()
