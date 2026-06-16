import os
import urllib.request
import ssl

# Desativa verificação de SSL temporariamente para evitar falhas em certificados antigos do python
ssl._create_default_https_context = ssl._create_unverified_context

def baixar_audio(url, caminho_destino):
    try:
        print(f"Buscando som: {url}")
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(caminho_destino, 'wb') as out_file:
                out_file.write(response.read())
        print(f"Salvo em: {caminho_destino}\n")
        return True
    except Exception as e:
        print(f"Não foi possível baixar {url}: {e}\n")
        return False

# Base de áudio contendo loops de carros de rua de alta fidelidade
# (Hospedado publicamente no CDN de demonstração de efeitos de áudio)
cdn_sounds = "https://www.soundjay.com/mechanical/sounds"

# 1. Downloads para a subpasta FORA (Vidro aberto, ronco de motor aberto e nítido)
baixar_audio(f"{cdn_sounds}/car-running-1.wav", "audio/carros/corolla/fora/idle.wav")
baixar_audio(f"{cdn_sounds}/car-accelerate-1.wav", "audio/carros/corolla/fora/low.wav")
baixar_audio(f"{cdn_sounds}/car-accelerate-2.wav", "audio/carros/corolla/fora/mid.wav")
baixar_audio(f"{cdn_sounds}/car-accelerate-3.wav", "audio/carros/corolla/fora/high.wav")
baixar_audio(f"{cdn_sounds}/gun-shot-1.wav", "audio/carros/corolla/fora/pipoco.wav")

# 2. Downloads para a subpasta DENTRO (Vidro fechado, ronco abafado e amortecido)
baixar_audio(f"{cdn_sounds}/car-interior-1.wav", "audio/carros/corolla/dentro/idle.wav")
baixar_audio(f"{cdn_sounds}/car-interior-1.wav", "audio/carros/corolla/dentro/low.wav")
baixar_audio(f"{cdn_sounds}/car-interior-1.wav", "audio/carros/corolla/dentro/mid.wav")
baixar_audio(f"{cdn_sounds}/car-interior-1.wav", "audio/carros/corolla/dentro/high.wav")
baixar_audio(f"{cdn_sounds}/gun-shot-1.wav", "audio/carros/corolla/dentro/pipoco.wav")

# 3. Mecânica do carro
baixar_audio("https://www.soundjay.com/mechanical/sounds/car-start-1.wav", "audio/carros/corolla/ligar.wav")
baixar_audio("https://www.soundjay.com/mechanical/sounds/car-door-close-1.wav", "audio/carros/corolla/desligar.wav")
baixar_audio("https://www.soundjay.com/mechanical/sounds/gear-change-1.wav", "audio/carros/corolla/marcha.wav")
baixar_audio("https://www.soundjay.com/mechanical/sounds/car-skid-1.wav", "audio/carros/corolla/freio.wav")

# 4. Sons de vidro
baixar_audio("https://www.soundjay.com/mechanical/sounds/power-window-1.wav", "audio/carros/corolla/abrir_vidro.wav")
baixar_audio("https://www.soundjay.com/mechanical/sounds/power-window-1.wav", "audio/carros/corolla/fechar_vidro.wav")

# 5. Sons de rodagem de pneus (asfalto e terra)
baixar_audio("https://www.soundjay.com/misc/sounds/gravel-tread-1.wav", "audio/carros/corolla/terra_loop.wav")
baixar_audio("https://www.soundjay.com/misc/sounds/gravel-tread-1.wav", "audio/carros/corolla/fora/terra_loop.wav")
baixar_audio("https://www.soundjay.com/misc/sounds/gravel-tread-1.wav", "audio/carros/corolla/dentro/terra_loop.wav")

print("Download dos áudios finalizado!")
