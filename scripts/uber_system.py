import random
import math
import pygame

class UberSystem:
    def __init__(self, audio, menu_principal):
        self.audio = audio
        self.menu = menu_principal # Referência para ler e salvar o dinheiro na carteira

        # Estados do Aplicativo
        self.cadastro_feito = False
        self.etapa_cadastro = 1  # 1: Nome, 2: CNH, 3: Placa
        self.cadastro_nome = ""
        self.cadastro_cnh = ""
        self.cadastro_placa = ""

        # Controle de Corrida
        self.estado_app = "MODOLIVRE" # MODOLIVRE, CELULAR_CADASTRO, CELULAR_MENU, ESPERANDO_CORRIDA, CHAMANDO, VIAGEM, CHEGOU
        self.tempo_chamada = 0
        self.nome_passageiro = ""
        self.ganho_corrida = 0.0
        self.nome_destino_rua = "" # Armazena o nome do local/rua de destino real

        # Coordenadas do Destino
        self.destino_x = 0.0
        self.destino_y = 0.0

        self.lista_passageiros = ["Seu Jorge", "Dona Maria", "Marcos Estudante", "Ana do Centro", "Doutor Juliano"]
        
        # BANCO DE DADOS DE DESTINOS REAIS (Baseado rigorosamente nas ruas existentes do mapa.py)
        # Formato: ("Nome falado", "Nome da Rua Interna", X_min, X_max, Y_min, Y_max)
        self.destinos_reais = [
            ("Avenida Central Leste", "Avenida Central", 200, 450, -10, 10),
            ("Avenida Central Oeste", "Avenida Central", -450, -200, -10, 10),
            ("Rua dos Buracos Norte", "Rua dos Buracos", -15, 15, -450, -200),
            ("Rua dos Buracos Sul", "Rua dos Buracos", -15, 15, 200, 450),
            ("Beco do Chevette", "Beco do Chevette", 40, 180, -15, 15)
        ]

    def abrir_celular(self):
        if self.estado_app in ["MODOLIVRE", "CHEGOU"]:
            if not self.cadastro_feito:
                self.estado_app = "CELULAR_CADASTRO"
                self.etapa_cadastro = 1
                self.cadastro_nome = ""
                self.audio.falar("Aplicativo Uber Driver. Para começar, digite seu nome e pressione Enter.")
            else:
                self.estado_app = "CELULAR_MENU"
                self.audio.falar(f"Olá {self.cadastro_nome}. Menu do Aplicativo. Pressione Espaço para ficar Online e procurar corridas.")
        elif self.estado_app in ["CELULAR_MENU", "CELULAR_CADASTRO"]:
            self.estado_app = "MODOLIVRE"
            self.audio.falar("Celular guardado.")

    def tratar_entrada_texto(self, evento):
        if evento.key == pygame.K_RETURN:
            if len(self.cadastro_nome.strip()) > 0:
                self.etapa_cadastro = 2
                self.audio.falar(f"Nome registrado: {self.cadastro_nome}. Agora digite o número da sua CNH usando o teclado numérico de 1 a 5 e pressione Espaço no final.")
            else:
                self.audio.falar("Nome inválido. Digite seu nome.")
        elif evento.key == pygame.K_BACKSPACE:
            self.cadastro_nome = self.cadastro_nome[:-1]
            if self.cadastro_nome:
                self.audio.falar(self.cadastro_nome[-1])
            else:
                self.audio.falar("Texto vazio.")
        else:
            caractere = evento.unicode
            if caractere.isalnum() or caractere == " ":
                self.cadastro_nome += caractere
                self.audio.falar(caractere)

    def tratar_teclado_cadastro(self, tecla):
        mapa_teclas = {
            pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3", pygame.K_4: "4", pygame.K_5: "5",
            pygame.K_KP1: "1", pygame.K_KP2: "2", pygame.K_KP3: "3", pygame.K_KP4: "4", pygame.K_KP5: "5"
        }
        if tecla in mapa_teclas:
            num = mapa_teclas[tecla]
            if self.etapa_cadastro == 2:
                self.cadastro_cnh += num
                self.audio.falar(num)
            elif self.etapa_cadastro == 3:
                self.cadastro_placa += num
                self.audio.falar(num)

    def confirmar_acao_espaco(self, tempo_atual, carro, mapa=None):
        # Trata confirmação de etapas numéricas do cadastro
        if self.estado_app == "CELULAR_CADASTRO":
            if self.etapa_cadastro == 2:
                if len(self.cadastro_cnh) >= 3:
                    self.etapa_cadastro = 3
                    self.audio.falar("CNH aceita. Agora digite os números da placa do seu veículo e pressione Espaço para concluir.")
                else:
                    self.audio.falar("CNH muito curta. Digite mais números.")
            elif self.etapa_cadastro == 3:
                if len(self.cadastro_placa) >= 3:
                    self.cadastro_feito = True
                    self.menu.motorista_nome = self.cadastro_nome
                    self.menu.salvar_progresso()
                    self.estado_app = "CELULAR_MENU"
                    self.audio.falar("Cadastro aprovado com sucesso! Você já pode trabalhar. Pressione Espaço para ficar Online.")
                else:
                    self.audio.falar("Placa inválida. Digite mais números.")
            return

        # Ficar Online / Buscar Corridas
        if self.estado_app == "CELULAR_MENU":
            self.estado_app = "ESPERANDO_CORRIDA"
            self.tempo_chamada = tempo_atual
            self.audio.falar("Você está Online. Aguardando chamada de passageiro...")
            return

        # Aceitar Corrida
        if self.estado_app == "CHAMANDO":
            self.estado_app = "VIAGEM"
            self.audio.falar(f"Corrida aceita! O passageiro {self.nome_passageiro} entrou no carro. Destino configurado para: {self.nome_destino_rua}. Siga asfalto ou estradas e use a tecla F para ouvir o GPS.")
            return

    def falar_gps(self, carro):
        if self.estado_app == "VIAGEM":
            dx = self.destino_x - carro.x
            dy = self.destino_y - carro.y
            distancia = math.sqrt(dx**2 + dy**2)
            
            # Descobre a direção cardeal aproximada para guiar o jogador sem fazê-lo cortar caminho
            direcao_texto = ""
            if abs(dx) > abs(dy):
                direcao_texto = "Siga para o Leste" if dx > 0 else "Siga para o Oeste"
            else:
                direcao_texto = "Siga para o Sul" if dy > 0 else "Siga para o Norte"
                
            self.audio.falar(f"GPS: Destino na {self.nome_destino_rua}. Faltam {int(distancia)} metros. {direcao_texto}.")
        else:
            self.audio.falar("O GPS está desligado pois você não está em uma corrida ativa.")

    def atualizar_logica(self, tempo_atual, carro, gerar_bipe_func):
        # Lógica de toque de chamada aleatória
        if self.estado_app == "ESPERANDO_CORRIDA":
            if tempo_atual - self.tempo_chamada > random.randint(4000, 8000):
                self.estado_app = "CHAMANDO"
                self.tempo_chamada = tempo_atual
                self.nome_passageiro = random.choice(self.lista_passageiros)
                
                # SELEÇÃO DE DESTINO REAL: Escolhe um local mapeado de verdade
                destino_selecionado = random.choice(self.destinos_reais)
                self.nome_destino_rua = destino_selecionado[0]
                
                # Sorteia uma coordenada real VÁLIDA estritamente de dentro dos limites daquela rua
                self.destino_x = float(random.randint(destino_selecionado[2], destino_selecionado[3]))
                self.destino_y = float(random.randint(destino_selecionado[4], destino_selecionado[5]))
                
                # Calcula a distância aproximada para estipular o preço justo
                dist_inicial = math.sqrt((self.destino_x - carro.x)**2 + (self.destino_y - carro.y)**2)
                self.ganho_corrida = round(15.0 + (dist_inicial * 0.12), 2)
                
                self.audio.falar(f"Atenção! Chamada recebida de {self.nome_passageiro}. Destino: {self.nome_destino_rua}. Valor: {self.ganho_corrida} reais. Pressione a barra de ESPAÇO para aceitar!")

        if self.estado_app == "CHAMANDO":
            # Bipe de celular tocando
            if tempo_atual % 1000 < 100:
                gerar_bipe_func(880, 120, 0.8, 0.8).play()
            if tempo_atual - self.tempo_chamada > 10000: # Cancela se demorar mais de 10 segundos para aceitar
                self.estado_app = "CELULAR_MENU"
                self.audio.falar("A chamada expirou porque você demorou para aceitar. Você continua Online.")
                self.tempo_chamada = tempo_atual

        # Monitoramento da viagem em andamento
        if self.estado_app == "VIAGEM":
            dx = self.destino_x - carro.x
            dy = self.destino_y - carro.y
            distancia_restante = math.sqrt(dx**2 + dy**2)

            # Efeito sonoro sutil de GPS guiando (Bipe Estéreo conforme o lado)
            if tempo_atual % 3000 < 30:
                if dx > 30: # Destino está para a direita
                    gerar_bipe_func(950, 80, 0.15, 1.0).play() 
                elif dx < -30: # Destino está para a esquerda
                    gerar_bipe_func(950, 80, 1.0, 0.15).play() 
                else:
                    gerar_bipe_func(600, 40, 0.4, 0.4).play() 

            if carro.cortando_giro and tempo_atual % 4000 < 20:
                self.audio.falar("O cliente reclama do barulho do motor!")

            if tempo_atual % 7000 < 20 and distancia_restante > 30:
                # O próprio GPS avisa o nome da rua de destino durante o trajeto de tempo em tempo
                self.audio.falar(f"GPS: Siga em direção a {self.nome_destino_rua}. Faltam {int(distancia_restante)} metros.")

            # Chegada no Destino (Ajustado para 30 metros de tolerância para ficar confortável estacionar na rua correta)
            if distancia_restante <= 30.0:
                self.estado_app = "CHEGOU"
                carro.velocidade = 0.0
                
                # ADICIONANDO O DINHEIRO NA CARTEIRA REAL DO JOGO!
                creditos_ganhos = int(self.ganho_corrida)
                self.menu.creditos += creditos_ganhos
                self.menu.salvar_progresso() # Grava no arquivo .ini de save automaticamente!
                
                self.audio.falar(f"Viagem concluída! Você chegou certinho na {self.nome_destino_rua}. Você recebeu {self.ganho_corrida} reais. Seu saldo agora é de {self.menu.creditos} créditos. Abra o celular com P para buscar a próxima.")
                self.tempo_chamada = tempo_atual