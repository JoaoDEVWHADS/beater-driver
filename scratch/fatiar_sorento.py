import os
import subprocess

def extrair_fatia(arquivo_ogg, caminho_wav, inicio_seg, duracao_seg):
    try:
        print(f"Processando fatia: {arquivo_ogg} ({inicio_seg}s -> {duracao_seg}s) -> {caminho_wav}")
        # Comando do FFmpeg para fatiar e converter para WAV 44100Hz 16bit estéreo
        comando = [
            "ffmpeg", "-y",
            "-ss", str(inicio_seg),
            "-t", str(duracao_seg),
            "-i", arquivo_ogg,
            "-ar", "44100",
            "-ac", "2",
            "-codec:a", "pcm_s16le",
            caminho_wav
        ]
        # Executa em silêncio
        subprocess.run(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("Fatia extraída com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao extrair {arquivo_ogg}: {e}")
        return False

# Pastas de destino
fora_dir = "audio/carros/corolla/fora"
dentro_dir = "audio/carros/corolla/dentro"
raiz_dir = "audio/carros/corolla"

os.makedirs(fora_dir, exist_ok=True)
os.makedirs(dentro_dir, exist_ok=True)

# Sons originais da pasta do Sorento
sorento_idle_int = "/home/admin/joao/suns de carros/sorento_idle_int.ogg"
sorento_engine_ext = "/home/admin/joao/suns de carros/sorento_engine_ext.ogg"
sorento_engine_int = "/home/admin/joao/suns de carros/sorento_engine_int.ogg"
sorento_start_ext = "/home/admin/joao/suns de carros/sorento_start_ext.ogg"
sorento_start_int = "/home/admin/joao/suns de carros/sorento_start_int.ogg"
sorento_stop_ext = "/home/admin/joao/suns de carros/sorento_stop_ext.ogg"
sorento_stop_int = "/home/admin/joao/suns de carros/sorento_stop_int.ogg"

# 1. Extração dos Sons de Motor Externos (fora/)
# A gravação sorento_engine_ext.ogg tem 4.74 segundos de aceleração progressiva
extrair_fatia(sorento_idle_int, f"{fora_dir}/idle.wav", 0.0, 1.6)      # Usa o idle do sorento
extrair_fatia(sorento_engine_ext, f"{fora_dir}/low.wav", 0.1, 1.2)    # Fatia inicial de giros baixos (0.1s a 1.3s)
extrair_fatia(sorento_engine_ext, f"{fora_dir}/mid.wav", 1.5, 1.2)    # Fatia média de giros (1.5s a 2.7s)
extrair_fatia(sorento_engine_ext, f"{fora_dir}/high.wav", 3.0, 1.2)   # Fatia máxima de giros (3.0s a 4.2s)
# Fallback ou cópia para pipoco de fora
extrair_fatia(sorento_engine_ext, f"{fora_dir}/pipoco.wav", 4.3, 0.4) # Final do giro antes do corte

# 2. Extração dos Sons de Motor Internos (dentro/)
# A gravação sorento_engine_int.ogg tem 4.74 segundos abafada
extrair_fatia(sorento_idle_int, f"{dentro_dir}/idle.wav", 0.0, 1.6)
extrair_fatia(sorento_engine_int, f"{dentro_dir}/low.wav", 0.1, 1.2)
extrair_fatia(sorento_engine_int, f"{dentro_dir}/mid.wav", 1.5, 1.2)
extrair_fatia(sorento_engine_int, f"{dentro_dir}/high.wav", 3.0, 1.2)
extrair_fatia(sorento_engine_int, f"{dentro_dir}/pipoco.wav", 4.3, 0.4)

# 3. Extração das Ações e Mecânicas (Ligar e Desligar)
# Para fora:
extrair_fatia(sorento_start_ext, f"{fora_dir}/ligar.wav", 0.0, 3.0)
extrair_fatia(sorento_stop_ext, f"{fora_dir}/desligar.wav", 0.0, 2.5)

# Para dentro:
extrair_fatia(sorento_start_int, f"{dentro_dir}/ligar.wav", 0.0, 3.0)
extrair_fatia(sorento_stop_int, f"{dentro_dir}/desligar.wav", 0.0, 2.5)

# Copia para a raiz do Corolla também (como fallback principal da classe Carro)
extrair_fatia(sorento_start_ext, f"{raiz_dir}/ligar.wav", 0.0, 3.0)
extrair_fatia(sorento_stop_ext, f"{raiz_dir}/desligar.wav", 0.0, 2.5)

print("Ajuste e fatiamento acústico com FFmpeg concluídos!")
