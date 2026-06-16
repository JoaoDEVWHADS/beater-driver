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

        self.velocidade = 0.0
        self.rpm_lenta = 750  
        self.rpm = 0.0 
        self.acelerador = 0.0
        self.acelerador_antigo = 0.0 

        # Câmbio Automático P R N D
        self.modos_cambio = ["P", "R", "N", "D"]
        self.indice_modo = 0  
        self.modo_atual = self.modos_cambio[self.indice_modo]
        self.marcha_automatica = 1 
        
        # Gerenciador de trocas automáticas (Histerese para evitar travamentos)
        self.tempo_ultima_troca = 0 
        
        self.som_ligar = "audio/carro_motor/ligar.wav"
        self.som_marcha = "audio/carro_motor/marcha.wav"
        self.som_freio = "audio/carro_motor/freio.wav"

        self.cortando_giro = False
        self.ultimo_pipoco = 0
        self.pipocos_restantes_tirada = 0
        self.ultimo_pipoco_tirada = 0

        # Estado do vidro
        self.vidro_aberto = True
        self.sinalizar_recarga_pistas = False
        self.som_vidro_abrir = "audio/carros/chevette/abrir_vidro.wav"
        self.som_vidro_fechar = "audio/carros/chevette/fechar_vidro.wav"

        # Define o modelo padrão (Chevette) na inicialização
        self.definir_modelo("chevette")

    def toggle_vidro(self):
        if not self.no_carro:
            return
        
        self.vidro_aberto = not self.vidro_aberto
        
        if self.vidro_aberto:
            self.audio.tocar(self.som_vidro_abrir)
            self.audio.falar("Vidro aberto")
        else:
            self.audio.tocar(self.som_vidro_fechar)
            self.audio.falar("Vidro fechado")
            
        # Re-carrega o áudio com o novo estado de abafamento
        self.sons_piso = self.sons_piso_fora if self.vidro_aberto else self.sons_piso_dentro
        self.som_ligar = self.som_ligar_fora if self.vidro_aberto else self.som_ligar_dentro
        self.som_marcha = self.som_marcha_fora if self.vidro_aberto else self.som_marcha_dentro
        self.som_freio = self.som_freio_fora if self.vidro_aberto else self.som_freio_dentro
        
        # Cria uma flag para o main.py recarregar os arquivos de pista
        self.sinalizar_recarga_pistas = True

        if hasattr(self.audio, "definir_estado_vidro"):
            self.audio.definir_estado_vidro(self.vidro_aberto, self.modelo)

    def definir_modelo(self, modelo):
        import os
        import configparser
        from scripts.config import obter_caminho_recurso

        self.modelo = modelo
        
        # Carrega as configurações físicas a partir do carro.ini correspondente
        ini_path = obter_caminho_recurso(f"audio/carros/{modelo}/carro.ini")
        config = configparser.ConfigParser()
        
        if os.path.exists(ini_path):
            try:
                config.read(ini_path, encoding='utf-8')
            except Exception as e:
                print(f"Erro ao ler {ini_path}: {e}")

        # Fallback para Chevette se as chaves ou o arquivo não existirem
        self.nome = config.get('CARRO', 'nome', fallback="Chevette Rústico")
        self.rpm_lenta = config.getint('FISICA', 'rpm_lenta', fallback=750)
        self.rpm_max = config.getint('FISICA', 'rpm_max', fallback=6500)
        self.rev_limiter = config.getint('FISICA', 'rev_limiter', fallback=6000)
        
        # Carrega as marchas
        self.config_marchas_auto = {}
        for m in [1, 2, 3]:
            secao = f"MARCHA_{m}"
            if secao in config:
                self.config_marchas_auto[m] = {
                    "vel_max": config.getfloat(secao, "vel_max"),
                    "forca": config.getfloat(secao, "forca")
                }
                if config.has_option(secao, "rpm_up"):
                    self.config_marchas_auto[m]["rpm_up"] = config.getint(secao, "rpm_up")
                if config.has_option(secao, "rpm_down"):
                    self.config_marchas_auto[m]["rpm_down"] = config.getint(secao, "rpm_down")
            else:
                # Fallbacks manuais padrão caso a seção não exista no INI
                if m == 1:
                    self.config_marchas_auto[m] = {"vel_max": 50.0,  "forca": 0.48, "rpm_up": 4500}
                elif m == 2:
                    self.config_marchas_auto[m] = {"vel_max": 95.0,  "forca": 0.28, "rpm_up": 5000, "rpm_down": 1800}
                elif m == 3:
                    self.config_marchas_auto[m] = {"vel_max": 140.0, "forca": 0.16, "rpm_down": 2000}

        # Configurações de som com fallback individual para o chevette
        def obter_caminho_som(nome_arquivo, subfolder=None):
            nomes_tentativas = [nome_arquivo]
            if nome_arquivo.endswith(".wav"):
                nomes_tentativas.append(nome_arquivo[:-4] + ".ogg")
                nomes_tentativas.append(nome_arquivo[:-4] + ".mp3")
            elif nome_arquivo.endswith(".ogg"):
                nomes_tentativas.append(nome_arquivo[:-4] + ".wav")
                nomes_tentativas.append(nome_arquivo[:-4] + ".mp3")

            if subfolder:
                for nome in nomes_tentativas:
                    caminho_modelo = f"audio/carros/{modelo}/{subfolder}/{nome}"
                    if os.path.exists(obter_caminho_recurso(caminho_modelo)):
                        return caminho_modelo
                for nome in nomes_tentativas:
                    caminho_chevette = f"audio/carros/chevette/{subfolder}/{nome}"
                    if os.path.exists(obter_caminho_recurso(caminho_chevette)):
                        return caminho_chevette
                        
            for nome in nomes_tentativas:
                caminho_modelo = f"audio/carros/{modelo}/{nome}"
                if os.path.exists(obter_caminho_recurso(caminho_modelo)):
                    return caminho_modelo

            return f"audio/carros/chevette/{nome_arquivo}"

        # Sons de ligar, marcha e freio (dentro e fora)
        self.som_ligar_fora = obter_caminho_som("ligar.wav", "fora")
        self.som_ligar_dentro = obter_caminho_som("ligar.wav", "dentro")
        
        self.som_marcha_fora = obter_caminho_som("marcha.wav", "fora")
        self.som_marcha_dentro = obter_caminho_som("marcha.wav", "dentro")
        
        self.som_freio_fora = obter_caminho_som("freio.wav", "fora")
        self.som_freio_dentro = obter_caminho_som("freio.wav", "dentro")
        
        # Atribui os sons mecânicos ativos
        self.som_ligar = self.som_ligar_fora if self.vidro_aberto else self.som_ligar_dentro
        self.som_marcha = self.som_marcha_fora if self.vidro_aberto else self.som_marcha_dentro
        self.som_freio = self.som_freio_fora if self.vidro_aberto else self.som_freio_dentro
        
        # Sons de abrir/fechar vidro
        self.som_vidro_abrir = obter_caminho_som("abrir_vidro.wav")
        self.som_vidro_fechar = obter_caminho_som("fechar_vidro.wav")
        
        # Caminhos de som de pista ambiente organizados em subpastas dentro/fora
        self.sons_piso_fora = {}
        self.sons_piso_dentro = {}
        for tipo in ["asfalto", "terra", "lama", "estrada", "rua"]:
            # 1. Carrega asfalto_loop, terra_loop, etc da seção [CARRO] se houver
            caminho_custom = config.get('CARRO', f'{tipo}_loop', fallback="")
            if caminho_custom and os.path.exists(obter_caminho_recurso(caminho_custom)):
                self.sons_piso_fora[tipo] = caminho_custom
                self.sons_piso_dentro[tipo] = caminho_custom
            else:
                # Caso contrário, busca nas pastas dentro/ e fora/ com suporte a .wav, .ogg e .mp3
                # Para fora:
                caminho_fora = f"audio/pista_ambiente/{tipo}_loop.wav"
                for ext in [".wav", ".ogg", ".mp3"]:
                    teste_fora = f"audio/carros/{modelo}/fora/{tipo}_loop{ext}"
                    if os.path.exists(obter_caminho_recurso(teste_fora)):
                        caminho_fora = teste_fora
                        break
                self.sons_piso_fora[tipo] = caminho_fora
                
                # Para dentro:
                caminho_dentro = None
                for ext in [".wav", ".ogg", ".mp3"]:
                    teste_dentro = f"audio/carros/{modelo}/dentro/{tipo}_loop{ext}"
                    if os.path.exists(obter_caminho_recurso(teste_dentro)):
                        caminho_dentro = teste_dentro
                        break
                
                if not caminho_dentro:
                    for ext in [".wav", ".ogg", ".mp3"]:
                        teste_chev = f"audio/carros/chevette/dentro/{tipo}_loop{ext}"
                        if os.path.exists(obter_caminho_recurso(teste_chev)):
                            caminho_dentro = teste_chev
                            break
                            
                if not caminho_dentro:
                    caminho_dentro = caminho_fora
                    
                self.sons_piso_dentro[tipo] = caminho_dentro
                
        # Define os caminhos ativos no momento
        self.sons_piso = self.sons_piso_fora if self.vidro_aberto else self.sons_piso_dentro
        
        # Notificar o AudioEngine para reconfigurar as amostras de motor para este modelo/carro
        if hasattr(self.audio, "carregar_sons_motor"):
            self.audio.carregar_sons_motor(modelo, self.vidro_aberto)

    def entrar_sair(self):
        self.no_carro = not self.no_carro
        if self.no_carro:
            self.audio.falar(f"Você entrou no {self.nome}")
        else:
            if self.motor_ligado:
                self.ligar_desligar_motor(desligar_forcado=True)
            self.velocidade = 0
            self.audio.falar(f"Você saiu do {self.nome}")

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
                self.audio.falar(f"Motor do {self.nome} desligado")
                
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
        if not self.motor_ligado and tecla_partida_segurada:
            if not self.no_carro:
                self.no_carro = True
                self.audio.falar(f"Você entrou no {self.nome}")

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
                self.audio.motor_rpm_velho(self.rpm / self.rpm_max, falhando=True, acelerador=self.acelerador, modo_atual=self.modo_atual, velocidade=self.velocidade)
                
                tempo_necessario = 2000
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
            self.audio.motor_rpm_velho(rpm_normal, self.cortando_giro, acelerador=self.acelerador, modo_atual=self.modo_atual, velocidade=self.velocidade)