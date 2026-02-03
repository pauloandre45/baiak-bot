# -*- coding: utf-8 -*-
"""
Baiak Bot - ElfBot Style
Entrada principal com interface estilo ElfBot
"""

import sys
import os

# Adiciona diretorio raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window_elf import BotWindowElfStyle


def main():
    print("=" * 50)
    print("    BAIAK BOT - ElfBot Style")
    print("    Interface compacta e organizada")
    print("=" * 50)
    
    try:
        app = BotWindowElfStyle()
        app.run()
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()
