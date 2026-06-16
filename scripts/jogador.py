# scripts/jogador.py
import pygame
import random
import os
from scripts.config import obter_caminho_recurso

class Jogador:
    def __init__(self, audio):
        self.audio = audio
        self.x = 0.0
        self.y = 0.0
        self.velocidade = 2.0
        self.ultimo_passo = 0
        
        # Carrega os efeitos sonoros de passos baseados nas suas pastas
        self.sons_asfalto = []
        self.sons_terra = []
        
        for i in range(1, 4):
            caminho_asfalto = obter_caminho_recurso(f"audio/jogador/passos_asfalto/passo_asfalto_{i}.wav")
            caminho_terra = obter_caminho_recurso(f"audio/jogador/passos_terra/passo_terra_{i}.wav")
            if os.path.exists(caminho_asfalto):
                self.sons_asfalto.append(pygame.mixer.Sound(caminho_asfalto))
            if os.path.exists(caminho_terra):
                self.sons_terra.append(pygame.mixer.Sound(caminho_terra))

    def atualizar(self, teclas, mapa):
        tempo_atual = pygame.time.get_ticks()
        movendo = False

        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            self.y -= self.velocidade
            movendo = True
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            self.y += self.velocidade
            movendo = True
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            self.x -= self.velocidade
            movendo = True
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            self.x += self.velocidade
            movendo = True

        if movendo and tempo_atual - self.ultimo_passo > 450:
            piso, nome_rua = mapa.obter_piso_e_rua(self.x, self.y)
            
            # Escolhe o som aleatório da pasta correspondente
            if piso == "asfalto" and self.sons_asfalto:
                som = random.choice(self.sons_asfalto)
            elif piso == "terra" and self.sons_terra:
                som = random.choice(self.sons_terra)
            else:
                som = None
                
            if som:
                self.audio.canal_passos.play(som)
                
            self.ultimo_passo = tempo_atual