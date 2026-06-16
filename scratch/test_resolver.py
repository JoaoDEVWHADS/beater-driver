import os
import sys

# Adiciona o caminho principal para poder importar os módulos
sys.path.append(os.path.abspath("."))

from scripts.config import obter_caminho_recurso

modelo = "corolla"
subpasta = "fora"

def resolver_caminho(nome_arquivo):
    nomes_tentativas = [nome_arquivo]
    if nome_arquivo.endswith(".wav"):
        nomes_tentativas.append(nome_arquivo[:-4] + ".ogg")
        nomes_tentativas.append(nome_arquivo[:-4] + ".mp3")
    elif nome_arquivo.endswith(".ogg"):
        nomes_tentativas.append(nome_arquivo[:-4] + ".wav")
        nomes_tentativas.append(nome_arquivo[:-4] + ".mp3")

    for nome in nomes_tentativas:
        caminho_especifico = f"audio/carros/{modelo}/{subpasta}/{nome}"
        caminho_abs = obter_caminho_recurso(caminho_especifico)
        print(f"Tentando caminho_especifico: {caminho_especifico} -> Existe? {os.path.exists(caminho_abs)}")
        if os.path.exists(caminho_abs):
            return caminho_especifico
        
        caminho_raiz_carro = f"audio/carros/{modelo}/{nome}"
        caminho_abs_raiz = obter_caminho_recurso(caminho_raiz_carro)
        print(f"Tentando caminho_raiz_carro: {caminho_raiz_carro} -> Existe? {os.path.exists(caminho_abs_raiz)}")
        if os.path.exists(caminho_abs_raiz):
            return caminho_raiz_carro
            
        caminho_chevette_subpasta = f"audio/carros/chevette/{subpasta}/{nome}"
        caminho_abs_chev = obter_caminho_recurso(caminho_chevette_subpasta)
        print(f"Tentando caminho_chevette_subpasta: {caminho_chevette_subpasta} -> Existe? {os.path.exists(caminho_abs_chev)}")
        if os.path.exists(caminho_abs_chev):
            return caminho_chevette_subpasta
        
    return f"audio/carros/chevette/{nome_arquivo}"

print("RESOLVENDO low.wav:")
print("RESULTADO:", resolver_caminho("low.wav"))
print("\nRESOLVENDO idle.wav:")
print("RESULTADO:", resolver_caminho("idle.wav"))
