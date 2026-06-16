import os
import urllib.request

def baixar_audio(url, caminho_destino):
    try:
        print(f"Baixando: {url} -> {caminho_destino}")
        # Configura um user-agent para simular um navegador e evitar ser bloqueado
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            with open(caminho_destino, 'wb') as out_file:
                out_file.write(response.read())
        print("Download Concluído com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
        return False

# Base URL para loops de motor realistas hospedados publicamente no OpenGameArt
base_url = "https://opengameart.org/sites/default/files"

# 1. Sons de Motor de Fora (Ronco Aberto e Alto)
# Usando loops de gravação estéreo de carros de rua esportivos/comuns
baixar_audio(f"{base_url}/suv_idle.wav", "audio/carros/corolla/fora/idle.wav")
baixar_audio(f"{base_url}/suv_low_0.wav", "audio/carros/corolla/fora/low.wav")
baixar_audio(f"{base_url}/suv_mid_0.wav", "audio/carros/corolla/fora/mid.wav")
baixar_audio(f"{base_url}/suv_high_0.wav", "audio/carros/corolla/fora/high.wav")

# 2. Sons de Motor de Dentro (Ronco Abafado e Isolado)
# Usando loops com filtros de cabine (ou loops mais silenciosos)
baixar_audio(f"{base_url}/car_interior_idle.wav", "audio/carros/corolla/dentro/idle.wav")
baixar_audio(f"{base_url}/car_interior_low.wav", "audio/carros/corolla/dentro/low.wav")
baixar_audio(f"{base_url}/car_interior_mid.wav", "audio/carros/corolla/dentro/mid.wav")
baixar_audio(f"{base_url}/car_interior_high.wav", "audio/carros/corolla/dentro/high.wav")

# 3. Sons Ambientes e Tráfego
baixar_audio(f"{base_url}/traffic_asphalt_loop.wav", "audio/carros/corolla/asfalto_loop.wav")
baixar_audio(f"{base_url}/window_open_close.wav", "audio/carros/corolla/abrir_vidro.wav")
baixar_audio(f"{base_url}/window_open_close.wav", "audio/carros/corolla/fechar_vidro.wav")

print("Processo finalizado!")
