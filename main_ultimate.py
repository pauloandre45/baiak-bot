# -*- coding: utf-8 -*-
"""
Baiak Bot - Ultimate Edition
Interface com ícones reais do Tibia
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window_icons import BotWindowWithIcons


def main():
    # Verifica Pillow
    try:
        from PIL import Image, ImageTk
    except ImportError:
        print("=" * 50)
        print("ERRO: Pillow não está instalado!")
        print("Execute: pip install Pillow")
        print("=" * 50)
        input("Pressione ENTER para sair...")
        return
    
    print("=" * 50)
    print("  🎮 BAIAK BOT - Ultimate Edition")
    print("  Interface com ícones reais do Tibia!")
    print("=" * 50)
    
    try:
        app = BotWindowWithIcons()
        app.run()
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()
