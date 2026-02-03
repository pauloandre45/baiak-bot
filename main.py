# -*- coding: utf-8 -*-
"""
Baiak Bot - Bot para Tibia 15.11
Desenvolvido para o projeto Crystal Server

Uso:
  python main.py
  
Requisitos:
  pip install -r requirements.txt
"""

import sys
import os

# Adiciona diretorio atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory.reader import TibiaMemoryReader
from screen.screen_reader import ScreenReader
from modules.healing import HealingModule
from gui.main_window import BotWindow


def main():
    """
    Funcao principal
    """
    print("=" * 50)
    print("  BAIAK BOT - Tibia 15.11")
    print("  Projeto Crystal Server")
    print("=" * 50)
    print()
    
    # Inicializa leitor de memoria (backup)
    print("[INIT] Inicializando leitor de memoria...")
    memory = TibiaMemoryReader()
    
    # Inicializa leitor de tela (principal)
    print("[INIT] Inicializando leitor de tela...")
    screen = ScreenReader()
    
    # Inicializa modulo de healing
    print("[INIT] Inicializando modulo de Healing...")
    healing = HealingModule(memory, screen)
    
    # Cria e executa interface
    print("[INIT] Iniciando interface grafica...")
    print()
    
    app = BotWindow(memory, screen, healing)
    app.run()
    
    print("\n[EXIT] Bot encerrado.")


if __name__ == "__main__":
    main()
