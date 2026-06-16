import pygame
import sys
import os
import configparser
import numpy as np
import platform

class MenuPrincipal:
    def __init__(self, audio_engine):
        self.audio = audio_engine
        
        # Caminho do arquivo de save em AppData/Roaming ou ~/.config
        if platform.system() == "Windows":
            base_dir = os.environ.get("APPDATA")
            if not base_dir:
                base_dir = os.path.expanduser("~/AppData/Roaming")
        else:
            base_dir = os.path.expanduser("~/.config")
            
        self.pasta_save = os.path.join(base_dir, "RideShareBrazil")
        self.arquivo_save = os.path.join(self.pasta_save, "progresso.ini")
        
        # Dados de Progresso do Jogador (Carregados ou Padrão)
        self.creditos = 1100  
        self.carros_comprados = ["chevette"]
        self.motorista_nome = "" # Armazena o nome customizado do motorista
        
        self.carregar_progresso()

        # Definição dos Carros do Jogo (Banco de dados interno - Carregado Dinamicamente!)
        self.dados_carros = {}
        self.lista_concessionaria = []
        self.indice_concessionaria = 0

        # Escanear pasta de carros dinamicamente
        from scripts.config import obter_caminho_recurso
        pasta_carros = obter_caminho_recurso("audio/carros")
        if os.path.exists(pasta_carros):
            for item in sorted(os.listdir(pasta_carros)):
                caminho_item = os.path.join(pasta_carros, item)
                if os.path.isdir(caminho_item):
                    ini_path = os.path.join(caminho_item, "carro.ini")
                    if os.path.exists(ini_path):
                        try:
                            car_config = configparser.ConfigParser()
                            car_config.read(ini_path, encoding='utf-8')
                            if 'CARRO' in car_config:
                                car_id = item
                                self.dados_carros[car_id] = {
                                    "nome": car_config.get('CARRO', 'nome', fallback=car_id.capitalize()),
                                    "preco": car_config.getint('CARRO', 'preco', fallback=1000),
                                    "info_concessionaria": car_config.get('CARRO', 'info_concessionaria', fallback=""),
                                    "historico": car_config.get('CARRO', 'historico', fallback=""),
                                    "pecas": [p.strip() for p in car_config.get('CARRO', 'pecas', fallback="").split(",") if p.strip()]
                                }
                                self.lista_concessionaria.append(car_id)
                        except Exception as e:
                            print(f"Erro ao ler {ini_path}: {e}")

        # Se por algum motivo não carregou nada, adiciona um fallback básico
        if not self.dados_carros:
            self.dados_carros["chevette"] = {
                "nome": "Chevette Rústico",
                "preco": 1000,
                "info_concessionaria": "Chevette Rústico. Preço: Mil créditos. Única unidade em estoque!",
                "historico": "Chevette adaptado.",
                "pecas": ["Motor 1.0"]
            }
            self.lista_concessionaria.append("chevette")

        # Opções do menu principal
        self.opcoes = []
        self.atualizar_opcoes_menu()
        self.indice_selecionado = 0
        
        # Cores da Interface
        self.COR_FUNDO = (15, 15, 20)
        self.COR_TEXTO_NORMAL = (150, 150, 150)
        self.COR_TEXTO_SELECIONADO = (255, 215, 0)
        
        self.fonte = pygame.font.SysFont("Arial", 30)
        self.fonte_titulo = pygame.font.SysFont("Arial", 40, bold=True)

    def tem_algum_carro(self):
        return len(self.carros_comprados) > 0

    def atualizar_opcoes_menu(self):
        if self.tem_algum_carro():
            self.opcoes = ["Carreira", "Carteira", "Garagem", "Concessionária", "Oficina", "Testar os Autofalantes", "Configuração", "Sair"]
        else:
            self.opcoes = ["Carreira", "Carteira", "Concessionária", "Oficina", "Testar os Autofalantes", "Configuração", "Sair"]

    def salvar_progresso(self):
        if not os.path.exists(self.pasta_save):
            os.makedirs(self.pasta_save)
        config = configparser.ConfigParser()
        config['PROGRESSO'] = {
            'creditos': str(self.creditos),
            'carros_comprados': ",".join(self.carros_comprados),
            'motorista_nome': str(self.motorista_nome)
        }
        with open(self.arquivo_save, 'w') as f:
            config.write(f)

    def carregar_progresso(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.arquivo_save):
            config.read(self.arquivo_save)
            if 'PROGRESSO' in config:
                self.creditos = config.getint('PROGRESSO', 'creditos', fallback=1100)
                carros_str = config.get('PROGRESSO', 'carros_comprados', fallback="chevette")
                self.carros_comprados = [c.strip() for c in os.path.expandvars(carros_str).split(",") if c.strip()]
                if "chevette" not in self.carros_comprados:
                    self.carros_comprados.append("chevette")
                self.motorista_nome = config.get('PROGRESSO', 'motorista_nome', fallback="")
        else:
            self.salvar_progresso()

    def gerar_bipe_menu(self, frequencia, duracao_ms):
        amostragem = 44100
        num_amostras = int(amostragem * (duracao_ms / 1000.0))
        t = np.linspace(0, duracao_ms / 1000.0, num_amostras, endpoint=False)
        sinal = np.sin(2 * np.pi * frequencia * t) * 16384
        sinal = sinal.astype(np.int16)
        matriz_estereo = np.column_stack((sinal, sinal))
        return pygame.sndarray.make_sound(matriz_estereo)

    def falar_opcao_atual(self):
        opcao = self.opcoes[self.indice_selecionado]
        self.audio.falar(opcao)

    def abrir_detalhes_carro(self, id_carro, tela, relogio):
        carro = self.dados_carros[id_carro]
        self.audio.falar(f"Opções para {carro['nome']}. Escolha Mecânica ou Histórico.")
        
        opcoes_detalhe = ["Mecânica", "Histórico"]
        idx_detalhe = 0
        self.audio.falar(opcoes_detalhe[idx_detalhe])
        
        bipe_mover = self.gerar_bipe_menu(600, 50)
        bipe_conf = self.gerar_bipe_menu(900, 150)
        
        executando = True
        while executando:
            tela.fill((25, 30, 45))
            txt_tit = self.fonte_titulo.render(carro['nome'].upper(), True, (255, 255, 255))
            tela.blit(txt_tit, (40, 30))
            
            for i, opt in enumerate(opcoes_detalhe):
                if i == idx_detalhe:
                    texto = self.fonte.render(f"> {opt} <", True, self.COR_TEXTO_SELECIONADO)
                else:
                    texto = self.fonte.render(f"  {opt}", True, self.COR_TEXTO_NORMAL)
                tela.blit(texto, (50, 140 + (i * 50)))
                
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif evento.type == pygame.KEYDOWN:
                    if evento.key in [pygame.K_DOWN, pygame.K_UP, pygame.K_s, pygame.K_w]:
                        idx_detalhe = (idx_detalhe + 1) % len(opcoes_detalhe)
                        bipe_mover.play()
                        self.audio.falar(opcoes_detalhe[idx_detalhe])
                        
                    elif evento.key == pygame.K_RETURN or evento.key == pygame.K_KP_ENTER:
                        bipe_conf.play()
                        escolha = opcoes_detalhe[idx_detalhe]
                        
                        if escolha == "Histórico":
                            self.audio.falar(carro["historico"])
                        elif escolha == "Mecânica":
                            texto_pecas = "Componentes atuais instalados: " + ", ".join(carro["pecas"])
                            self.audio.falar(texto_pecas)
                            
                    elif evento.key == pygame.K_ESCAPE:
                        executando = False
                        
            pygame.display.flip()
            relogio.tick(60)

    def abrir_garagem(self, tela, relogio):
        bipe_mover = self.gerar_bipe_menu(600, 50)
        bipe_conf = self.gerar_bipe_menu(900, 150)
        
        meus_carros_ids = self.carros_comprados
        
        idx_garagem = 0
        id_atual = meus_carros_ids[idx_garagem]
        self.audio.falar(f"Garagem aberta. Carro selecionado: {self.dados_carros[id_atual]['nome']}. Pressione Enter para inspecionar.")

        executando = True
        while executando:
            tela.fill((30, 25, 35))
            txt_titulo = self.fonte_titulo.render("SUA GARAGEM", True, (255, 255, 255))
            tela.blit(txt_titulo, (40, 30))
            
            for i, cid in enumerate(meus_carros_ids):
                nome_c = self.dados_carros[cid]["nome"]
                if i == idx_garagem:
                    texto = self.fonte.render(f"> {nome_c} <", True, self.COR_TEXTO_SELECIONADO)
                else:
                    texto = self.fonte.render(f"  {nome_c}", True, self.COR_TEXTO_NORMAL)
                tela.blit(texto, (50, 120 + (i * 45)))
                
            txt_ajuda = self.fonte.render("[Enter] Abrir Opções  [ESC] Voltar", True, (100, 100, 100))
            tela.blit(txt_ajuda, (30, 350))
            
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif evento.type == pygame.KEYDOWN:
                    if evento.key in [pygame.K_DOWN, pygame.K_s]:
                        idx_garagem = (idx_garagem + 1) % len(meus_carros_ids)
                        bipe_mover.play()
                        self.audio.falar(self.dados_carros[meus_carros_ids[idx_garagem]]['nome'])
                    elif evento.key in [pygame.K_UP, pygame.K_w]:
                        idx_garagem = (idx_garagem - 1) % len(meus_carros_ids)
                        bipe_mover.play()
                        self.audio.falar(self.dados_carros[meus_carros_ids[idx_garagem]]['nome'])
                    elif evento.key == pygame.K_RETURN or evento.key == pygame.K_KP_ENTER:
                        bipe_conf.play()
                        pygame.time.wait(150)
                        self.abrir_detalhes_carro(meus_carros_ids[idx_garagem], tela, relogio)
                        self.audio.falar("Voltando para a lista da garagem.")
                    elif evento.key == pygame.K_ESCAPE:
                        self.audio.falar("Voltando ao menu principal.")
                        executando = False
                        
            pygame.display.flip()
            relogio.tick(60)

    def abrir_concessionaria(self, tela, relogio):
        self.audio.falar("Concessionária. Use as setas laterais para navegar.")
        bipe_mover = self.gerar_bipe_menu(600, 50)
        
        id_focado = self.lista_concessionaria[self.indice_concessionaria]
        self.audio.falar(self.dados_carros[id_focado]["info_concessionaria"])
        
        executando = True
        while executando:
            tela.fill((20, 30, 40))
            txt_titulo = self.fonte_titulo.render("CONCESSIONÁRIA", True, (255, 255, 255))
            tela.blit(txt_titulo, (40, 30))
            
            id_focado = self.lista_concessionaria[self.indice_concessionaria]
            carro = self.dados_carros[id_focado]
            
            ja_comprado = id_focado in self.carros_comprados
            status_txt = "Já Comprado" if ja_comprado else "Disponível!"
            if id_focado == "chevette" and "chevette" not in self.carros_comprados:
                status_txt = "Única Unidade!"
            
            txt_nome = self.fonte.render(f"Carro: {carro['nome']}", True, self.COR_TEXTO_SELECIONADO)
            txt_preco = self.fonte.render(f"Preço: {carro['preco']} Créditos", True, self.COR_TEXTO_NORMAL)
            txt_status = self.fonte.render(f"Estoque: {status_txt}", True, (255, 100, 100) if ja_comprado else (100, 255, 100))
            
            tela.blit(txt_nome, (50, 120))
            tela.blit(txt_preco, (50, 170))
            tela.blit(txt_status, (50, 220))
            
            txt_ajuda = self.fonte.render("[Setas Laterais] Mudar  [Enter] Comprar  [ESC] Voltar", True, (120, 120, 120))
            tela.blit(txt_ajuda, (20, 350))

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif evento.type == pygame.KEYDOWN:
                    if evento.key in [pygame.K_RIGHT, pygame.K_d]:
                        self.indice_concessionaria = (self.indice_concessionaria + 1) % len(self.lista_concessionaria)
                        bipe_mover.play()
                        id_focado = self.lista_concessionaria[self.indice_concessionaria]
                        self.audio.falar(self.dados_carros[id_focado]["info_concessionaria"])
                        
                    elif evento.key in [pygame.K_LEFT, pygame.K_a]:
                        self.indice_concessionaria = (self.indice_concessionaria - 1) % len(self.lista_concessionaria)
                        bipe_mover.play()
                        id_focado = self.lista_concessionaria[self.indice_concessionaria]
                        self.audio.falar(self.dados_carros[id_focado]["info_concessionaria"])
                    
                    elif evento.key == pygame.K_RETURN or evento.key == pygame.K_KP_ENTER:
                        id_focado = self.lista_concessionaria[self.indice_concessionaria]
                        carro = self.dados_carros[id_focado]
                        
                        ja_comprado = id_focado in self.carros_comprados
                        
                        if ja_comprado:
                            self.gerar_bipe_menu(400, 150).play()
                            self.audio.falar(f"Você já tem o {carro['nome']} na sua garagem!")
                        elif self.creditos >= carro['preco']:
                            self.creditos -= carro['preco']
                            self.carros_comprados.append(id_focado)
                            
                            self.salvar_progresso()
                            self.atualizar_opcoes_menu()
                            self.gerar_bipe_menu(900, 300).play()
                            self.audio.falar(f"Sucesso! Você comprou o {carro['nome']}! Ele foi enviado para a sua garagem.")
                        else:
                            self.gerar_bipe_menu(400, 150).play()
                            self.audio.falar("Saldo insuficiente.")
                            
                    elif evento.key == pygame.K_ESCAPE:
                        self.audio.falar("Voltando ao menu principal.")
                        executando = False

            pygame.display.flip()
            relogio.tick(60)

    def iniciar(self, tela, relogio):
        self.atualizar_opcoes_menu()
        self.audio.falar("Menu Principal.")
        self.falar_opcao_atual()
        
        bipe_mover = self.gerar_bipe_menu(600, 50)
        bipe_confirmar = self.gerar_bipe_menu(900, 150)

        executando_menu = True
        while executando_menu:
            tela.fill(self.COR_FUNDO)
            txt_titulo = self.fonte_titulo.render("RIDE SHARE: BRAZIL", True, (255, 255, 255))
            tela.blit(txt_titulo, (40, 25))
            
            for i, opcao in enumerate(self.opcoes):
                if i == self.indice_selecionado:
                    texto = self.fonte.render(f"> {opcao} <", True, self.COR_TEXTO_SELECIONADO)
                else:
                    texto = self.fonte.render(f"  {opcao}", True, self.COR_TEXTO_NORMAL)
                tela.blit(texto, (50, 90 + (i * 36)))

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                elif evento.type == pygame.KEYDOWN:
                    if evento.key in [pygame.K_DOWN, pygame.K_s]:
                        self.indice_selecionado = (self.indice_selecionado + 1) % len(self.opcoes)
                        bipe_mover.play()
                        self.falar_opcao_atual()
                        
                    elif evento.key in [pygame.K_UP, pygame.K_w]:
                        self.indice_selecionado = (self.indice_selecionado - 1) % len(self.opcoes)
                        bipe_mover.play()
                        self.falar_opcao_atual()
                        
                    elif evento.key == pygame.K_RETURN or evento.key == pygame.K_KP_ENTER:
                        escolha = self.opcoes[self.indice_selecionado]
                        
                        if escolha in ["Carreira", "Sair"]:
                            bipe_confirmar.play()
                            return escolha
                                
                        elif escolha == "Carteira":
                            bipe_confirmar.play()
                            self.audio.falar(f"Seu saldo atual é de {self.creditos} créditos.")
                            
                        elif escolha == "Concessionária":
                            bipe_confirmar.play()
                            self.abrir_concessionaria(tela, relogio)
                            self.indice_selecionado = 0
                            self.audio.falar("Menu Principal.")
                            self.falar_opcao_atual()
                            
                        elif escolha == "Garagem":
                            bipe_confirmar.play()
                            self.abrir_garagem(tela, relogio)
                            self.indice_selecionado = 0
                            self.audio.falar("Menu Principal.")
                            self.falar_opcao_atual()
                        
                        else:
                            self.gerar_bipe_menu(400, 150).play()
                            self.audio.falar(f"{escolha}, desativado.")

            pygame.display.flip()
            relogio.tick(60)

    def abrir_selecao_carro(self, tela, relogio):
        bipe_mover = self.gerar_bipe_menu(600, 50)
        bipe_conf = self.gerar_bipe_menu(900, 150)
        
        meus_carros_ids = []
        if self.chevette_comprado: meus_carros_ids.append("chevette")
        if self.corsa_comprado: meus_carros_ids.append("corsa")
        if self.gol_comprado: meus_carros_ids.append("gol")
        
        if not meus_carros_ids:
            self.audio.falar("Você não tem nenhum carro comprado na garagem! Visite a concessionária.")
            return None
            
        idx_selecionado = 0
        id_atual = meus_carros_ids[idx_selecionado]
        self.audio.falar(f"Escolha um carro para a carreira. Selecionado: {self.dados_carros[id_atual]['nome']}. Pressione Enter para confirmar.")

        executando = True
        while executando:
            tela.fill((15, 15, 20))
            txt_titulo = self.fonte_titulo.render("ESCOLHA SEU CARRO", True, (255, 255, 255))
            tela.blit(txt_titulo, (40, 30))
            
            for i, cid in enumerate(meus_carros_ids):
                nome_c = self.dados_carros[cid]["nome"]
                if i == idx_selecionado:
                    texto = self.fonte.render(f"> {nome_c} <", True, self.COR_TEXTO_SELECIONADO)
                else:
                    texto = self.fonte.render(f"  {nome_c}", True, self.COR_TEXTO_NORMAL)
                tela.blit(texto, (50, 120 + (i * 45)))
                
            txt_ajuda = self.fonte.render("[Enter] Escolher  [ESC] Cancelar", True, (100, 100, 100))
            tela.blit(txt_ajuda, (30, 350))
            
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif evento.type == pygame.KEYDOWN:
                    if evento.key in [pygame.K_DOWN, pygame.K_s]:
                        idx_selecionado = (idx_selecionado + 1) % len(meus_carros_ids)
                        bipe_mover.play()
                        self.audio.falar(self.dados_carros[meus_carros_ids[idx_selecionado]]['nome'])
                    elif evento.key in [pygame.K_UP, pygame.K_w]:
                        idx_selecionado = (idx_selecionado - 1) % len(meus_carros_ids)
                        bipe_mover.play()
                        self.audio.falar(self.dados_carros[meus_carros_ids[idx_selecionado]]['nome'])
                    elif evento.key == pygame.K_RETURN or evento.key == pygame.K_KP_ENTER:
                        bipe_conf.play()
                        pygame.time.wait(150)
                        return meus_carros_ids[idx_selecionado]
                    elif evento.key == pygame.K_ESCAPE:
                        self.audio.falar("Seleção de carro cancelada.")
                        return None
                        
            pygame.display.flip()
            relogio.tick(60)