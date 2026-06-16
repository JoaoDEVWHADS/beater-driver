import os
import sys

def obter_caminho_recurso(caminho_relativo):
    """ Retorna o caminho absoluto do recurso, funcionando tanto em desenvolvimento quanto no executável do PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, caminho_relativo)
