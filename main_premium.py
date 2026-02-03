# -*- coding: utf-8 -*-
"""
Baiak Bot - Premium Edition
Interface moderna com ícones de spells
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window_modern import ModernBotWindow


def main():
    print("=" * 50)
    print("  🎮 BAIAK BOT - Premium Edition")
    print("  Interface moderna com ícones de spells")
    print("=" * 50)
    
    try:
        app = ModernBotWindow()
        app.run()
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()
