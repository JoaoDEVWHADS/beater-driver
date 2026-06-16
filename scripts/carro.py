import pygame
import math
import random

class Carro:

    def __init__(self, audio):
        self.audio = audio

        # Estado do veículo e posição no mapa real (Coordenadas X, Y)
        self.no_carro = False
        self.motor_ligado = False
        self.x = 0.0
        self.y = 0.0
        self.angulo = 0 # 0 = Norte, 90 = Leste, 180 = Sul, 270 = Oeste
        
        # Sistema mecânico de carro velho
        self.temperatura_motor = 20.0  
        self.tempo_segurando_chave = 0.0  
        self.ultimo_tque_arranque = 0
        self.tentando_partida = False

        # --- MOTOR 1.6 OHC AUTOMÁTICO REALISTA ---
        self.velocidade = 0.0
        self.rpm_lenta = 750  
        self.rpm = 0.0 
        self.rpm_max = 6500  
        self.rev_limiter = 6000  

        self.acelerador = 0.0
        self.acelerador_antigo = 0.0 

        # Câmbio Automático P R N D
        self.modos_cambio = ["P", "R", "N", "D"]
        self.indice_modo = 0  
        self.modo_atual = self.modos_cambio[self.indice_modo]
        self.marcha_automatica = 1 
        
        # Gerenciador de trocas automáticas (Histerese para evitar travamentos)
        self.tempo_ultima_troca = 0 
        
        # Relações de marcha reais do Chevette automático de 3 velocidades
        self.config_marchas_auto = {
            1: {"vel_max": 50.0,  "forca": 0.48, "rpm_up": 4500},
            2: {"vel_max": 95.0,  "forca": 0.28, "rpm_up": 5000, "rpm_down": 1800},
            3: {"vel_max": 140.0, "forca": 0.16, "rpm_down": 2000}
        }

        self.som_ligar = "audio/carro_motor/ligar.wav"
        self.som_marcha = "audio/carro_motor/marcha.wav"
        self.som_freio = "audio/carro_motor/freio.wav"

        self.cortando_giro = False
        self.ultimo_pipoco = 0
        self.pipocos_restantes_tirada = 0
        self.ultimo_pipoco_tirada = 0

    def entrar_sair(self):
        self.no_carro = not self.no_carro
        if self.no_carro:
            self.audio.falar("Você entrou no Chevette")
        else:
            if self.motor_ligado:
                self.ligar_desligar_motor(desligar_forcado=True)
            self.velocidade = 0
            self.audio.falar("Você saiu do Chevette")

    def ligar_desligar_motor(self, desligar_forcado=False, motivo=""):
        if self.motor_ligado or desligar_forcado:
            self.motor_ligado = False
            self.tentando_partida = False  
            self.rpm = 0
            self.velocidade = 0
            self.tempo_segurando_chave = 0.0  
            
            self.audio.motor_stop()
            if hasattr(self.audio, 'canal_arranque'): 
                self.audio.canal_arranque.stop()
            
            if motivo: 
                self.audio.falar(motivo)
            else: 
                self.audio.falar("Motor do Chevette desligado")
                
            if random.random() < 0.80: 
                self.audio.tocar_pipoco_unico()
        else:
            if self.modo_atual in ["P", "N"]:
                self.tentando_partida = True
            else:
                self.audio.falar("O motor não liga! Coloque o câmbio automático em P ou N.")

    def subir_marcha(self):
        if self.indice_modo > 0:
            self.indice_modo -= 1
            self.modo_atual = self.modos_cambio[self.indice_modo]
            self.marcha_automatica = 1 
            self.audio.tocar(self.som_marcha)
            self.audio.falar(f"Câmbio em {self.modo_atual}")

    def reduzir_marcha(self):
        if self.indice_modo < len(self.modos_cambio) - 1:
            self.indice_modo += 1
            self.modo_atual = self.modos_cambio[self.indice_modo]
            self.marcha_automatica = 1
            self.audio.tocar(self.som_marcha)
            self.audio.falar(f"Câmbio em {self.modo_atual}")

    def ler_item_painel(self, numero_tecla):
        if numero_tecla == pygame.K_1:
            self.audio.falar(f"Motor ligado: {'Sim' if self.motor_ligado else 'Não'}")
        elif numero_tecla == pygame.K_2:
            if self.modo_atual == "D":
                self.audio.falar(f"Câmbio em Drive, marcha {self.marcha_automatica}")
            else:
                self.audio.falar(f"Câmbio na posição {self.modo_atual}")
        elif numero_tecla == pygame.K_3:
            self.audio.falar(f"Velocidade atual: {int(self.velocidade)} quilômetros por hora")
        elif numero_tecla == pygame.K_4:
            self.audio.falar(f"Giro do motor: {int(self.rpm)} R P M")
        elif numero_tecla == pygame.K_5:
            self.audio.falar(f"Temperatura da água: {int(self.temperatura_motor)} graus")

    def atualizar(self, teclas, tecla_partida_segurada):
        tempo_atual = pygame.time.get_ticks()

        if not self.motor_ligado and self.temperatura_motor > 20.0:
            self.temperatura_motor -= 0.005

        # Partida rústica com chave segurada
        if self.no_carro and not self.motor_ligado and tecla_partida_segurada:
            if self.modo_atual not in ["P", "N"]:
                return

            self.audio.tocar_som_start_loop(self.som_ligar)
            acelerando = teclas[pygame.K_w]
            self.acelerador = min(1.0, self.acelerador + 0.05) if acelerando else 0.0

            if tempo_atual - self.ultimo_tque_arranque > 140:
                giro_base_arranque = random.randint(180, 350)
                if acelerando:
                    if random.random() < 0.50:
                        giro_base_arranque += random.randint(800, 2200) 
                        if random.random() < 0.40: self.audio.tocar_pipoco_corte()
                
                self.rpm = giro_base_arranque
                self.audio.motor_rpm_velho(self.rpm / self.rpm_max, falhando=True)
                
                tempo_necessario = 3500 if acelerando else 5500
                self.tempo_segurando_chave += 140
                
                if self.tempo_segurando_chave >= tempo_necessario:
                    self.motor_ligado = True
                    self.tentando_partida = False  
                    self.tempo_segurando_chave = 0
                    if hasattr(self.audio, 'canal_arranque'): self.audio.canal_arranque.fadeout(200)
                    else: self.audio.parar_som_start()
                        
                    self.audio.motor_start()
                    self.audio.tocar_pipoco_unico() 
                    self.rpm = self.rpm_lenta + (1500 if acelerando else 400)
                self.ultimo_tque_arranque = tempo_atual
        else:
            if not self.motor_ligado:
                self.tempo_segurando_chave = 0
                self.rpm = max(0, self.rpm - 60)
                if not tecla_partida_segurada: self.audio.parar_som_start()

        # Funcionamento mecânico ativo com o motor girando
        if self.motor_ligado:
            if self.temperatura_motor < 90.0:
                self.temperatura_motor += 0.02 + (self.rpm / self.rpm_max) * 0.05

            acelerando = teclas[pygame.K_w]
            self.acelerador_antigo = self.acelerador

            if acelerando:
                self.acelerador = min(1.0, self.acelerador + 0.03) 
            else:
                self.acelerador = max(0.0, self.acelerador - 0.08)

            if self.acelerador_antigo > 0.6 and self.acelerador == 0.0 and self.rpm > 3000:
                self.pipocos_restantes_tirada = random.randint(1, 3)
                self.ultimo_pipoco_tirada = tempo_atual
                self.audio.tocar_pipoco_unico() 

            # Simulação física da oscilação da marcha lenta de motor velho
            tempo_osc = tempo_atual / 100.0
            variacao_lenta = (math.sin(tempo_osc) * 45) + (math.cos(tempo_osc * 2.4) * 20)
            if self.acelerador == 0.0:
                if random.random() < 0.12: variacao_lenta -= random.randint(80, 160)
            lenta_atual = self.rpm_lenta + variacao_lenta

            # ---- MODOS DE CÂMBIO ----
            if self.modo_atual in ["P", "N"]:
                alvo_rpm = lenta_atual + (self.acelerador * (self.rpm_max - lenta_atual))
                self.rpm += (alvo_rpm - self.rpm) * 0.18
                self.velocidade = max(0.0, self.velocidade * 0.95) if self.modo_atual == "N" else 0.0

            elif self.modo_atual == "R":
                limite_re = 35.0
                rpm_roda = lenta_atual + ((self.velocidade / limite_re) * (self.rev_limiter - 1500 - lenta_atual))
                alvo_rpm = rpm_roda + (self.acelerador * 1500.0)
                self.rpm += (alvo_rpm - self.rpm) * 0.12
                
                if acelerando and not self.cortando_giro:
                    self.velocidade += 0.35 * (0.2 + self.acelerador * 0.8)
                self.velocidade = max(0.0, min(self.velocidade, limite_re))

            elif self.modo_atual == "D":
                cfg = self.config_marchas_auto[self.marcha_automatica]
                limite_marcha = cfg["vel_max"]
                forca_marcha = cfg["forca"]

                # Física do Conversor de Torque
                rpm_roda = lenta_atual + ((self.velocidade / limite_marcha) * (self.rev_limiter - 1000 - lenta_atual))
                alvo_rpm = rpm_roda + (self.acelerador * 1600.0)
                self.rpm += (alvo_rpm - self.rpm) * 0.12

                # Troca de Marchas Inteligente com Verificação de Segurança (Impede o jogo de fechar)
                if tempo_atual - self.tempo_ultima_troca > 1500:
                    # Passar marcha acima (Apenas se existir "rpm_up" configurado na marcha atual)
                    if "rpm_up" in cfg and self.rpm > cfg["rpm_up"] and self.marcha_automatica < 3:
                        self.marcha_automatica += 1
                        self.tempo_ultima_troca = tempo_atual
                        self.audio.tocar(self.som_marcha)
                        self.rpm -= 1500
                    # Reduzir marcha (Kickdown ou desaceleração extrema)
                    elif "rpm_down" in cfg and self.rpm < cfg["rpm_down"] and self.marcha_automatica > 1:
                        self.marcha_automatica -= 1
                        self.tempo_ultima_troca = tempo_atual
                        self.audio.tocar(self.som_marcha)
                        self.rpm += 1200

                if acelerando and not self.cortando_giro:
                    self.velocidade += forca_marcha * (0.20 + self.acelerador * 0.80)
                
                self.velocidade = max(0.0, min(self.velocidade, limite_marcha))

            # Limitador de Giro
            if self.rpm >= self.rev_limiter and acelerando:
                self.cortando_giro = True
                self.rpm = self.rev_limiter - random.randint(250, 500)
                if tempo_atual - self.ultimo_pipoco > 65: 
                    self.audio.tocar_pipoco_corte()
                    self.ultimo_pipoco = tempo_atual
            else:
                self.cortando_giro = False

            # Frenagem ativa
            if teclas[pygame.K_s]:
                self.velocidade = max(0.0, self.velocidade - 0.75)
                if self.velocidade > 1.0 and tempo_atual % 300 < 30:
                    self.audio.tocar(self.som_freio)

            if self.modo_atual in ["D", "R"] and not acelerando:
                self.velocidade *= 0.988 

            if self.rpm > self.rpm_max: self.rpm = self.rpm_max - 50
            if self.rpm < lenta_atual - 150: self.rpm = lenta_atual - 150

        # Direção Ágil
        if teclas[pygame.K_a]: 
            self.angulo = (self.angulo - 6) % 360
        if teclas[pygame.K_d]: 
            self.angulo = (self.angulo + 6) % 360

        # Movimentação Vetorial
        if self.velocidade > 0:
            radianos = math.radians(self.angulo)
            fator_movimento = 0.08 
            
            if self.modo_atual == "R":
                self.x -= math.sin(radianos) * self.velocidade * fator_movimento
                self.y += math.cos(radianos) * self.velocidade * fator_movimento
            else:
                self.x += math.sin(radianos) * self.velocidade * fator_movimento
                self.y -= math.cos(radianos) * self.velocidade * fator_movimento

        if self.pipocos_restantes_tirada > 0:
            if tempo_atual - self.ultimo_pipoco_tirada > random.randint(70, 130):
                self.audio.tocar_pipoco_corte()
                self.pipocos_restantes_tirada -= 1
                self.ultimo_pipoco_tirada = tempo_atual

        if self.motor_ligado:
            rpm_normal = max(0.0, min(1.0, (self.rpm / self.rpm_max) * 1.10))
            self.audio.motor_rpm_velho(rpm_normal, self.cortando_giro)