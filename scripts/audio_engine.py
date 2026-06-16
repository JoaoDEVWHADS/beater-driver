import pygame
import sounddevice as sd
import numpy as np
import math
import random
from scripts.fala import SistemaFala
from scripts.config import obter_caminho_recurso

class AudioEngine:

    def __init__(self):
        self.fala = SistemaFala()

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        pygame.mixer.set_num_channels(16)
        
        self.canal_passos = pygame.mixer.Channel(1)
        self.canal_sfx = pygame.mixer.Channel(4)
        self.canal_pipoco_a = pygame.mixer.Channel(5)
        self.canal_pipoco_b = pygame.mixer.Channel(6)
        self.canal_arranque = pygame.mixer.Channel(7) 
        
        self.usar_canal_a = True

        self.carregar_matriz_audio_func = None
        def carregar_matriz_audio(caminho):
            try:
                som = pygame.mixer.Sound(obter_caminho_recurso(caminho))
                dados = pygame.sndarray.array(som).astype(np.float32) / 32768.0
                if len(dados.shape) == 1:
                    dados = np.column_stack((dados, dados))
                return dados
            except Exception as e:
                print(f"Erro ao carregar {caminho}: {e}")
                return None
        self.carregar_matriz_audio_func = carregar_matriz_audio

        self.som_pipoco_objeto = None
        self.carregar_sons_motor("chevette")

        self.taxa_amostragem = 44100
        self.motor_rodando = False
        self.stream = None
        self.falhando = False
        self.morrendo_natural = False 

        self.pos_idle = 0.0
        self.pos_low = 0.0
        self.pos_mid = 0.0
        self.pos_high = 0.0

        self.rpm_alvo = 0.0
        self.rpm_atual = 0.0

    def falar(self, texto):
        self.fala.falar(texto)

    def _callback_audio(self, outdata, frames, time, status):
        if not self.motor_rodando:
            outdata.fill(0)
            return

        if self.morrendo_natural:
            self.rpm_atual -= 0.03 
            if self.rpm_atual <= 0.0:
                self.rpm_atual = 0.0
                outdata.fill(0)
                return
        else:
            self.rpm_atual += (self.rpm_alvo - self.rpm_atual) * 0.18

        if self.falhando:
            vol_idle = 0.05
            vol_low  = 0.30
            vol_mid  = 0.60
            vol_high = 1.10
            fator_pitch = 1.70 + random.uniform(-0.08, 0.08)
        else:
            vol_idle = max(0.0, 1.0 - self.rpm_atual * 3.5)
            vol_low  = max(0.0, 1.0 - abs(self.rpm_atual - 0.28) * 2.5)
            vol_mid  = max(0.0, 1.0 - abs(self.rpm_atual - 0.60) * 2.5)
            vol_high = max(0.0, 1.0 - abs(self.rpm_atual - 0.90) * 3.0)
            fator_pitch = 0.75 + (self.rpm_atual * 1.15)

        passo = fator_pitch
        indices = np.arange(frames) * passo
        mix_final = np.zeros_like(outdata)

        if self.dados_idle is not None and vol_idle > 0.0:
            idx = ((self.pos_idle + indices) % len(self.dados_idle)).astype(np.int32)
            mix_final += self.dados_idle[idx] * (vol_idle * 0.7)
            self.pos_idle = (self.pos_idle + frames * passo) % len(self.dados_idle)

        if self.dados_low is not None and vol_low > 0.0:
            idx = ((self.pos_low + indices) % len(self.dados_low)).astype(np.int32)
            mix_final += self.dados_low[idx] * (vol_low * 0.8)
            self.pos_low = (self.pos_low + frames * passo) % len(self.dados_low)

        if self.dados_mid is not None and vol_mid > 0.0:
            idx = ((self.pos_mid + indices) % len(self.dados_mid)).astype(np.int32)
            mix_final += self.dados_mid[idx] * (vol_mid * 0.9)
            self.pos_mid = (self.pos_mid + frames * passo) % len(self.dados_mid)

        if self.dados_high is not None and vol_high > 0.0:
            idx = ((self.pos_high + indices) % len(self.dados_high)).astype(np.int32)
            mix_final += self.dados_high[idx] * (vol_high * 1.25)
            self.pos_high = (self.pos_high + frames * passo) % len(self.dados_high)

        if not self.falhando and self.rpm_atual < 0.15:
            tempo_osc = pygame.time.get_ticks() / 80.0
            mix_final *= (1.0 + math.sin(tempo_osc) * 0.08)

        # Reduz o volume geral do motor se o vidro estiver fechado
        if not self.vidro_aberto_atual:
            mix_final *= 0.45

        outdata[:] = mix_final

    # SISTEMA DE LOOP SUAVE: Usa fade de 50ms para maquiar e cortar o final bugado do arquivo
    def tocar_som_start_loop(self, caminho_som):
        if not self.canal_arranque.get_busy():
            try:
                som = pygame.mixer.Sound(obter_caminho_recurso(caminho_som))
                self.canal_arranque.play(som, loops=-1, fade_ms=50) 
            except Exception as e:
                print(f"Erro ao tocar som de arranque: {e}")

    def parar_som_start(self):
        if self.canal_arranque.get_busy():
            self.canal_arranque.stop()

    def motor_start(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
            self.stream = None

        self.pos_idle = 0.0
        self.pos_low = 0.0
        self.pos_mid = 0.0
        self.pos_high = 0.0
        self.rpm_atual = 0.0
        self.rpm_alvo = 0.0
        self.falhando = False
        self.morrendo_natural = False
        
        self.motor_rodando = True
        
        self.stream = sd.OutputStream(
            samplerate=self.taxa_amostragem,
            channels=2,
            callback=self._callback_audio,
            blocksize=256
        )
        self.stream.start()

    def motor_morrer_natural(self):
        self.morrendo_natural = True

    def motor_stop(self):
        self.motor_rodando = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
            self.stream = None

    def motor_rpm_velho(self, rpm_normal, falhando=False):
        if not self.motor_rodando or self.morrendo_natural:
            return
        self.falhando = falhando
        self.rpm_alvo = rpm_normal

    def tocar_pipoco_corte(self):
        if self.som_pipoco_objeto is None: return
        volume_aleatorio = random.uniform(1.2, 1.5)
        
        # Reduz volume do pipoco se o vidro estiver fechado
        if not self.vidro_aberto_atual:
            volume_aleatorio *= 0.45
            
        if self.usar_canal_a:
            self.canal_pipoco_a.set_volume(volume_aleatorio)
            self.canal_pipoco_a.play(self.som_pipoco_objeto)
        else:
            self.canal_pipoco_b.set_volume(volume_aleatorio)
            self.canal_pipoco_b.play(self.som_pipoco_objeto)
        
        self.usar_canal_a = not self.usar_canal_a

    def tocar_pipoco_unico(self):
        if self.som_pipoco_objeto is None: return
        vol = 1.5
        if not self.vidro_aberto_atual:
            vol *= 0.45
        self.canal_pipoco_a.set_volume(vol)
        self.canal_pipoco_a.play(self.som_pipoco_objeto)

    def tocar(self, caminho_som):
        try:
            som = pygame.mixer.Sound(obter_caminho_recurso(caminho_som))
            self.canal_sfx.play(som)
        except Exception as e:
            print(f"Erro ao tocar SFX {caminho_som}: {e}")

    def carregar_sons_motor(self, modelo, vidro_aberto=True):
        import os
        from scripts.config import obter_caminho_recurso
        
        # Salva o modelo e estado do vidro atuais no AudioEngine
        self.modelo_atual = modelo
        self.vidro_aberto_atual = vidro_aberto

        subpasta = "fora" if vidro_aberto else "dentro"
        
        def resolver_caminho(nome_arquivo):
            nomes_tentativas = [nome_arquivo]
            if nome_arquivo.endswith(".wav"):
                nomes_tentativas.append(nome_arquivo[:-4] + ".ogg")
                nomes_tentativas.append(nome_arquivo[:-4] + ".mp3")
            elif nome_arquivo.endswith(".ogg"):
                nomes_tentativas.append(nome_arquivo[:-4] + ".wav")
                nomes_tentativas.append(nome_arquivo[:-4] + ".mp3")

            for nome in nomes_tentativas:
                # 1. Tenta achar na subpasta específica (fora/ ou dentro/)
                caminho_especifico = f"audio/carros/{modelo}/{subpasta}/{nome}"
                if os.path.exists(obter_caminho_recurso(caminho_especifico)):
                    return caminho_especifico
                
                # 2. Se não achar, tenta achar na raiz da pasta do carro
                caminho_raiz_carro = f"audio/carros/{modelo}/{nome}"
                if os.path.exists(obter_caminho_recurso(caminho_raiz_carro)):
                    return caminho_raiz_carro
                    
                # 3. Fallback: tenta achar na subpasta correspondente do Chevette
                caminho_chevette_subpasta = f"audio/carros/chevette/{subpasta}/{nome}"
                if os.path.exists(obter_caminho_recurso(caminho_chevette_subpasta)):
                    return caminho_chevette_subpasta
                
            # Fallback absoluto
            return f"audio/carros/chevette/{nome_arquivo}"

        self.dados_idle = self.carregar_matriz_audio_func(resolver_caminho("idle.wav"))
        self.dados_low  = self.carregar_matriz_audio_func(resolver_caminho("low.wav"))
        self.dados_mid  = self.carregar_matriz_audio_func(resolver_caminho("mid.wav"))
        self.dados_high = self.carregar_matriz_audio_func(resolver_caminho("high.wav"))
        
        try:
            self.som_pipoco_objeto = pygame.mixer.Sound(obter_caminho_recurso(resolver_caminho("pipoco.wav")))
        except Exception as e:
            print(f"Erro ao carregar pipoco para {modelo}: {e}")
            self.som_pipoco_objeto = None

    def definir_estado_vidro(self, vidro_aberto, modelo):
        self.carregar_sons_motor(modelo, vidro_aberto)